import yfinance as yf
import pandas as pd
import numpy as np
import math

class P3H1Funnel:
    def __init__(self, tickers=None):
        if tickers is None:
            self.tickers = ["EURUSD=X", "GBPUSD=X", "GC=F", "NQ=F"]
        else:
            self.tickers = tickers

        self.PIP_MAP = {
            'EURUSD=X': 0.0001,
            'GBPUSD=X': 0.0001,
            'GC=F': 0.1,
            'NQ=F': 0.25
        }

    def fetch_data(self, ticker):
        df = yf.download(ticker, period="730d", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        if df.empty:
            return df

        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')
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

    def evaluate_market_trade(self, bars, signal, entry, sl, tp1, tp2):
        tp1_hit = False
        original_risk = abs(entry - sl)
        if original_risk == 0: return 0.0

        for _, bar in bars.iterrows():
            high, low, close = bar['High'], bar['Low'], bar['Close']

            if signal == 'Bullish':
                if low <= sl: return -1.0 if not tp1_hit else 0.75
                if high >= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry
                if high >= tp2 and tp1_hit: return 2.25
            else:
                if high >= sl: return -1.0 if not tp1_hit else 0.75
                if low <= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry
                if low <= tp2 and tp1_hit: return 2.25

        final_close = bars.iloc[-1]['Close']
        if signal == 'Bullish': floating_r = (final_close - entry) / original_risk
        else: floating_r = (entry - final_close) / original_risk

        if tp1_hit: return 0.75 + (0.5 * floating_r)
        else: return floating_r

    def run_funnel(self, ticker, df):
        pip_inc = self.PIP_MAP.get(ticker, 0.0001)
        trades_A = []
        trades_B = []
        trades_C = []

        for i in range(1, len(df) - 15):
            current = df.iloc[i]
            prev = df.iloc[i - 1]
            c_plus_1 = df.iloc[i + 1]

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

            # CONFIG A: Pattern + Session + EMA200
            is_valid_session = 8 <= current.name.hour <= 21
            if not is_valid_session: continue

            signal = None
            if is_hammer and current['Close'] > ema: signal = 'Bullish'
            elif is_bullish_engulfing and current['Close'] > ema: signal = 'Bullish'
            elif is_shooting_star and current['Close'] < ema: signal = 'Bearish'
            elif is_bearish_engulfing and current['Close'] < ema: signal = 'Bearish'

            if not signal: continue

            pattern_high = current['High']
            pattern_low = current['Low']
            sl = pattern_low if signal == 'Bullish' else pattern_high

            market_entry = c_plus_1['Close']
            market_risk = market_entry - sl if signal == 'Bullish' else sl - market_entry

            if market_risk > 0:
                market_tp1 = market_entry + (1.5 * market_risk) if signal == 'Bullish' else market_entry - (1.5 * market_risk)
                market_tp2 = market_entry + (3.0 * market_risk) if signal == 'Bullish' else market_entry - (3.0 * market_risk)
                forward_bars = df.iloc[i+2 : i+12]
                r = self.evaluate_market_trade(forward_bars, signal, market_entry, sl, market_tp1, market_tp2)
                trades_A.append(r - 0.05)

            # CONFIG B: Config A + Dual-Regime RSI + Volume > 1.2x Avg
            bullish_context = self.dual_regime_rsi(rsi, True, current['Close'], ema)
            bearish_context = self.dual_regime_rsi(rsi, False, current['Close'], ema)

            rsi_pass = (signal == 'Bullish' and bullish_context) or (signal == 'Bearish' and bearish_context)
            vol_pass = (vol > 1.2 * avg_vol) or pd.isna(avg_vol) or avg_vol == 0

            if rsi_pass and vol_pass and market_risk > 0:
                trades_B.append(r - 0.05)

                # CONFIG C: Config B + Exhaustion Filter (C+1 < 2x ATR) + Method 3 Stop (4 candles valid)
                c_plus_1_range = c_plus_1['High'] - c_plus_1['Low']
                exhaustion_pass = c_plus_1_range < (2 * atr)

                if exhaustion_pass:
                    stop_entry = c_plus_1['High'] + pip_inc if signal == 'Bullish' else c_plus_1['Low'] - pip_inc
                    stop_risk = stop_entry - sl if signal == 'Bullish' else sl - stop_entry

                    if stop_risk > 0:
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
                            r_stop = self.evaluate_market_trade(forward_bars, signal, stop_entry, sl, stop_tp1, stop_tp2)
                            trades_C.append(r_stop - 0.05)

        return trades_A, trades_B, trades_C

    def calc_metrics(self, trades):
        n = len(trades)
        if n == 0: return n, 0.0, 0.0, 0.0, "FAIL"
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t <= 0]

        wr = (len(wins) / n) * 100
        pf = sum(wins) / (abs(sum(losses)) if sum(losses) != 0 else 0.0001)
        status = "GO" if (wr >= 50 and pf >= 1.1) else "NO-GO"
        return n, wr, np.mean(trades), pf, status

    def run_all(self):
        results = []
        counts = {'A': 0, 'B': 0, 'C': 0}

        for ticker in self.tickers:
            df = self.fetch_data(ticker)
            if df.empty: continue
            df = self.calculate_indicators(df)
            tA, tB, tC = self.run_funnel(ticker, df)

            nA, wrA, avgA, pfA, stA = self.calc_metrics(tA)
            nB, wrB, avgB, pfB, stB = self.calc_metrics(tB)
            nC, wrC, avgC, pfC, stC = self.calc_metrics(tC)

            counts['A'] += nA
            counts['B'] += nB
            counts['C'] += nC

            results.append([ticker, "A (Session+EMA)", nA, f"{wrA:.1f}", f"{pfA:.2f}", stA])
            results.append([ticker, "B (+RSI+Vol)", nB, f"{wrB:.1f}", f"{pfB:.2f}", stB])
            results.append([ticker, "C (+Exhaust+M3)", nC, f"{wrC:.1f}", f"{pfC:.2f}", stC])

        print("## Protocol 3 H1 Funnel Analysis")
        print("| Ticker | Config | N | WR | PF | Status |")
        print("|--------|--------|---|----|----|--------|")
        for r in results:
            print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |")

        print("\n## Funnel Diagnosis")
        print(f"- **Config A (Base):** {counts['A']} trades")
        print(f"- **Config B (RSI+Vol):** {counts['B']} trades")
        print(f"- **Config C (Strict M3):** {counts['C']} trades")

        if counts['A'] > 0:
            drop_ab = (counts['A'] - counts['B']) / counts['A'] * 100
            print(f"**Drop-Off A -> B (RSI & Volume Filters):** -{drop_ab:.1f}%")
            if drop_ab > 80:
                print("⚠️ **Severe Drop-Off at B:** The Dual-Regime RSI and 1.2x Volume filters are choking out almost all H1 signals. The timeframe lacks the requisite volatility sweeps needed to meet these criteria.")
            elif drop_ab > 50:
                print("Moderate Drop-Off at B: RSI and Volume are filtering half the setups.")

        if counts['B'] > 0:
            drop_bc = (counts['B'] - counts['C']) / counts['B'] * 100
            print(f"**Drop-Off B -> C (Exhaustion & M3 Stop execution):** -{drop_bc:.1f}%")
            if drop_bc > 50:
                print("⚠️ **Severe Drop-Off at C:** The Method 3 Stop logic (1 pip beyond C+1) combined with the Exhaustion filter fails to trigger. The H1 momentum doesn't carry through the confirmation candle sufficiently.")

if __name__ == '__main__':
    bt = P3H1Funnel()
    bt.run_all()
