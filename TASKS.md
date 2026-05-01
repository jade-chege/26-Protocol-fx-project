# TASKS - Forex Master Project

## MASTER PROJECT: Make Money Through Forex
> Goal: Deploy 5-10 mechanical strategies via prop firm funded accounts

### Phase 1: Optimize Protocol Engine (CURRENT)
- [x] Build Protocol Engine with COT, FRED, rate diffs, events, conviction matrix
- [x] Fix COT data pipeline (loads all 3 report types, maps all CFTC codes correctly)
- [x] Implement WillCo percentile formula (26-week rolling, Q-ratio based)
- [x] Build instrument selection engine with regime permissions
- [x] Build conviction matrix with 6-layer SUPPORTS/OPPOSES classification
- [x] Add SEVERE_RISK_OFF tier to v2.3.4 (classify_layer fix only — NOT the full 5-tier SEVERE spec)
- [x] Fix classify_layer for risk sentiment (v2.3.4)
- [x] **Implement SEVERE_RISK_OFF v2.4** — full 5-tier spec implemented in v2.3.4 across all 6 code touchpoints
- [x] Fix AUTO risk sentiment thresholds to align with P19 (<16/16-20/20-30/30-40/>40)
- [x] Country-aware event matching (non-US CPI/PPI/GDP correctly scoped)
- [x] ADP/NFP keyword collision fix
- [ ] Fix FRED API reliability (VIX and USD TWI intermittent failures)
- [ ] Add auto-fetch for foreign 2Y yields (currently manual in FOREIGN_YIELDS dict)
- [ ] Collect more historical COT data (need 156+ weeks for secular WillCo calculation)
- [ ] Add VIX term structure auto-fetch (currently manual check on vixcentral.com)
- [ ] Add %-Long/%-Short confirmation metric to COT engine (Spec_Longs/(Longs+Shorts)×100)
- [ ] Differentiate COT lookback periods: 13 weeks for NAS/S&P/WTI, 26 weeks for forex/gold

### Phase 2: Complete Protocol Suite
- [x] Write all 26 protocol documents with mechanical rules
- [ ] Validate all 15 technical protocols with documented backtests (sample size, dates, stress tests)
- [ ] Refine Protocol 18: Interest Rate Differential (document vs engine alignment)
- [ ] Refine Protocol 19: Risk Sentiment (multi-factor vs VIX-only AUTO mode)
- [ ] Refine Protocol 21: Fiscal Policy (document vs FISCAL_BIAS dict alignment)
- [ ] Refine Protocol 22: COT (address LOW_OI prevalence, %-confirmation thresholds)
- [ ] Fix Protocol 15 Divergence: Method 1 TP1 ratio check always fails (1R/stop = 1.0 < 2.0 → always skips)
- [ ] Build formal Pair Selection Protocol (currently implicit in InstrumentSelector engine)
- [ ] Build Multi-Strategy Conflict Resolution rules (what when 2+ protocols signal same pair?)
- [ ] Define instrument scope (currently 35 in INSTRUMENT_DNA — validate this is correct)
- [ ] Formalize Code vs Chat boundary (code: WillCo/rate diffs/selection; chat: events/qualitative macro)
- [ ] Refresh Deep Search macro data (last run: 27-03-2026, now stale by ~2 weeks)

### Phase 3: Pine Script Deployment
- [x] Review/audit Gauntlet v3.0 Pine Script — PASS (0 critical, 4 minor: add dynamic alerts recommended)
- [x] Review/audit P9 MACD Crossover v3.0 — PASS (clean, no issues)
- [x] Review/audit S&R Volume Profile v3.7 — PASS (exemplary: proper array guards, dynamic alerts, silver merge)
- [ ] Apply Gauntlet v3.1 fix (add dynamic alert() calls with regime name + ADX value)
- [ ] Code protocols 11-15 into Pine Script indicators
- [ ] Code protocol 16 (regime/ADX) into Pine Script
- [ ] Code protocol 17 (retracement vs reversal) into Pine Script
- [ ] Code protocol 24 (cross-pair relative strength) into Pine Script
- [ ] Build master dashboard indicator combining regime + bias + entry signals

### Phase 3.5: Informed Flow Detection (P23 Appendix — PILOT)
- [x] Concept analysis — detection mechanizable, interpretation conditional on geopolitical regime
- [x] Iran ceasefire case study (Mar 23, 2026) — 8.9× volume, 14-min window, validates concept
- [x] Draft trigger rules (5 conditions + intermarket confirmation, 0.25% max risk)
- [x] Quantitative validation review — 7 findings, deploy at 0.25% not 0.5%
- [ ] Collect 10+ historical cases for statistical validation (currently n=14, clustered)
- [ ] Document all 14 cases individually (5+ TPs and 3 FPs undocumented)
- [ ] Determine median winner (avg 9.4% likely skewed by 2-3 outliers)
- [ ] Decide: manual execution with pre-set alerts OR API automation required?
- [ ] Formalize as P23 appendix or standalone protocol

### Phase 3.75: Protocol Consistency Audit (4 Waves + Wave 5)
Systematic audit of all 26 protocols via protocol-consistency-checker skill. 3-phase workflow per protocol: Audit → Research Brief (Type A inline / Type B Deep Research) → Revision Directive. Apply Stage 2 Deference Rule: 3-source validated parameters require strong math/logic reason to flag.

**Wave 1 — Backbone (macro bias + regime foundation)**
- [x] P16 Regime Classification v1.1 — audit 3-layer sequential (ADX → SMA → BB) — CLOSED 2026-04-15 (9 doc changes; BBW N=50→200 HAR-calibrated; classification completeness 100%; BBW cross-protocol flags logged for P8/P11/P12/P14 Wave 3)
- [x] P19 Risk Sentiment Bias v2.0 — CLOSED 2026-04-16 (13 findings: 1 CRIT, 5 WARN, 5 NOTE, 2 OBS; all resolved; v1.0→v2.0 rewrite: 5-tier VIX table, conditional aging by shock type, asymmetric hysteresis 5pt/3-day, stepped integration table, NBFI liquidity overlay, BC priority resolution, JPY/EUR/Gold conditional rules; engine sync deferred — derive_risk_sentiment() needs VIX 45 threshold + hysteresis + aging automation)
- [ ] P18 Interest Rate Differential v2.0 — audit 2Y spread + 4-gate carry viability (Part 1 + Part 2)
- [ ] P21 Fiscal Policy Bias v2.0 — audit credibility / r-g / doom loop

**Wave 2 — Macro (remaining bias layers + process)**
- [ ] P20 News Event Execution v1.0 — 3-layer macro bias + portfolio risk
- [ ] P22 COT Contrarian Reversal v1.0 — WillCo + %-L/S + OI gate
- [ ] P23 Reassessment Cadence v1.0 — fatigue toolkit + Informed Flow appendix
- [ ] P24 Cross-Pair Relative Strength v1.0
- [ ] P25 Retail Sentiment Contrarian v2.0 — IG offline, FXSSI/Myfxbook hierarchy
- [ ] P26 Global Liquidity Regime v1.0 — scoring dashboard, crisis phases

**Wave 3 — Technical (mechanical entry strategies)**
- [ ] P1 Support & Resistance v3.4
- [ ] P2 Psychological Level Liquidity v3.0
- [ ] P3 Candlestick Reversal v3.0
- [ ] P4 Fibonacci Trading System v3.0
- [ ] P5 Moving Average Trend v2.0
- [ ] P6 MAE Dual v2.0
- [ ] P7 GMMA Trend v1.1
- [ ] P8 Bollinger Bands v2.0
- [ ] P9 MACD Crossover
- [ ] P10 RSI Reversal v2.0
- [ ] P11 Indicator Combination Framework v2.0
- [ ] P12 TTM Squeeze v2.0
- [ ] P13 Pivot Points v1.1
- [ ] P14 Master Chart Patterns v1.1
- [ ] P15 Divergence v1.1 — includes TP1 ratio bug resolution
- [ ] P17 Retracement vs Reversal v1.0

**Wave 4 — Cross-Protocol Reconciliation**
- [ ] Cross-section reconciliation sweep (contradictions across protocols)
- [ ] Formalize Multi-Strategy Conflict Resolution rules (Known Issue #9)
- [ ] Reconcile P18 integrations across P15/P17/P19/P20/P21/P25/P26

**Wave 5 — Deep Search Skill Build-Out (batched Type B prompt infrastructure)**
- [ ] Build Deep Search Skill A — Global Liquidity Regime refresh (Prompt A)
- [ ] Build Deep Search Skill B — Risk Sentiment Deep Dive (Prompt B)
- [ ] Build Deep Search Skill C — Foreign Yields + CB Tone refresh (Prompt C)
- [ ] Build Deep Search Skill D — Fiscal Policy + Credibility refresh (Prompt D)

### Phase 4: Prop Firm Competition
- [ ] Complete BabyPips training (remaining ~33%)
- [ ] Select 3-5 strongest protocols for competition deployment
- [ ] Paper trade for 2 weeks with full Protocol Engine workflow
- [ ] Enter free competitions (The5ers, The Funded Trader)
- [ ] Document live results in trade journal

---

## SUB-PROJECT: 26 Protocols Status Tracker

| # | Protocol | Doc | Engine | Backtest | Pine Script |
|---|----------|-----|--------|----------|-------------|
| 1 | Support & Resistance v3.4 | DONE | — | Needs validation | Gauntlet v3.0 |
| 2 | Psychological Level Liquidity v3.0 | DONE | — | Needs validation | Gauntlet v3.0 |
| 3 | Candlestick Reversal v3.0 | DONE | — | Needs validation | Gauntlet v3.0 |
| 4 | Fibonacci Trading System v3.0 | DONE | — | Needs validation | Gauntlet v3.0 |
| 5 | Moving Average Trend v2.0 | DONE | — | Needs validation | Gauntlet v3.0 |
| 6 | MAE Dual v2.0 | DONE | — | Needs validation | Gauntlet v3.0 |
| 7 | GMMA Trend v1.1 | DONE | — | Needs validation | Gauntlet v3.0 |
| 8 | Bollinger Bands v2.0 | DONE | — | Needs validation | Gauntlet v3.0 |
| 9 | MACD Crossover | DONE | — | Needs validation | Gauntlet v3.0 + P9 v3.0 (standalone) |
| 10 | RSI Reversal | DONE | — | Needs validation | Gauntlet v3.0 |
| 11 | Indicator Combination Framework v2.0 | DONE | — | Needs validation | Needs coding |
| 12 | TTM Squeeze v2.0 | DONE | — | Needs validation | Needs coding |
| 13 | Pivot Points v1.1 | DONE | — | Needs validation | Needs coding |
| 14 | Master Chart Patterns v1.1 | DONE | — | Needs validation | Needs coding |
| 15 | Divergence v1.1 | DONE | — | Needs validation (TP1 bug) | Needs coding |
| 16 | Regime Classification v1.1 | DONE | InstrumentSelector + Cell 2 ADX | N/A | Gauntlet v3.0 (primary) |
| 17 | Retracement vs Reversal v1.0 | DONE | — | Needs validation | Needs coding |
| 18 | Interest Rate Differential v2.0 | DONE | RateDiffEngine (28 pairs) | N/A (macro) | N/A |
| 19 | Risk Sentiment Bias v1.0 | DONE | FREDDashboard + derive_risk_sentiment | N/A (macro) | N/A |
| 20 | News Event Execution v1.0 | DONE | EventCalendar (FF API) | N/A (playbook) | N/A |
| 21 | Fiscal Policy Bias v2.0 | DONE | FISCAL_BIAS dict + derive_pair_fiscal | N/A (macro) | N/A |
| 22 | COT Contrarian Reversal v1.0 | DONE | COTProcessor + WillCo (%-L/S missing) | N/A (macro) | N/A |
| 23 | Reassessment Cadence v1.0 | DONE | SessionState persistence | N/A (process) | N/A |
| 24 | Cross-Pair Relative Strength v1.0 | DONE | InstrumentSelector scoring | Needs validation | Needs coding |
| 25 | Retail Sentiment Contrarian v2.0 | DONE | RETAIL_SENTIMENT dict + classify_layer | N/A (macro) | N/A |
| 26 | Global Liquidity Regime v1.0 | DONE | GLOBAL_LIQUIDITY + classify_layer | N/A (framework) | N/A |

### Legend
- **Doc**: Protocol document written with mechanical rules
- **Engine**: Implemented in Protocol Engine v2.3.4
- **Backtest**: Documented backtest with dates, sample sizes, results
- **Pine Script**: TradingView indicator implementation
- **Gauntlet v3.0**: P16 regime classifier + routing for protocols 1-10 (audited: PASS)
- **P9 v3.0**: Standalone MACD crossover indicator (audited: PASS)
- **S&R VP v3.7**: P1 volume profile with confluence + silver merge (audited: PASS)
