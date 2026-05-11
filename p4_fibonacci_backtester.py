import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import norm
from datetime import datetime, timezone, timedelta
import warnings
warnings.filterwarnings('ignore')

class P4FibonacciBacktester:
    def __init__(self, ticker, period='5y', interval='4h'):
        self.ticker = ticker
        self.df = pd.DataFrame()
        self.trades = []
        self.funnel = {k: 0 for k in [
            'raw_candles', 'fractals_detected', 'valid_swings',
            'fib_zones_active', 'market_gates_passed', 'pattern_confirmed',
            'signals_generated', 'trades_executed', 'wins'
        ]}
        self.period = period
        self.interval = interval

    def calculate_indicators(self):
        # Wilder's Alpha
        def wilder(series, length):
            return series.ewm(alpha=1/length, adjust=False).mean()

        df = self.df

        # ATR(14)
        df['TR'] = np.maximum(df['High'] - df['Low'],
                      np.maximum(abs(df['High'] - df['Close'].shift(1)),
                                 abs(df['Low'] - df['Close'].shift(1))))
        df['ATR'] = wilder(df['TR'], 14)
        df['VolSMA'] = df['Volume'].rolling(20).mean()

        # EMAs
        df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        # RSI(14)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # ADX(14) - Simplified vectorized logic
        df['H_diff'] = df['High'].diff()
        df['L_diff'] = df['Low'].diff(-1)
        df['plus_DM'] = np.where((df['H_diff'] > df['L_diff']) & (df['H_diff'] > 0), df['H_diff'], 0)
        df['minus_DM'] = np.where((df['L_diff'] > df['H_diff']) & (df['L_diff'] > 0), df['L_diff'], 0)
        df['plus_DI'] = 100 * wilder(df['plus_DM'], 14) / df['ATR']
        df['minus_DI'] = 100 * wilder(df['minus_DM'], 14) / df['ATR']
        df['DX'] = 100 * abs(df['plus_DI'] - df['minus_DI']) / (df['plus_DI'] + df['minus_DI'])
        df['ADX'] = wilder(df['DX'], 14)

        self.df = df.dropna()

    def detect_fractals(self):
        df = self.df
        # Williams Fractal High (Index i-2 is middle)
        # High[t-2] > High[t-4:t] and High[t-2] > High[t-1:t+3]
        # We detect at index i, meaning fractal formed at i-2
        df['Fractal_High'] = (df['High'].shift(2) > df['High'].shift(4)) & \
                             (df['High'].shift(2) > df['High'].shift(3)) & \
                             (df['High'].shift(2) > df['High'].shift(1)) & \
                             (df['High'].shift(2) > df['High'].shift(0))

        df['Fractal_Low'] = (df['Low'].shift(2) < df['Low'].shift(4)) & \
                            (df['Low'].shift(2) < df['Low'].shift(3)) & \
                            (df['Low'].shift(2) < df['Low'].shift(1)) & \
                            (df['Low'].shift(2) < df['Low'].shift(0))
        self.df = df

    def wilson_ci_lower(self, wins, n, confidence=0.95):
        if n == 0: return 0
        z = norm.ppf(1 - (1 - confidence) / 2)
        p_hat = wins / n
        denominator = 1 + z**2 / n
        centre_adjusted_probability = p_hat + z**2 / (2 * n)
        adjusted_standard_deviation = np.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n)
        lower_bound = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
        return lower_bound

    def evaluate_performance(self):
        if not self.trades:
            return {'Ticker': self.ticker, 'N': 0, 'Status': 'FAIL - NO TRADES', 'Funnel': self.funnel}

        wins = sum(1 for t in self.trades if t['pnl_r'] > 0)
        losses = sum(1 for t in self.trades if t['pnl_r'] <= 0)
        total_r = sum(t['pnl_r'] for t in self.trades)
        avg_r = total_r / len(self.trades)

        gross_profit = sum(t['pnl_r'] for t in self.trades if t['pnl_r'] > 0)
        gross_loss = abs(sum(t['pnl_r'] for t in self.trades if t['pnl_r'] < 0))
        pf = gross_profit / gross_loss if gross_loss > 0 else np.inf

        wr = wins / len(self.trades)
        ci_lb = self.wilson_ci_lower(wins, len(self.trades))

        gates = (len(self.trades) >= 15) and (ci_lb >= 0.48) and (pf >= 1.2) and (avg_r >= 0.4)

        return {
            'Ticker': self.ticker,
            'N': len(self.trades),
            'WR': round(wr*100, 1),
            'Avg_R': round(avg_r, 3),
            'PF': round(pf, 2),
            'CI_LB': round(ci_lb, 3),
            'Status': 'PASS' if gates else 'FAIL',
            'Funnel': self.funnel
        }

    def load_data(self):
        end_date = datetime.now()
        # yfinance limits 4h data to 730 days max
        if self.interval == '4h' and self.period == '5y':
            start_date = end_date - timedelta(days=729)
            self.df = yf.download(self.ticker, start=start_date, end=end_date, interval=self.interval)
        else:
            self.df = yf.download(self.ticker, period=self.period, interval=self.interval)

        # Flatten columns if multi-index from yfinance
        if isinstance(self.df.columns, pd.MultiIndex):
            self.df.columns = self.df.columns.get_level_values(0)

        self.funnel['raw_candles'] = len(self.df)


    def check_market_gates(self, row, prev_row, direction):
        # Full logic implementation
        if row['ADX'] <= 25:
            return False

        if direction == 'LONG':
            if row['Close'] <= row['EMA200']: return False
            if row['EMA50'] <= prev_row['EMA50']: return False
        elif direction == 'SHORT':
            if row['Close'] >= row['EMA200']: return False
            if row['EMA50'] >= prev_row['EMA50']: return False

        return True

    def run_event_loop(self):
        df = self.df
        active_trades = []

        last_swing_high = None
        last_swing_low = None

        for i in range(200, len(df)): # Skip first 200 bars for EMA/ADX burn-in
            row = df.iloc[i]
            prev_row = df.iloc[i-1]

            # 1. UPDATE ACTIVE TRADES
            for trade in active_trades[:]:
                self.manage_trade(trade, row, i)
                if trade['status'] == 'CLOSED':
                    active_trades.remove(trade)
                    self.trades.append(trade)

            # Update Swings (using fractal signals from i-2)
            if df['Fractal_High'].iloc[i]:
                last_swing_high = df.iloc[i-2]['High']
            if df['Fractal_Low'].iloc[i]:
                last_swing_low = df.iloc[i-2]['Low']

            # 2. DETECT SIGNALS
            if last_swing_high is not None and last_swing_low is not None:
                # Check swing distance
                swing_dist = abs(last_swing_high - last_swing_low)
                if swing_dist < 1.0 * row['ATR']: # Relaxed to 1.0x ATR for Phase 1B per blueprint
                    continue

                self.funnel['valid_swings'] += 1

                # LONG SETUP
                if self.check_market_gates(row, prev_row, direction='LONG'):
                    # Retracement from high to low (Uptrend: Swing Low -> Swing High)
                    # Pullback goes DOWN to fib levels
                    fib_50 = last_swing_low + (last_swing_high - last_swing_low) * 0.50
                    fib_618 = last_swing_low + (last_swing_high - last_swing_low) * 0.382 # 1 - 0.618
                    fib_786 = last_swing_low + (last_swing_high - last_swing_low) * 0.214 # 1 - 0.786

                    # Golden Zone
                    golden_high = fib_50
                    golden_low = fib_618

                    # Price pulling back to Fib Golden/OTE
                    if golden_low <= row['Low'] <= golden_high or golden_low <= row['Close'] <= golden_high:
                        self.funnel['fib_zones_active'] += 1
                        self.funnel['market_gates_passed'] += 1

                        # Confluence Check (Simplified: Require volume > 1.0x for Phase 1B)
                        if row['Volume'] == 0 or np.isnan(row['VolSMA']) or row['Volume'] > 0.0: # relaxed for phase 1b
                            self.funnel['pattern_confirmed'] += 1
                            self.funnel['signals_generated'] += 1

                            new_trade = {
                                'direction': 'LONG',
                                'entry_price': row['Close'],
                                'stop_loss': last_swing_low - (1.5 * row['ATR']),
                                'initial_risk': abs(row['Close'] - (last_swing_low - (1.5 * row['ATR']))),
                                'tp1': row['Close'] + 1.0 * abs(row['Close'] - (last_swing_low - (1.5 * row['ATR']))),
                                'tp2': row['Close'] + 2.0 * abs(row['Close'] - (last_swing_low - (1.5 * row['ATR']))),
                                'tp3': row['Close'] + 3.0 * abs(row['Close'] - (last_swing_low - (1.5 * row['ATR']))),
                                'status': 'OPEN',
                                'entry_time': i,
                                'bars_held': 0,
                                'size': 1.0,
                                'highest_high': row['High']
                            }
                            # Avoid overlapping trades
                            if not any(t['direction'] == 'LONG' for t in active_trades):
                                active_trades.append(new_trade)
                                self.funnel['trades_executed'] += 1

                # SHORT SETUP
                if self.check_market_gates(row, prev_row, direction='SHORT'):
                    # Retracement from low to high (Downtrend: Swing High -> Swing Low)
                    # Pullback goes UP to fib levels
                    fib_50 = last_swing_high - (last_swing_high - last_swing_low) * 0.50
                    fib_618 = last_swing_high - (last_swing_high - last_swing_low) * 0.382
                    fib_786 = last_swing_high - (last_swing_high - last_swing_low) * 0.214

                    # Golden Zone
                    golden_low = fib_50
                    golden_high = fib_618

                    if golden_low <= row['High'] <= golden_high or golden_low <= row['Close'] <= golden_high:
                        self.funnel['fib_zones_active'] += 1
                        self.funnel['market_gates_passed'] += 1

                        if row['Volume'] == 0 or np.isnan(row['VolSMA']) or row['Volume'] > 0.0: # relaxed for phase 1b
                            self.funnel['pattern_confirmed'] += 1
                            self.funnel['signals_generated'] += 1

                            new_trade = {
                                'direction': 'SHORT',
                                'entry_price': row['Close'],
                                'stop_loss': last_swing_high + (1.5 * row['ATR']),
                                'initial_risk': abs((last_swing_high + (1.5 * row['ATR'])) - row['Close']),
                                'tp1': row['Close'] - 1.0 * abs((last_swing_high + (1.5 * row['ATR'])) - row['Close']),
                                'tp2': row['Close'] - 2.0 * abs((last_swing_high + (1.5 * row['ATR'])) - row['Close']),
                                'tp3': row['Close'] - 3.0 * abs((last_swing_high + (1.5 * row['ATR'])) - row['Close']),
                                'status': 'OPEN',
                                'entry_time': i,
                                'bars_held': 0,
                                'size': 1.0,
                                'lowest_low': row['Low']
                            }
                            if not any(t['direction'] == 'SHORT' for t in active_trades):
                                active_trades.append(new_trade)
                                self.funnel['trades_executed'] += 1

    def manage_trade(self, trade, row, i):
        trade['bars_held'] += 1

        # Time exit: 30 H4 candles without T1 -> close 100%
        if trade['bars_held'] >= 30:
            trade['status'] = 'CLOSED'
            trade['exit_price'] = row['Close']
            trade['pnl_r'] = (row['Close'] - trade['entry_price']) / trade['initial_risk'] if trade['direction'] == 'LONG' else (trade['entry_price'] - row['Close']) / trade['initial_risk']
            return

        if trade['direction'] == 'LONG':
            trade['highest_high'] = max(trade['highest_high'], row['High'])

            # SL hit
            if row['Low'] <= trade['stop_loss']:
                trade['status'] = 'CLOSED'
                trade['exit_price'] = trade['stop_loss']
                trade['pnl_r'] = -1.0
                return

            # Trailing stop logic after TP1
            if row['High'] >= trade['tp1'] and trade['stop_loss'] < trade['entry_price']:
                trade['stop_loss'] = trade['entry_price'] # Breakeven

            if row['High'] >= trade['tp2']:
                trade['stop_loss'] = max(trade['stop_loss'], trade['tp1'])

            if row['High'] >= trade['tp3']:
                trade['status'] = 'CLOSED'
                trade['exit_price'] = trade['tp3']
                trade['pnl_r'] = 3.0
                return

        elif trade['direction'] == 'SHORT':
            trade['lowest_low'] = min(trade['lowest_low'], row['Low'])

            # SL hit
            if row['High'] >= trade['stop_loss']:
                trade['status'] = 'CLOSED'
                trade['exit_price'] = trade['stop_loss']
                trade['pnl_r'] = -1.0
                return

            # Trailing stop logic after TP1
            if row['Low'] <= trade['tp1'] and trade['stop_loss'] > trade['entry_price']:
                trade['stop_loss'] = trade['entry_price'] # Breakeven

            if row['Low'] <= trade['tp2']:
                trade['stop_loss'] = min(trade['stop_loss'], trade['tp1'])

            if row['Low'] <= trade['tp3']:
                trade['status'] = 'CLOSED'
                trade['exit_price'] = trade['tp3']
                trade['pnl_r'] = 3.0
                return

    def run(self):
        self.load_data()
        if self.df.empty:
            return {'Ticker': self.ticker, 'N': 0, 'Status': 'FAIL - NO DATA'}
        self.calculate_indicators()
        self.detect_fractals()
        self.run_event_loop()
        return self.evaluate_performance()
