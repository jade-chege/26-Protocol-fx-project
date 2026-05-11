import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import math

class P3MT5SplitValidation:
    def __init__(self):
        self.ticker = "NAS100.pro"
        self.pip_value = 1.0

    def init_mt5(self):
        if not mt5.initialize():
            print(f"initialize() failed, error code = {mt5.last_error()}")
            return False
        return True

    def fetch_data(self):
        timezone = pytz.timezone("America/New_York")
        utc_from = datetime(2020, 1, 1, tzinfo=pytz.utc)
        utc_to = datetime(2025, 12, 31, tzinfo=pytz.utc)

        print(f"Fetching {self.ticker} H1 data from MT5...")
        rates = mt5.copy_rates_range(self.ticker, mt5.TIMEFRAME_H1, utc_from, utc_to)

        if rates is None or len(rates) == 0:
            print("Failed to fetch rates")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df.set_index('time', inplace=True)
        df.index = df.index.tz_convert(timezone)

        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'tick_volume': 'Volume'}, inplace=True)

        print(f"Fetched {len(df)} bars.")
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

        df['AvgVol20'] = df['Volume'].rolling(window=20).mean()

        return df

    def dual_regime_rsi(self, rsi, is_bullish, price, ema):
        if is_bullish:
            if price > ema: return rsi < 50
            else: return rsi < 35
        else:
            if price < ema: return rsi > 50
            else: return rsi > 65

    def run_config_c(self, df, start_year, end_year):
        mask = (df.index.year >= start_year) & (df.index.year <= end_year)
        indices_in_split = np.where(mask)[0]

        trades = []

        for i in indices_in_split:
            if i >= len(df) - 15:
                continue

            current = df.iloc[i]
            prev = df.iloc[i - 1]
            c_plus_1 = df.iloc[i + 1]

            # NY indices session filter (10:00 - 15:30 ET) + Overlap
            hour = current.name.hour
            minute = current.name.minute
            is_valid_session = (hour > 10 or (hour == 10 and minute >= 0)) and (hour < 15 or (hour == 15 and minute <= 30))
            if not is_valid_session:
                continue

            body_size = abs(current['Close'] - current['Open'])
            wick_upper = current['High'] - max(current['Close'], current['Open'])
            wick_lower = min(current['Close'], current['Open']) - current['Low']

            rsi = current['RSI14']
            ema = current['EMA200']
            atr = current['ATR14']
            vol = current['Volume']
            avg_vol = current['AvgVol20']

            is_hammer = (wick_lower >= 2 * body_size) and (wick_upper < 0.5 * body_size)
            is_shooting_star = (wick_upper >= 2 * body_size) and (wick_lower < 0.5 * body_size)

            c1_bullish = prev['Close'] > prev['Open']
            c2_bearish = current['Close'] < current['Open']
            is_bearish_engulfing = c1_bullish and c2_bearish and (current['Close'] < prev['Open']) and (current['Open'] > prev['Close'])

            c1_bearish = prev['Close'] < prev['Open']
            c2_bullish = current['Close'] > current['Open']
            is_bullish_engulfing = c1_bearish and c2_bullish and (current['Close'] > prev['Open']) and (current['Open'] < prev['Close'])

            if not any([is_hammer, is_shooting_star, is_bearish_engulfing, is_bullish_engulfing]):
                continue

            signal = None
            if is_hammer and current['Close'] > ema: signal = 'Bullish'
            elif is_bullish_engulfing and current['Close'] > ema: signal = 'Bullish'
            elif is_shooting_star and current['Close'] < ema: signal = 'Bearish'
            elif is_bearish_engulfing and current['Close'] < ema: signal = 'Bearish'

            if not signal: continue

            # Dual-Regime RSI + Volume
            bullish_context = self.dual_regime_rsi(rsi, True, current['Close'], ema)
            bearish_context = self.dual_regime_rsi(rsi, False, current['Close'], ema)

            rsi_pass = (signal == 'Bullish' and bullish_context) or (signal == 'Bearish' and bearish_context)
            vol_pass = (vol > 1.2 * avg_vol) or pd.isna(avg_vol) or avg_vol == 0

            if rsi_pass and vol_pass:
                # Exhaustion Filter (C+1 < 2x ATR)
                c_plus_1_range = c_plus_1['High'] - c_plus_1['Low']
                exhaustion_pass = c_plus_1_range < (2 * atr)

                if exhaustion_pass:
                    pattern_high = current['High']
                    pattern_low = current['Low']
                    sl = pattern_low if signal == 'Bullish' else pattern_high

                    stop_entry = c_plus_1['High'] + self.pip_value if signal == 'Bullish' else c_plus_1['Low'] - self.pip_value
                    stop_risk = stop_entry - sl if signal == 'Bullish' else sl - stop_entry

                    if stop_risk > 0:
                        be_threshold = stop_entry + stop_risk if signal == 'Bullish' else stop_entry - stop_risk
                        stop_tp1 = stop_entry + (1.5 * stop_risk) if signal == 'Bullish' else stop_entry - (1.5 * stop_risk)
                        stop_tp2 = stop_entry + (3.0 * stop_risk) if signal == 'Bullish' else stop_entry - (3.0 * stop_risk)

                        # Evaluate forward 4 bars for trigger
                        triggered = False
                        trigger_idx = -1
                        for j in range(2, 6):
                            test_bar = df.iloc[i+j]
                            if signal == 'Bullish' and test_bar['High'] >= stop_entry:
                                triggered = True
                                trigger_idx = j
                                break
                            elif signal == 'Bearish' and test_bar['Low'] <= stop_entry:
                                triggered = True
                                trigger_idx = j
                                break

                        if triggered:
                            forward_bars = df.iloc[i + trigger_idx : i + trigger_idx + 10]
                            r_stop = self.evaluate_market_trade(forward_bars, signal, stop_entry, sl, be_threshold, stop_tp1, stop_tp2)
                            trades.append(r_stop)

        return trades

    def evaluate_market_trade(self, bars, signal, entry, sl, be_threshold, tp1, tp2):
        tp1_hit = False
        be_hit = False
        original_risk = abs(entry - sl)
        if original_risk == 0: return 0.0

        for _, bar in bars.iterrows():
            high, low, close = bar['High'], bar['Low'], bar['Close']

            if signal == 'Bullish':
                if low <= sl: return -1.0 if not be_hit else (0.75 if tp1_hit else 0.0)

                if high >= be_threshold and not be_hit:
                    be_hit = True
                    sl = entry

                if high >= tp1 and not tp1_hit:
                    tp1_hit = True

                if high >= tp2 and tp1_hit: return 2.25
            else:
                if high >= sl: return -1.0 if not be_hit else (0.75 if tp1_hit else 0.0)

                if low <= be_threshold and not be_hit:
                    be_hit = True
                    sl = entry

                if low <= tp1 and not tp1_hit:
                    tp1_hit = True

                if low <= tp2 and tp1_hit: return 2.25

        final_close = bars.iloc[-1]['Close']
        if signal == 'Bullish': floating_r = (final_close - entry) / original_risk
        else: floating_r = (entry - final_close) / original_risk

        if tp1_hit: return 0.75 + (0.5 * floating_r)
        else: return floating_r

    def calculate_drawdown(self, trades):
        cum_r = 0
        peak = 0
        max_dd = 0
        for t in trades:
            cum_r += t
            if cum_r > peak:
                peak = cum_r
            dd = peak - cum_r
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def calculate_metrics(self, trades):
        n = len(trades)
        if n == 0:
            return 0, 0.0, 0.0, 0.0, 0.0, 0.0

        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t <= 0]

        win_rate = len(wins) / n
        win_rate_pct = win_rate * 100
        avg_r = np.mean(trades)

        gross_profit = sum(wins)
        gross_loss = abs(sum(losses)) if sum(losses) != 0 else 0.0001
        profit_factor = gross_profit / gross_loss

        max_dd = self.calculate_drawdown(trades)

        # Wilson Score Interval (95% confidence)
        z = 1.96
        denominator = 1 + z**2/n
        cap = win_rate + z**2 / (2*n)
        asd = math.sqrt((win_rate*(1 - win_rate) + z**2 / (4*n)) / n)
        wilson_lower = (cap - z*asd) / denominator
        wilson_lb_pct = max(0.0, wilson_lower * 100)

        return n, win_rate_pct, avg_r, profit_factor, max_dd, wilson_lb_pct

    def run(self):
        if not self.init_mt5(): return

        df = self.fetch_data()
        mt5.shutdown()

        if df.empty: return
        df = self.calculate_indicators(df)

        train_trades = self.run_config_c(df, 2020, 2022)
        test_trades = self.run_config_c(df, 2023, 2025)

        # Deduct 0.05R spread/slippage
        train_trades = [t - 0.05 for t in train_trades]
        test_trades = [t - 0.05 for t in test_trades]

        t_n, t_wr, t_ar, t_pf, t_dd, t_wil = self.calculate_metrics(train_trades)
        s_n, s_wr, s_ar, s_pf, s_dd, s_wil = self.calculate_metrics(test_trades)

        print("\n## P3 NQ=F (NAS100.pro) H1 5-Year MT5 Validation")
        print("| Split | Years | N | Win Rate (%) | Avg R | PF | Max DD (R) | Wilson CI LB (%) |")
        print("|-------|-------|---|--------------|-------|----|------------|------------------|")
        print(f"| **Train** | 2020-2022 | {t_n} | {t_wr:.1f} | {t_ar:.2f} | {t_pf:.2f} | {t_dd:.2f} | {t_wil:.1f} |")
        print(f"| **Test**  | 2023-2025 | {s_n} | {s_wr:.1f} | {s_ar:.2f} | {s_pf:.2f} | {s_dd:.2f} | {s_wil:.1f} |")

        print("\n--- Decision Gate ---")
        train_pass = (t_n >= 30 and t_pf >= 1.2 and t_wr >= 50.0)
        test_pass = (s_n >= 30 and s_pf >= 1.2 and s_wr >= 50.0)

        if train_pass and test_pass:
            print("Status: VALIDATED")
            print("P3 NQ H1 strategy passes strictly across both the Train and Test regime splits.")
        else:
            print("Status: RETIRE P3")
            print("Edge collapses in either the Train split, Test split, or sample size (N<30) is insufficient. Pivot to Protocol 4.")

if __name__ == "__main__":
    validator = P3MT5SplitValidation()
    validator.run()
