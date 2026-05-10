import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

class P3Backtester:
    def __init__(self, tickers=None):
        if tickers is None:
            self.tickers = ["EURUSD=X", "GBPUSD=X", "GC=F", "NQ=F"]
        else:
            self.tickers = tickers

    def fetch_data(self, ticker, period="2y", interval="4h"):
        """Fetches data using yfinance and converts timezone to Europe/London."""
        df = yf.download(ticker, period=period, interval=interval, progress=False)

        # yf sometimes returns multi-index columns depending on the version
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        if df.empty:
            return df

        # Timezone conversion
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        df.index = df.index.tz_convert('Europe/London')

        return df

    def calculate_indicators(self, df):
        """Calculates required technical indicators."""
        df = df.copy()

        # EMA200
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        # Wilder's Smoothing for ATR and RSI
        def wilder_smooth(s, window):
            """Wilder's Smoothing (Exponential Moving Average logic matching MT5/TradingView)."""
            alpha = 1.0 / window
            return s.ewm(alpha=alpha, adjust=False).mean()

        # ATR (14)
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['TR'] = true_range
        df['ATR14'] = wilder_smooth(true_range, 14)

        # Average volume for 20 periods
        df['AvgVol20'] = df['Volume'].rolling(window=20).mean()

        # RSI (14) using Wilder's Smoothing
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0))
        loss = (-delta.where(delta < 0, 0))
        avg_gain = wilder_smooth(gain, 14)
        avg_loss = wilder_smooth(loss, 14)
        rs = avg_gain / avg_loss
        df['RSI14'] = 100 - (100 / (1 + rs))
        df['RSI14'] = df['RSI14'].fillna(50)  # default for early periods

        # ADX (14)
        up_move = df['High'] - df['High'].shift(1)
        down_move = df['Low'].shift(1) - df['Low']

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        plus_dm_series = pd.Series(plus_dm, index=df.index)
        minus_dm_series = pd.Series(minus_dm, index=df.index)

        smoothed_plus_dm = wilder_smooth(plus_dm_series, 14)
        smoothed_minus_dm = wilder_smooth(minus_dm_series, 14)

        plus_di = 100 * (smoothed_plus_dm / df['ATR14'])
        minus_di = 100 * (smoothed_minus_dm / df['ATR14'])

        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        df['ADX14'] = wilder_smooth(dx.fillna(0), 14)

        return df

    def dual_regime_rsi(self, rsi, is_bullish, price, ema):
        """Dual-Regime RSI Filter Logic"""
        # If price > EMA200, it's an uptrend pullback (RSI < 50 threshold for bullish)
        # If price < EMA200, it's a downtrend reversal (RSI < 35 threshold for bullish)
        if is_bullish:
            if price > ema:
                return rsi < 50
            else:
                return rsi < 35
        else:
            if price < ema:
                return rsi > 50
            else:
                return rsi > 65

    def detect_patterns(self, df):
        """Detects candlestick patterns and filters them against the protocol conditions."""
        df = df.copy()

        # Output columns
        df['Signal'] = None
        df['Pattern'] = None
        df['Confirmed'] = False

        # Iterate over the dataframe to find patterns
        # We need at least 1 previous bar for engulfing and prior trend context
        # We also evaluate the current forming/last candle without confirmation
        for i in range(1, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i - 1]

            # For confirmation we check if there's a next bar, else it's unconfirmed
            if i + 1 < len(df):
                next_bar = df.iloc[i + 1]
            else:
                next_bar = None

            body_size = abs(current['Close'] - current['Open'])
            wick_upper = current['High'] - max(current['Close'], current['Open'])
            wick_lower = min(current['Close'], current['Open']) - current['Low']

            # Universal Filter Values
            rsi = current['RSI14']
            ema = current['EMA200']
            atr = current['ATR14']
            range_len = current['High'] - current['Low']
            # Based on 4H interval boundary checks, times might be e.g. 12, 16, etc.
            # London 08:00 - 16:00, NY 13:00 - 21:00
            # 13:00-16:00 means hour can be anywhere >=8 and <=20 depending on overlapping interval
            # We'll allow the entire London & NY sessions for the scanner (8 to 20)
            is_valid_session = 8 <= current.name.hour <= 20

            # Filter 1 & 4 Context Logic

            # 1. Hammer (Bullish)
            # Lower wick >= 2x body, Upper wick < 0.5x body
            is_hammer = (wick_lower >= 2 * body_size) and (wick_upper < 0.5 * body_size)
            bullish_context = self.dual_regime_rsi(rsi, is_bullish=True, price=current['Close'], ema=ema)
            if is_hammer and bullish_context and current['Close'] > ema and range_len > atr:
                # Add Session filter
                if is_valid_session:
                    df.at[df.index[i], 'Pattern'] = 'Hammer'
                    df.at[df.index[i], 'Signal'] = 'Bullish'
                    if next_bar is not None and next_bar['Close'] > current['High']:
                        df.at[df.index[i], 'Confirmed'] = True

            # 2. Shooting Star (Bearish)
            # Upper wick >= 2x body, Lower wick < 0.5x body
            is_shooting_star = (wick_upper >= 2 * body_size) and (wick_lower < 0.5 * body_size)
            bearish_context = self.dual_regime_rsi(rsi, is_bullish=False, price=current['Close'], ema=ema)
            if is_shooting_star and bearish_context and current['Close'] < ema and range_len > atr:
                if is_valid_session:
                    df.at[df.index[i], 'Pattern'] = 'Shooting Star'
                    df.at[df.index[i], 'Signal'] = 'Bearish'
                    if next_bar is not None and next_bar['Close'] < current['Low']:
                        df.at[df.index[i], 'Confirmed'] = True

            # 3. Bearish Engulfing
            # C1 small bullish, C2 large bearish. Close(C2) < Open(C1) and Open(C2) > Close(C1)
            prev_body = abs(prev['Close'] - prev['Open'])
            c1_bullish = prev['Close'] > prev['Open']
            c2_bearish = current['Close'] < current['Open']
            is_bearish_engulfing = c1_bullish and c2_bearish and (current['Close'] < prev['Open']) and (current['Open'] > prev['Close'])

            if is_bearish_engulfing and bearish_context and current['Close'] < ema and range_len > atr:
                if is_valid_session:
                    df.at[df.index[i], 'Pattern'] = 'Bearish Engulfing'
                    df.at[df.index[i], 'Signal'] = 'Bearish'
                    if next_bar is not None and next_bar['Close'] < current['Low']:
                        df.at[df.index[i], 'Confirmed'] = True

            # 4. Bullish Engulfing
            # C1 small bearish, C2 large bullish. Close(C2) > Open(C1) and Open(C2) < Close(C1)
            c1_bearish = prev['Close'] < prev['Open']
            c2_bullish = current['Close'] > current['Open']
            is_bullish_engulfing = c1_bearish and c2_bullish and (current['Close'] > prev['Open']) and (current['Open'] < prev['Close'])

            # Protocol note: Bullish engulfing specifically requires RSI < 30
            strict_bullish_context = (current['Close'] > ema) and (rsi < 30)
            if is_bullish_engulfing and strict_bullish_context and range_len > atr:
                if is_valid_session:
                    df.at[df.index[i], 'Pattern'] = 'Bullish Engulfing'
                    df.at[df.index[i], 'Signal'] = 'Bullish'
                    if next_bar is not None and next_bar['Close'] > current['High']:
                        df.at[df.index[i], 'Confirmed'] = True

        return df

    def evaluate_trade(self, bars, signal, entry, sl, tp1, tp2):
        """Evaluates trade progression bar-by-bar to determine final R-multiple."""
        tp1_hit = False
        original_risk = abs(entry - sl)
        if original_risk == 0:
            return 0.0

        for _, bar in bars.iterrows():
            high, low, close = bar['High'], bar['Low'], bar['Close']

            if signal == 'Bullish':
                if low <= sl:
                    return -1.0 if not tp1_hit else 0.75 # 0.5 * 1.5R secured at TP1, remainder BE
                if high >= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry # Move stop to BE
                if high >= tp2 and tp1_hit:
                    return 2.25 # TP1 (0.5 * 1.5R) + TP2 (0.5 * 3.0R)

            else: # Bearish
                if high >= sl:
                    return -1.0 if not tp1_hit else 0.75
                if low <= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry
                if low <= tp2 and tp1_hit:
                    return 2.25

        # Time stop (10 bars elapsed)
        final_close = bars.iloc[-1]['Close']
        if signal == 'Bullish':
            floating_r = (final_close - entry) / original_risk
        else:
            floating_r = (entry - final_close) / original_risk

        if tp1_hit:
            return 0.75 + (0.5 * floating_r)
        else:
            # Full position closed at time stop
            return floating_r

    def run_backtest(self, df):
        """Executes trades over the dataframe and computes metrics."""
        trades_market = []
        trades_stop = []

        # We loop up to len(df)-10 to ensure we have room for the 10-bar time stop
        for i in range(1, len(df) - 10):
            if pd.isna(df['Signal'].iloc[i]):
                continue

            signal = df['Signal'].iloc[i]
            # Pattern extreme (C bar extreme) is used for the SL, but the document asks for stop entries on C+1 extreme.
            pattern_high = df['High'].iloc[i]
            pattern_low = df['Low'].iloc[i]

            c_plus_1 = df.iloc[i + 1] # C+1 bar

            # SL is placed at Pattern (C bar) Extreme
            sl = pattern_low if signal == 'Bullish' else pattern_high

            # 1. Market-on-C+1-Close execution
            market_entry = c_plus_1['Close']
            market_risk = market_entry - sl if signal == 'Bullish' else sl - market_entry

            if market_risk > 0: # valid risk
                market_tp1 = market_entry + (1.5 * market_risk) if signal == 'Bullish' else market_entry - (1.5 * market_risk)
                market_tp2 = market_entry + (3.0 * market_risk) if signal == 'Bullish' else market_entry - (3.0 * market_risk)

                # Simulate forward 10 bars (starting from C+2)
                forward_bars = df.iloc[i+2 : i+12]
                trade_r = self.evaluate_trade(forward_bars, signal, market_entry, sl, market_tp1, market_tp2)
                trades_market.append(trade_r)

            # 2. Method 3 Stop Order Execution
            # Stop order placed 1 pip beyond C+1 extreme, simulated starting from C+2
            if i + 2 < len(df):
                c_plus_2 = df.iloc[i + 2]

                c_plus_1_high = c_plus_1['High']
                c_plus_1_low = c_plus_1['Low']

                if signal == 'Bullish':
                    stop_entry_price = c_plus_1_high + (c_plus_1_high * 0.0001) # proxy for 1 pip
                else:
                    stop_entry_price = c_plus_1_low - (c_plus_1_low * 0.0001)

                triggered = False
                stop_risk = stop_entry_price - sl if signal == 'Bullish' else sl - stop_entry_price

                if stop_risk > 0:
                    # Check if C+2 hits the stop entry
                    if signal == 'Bullish' and c_plus_2['High'] >= stop_entry_price:
                        triggered = True
                    elif signal == 'Bearish' and c_plus_2['Low'] <= stop_entry_price:
                        triggered = True

                    if triggered:
                        stop_tp1 = stop_entry_price + (1.5 * stop_risk) if signal == 'Bullish' else stop_entry_price - (1.5 * stop_risk)
                        stop_tp2 = stop_entry_price + (3.0 * stop_risk) if signal == 'Bullish' else stop_entry_price - (3.0 * stop_risk)

                        # Forward bars include remainder of C+2 plus 9 bars
                        forward_bars = df.iloc[i+2 : i+12]
                        trade_r = self.evaluate_trade(forward_bars, signal, stop_entry_price, sl, stop_tp1, stop_tp2)
                        trades_stop.append(trade_r)

        return trades_market, trades_stop

    def backtest_all(self):
        """Runs the backtest across all tickers and outputs metrics table."""
        results = []
        for ticker in self.tickers:
            df = self.fetch_data(ticker)
            if df.empty:
                continue
            df = self.calculate_indicators(df)
            df = self.detect_patterns(df)

            t_market, t_stop = self.run_backtest(df)

            def calc_metrics(trades, method_name):
                if not trades:
                    return [ticker, method_name, 0, 0.0, 0.0, 0.0]

                wins = [t for t in trades if t > 0]
                losses = [t for t in trades if t < 0]

                win_rate = (len(wins) / len(trades)) * 100
                avg_r = np.mean(trades)

                gross_profit = sum(wins)
                gross_loss = abs(sum(losses)) if sum(losses) != 0 else 0.0001
                profit_factor = gross_profit / gross_loss

                return [ticker, method_name, len(trades), round(win_rate, 2), round(avg_r, 2), round(profit_factor, 2)]

            results.append(calc_metrics(t_market, "Market-on-C+1-Close"))
            results.append(calc_metrics(t_stop, "Method 3 Stop Order"))

        print("\n--- Protocol 3: Backtest Performance Summary ---")
        results_df = pd.DataFrame(results, columns=[
            "Ticker", "Entry Logic", "Total Trades (N)", "Win Rate (%)", "Avg R-Multiple", "Profit Factor"
        ])
        print(results_df.to_string(index=False))

if __name__ == "__main__":
    bt = P3Backtester()
    bt.backtest_all()
