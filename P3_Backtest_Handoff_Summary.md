# PROTOCOL 3 (P3) CANDLESTICK REVERSAL BACKTEST — DEVELOPMENT SUMMARY & HANDOFF
**Generated:** 2026-05-XX  
**Status:** Phase 3.75 (Protocol Consistency Audit / Backtest Validation)  
**Next Session:** Will resume with statistical optimization and macro-filter integration.

---

## 🎯 1. ORIGINAL MANDATE (FIRST MESSAGE)
**Goal:** Build a rigorous, event-driven backtesting framework to validate the P3 Candlestick Reversal v3.0 strategy across 35 instruments (Forex, Metals, Oil, Indices).  
**Core Requirements:**
- Model the **8-filter convergence stack** (Trend, Vol, Volume, Momentum, Confirmation, R:R, Session, News).
- Implement **instrument-specific calibrations** (Gold 1.5x ATR, Silver 1.75x, Index VIX routing, etc.).
- Use **VectorBT/Pandas** for signal generation + event-driven simulation for realistic trade execution.
- Enforce **P3 Method 3** (1-candle patterns): Stop order 1 pip beyond C+1 extreme, valid for 2 candles.
- Output: Pivot tables, 95% Wilson CI, Scale-out modeling (50% @ 1R, 50% @ 2R/3R), and pass/fail report against 52% WR threshold.

---

## ⚙️ 2. ARCHITECTURE & DATA PIPELINE EVOLUTION
- **Initial Data Source:** `yfinance` (failed due to 730-day hard limit on H4 data).
- **Current Data Source:** `MetaTrader5` Python API (`SCFM MT5 Terminal`). Successfully pulls 5Y H4 OHLCV across 14 instruments.
- **Timezone/DST Handling:** Converted all timestamps to `Europe/London` to accurately enforce London/NY session filters without DST breaks.
- **Indicator Standardization:** Switched from SMA to **Wilder's Smoothing (EWMA)** for ATR, RSI, and ADX to match MT5/TradingView calculations exactly.
- **Simulation Engine:** Built custom `P3StrictValidator` class. Vectorized boolean masks for signal generation → Event-driven `for` loop for Stop Order execution, slippage/gap handling, and scale-out math.

---

## 🚨 3. CRITICAL BOTTLENECKS IDENTIFIED
1. **Trend/Momentum Paradox:** The strict P3 rule (`Price > EMA200` + `RSI < 35`) is mathematically contradictory on H4. Strong uptrends rarely dip to RSI < 35 without breaking the trend. This filtered out 99.8% of valid setups.
2. **Boolean Death Spiral:** Applying all 8 filters with strict `AND` logic across 7,500 candles yielded `N < 5` trades over 5 years, making statistical validation impossible.
3. **Stop Order Trigger Failure (Method 3):** P3 requires placing a stop order beyond the Confirmation Candle (C+1). In practice, C+1 often exhausts the move. When price pulls back to trigger the order, the trend has already reversed, or the R:R is destroyed.
4. **RSI Calculation Bug (Historical):** Early code used `.replace(0, np.inf)` before division, artificially capping RSI at ~40 and killing all bearish (`RSI > 65`) signals.
5. **Exhaustion Trap:** Massive confirmation candles place stop orders too far from current price. When triggered, entry occurs at exhaustion, leading to immediate stop-outs.

---

## 🛠️ 4. SOLUTIONS IMPLEMENTED
- **Dual-Regime RSI Routing:** 
  - Pullback Mode: `Price > EMA200` + `RSI < 50`
  - Reversal Mode: `Price < EMA200` + `RSI < 30`
  - *Result:* Broke the paradox and allowed healthy trend continuations to enter.
- **Exhaustion Filter:** Rejected setups where Confirmation Candle (C+1) range > `2.0 × ATR`. Prevents chasing exhausted moves.
- **Funnel Debugging:** Added step-by-step printouts (`Raw Signals → Confirmed → Triggered → Executed`) to isolate exactly where trades die.
- **Validation Mode Relaxations:** 
  - Pattern Geometry: Wick ≥ `1.5x` body (instead of 2.0x)
  - ADX Threshold: `≥ 15` (instead of 20)
  - *Purpose:* Increase `N` to ≥30 to test statistical significance before tightening for live deployment.
- **Event-Driven Execution Loop:** Accurately models P3 Method 3 stop orders, gap fills, 2-candle expiry, and scale-out math (`0.5*1.0 + 0.5*R` if TP hit).

---

## 🔍 5. WHAT THE LATEST CODE ATTEMPTED TO ACHIEVE
The latest script (`P3StrictValidator` v3) was a **stress test of the core P3 logic under validation conditions**. It aimed to:
1. Break the `0 trades` deadlock by combining Dual-Regime RSI, relaxed ADX/Geometry, and the Exhaustion Filter.
2. Enforce **strict Stop Order execution** (Method 3) to prove the protocol's entry mechanic actually works in real H4 price action.
3. Generate a minimum of `N ≥ 30` trades per instrument to calculate statistically valid Win Rates, Expectancy, and Wilson Confidence Intervals.
4. Quantify the impact of realistic fees, buffers, and scale-outs on net R-multiple performance.

---

## 📊 6. CURRENT STATUS & OUTPUT ANALYSIS
**Latest Run Output:**
| Instrument | Raw Signals | N_Trades | Win_Rate | Exp_R | Confidence |
|------------|-------------|----------|----------|-------|------------|
| EURUSD=X   | 82          | 15       | 20.0%    | -0.47 | LOW        |
| NAS100     | 36          | 7        | 0.0%     | -0.95 | LOW        |
| GC=F       | 24          | 1        | 0.0%     | -1.00 | LOW        |

**Diagnosis:**
- **Sample Size Still Low:** Even with relaxations, strict Stop Order triggers filtered out ~80% of signals. `N < 30` means results are not yet statistically valid.
- **Negative Expectancy:** The Stop Order mechanic is likely entering trades at the top of short-term swings (buying breakouts that immediately mean-revert). The "Confirmation + Breakout" double-confirmation is too heavy for H4 reversals.
- **Conclusion:** The 8-filter stack works for signal identification, but **Method 3 (Stop Order)** may be too restrictive for this timeframe. A Market-on-Confirmation entry (with tight invalidation) or a hybrid trigger may be required to capture the edge.

---

## 🚧 7. PENDING TASKS & NEXT STEPS
1. **Statistical Validation Breakthrough:** Implement a "Market-on-Confirmation" fallback or extend Stop Order validity to 3-4 candles to reach `N ≥ 50` without violating P3 core intent.
2. **Macro Regime Integration:** Hook in VIX, Liquidity Scorer, and News Blackout filters from `Protocol Engine v2.5.2` to filter trades during high-impact releases or risk-off regimes.
3. **Walk-Forward Validation:** Split 5Y data into 70/30 train/test windows to prevent curve-fitting on relaxed parameters.
4. **Live Execution Wrapper:** Port validated logic to the MT5 `CustomStrategy` hybrid architecture (Video 3 reference) for prop firm paper trading.
5. **Cross-Protocol Reconciliation:** Align P3 signals with P16 (ADX Regime) and P22 (COT) for confluence scoring.

---

## 📁 REFERENCE FILES & CONFIG
- **P3 Protocol:** `3 CANDLESTICK REVERSAL PROTOCOL.docx` (v3.0)
- **Macro Engine:** `Code for macro analysis.ipynb` (v2.5.2, Liquidity Scorer active)
- **Task Tracker:** `TASKS.md` (Wave 3 Technical Audits in progress)
- **Latest Code:** `p3_strict_method3_v3.py` / `P3StrictValidator` class
- **MT5 Path:** `C:\Program Files\SCFM MT5 Terminal\terminal64.exe`
- **Symbols:** `EURUSD.pro`, `XAUUSD.pro`, `XAGUSD.pro`, `USOIL`, `NAS100.pro`, etc.

*Note for Next Session:* Start by addressing the `N < 30` bottleneck. Consider testing `Market-on-C+1-Close` entry with a `1.5x ATR` time-stop to isolate the raw pattern edge before re-introducing stop-order friction.
