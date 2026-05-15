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
            'signals_generated', 'r_r_skipped', 'trades_executed', 'wins'
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
        df['ATR_SMA'] = df['ATR'].rolling(20).mean()
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

        # ADX(14) - Wilder's Vectorized
        high = df['High']
        low = df['Low']
        high_shift = high.shift(1)
        low_shift = low.shift(1)

        plusDM = np.where((high - high_shift) > (low_shift - low), np.maximum(high - high_shift, 0), 0)
        minusDM = np.where((low_shift - low) > (high - high_shift), np.maximum(low_shift - low, 0), 0)

        plusDM_series = pd.Series(plusDM, index=df.index)
        minusDM_series = pd.Series(minusDM, index=df.index)

        plusDI = 100 * wilder(plusDM_series, 14) / df['ATR']
        minusDI = 100 * wilder(minusDM_series, 14) / df['ATR']

        df['DX'] = 100 * abs(plusDI - minusDI) / (plusDI + minusDI)
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


    def detect_pattern_tier(self, i):
        df = self.df
        row = df.iloc[i]
        prev = df.iloc[i-1]
        prev2 = df.iloc[i-2]

        def is_bullish(r): return r['Close'] > r['Open']
        def is_bearish(r): return r['Close'] < r['Open']
        def body(r): return abs(r['Close'] - r['Open'])
        def r_range(r): return r['High'] - r['Low']
        def upper_wick(r): return r['High'] - max(r['Open'], r['Close'])
        def lower_wick(r): return min(r['Open'], r['Close']) - r['Low']
        def midpoint(r): return (r['Open'] + r['Close']) / 2.0

        # Tier 1 - Bullish Engulfing
        if is_bearish(prev) and is_bullish(row) and row['Open'] < prev['Close'] and row['Close'] > prev['Open']:
            return 1, 'LONG'
        # Tier 1 - Bearish Engulfing
        if is_bullish(prev) and is_bearish(row) and row['Open'] > prev['Close'] and row['Close'] < prev['Open']:
            return 1, 'SHORT'

        # Tier 1 - Morning Star
        if is_bearish(prev2) and (body(prev) < 0.3 * r_range(prev)) and is_bullish(row) and row['Close'] > midpoint(prev2):
            return 1, 'LONG'
        # Tier 1 - Evening Star
        if is_bullish(prev2) and (body(prev) < 0.3 * r_range(prev)) and is_bearish(row) and row['Close'] < midpoint(prev2):
            return 1, 'SHORT'

        # Tier 2 - Hammer (Bullish)
        if lower_wick(row) >= 2 * body(row) and upper_wick(row) <= 0.5 * body(row) and row['Close'] >= row['Low'] + 0.75 * r_range(row):
            return 2, 'LONG'
        # Tier 2 - Shooting Star (Bearish)
        if upper_wick(row) >= 2 * body(row) and lower_wick(row) <= 0.5 * body(row) and row['Close'] <= row['Low'] + 0.25 * r_range(row):
            return 2, 'SHORT'

        # Tier 3 - Doji (Bullish / Bearish based on RSI)
        if r_range(row) > 0 and (body(row) / r_range(row)) <= 0.10 and upper_wick(row) > 0 and lower_wick(row) > 0:
            if row['RSI'] < 30:
                return 3, 'LONG'
            if row['RSI'] > 70:
                return 3, 'SHORT'

        return 0, None

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
        use_from_bar_high = 0
        use_from_bar_low = 0

        for i in range(200, len(df)):
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
                use_from_bar_high = i + 2
                self.funnel['fractals_detected'] += 1
            if df['Fractal_Low'].iloc[i]:
                last_swing_low = df.iloc[i-2]['Low']
                use_from_bar_low = i + 2
                self.funnel['fractals_detected'] += 1

            # 2. DETECT SIGNALS
            if last_swing_high is not None and last_swing_low is not None:
                if i < use_from_bar_high or i < use_from_bar_low:
                    continue

                # Check swing distance
                swing_dist = abs(last_swing_high - last_swing_low)
                if swing_dist < 1.5 * row['ATR']:
                    continue

                self.funnel['valid_swings'] += 1

                tier, p_dir = self.detect_pattern_tier(i)

                # LONG SETUP
                if p_dir == 'LONG':
                    fib_50 = last_swing_low + (last_swing_high - last_swing_low) * 0.50
                    fib_618 = last_swing_low + (last_swing_high - last_swing_low) * 0.382
                    golden_high = fib_50
                    golden_low = fib_618

                    if golden_low <= row['Low'] <= golden_high or golden_low <= row['Close'] <= golden_high:
                        self.funnel['fib_zones_active'] += 1

                        if self.check_market_gates(row, prev_row, direction='LONG'):
                            self.funnel['market_gates_passed'] += 1

                        vol_ok = False
                        if tier == 1:
                            vol_ok = True
                        elif tier == 2 and (row['Volume'] == 0 or np.isnan(row['VolSMA']) or row['Volume'] > 1.2 * row['VolSMA']):
                            vol_ok = True
                        elif tier == 3 and (row['Volume'] == 0 or np.isnan(row['VolSMA']) or row['Volume'] > 1.2 * row['VolSMA']) and row['RSI'] < 30:
                            vol_ok = True

                        if vol_ok:
                            self.funnel['pattern_confirmed'] += 1
                            self.funnel['signals_generated'] += 1

            # --- DYNAMIC STOP ROUTING FOR LONGS ---
                            vol_ratio = row['ATR'] / row['ATR_SMA'] if pd.notna(row['ATR_SMA']) and row['ATR_SMA'] > 0 else 1.0

                            if vol_ratio > 1.5:
                                stop_method = 'B'
                                # Method B: Swing Low - 2.0x ATR Buffer
                                stop_loss = last_swing_low - (2.0 * row['ATR'])
                            else:
                                stop_method = 'A'
                                # Method A: 78.6% Retracement Anchor (No extra ATR buffer)
                                stop_loss = last_swing_high - (swing_dist * 0.786)

                            # PROTOCOL GATE: 1.5:1 R:R Minimum at Entry
                            entry_risk = abs(row['Close'] - stop_loss)
                            entry_reward_t1 = abs(last_swing_high - row['Close'])

                            if entry_risk <= 0 or (entry_reward_t1 / entry_risk) < 1.5:
                                self.funnel['r_r_skipped'] += 1
                                continue

                            new_trade = {
                                'direction': 'LONG',
                                'entry_price': row['Close'],
                                'stop_loss': stop_loss,
                                'initial_risk': entry_risk,
                                'tp1': last_swing_high,
                                'tp2': last_swing_high + (swing_dist * 0.272),
                                'tp3': last_swing_high + (swing_dist * 0.618),
                                'tp4': last_swing_high + (swing_dist * 1.618),
                                'status': 'OPEN',
                                'entry_time': i,
                                'bars_held': 0,
                                'size': 1.0,
                                'locked_pnl_r': 0.0,
                                't1_hit': False,
                                't2_hit': False,
                                'highest_high': row['High'],
                                'volatility_ratio': vol_ratio,
                                'stop_method': stop_method,
                                'swing_dist': swing_dist,
                                'reach_tracker': {'t1': False, 't2': False, 't3': False},
                                'exit_reason': None,
                                't3_hit': False
                            }
                            if not any(t['direction'] == 'LONG' for t in active_trades):
                                active_trades.append(new_trade)
                                self.funnel['trades_executed'] += 1

                # SHORT SETUP
                if p_dir == 'SHORT':
                    fib_50 = last_swing_high - (last_swing_high - last_swing_low) * 0.50
                    fib_618 = last_swing_high - (last_swing_high - last_swing_low) * 0.382
                    golden_low = fib_50
                    golden_high = fib_618

                    if golden_low <= row['High'] <= golden_high or golden_low <= row['Close'] <= golden_high:
                        self.funnel['fib_zones_active'] += 1

                        if self.check_market_gates(row, prev_row, direction='SHORT'):
                            self.funnel['market_gates_passed'] += 1

                        vol_ok = False
                        if tier == 1:
                            vol_ok = True
                        elif tier == 2 and (row['Volume'] == 0 or np.isnan(row['VolSMA']) or row['Volume'] > 1.2 * row['VolSMA']):
                            vol_ok = True
                        elif tier == 3 and (row['Volume'] == 0 or np.isnan(row['VolSMA']) or row['Volume'] > 1.2 * row['VolSMA']) and row['RSI'] > 70:
                            vol_ok = True

                        if vol_ok:
                            self.funnel['pattern_confirmed'] += 1
                            self.funnel['signals_generated'] += 1

            # --- DYNAMIC STOP ROUTING FOR SHORTS ---
                            vol_ratio = row['ATR'] / row['ATR_SMA'] if pd.notna(row['ATR_SMA']) and row['ATR_SMA'] > 0 else 1.0

                            if vol_ratio > 1.5:
                                stop_method = 'B'
                                # Method B: Swing High + 2.0x ATR Buffer
                                stop_loss = last_swing_high + (2.0 * row['ATR'])
                            else:
                                stop_method = 'A'
                                # Method A: 78.6% Retracement Anchor (No extra ATR buffer)
                                stop_loss = last_swing_low + (swing_dist * 0.786)

                            # PROTOCOL GATE: 1.5:1 R:R Minimum at Entry
                            entry_risk = abs(row['Close'] - stop_loss)
                            entry_reward_t1 = abs(row['Close'] - last_swing_low)

                            if entry_risk <= 0 or (entry_reward_t1 / entry_risk) < 1.5:
                                self.funnel['r_r_skipped'] += 1
                                continue

                            new_trade = {
                                'direction': 'SHORT',
                                'entry_price': row['Close'],
                                'stop_loss': stop_loss,
                                'initial_risk': entry_risk,
                                'tp1': last_swing_low,
                                'tp2': last_swing_low - (swing_dist * 0.272),
                                'tp3': last_swing_low - (swing_dist * 0.618),
                                'tp4': last_swing_low - (swing_dist * 1.618),
                                'status': 'OPEN',
                                'entry_time': i,
                                'bars_held': 0,
                                'size': 1.0,
                                'locked_pnl_r': 0.0,
                                't1_hit': False,
                                't2_hit': False,
                                'lowest_low': row['Low'],
                                'volatility_ratio': vol_ratio,
                                'stop_method': stop_method,
                                'swing_dist': swing_dist,
                                'reach_tracker': {'t1': False, 't2': False, 't3': False},
                                'exit_reason': None,
                                't3_hit': False
                            }
                            if not any(t['direction'] == 'SHORT' for t in active_trades):
                                active_trades.append(new_trade)
                                self.funnel['trades_executed'] += 1

    def manage_trade(self, trade, row, i):
        trade['bars_held'] += 1

        # Reach Tracking
        if trade['direction'] == 'LONG':
            if row['High'] >= trade['tp1']: trade['reach_tracker']['t1'] = True
            if row['High'] >= trade['tp2']: trade['reach_tracker']['t2'] = True
            if row['High'] >= trade['tp3']: trade['reach_tracker']['t3'] = True
        else:
            if row['Low'] <= trade['tp1']: trade['reach_tracker']['t1'] = True
            if row['Low'] <= trade['tp2']: trade['reach_tracker']['t2'] = True
            if row['Low'] <= trade['tp3']: trade['reach_tracker']['t3'] = True

        # Time exits
        if trade['bars_held'] >= 30 and not trade['t1_hit']:
            trade['status'] = 'CLOSED'
            trade['exit_price'] = row['Close']
            trade['exit_reason'] = 'Time Stop (30 Bars)'
            if trade['direction'] == 'LONG':
                trade['locked_pnl_r'] += trade['size'] * ((trade['exit_price'] - trade['entry_price']) / trade['initial_risk'])
            else:
                trade['locked_pnl_r'] += trade['size'] * ((trade['entry_price'] - trade['exit_price']) / trade['initial_risk'])
            trade['pnl_r'] = trade['locked_pnl_r']
            return

        # 20 bars without T1 and profit > 0
        if trade['bars_held'] >= 20 and not trade['t1_hit']:
            is_profit = (row['Close'] > trade['entry_price']) if trade['direction'] == 'LONG' else (row['Close'] < trade['entry_price'])
            if is_profit:
                trade['status'] = 'CLOSED'
                trade['exit_price'] = row['Close']
                trade['exit_reason'] = 'Time Stop (20 Bars)'
                if trade['direction'] == 'LONG':
                    trade['locked_pnl_r'] += trade['size'] * ((trade['exit_price'] - trade['entry_price']) / trade['initial_risk'])
                else:
                    trade['locked_pnl_r'] += trade['size'] * ((trade['entry_price'] - trade['exit_price']) / trade['initial_risk'])
                trade['pnl_r'] = trade['locked_pnl_r']
                return

        if trade['direction'] == 'LONG':
            trade['highest_high'] = max(trade['highest_high'], row['High'])

            # Check Trailing/SL hit first
            if row['Low'] <= trade['stop_loss']:
                trade['status'] = 'CLOSED'
                trade['exit_price'] = trade['stop_loss']
                if trade.get('t2_hit', False):
                    trade['exit_reason'] = 'Trailing Stop Hit'
                else:
                    trade['exit_reason'] = 'Initial Stop Loss'
                trade['locked_pnl_r'] += trade['size'] * ((trade['exit_price'] - trade['entry_price']) / trade['initial_risk'])
                trade['pnl_r'] = trade['locked_pnl_r']
                return

            # Check T1
            if row['High'] >= trade['tp1'] and not trade['t1_hit']:
                trade['locked_pnl_r'] += 0.5 * ((trade['tp1'] - trade['entry_price']) / trade['initial_risk'])
                trade['size'] -= 0.5
                trade['stop_loss'] = trade['entry_price']
                trade['t1_hit'] = True
                trade['exit_reason'] = 'T1 Partial (50%)'

            # Check T2
            if row['High'] >= trade['tp2'] and trade['t1_hit'] and not trade['t2_hit']:
                trade['locked_pnl_r'] += 0.25 * ((trade['tp2'] - trade['entry_price']) / trade['initial_risk'])
                trade['size'] -= 0.25
                trade['stop_loss'] = trade['tp1']
                trade['t2_hit'] = True
                trade['exit_reason'] = 'T2 Partial (75% Total)'

            # Check T3 full hit
            if row['High'] >= trade['tp3'] and trade['t2_hit']:
                trade['status'] = 'CLOSED'
                trade['exit_price'] = trade['tp3']
                trade['exit_reason'] = 'T3 Full Target'
                trade['t3_hit'] = True
                trade['reach_tracker']['t3'] = True
                trade['locked_pnl_r'] += trade['size'] * ((trade['exit_price'] - trade['entry_price']) / trade['initial_risk'])
                trade['pnl_r'] = trade['locked_pnl_r']
                return

            # Trailing logic
            if trade['t2_hit']:
                trade['stop_loss'] = max(trade['stop_loss'], trade['highest_high'] - (2.0 * row['ATR']))

        elif trade['direction'] == 'SHORT':
            trade['lowest_low'] = min(trade['lowest_low'], row['Low'])

            if row['High'] >= trade['stop_loss']:
                trade['status'] = 'CLOSED'
                trade['exit_price'] = trade['stop_loss']
                if trade.get('t2_hit', False):
                    trade['exit_reason'] = 'Trailing Stop Hit'
                else:
                    trade['exit_reason'] = 'Initial Stop Loss'
                trade['locked_pnl_r'] += trade['size'] * ((trade['entry_price'] - trade['exit_price']) / trade['initial_risk'])
                trade['pnl_r'] = trade['locked_pnl_r']
                return

            # Check T1
            if row['Low'] <= trade['tp1'] and not trade['t1_hit']:
                trade['locked_pnl_r'] += 0.5 * ((trade['entry_price'] - trade['tp1']) / trade['initial_risk'])
                trade['size'] -= 0.5
                trade['stop_loss'] = trade['entry_price']
                trade['t1_hit'] = True
                trade['exit_reason'] = 'T1 Partial (50%)'

            # Check T2
            if row['Low'] <= trade['tp2'] and trade['t1_hit'] and not trade['t2_hit']:
                trade['locked_pnl_r'] += 0.25 * ((trade['entry_price'] - trade['tp2']) / trade['initial_risk'])
                trade['size'] -= 0.25
                trade['stop_loss'] = trade['tp1']
                trade['t2_hit'] = True
                trade['exit_reason'] = 'T2 Partial (75% Total)'

            if row['Low'] <= trade['tp3'] and trade['t2_hit']:
                trade['status'] = 'CLOSED'
                trade['exit_price'] = trade['tp3']
                trade['exit_reason'] = 'T3 Full Target'
                trade['t3_hit'] = True
                trade['reach_tracker']['t3'] = True
                trade['locked_pnl_r'] += trade['size'] * ((trade['entry_price'] - trade['exit_price']) / trade['initial_risk'])
                trade['pnl_r'] = trade['locked_pnl_r']
                return

            # Trailing logic
            if trade['t2_hit']:
                trade['stop_loss'] = min(trade['stop_loss'], trade['lowest_low'] + (2.0 * row['ATR']))

    def run(self):
        self.load_data()
        if self.df.empty:
            return {'Ticker': self.ticker, 'N': 0, 'Status': 'FAIL - NO DATA'}
        self.calculate_indicators()
        self.detect_fractals()
        self.run_event_loop()
        return self.evaluate_performance()
    def print_diagnostics(self):
        if not self.trades:
            print("No trades to analyze.")
            return

        print("\n=== DIAGNOSTIC REPORT ===")
        print(f"Instrument: {self.ticker}")
        print(f"Total Trades: {len(self.trades)}\n")

        # Method Split Diagnostics
        def calc_stats(method_trades):
            if not method_trades: return "N=0"
            n = len(method_trades)
            avg_r = sum(t['pnl_r'] for t in method_trades) / n
            avg_tp1_r = sum(abs(t['tp1'] - t['entry_price']) / t['initial_risk'] for t in method_trades) / n
            wr = sum(1 for t in method_trades if t['pnl_r'] > 0) / n
            return f"N={n} | WR: {wr*100:.1f}% | Avg TP1 R/R: {avg_tp1_r:.2f} | Avg R: {avg_r:.2f}"

        print("--- Stop Method Performance Split ---")
        print(f"Method A (Fib 78.6): {calc_stats([t for t in self.trades if t.get('stop_method') == 'A'])}")
        print(f"Method B (Swing Point): {calc_stats([t for t in self.trades if t.get('stop_method') == 'B'])}")

        # Target Reach Rates
        print("\n--- Target Hit Rates ---")
        t1_reach = sum(1 for t in self.trades if t['reach_tracker']['t1'])
        t2_reach = sum(1 for t in self.trades if t['reach_tracker']['t2'])
        t3_reach = sum(1 for t in self.trades if t['reach_tracker']['t3'])
        t1_exit = sum(1 for t in self.trades if t['t1_hit'])
        t2_exit = sum(1 for t in self.trades if t['t2_hit'])
        t3_exit = sum(1 for t in self.trades if t['t3_hit'])
        n = len(self.trades)

        reach_data = [
            {'Target': 'T1', '% Reached': f"{(t1_reach/n)*100:.1f}%", '% Closed At': f"{(t1_exit/n)*100:.1f}%"},
            {'Target': 'T2', '% Reached': f"{(t2_reach/n)*100:.1f}%", '% Closed At': f"{(t2_exit/n)*100:.1f}%"},
            {'Target': 'T3', '% Reached': f"{(t3_reach/n)*100:.1f}%", '% Closed At': f"{(t3_exit/n)*100:.1f}%"}
        ]
        import pandas as pd
        print(pd.DataFrame(reach_data).to_markdown(index=False))

        # Exit Reason Distribution
        print("\n--- Exit Reason Distribution ---")
        reasons = {}
        for t in self.trades:
            reason = t.get('exit_reason', 'Unknown')
            reasons.setdefault(reason, {'count': 0, 'total_r': 0})
            reasons[reason]['count'] += 1
            reasons[reason]['total_r'] += t['pnl_r']

        exit_data = [{'Exit Reason': r, 'Count': d['count'], 'Avg R': f"{d['total_r']/d['count']:.2f}"}
                     for r, d in sorted(reasons.items(), key=lambda x: x[1]['count'], reverse=True)]
        print(pd.DataFrame(exit_data).to_markdown(index=False))

        # Risk Geometry
        print("\n--- Risk Geometry ---")
        avg_risk = sum(t['initial_risk'] for t in self.trades) / n
        avg_swing = sum(t['swing_dist'] for t in self.trades) / n
        avg_tp1_r = sum(abs(t['tp1'] - t['entry_price']) / t['initial_risk'] for t in self.trades) / n
        geom_data = [
            {'Metric': 'Average Initial Risk', 'Value': f"{avg_risk:.5f}"},
            {'Metric': 'Average Swing Distance', 'Value': f"{avg_swing:.5f}"},
            {'Metric': 'Avg TP1 Reward / Risk', 'Value': f"{avg_tp1_r:.2f}R"}
        ]
        print(pd.DataFrame(geom_data).to_markdown(index=False))

        # PHASE B.0: FAILURE ANALYSIS
        print("\n--- Phase B.0: Failure Analysis ---")

        # 1. Avg Entry Retracement Depth %
        depths = []
        for t in self.trades:
            # Safe division using max() to prevent ZeroDivisionError
            safe_dist = max(t['swing_dist'], 1e-9)
            depth_from_top = abs(t['tp1'] - t['entry_price']) / safe_dist
            depths.append(depth_from_top)

        avg_depth = sum(depths) / len(depths) if depths else 0
        print(f"Avg Entry Retracement Depth (from Swing Extreme): {avg_depth:.1%}")

        # 2. Stop Hit Velocity (Bars Held for Losers)
        losers = [t for t in self.trades if t['pnl_r'] < 0]
        if losers:
            stop_bars = [t['bars_held'] for t in losers]
            immediate_stops = sum(1 for b in stop_bars if b < 5)
            print(f"Avg Bars Held (Stopped Trades): {sum(stop_bars)/len(stop_bars):.1f}")
            print(f"Immediate Stops (< 5 Bars): {immediate_stops}/{len(losers)} ({immediate_stops/len(losers)*100:.0f}%)")
        else:
            print("No stopped trades to analyze.")

        # 3. Method Usage
        method_a = sum(1 for t in self.trades if t.get('stop_method') == 'A')
        method_b = sum(1 for t in self.trades if t.get('stop_method') == 'B')
        print(f"Method A Usage: {method_a} ({method_a/n*100:.0f}%)")
        print(f"Method B Usage: {method_b} ({method_b/n*100:.0f}%)")

        print("=========================\n")
if __name__ == '__main__':
    # EXPAND UNIVERSE TO CORE ASSETS
    # Forex Majors + Gold + Nasdaq to aggregate sample size
    tickers = ['GBPUSD=X', 'EURUSD=X', 'GC=F', 'NQ=F']

    all_results = []
    all_trades = []
    aggregate_funnel = {
        'signals_generated': 0, 'r_r_skipped': 0, 'trades_executed': 0, 'wins': 0
    }

    print("="*60)
    print("PHASE B.0: FAILURE ANALYSIS")
    print("="*60)

    for ticker in tickers:
        print(f"\n>>> PROCESSING: {ticker} <<<")
        p4 = P4FibonacciBacktester(ticker=ticker)
        res = p4.run()

        # Collect individual stats
        all_results.append(res)

        # Collect individual trades for combined analysis
        all_trades.extend(p4.trades)

        # Aggregate Funnel with Safe Key Handling
        for key in aggregate_funnel:
            if key in p4.funnel:
                aggregate_funnel[key] += p4.funnel[key]

        # Print individual diagnostics
        p4.print_diagnostics()

    # --- AGGREGATE PERFORMANCE ANALYSIS ---
    print("\n" + "="*60)
    print("AGGREGATED RESULTS (ALL INSTRUMENTS)")
    print("="*60)

    if not all_trades:
        print("NO TRADES EXECUTED ACROSS ALL INSTRUMENTS.")
    else:
        n = len(all_trades)
        wins = sum(1 for t in all_trades if t['pnl_r'] > 0)
        total_r = sum(t['pnl_r'] for t in all_trades)
        avg_r = total_r / n

        wr = wins / n
        gross_profit = sum(t['pnl_r'] for t in all_trades if t['pnl_r'] > 0)
        gross_loss = abs(sum(t['pnl_r'] for t in all_trades if t['pnl_r'] < 0))
        pf = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Wilson CI Calculation for Aggregate
        z = norm.ppf(1 - (1 - 0.95) / 2)
        denominator = 1 + z**2 / n
        centre_adjusted_probability = wr + z**2 / (2 * n)
        adjusted_standard_deviation = np.sqrt((wr * (1 - wr) + z**2 / (4 * n)) / n)
        ci_lb = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator

        gates = (n >= 40) and (ci_lb >= 0.48) and (pf >= 1.2) and (avg_r >= 0.4)

        print(f"Combined N: {n}")
        print(f"Win Rate: {wr*100:.1f}%")
        print(f"Avg R: {avg_r:.3f}")
        print(f"Profit Factor: {pf:.2f}")
        print(f"Wilson CI LB: {ci_lb:.3f}")
        print(f"STATUS: {'PASS' if gates else 'FAIL'}")

        sigs = aggregate_funnel.get('signals_generated', 1)
        skips = aggregate_funnel.get('r_r_skipped', 0)
        print(f"Signals Skipped by R/R Gate: {skips} ({(skips/max(1,sigs))*100:.1f}%)")
        print(f"Executed: {aggregate_funnel['trades_executed']}")

        print("\n--- PER-INSTRUMENT BREAKDOWN ---")
        df_summary = pd.DataFrame(all_results)
        if 'Funnel' in df_summary.columns:
            display_cols = ['Ticker', 'N', 'WR', 'Avg_R', 'PF', 'CI_LB', 'Status']
            print(df_summary[display_cols].to_markdown(index=False))
        else:
            print(df_summary.to_markdown(index=False))

    print("\n" + "="*60)
    print("EXECUTION COMPLETE")
    print("="*60)
