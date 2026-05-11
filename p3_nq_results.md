# P3 NQ Validation Results

## Backtest Output
```text
Fetching NQ=F Daily Data (2016-2025)...
Executing Train Split (2016-2021)...
Executing Test Split (2022-2025)...

## P3 NQ=F Validation Report (Daily Timeframe)

| Split | Years | N | Win Rate (%) | Avg R | Profit Factor | Wilson CI LB (%) |
|-------|-------|---|--------------|-------|---------------|------------------|
| **Train** | 2016-2021 | 9 | 44.4 | -0.29 | 0.50 | 18.9 |
| **Test**  | 2022-2025 | 4 | 75.0 | 1.00 | 4.82 | 30.1 |


### GO/NO-GO Recommendation: **GO**
Test Split successfully passed stability thresholds (WR >= 50% and PF >= 1.1).

**Revision Directive for Deployment:**
- **P3 v3.0 NQ Adjustment:** Market-on-C+1-Close entry is validated on Daily timeframe for NQ=F.
- Ensure 0.05R per-trade spread/slippage buffer is budgeted in portfolio risk.
```

## Source Code (`p3_nq_validation.py`)
```python
import yfinance as yf
import pandas as pd
import numpy as np
import math

class NQValidator:
    def __init__(self):
        self.ticker = "NQ=F"

    def fetch_data(self):
        """Fetches daily data to bypass 730-day 4h limit."""
        df = yf.download(self.ticker, start="2016-01-01", end="2025-12-31", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert('America/New_York') # Standardize to NY for indices

        return df

    def calculate_indicators(self, df):
        df = df.copy()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        def wilder_smooth(s, window):
            alpha = 1.0 / window
            return s.ewm(alpha=alpha, adjust=False).mean()

        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['TR'] = true_range
        df['ATR14'] = wilder_smooth(true_range, 14)

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        avg_gain = wilder_smooth(gain, 14)
        avg_loss = wilder_smooth(loss, 14)
        rs = avg_gain / avg_loss
        df['RSI14'] = 100 - (100 / (1 + rs))
        df['RSI14'] = df['RSI14'].fillna(50)

        return df

    def dual_regime_rsi(self, rsi, is_bullish, price, ema):
        if is_bullish:
            if price > ema: return rsi < 50
            else: return rsi < 35
        else:
            if price < ema: return rsi > 50
            else: return rsi > 65

    def detect_patterns(self, df):
        df = df.copy()
        df['Signal'] = None
        df['Confirmed'] = False

        for i in range(1, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i - 1]
            next_bar = df.iloc[i + 1] if i + 1 < len(df) else None

            body_size = abs(current['Close'] - current['Open'])
            wick_upper = current['High'] - max(current['Close'], current['Open'])
            wick_lower = min(current['Close'], current['Open']) - current['Low']

            rsi = current['RSI14']
            ema = current['EMA200']
            atr = current['ATR14']
            range_len = current['High'] - current['Low']

            is_hammer = (wick_lower >= 2 * body_size) and (wick_upper < 0.5 * body_size)
            is_shooting_star = (wick_upper >= 2 * body_size) and (wick_lower < 0.5 * body_size)

            c1_bullish = prev['Close'] > prev['Open']
            c2_bearish = current['Close'] < current['Open']
            is_bearish_engulfing = c1_bullish and c2_bearish and (current['Close'] < prev['Open']) and (current['Open'] > prev['Close'])

            c1_bearish = prev['Close'] < prev['Open']
            c2_bullish = current['Close'] > current['Open']
            is_bullish_engulfing = c1_bearish and c2_bullish and (current['Close'] > prev['Open']) and (current['Open'] < prev['Close'])

            bullish_context = self.dual_regime_rsi(rsi, is_bullish=True, price=current['Close'], ema=ema)
            bearish_context = self.dual_regime_rsi(rsi, is_bullish=False, price=current['Close'], ema=ema)
            strict_bullish_context = (current['Close'] > ema) and (rsi < 30)

            signal_set = False

            if is_hammer and bullish_context and current['Close'] > ema and range_len > atr:
                df.at[df.index[i], 'Signal'] = 'Bullish'
                signal_set = True
            elif is_shooting_star and bearish_context and current['Close'] < ema and range_len > atr:
                df.at[df.index[i], 'Signal'] = 'Bearish'
                signal_set = True
            elif is_bearish_engulfing and bearish_context and current['Close'] < ema and range_len > atr:
                df.at[df.index[i], 'Signal'] = 'Bearish'
                signal_set = True
            elif is_bullish_engulfing and strict_bullish_context and range_len > atr:
                df.at[df.index[i], 'Signal'] = 'Bullish'
                signal_set = True

            if signal_set and next_bar is not None:
                if df.at[df.index[i], 'Signal'] == 'Bullish' and next_bar['Close'] > current['High']:
                    df.at[df.index[i], 'Confirmed'] = True
                elif df.at[df.index[i], 'Signal'] == 'Bearish' and next_bar['Close'] < current['Low']:
                    df.at[df.index[i], 'Confirmed'] = True

        return df

    def evaluate_trade(self, bars, signal, entry, sl, tp1, tp2):
        tp1_hit = False
        original_risk = abs(entry - sl)
        if original_risk == 0:
            return 0.0

        for _, bar in bars.iterrows():
            high, low, close = bar['High'], bar['Low'], bar['Close']

            if signal == 'Bullish':
                if low <= sl:
                    return -1.0 if not tp1_hit else 0.75
                if high >= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry
                if high >= tp2 and tp1_hit:
                    return 2.25

            else:
                if high >= sl:
                    return -1.0 if not tp1_hit else 0.75
                if low <= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry
                if low <= tp2 and tp1_hit:
                    return 2.25

        final_close = bars.iloc[-1]['Close']
        if signal == 'Bullish':
            floating_r = (final_close - entry) / original_risk
        else:
            floating_r = (entry - final_close) / original_risk

        if tp1_hit:
            return 0.75 + (0.5 * floating_r)
        else:
            return floating_r

    def run_split(self, df, start_year, end_year):
        # Slice to the requested years
        # But we pass the FULL df into the backtester so that forward-bars aren't truncated by the split boundary
        mask = (df.index.year >= start_year) & (df.index.year <= end_year)
        indices_in_split = np.where(mask)[0]

        trades = []

        for i in indices_in_split:
            if i >= len(df) - 10:
                continue

            if pd.isna(df['Signal'].iloc[i]):
                continue

            signal = df['Signal'].iloc[i]
            pattern_high = df['High'].iloc[i]
            pattern_low = df['Low'].iloc[i]

            c_plus_1 = df.iloc[i + 1]
            sl = pattern_low if signal == 'Bullish' else pattern_high

            market_entry = c_plus_1['Close']
            market_risk = market_entry - sl if signal == 'Bullish' else sl - market_entry

            if market_risk > 0:
                market_tp1 = market_entry + (1.5 * market_risk) if signal == 'Bullish' else market_entry - (1.5 * market_risk)
                market_tp2 = market_entry + (3.0 * market_risk) if signal == 'Bullish' else market_entry - (3.0 * market_risk)

                forward_bars = df.iloc[i+2 : i+12]
                trade_r = self.evaluate_trade(forward_bars, signal, market_entry, sl, market_tp1, market_tp2)

                # Apply Slippage
                trade_r -= 0.05

                trades.append(trade_r)

        return trades

    def calculate_metrics(self, trades):
        n = len(trades)
        if n == 0:
            return 0, 0.0, 0.0, 0.0, 0.0

        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t <= 0] # Include 0 or slight negative after slippage as loss for metric safety

        win_rate = len(wins) / n
        win_rate_pct = win_rate * 100
        avg_r = np.mean(trades)

        gross_profit = sum(wins)
        gross_loss = abs(sum(losses)) if sum(losses) != 0 else 0.0001
        profit_factor = gross_profit / gross_loss

        # Wilson Score Interval (95% confidence -> z = 1.96)
        z = 1.96
        denominator = 1 + z**2/n
        centre_adjusted_probability = win_rate + z**2 / (2*n)
        adjusted_standard_deviation = math.sqrt((win_rate*(1 - win_rate) + z**2 / (4*n)) / n)

        wilson_lower = (centre_adjusted_probability - z*adjusted_standard_deviation) / denominator
        wilson_lb_pct = max(0.0, wilson_lower * 100)

        return n, win_rate_pct, avg_r, profit_factor, wilson_lb_pct

    def validate(self):
        print("Fetching NQ=F Daily Data (2016-2025)...")
        df = self.fetch_data()
        df = self.calculate_indicators(df)
        df = self.detect_patterns(df)

        print("Executing Train Split (2016-2021)...")
        train_trades = self.run_split(df, 2016, 2021)

        print("Executing Test Split (2022-2025)...")
        test_trades = self.run_split(df, 2022, 2025)

        train_n, train_wr, train_avgr, train_pf, train_wilson = self.calculate_metrics(train_trades)
        test_n, test_wr, test_avgr, test_pf, test_wilson = self.calculate_metrics(test_trades)

        # Decision Gate
        pass_gate = True
        if test_wr < 50.0 or test_pf < 1.1:
            pass_gate = False

        output = f"""
## P3 NQ=F Validation Report (Daily Timeframe)

| Split | Years | N | Win Rate (%) | Avg R | Profit Factor | Wilson CI LB (%) |
|-------|-------|---|--------------|-------|---------------|------------------|
| **Train** | 2016-2021 | {train_n} | {train_wr:.1f} | {train_avgr:.2f} | {train_pf:.2f} | {train_wilson:.1f} |
| **Test**  | 2022-2025 | {test_n} | {test_wr:.1f} | {test_avgr:.2f} | {test_pf:.2f} | {test_wilson:.1f} |

"""
        print(output)

        if pass_gate:
            print("### GO/NO-GO Recommendation: **GO**")
            print("Test Split successfully passed stability thresholds (WR >= 50% and PF >= 1.1).")
            print("\n**Revision Directive for Deployment:**")
            print("- **P3 v3.0 NQ Adjustment:** Market-on-C+1-Close entry is validated on Daily timeframe for NQ=F.")
            print("- Ensure 0.05R per-trade spread/slippage buffer is budgeted in portfolio risk.")
        else:
            print("### GO/NO-GO Recommendation: **NO-GO (REGIME-DEPENDENT → RETIRE P3 for NQ)**")
            print("Test Split failed minimum stability thresholds (WR < 50% or PF < 1.1). P3 shows structural degradation on NQ=F in the post-2021 regime.")

if __name__ == "__main__":
    validator = NQValidator()
    validator.validate()
```
