FOREX MASTER PROJECT - Working Memory
Owner
Edwin Chege (jade.chege24@gmail.com)

Mission
Systematically build, validate, and deploy a portfolio of elite, 100% mechanical forex trading strategies through the "Project Playbook Gauntlet" framework. Generate capital via prop firm competitions (zero-risk path) then scale.

Current Phase
Optimize & Complete - Protocol Engine v2.5.2 is operational. Focus: fix remaining issues, complete fundamental protocols, validate with backtests, prep for prop firm. Wave 1 (Backbone) and Wave 2 (Macro) audits are CLOSED. Actively executing Wave 3 Audits (P1-P15 Technical Strategies).

Architecture Overview
Version Control Status (Active)
System: Local Git Repository.

Tracked Assets: Engine code (Code for macro analysis.ipynb), all 47 protocol documents, and system architecture markdown files.

Ignored Assets: Jupyter checkpoints, Word temp files (~$), and daily data outputs (cot_data, .json) are safely excluded via .gitignore.

Standard Operating Procedure (Save Routine):

Clear all Jupyter cell outputs.

Run git add .

Run git commit -m "Description of changes"

AI Directive: Before suggesting massive code rewrites or protocol overhauls, remind me to run a Git commit to establish a restore point.

The 26 Protocol System
Derived from BabyPips "School of Pipsology" (372 lessons). Five categories:

Cat 1 - Mechanical Strategies (Technical): Protocols 1-15

P1: Support & Resistance (v3.5) | P2: Psychological Level Liquidity | P3: Candlestick Reversal

P4: Fibonacci | P5: Moving Average Trend | P6: MAE Dual | P7: GMMA Trend

P8: Bollinger Bands | P9: MACD Crossover | P10: RSI Reversal

P11: Indicator Combination Framework | P12: TTM Squeeze | P13: Pivot Points

P14: Master Chart Patterns | P15: Divergence

Cat 2 - Regime & Classification: Protocol 16 (Regime Classification via ADX)

Cat 3 - Retracement vs Reversal: Protocol 17

Cat 4A - Market Bias Models (Macro/Ongoing):

P18: Interest Rate Differential | P19: Risk Sentiment | P21: Fiscal Policy

P22: COT Contrarian Reversal | P25: Retail Sentiment Contrarian | P26: Global Liquidity Regime

Cat 4B - Macro Event Playbooks: P20: News Event Execution

Cat 5 - Meta/Process: P23: Reassessment Cadence | P24: Cross-Pair Relative Strength Selection

Protocol Engine v2.5.2 (OPERATIONAL)
Located: C:\Users\Chege\Documents\forex\forex learnings\Code for macro analysis.ipynb
The notebook is ~324KB and fully synced to the Cowork folder. A full copy of the engine code also exists in Pine Scripts.docx.
The ConvictionMatrix Counter() bug has been confirmed fixed — classify_layer() normalizes all 6 layers to SUPPORTS/OPPOSES/NEUTRAL per trade direction using INSTRUMENT_DNA. The old Counter() logic is gone.

8 Engines:

COT Processor — Downloads/caches CFTC data (disagg, tff, legacy), maps CFTC codes, calculates WillCo percentile. Tracks 12 instruments (7 forex, 3 commodities, 2 indices).

FRED Dashboard — Pulls VIX, HY OAS, US 2Y/10Y, TIPS, Breakeven, USD TWI from FRED API.

Rate Diff Engine — Calculates 28-pair interest rate differentials (7 majors + 21 crosses) with shift tracking.

Event Calendar — Forex Factory API integration with country-aware matching, ADP/NFP collision fix, tiered blackout windows.

Session State — Persists positions, P&L, risk usage, liquidity regime, VIX>25 duration tracking across sessions via JSON.

Conviction Matrix — Normalizes 6 layers (liquidity, fiscal, rate_diff, risk_sentiment, retail, regime) to SUPPORTS/OPPOSES/NEUTRAL per trade direction using INSTRUMENT_DNA.

Instrument Selector — Scores all 35 instruments, applies regime permissions, concentration limits, session compatibility. Outputs ranked watchlist.

Liquidity Scorer — Autonomously calculates G5 Net Liquidity, DXY 200-SMA, and Stress Triggers (SOFR/TGA). Uses a multi-source pipeline (FRED, BoE IADB, yfinance, smdx). Eliminates FX look-ahead bias via daily historical multipliers and mitigates Pandas timeline wipeouts via a 400-day ffill buffer.

Key Config (Cell 1 — change per macro assessment):

GLOBAL_LIQUIDITY, GLOBAL_RISK_SENTIMENT, FISCAL_BIAS, RETAIL_SENTIMENT

FOREIGN_YIELDS (manual 2Y yields for 7 currencies)

FRED_KEY: ffc67e085d555e2dca3d514470edf6b0

Quick Run Config (Cell 2 — change per session):

CURRENT_SESSION, INSTRUMENT_REGIME (ADX values), COT_WEEKLY_ADX, retail sentiment updates

Platform Stack
Charting: TradingView (Pine Script indicators)

Execution: MT4/MT5

Analysis: Python/Jupyter (Protocol Engine), Claude AI, Gemini/Grok

Data: CFTC COT (via CFTC zip files), FRED API, Forex Factory API, central bank rates (manual), retail sentiment (manual from FXSSI/Myfxbook), yfinance (DXY, CBON proxy), BoE IADB API.

Multi-Chat Architecture (from prior LM Arena sessions)
Three specialized AI chat roles were designed:

Chief of Staff — System architecture, protocol design, prompt engineering, concept analysis

Jupyter Code Writer — Protocol Engine development, code review, config verification

Implementation Guide — Live trading execution, session state, chart scanning, trade management
Each has a 10-section Session Handoff Protocol + 3-tier Context Management (Tier 1: rolling footer from exchange 10+, Tier 2: warning from exchange 20+, Tier 3: auto-handoff at ~80% context)

Key Design Decisions (from prior sessions)
Prompt C (Foreign Yields) split: TradingView for 7 exact yields (3 min weekly) + search for CB tone analysis (monthly)

Daily risk sentiment workflow: VIX <16 or >35 → AUTO reliable; VIX 16-25 → 60-sec manual check (vixcentral + VVIX + HY); regime change → full Prompt D search

FOREIGN_YIELDS cadence: Weekly per P18, plus after CB decisions and Tier 1 data releases

COT_WEEKLY_ADX source: TradingView weekly chart ADX(14) for currencies with extreme WillCo

INSTRUMENT_REGIME timeframe: Execution timeframe (H4), NOT weekly

classify_layer rate_diff (Hybrid Model v2.0): Directional bias uses SHIFT (spread change): shift ≥50bp = STRONG → SUPPORTS/OPPOSES; shift 25-50bp = MODERATE → NEUTRAL; shift <25bp = LOW → NEUTRAL. Carry viability (Part 2) uses ABSOLUTE spread level: >200bp = MAX, >100bp = STRONG, >50bp = MOD, ≤50bp = LOW. Engine _rate_diff_direction() derives conviction from shift_class, not strength

TRANSITIONAL regime in conviction matrix: Counts as populated (not empty) but generates NEUTRAL — design choice, not bug

derive_pair_fiscal() both-BEARISH logic: When both currencies are BEARISH, higher intensity rank = MORE bearish = WORSE for that currency. So base_rank > quote_rank → base is more bearish → short the base → return BEARISH. This is the OPPOSITE of the both-BULLISH case (where higher rank = stronger = long the base).

FISCAL_BIAS staleness tracking: Dict entries include 'updated' date. Engine prints ⚠ warning for entries >30 days old. _fb_get() helper reads both old tuple and new dict format.

P26 Liquidity Automation: Manual string input replaced by LiquidityScorer. Uses CBON ETF as a proxy for Chinese yields to bypass hostile APIs. Enforces a "Core G4 Hard Stop" (halts sizing if US, EU, UK, or JP data feeds fail).

Known Issues (Current)
1. FRED API Intermittent Failures
VIX (VIXCLS) and USD Broad TWI (DTWEXBGS) sometimes fail with DNS resolution or 500 errors

Regime falls back to UNKNOWN when VIX unavailable; carry shows UNKNOWN

Workaround: Manual GLOBAL_RISK_SENTIMENT override (currently using EXTREME_RISK_OFF), or we can use smdx data source This is something to work on in the future

2. COT OI Gate Mostly Failing
Most instruments show OI Gate: FAIL (OI ratio < 1.0 vs 52-week average)

Only GBP, AUD, WTI showing OI Gate: PASS

This is likely market-wide low participation, not a code bug — but limits P22 setup validity

3. WillCo Edge Cases
EUR, NZD, NAS all at 0.0 (extreme short) — contrarian BULL signals but LOW_OI prevents setup_valid

WTI at 100.0 (extreme long) — contrarian BEAR, OI PASS, but %-L not confirmed

With only 64 rows per instrument (about 15 months), percentile calculations work but longer lookback (156w) not possible yet

4. Conviction Matrix Conservative
Current run: only XAU/USD and GBP/USD tradeable (REDUCE SIZE). USD/CHF, NZD/CHF, GBP/JPY all DO NOT TRADE

Rate diff opposition (USD strength via large spread shifts) creating OPPOSES on many pairs

This is working as designed — the system correctly blocks low-conviction trades

5. Foreign Yield Staleness
Manual entry, last updated 2026-04-01

No auto-fetch mechanism; relies on Edwin manually updating FOREIGN_YIELDS dict

Will show STALE warnings after 7 days

6. Protocol 15 (Divergence) — TP1 Ratio Bug
Method 1 checks: "TP1 distance ÷ stop distance < 2.0 → skip"

TP1 defaults to 1R (1:1), so ratio = 1.0, which ALWAYS fails the < 2.0 check

Architect flagged: likely should check TP2 potential or nearest structural target instead

Original logic preserved pending review

7. Multi-Strategy Conflict Resolution (Not Yet Built)
No formal tiebreaker when 2+ protocols signal on same pair simultaneously

"Questions and thoughts" doc proposes ranking by trade count + time-based metrics

Need formal Protocol Conflict Resolution rules

8. IG Client Sentiment Permanently Offline
Engine now supports dict-based RETAIL_SENTIMENT with 1-day staleness tracking, source-count gating for JPY, and fractional veto (0.5 opposes) for Standard-tier readings.

9. Informed Flow Detection (Moved to P19 Appendix — DRAFT, Unvalidated)
Concept: detect anomalous price moves preceding unscheduled geopolitical events

Iran ceasefire case study (Mar 23, 2026): 8.9× volume spike, 14-min execution window

Draft trigger: 5 simultaneous conditions + intermarket confirmation

Risk cap: 0.25% max (non-negotiable until 10+ cases backtested)

Positive expectancy directionally robust but FPR has wide CI (12.8-64.1%, n=14)

Status: PILOT DRAFT, needs 10+ historical cases for validation

Open questions: false positive base rate, median winner vs outlier-skewed avg, manual vs API execution

10. Gauntlet Script Instrument Mode Must Match Pair
Gold mode must be enabled when analyzing XAU/USD (fan-out 0.75, persistence 3 bars)

Prior session bug: Gold mode left enabled for all 8 instruments → false thresholds on forex/indices

Conversely: Gold mode disabled on XAU/USD → too permissive (fan-out 0.50, persistence 2)

Reminder: toggle instrument mode in Gauntlet settings per pair being analyzed

Key Files
Code for macro analysis.ipynb — Protocol Engine v2.5.2

Semi_automation/cot_data/ — CFTC data: disagg, tff, legacy CSVs for 2025-2026

Semi_automation/rate_diffs_*.json — Daily rate differential snapshots

Semi_automation/session_state_*.json — Session state persistence

PROJECT PLAYBOOK GAUNTLET.docx — Master strategic document

Pine Scripts.docx — Phase 1 Gauntlet v3.0 indicator code

Pine script 2 P1 S&R Levels Volume Profile.docx — S&R + Volume Profile indicator

Text in protocols creation.docx — Protocol creation methodology

Meta strategist prompt.docx — AI dispatcher prompt

Core Synthesis/ — Reference library (books, summaries, strategic plans)

Questions and thoughts on our forex project.docx — Strategic brainstorming (chat architecture, conflict resolution, pair selection)

Trading system rough work edwin.docx — Code vs Chat boundary decisions, automation opportunities

Prompts for forex.docx — Master AI prompts (sentiment analysis, risk regime, protocol auditor v2.1)

DEEP SEARCH PROMPTS OUTPUT.docx — Weekly macro research output (Global Liquidity = EXPANSION)

9 MACD CROSSOVER PROTOCOL.docx — P9 standalone protocol doc

15 DIVERGENCE PROTOCOL.docx — P15 with architect-flagged TP1 ratio bug

19 RISK SENTIMENT BIAS MODEL.docx — P19 v2.0 (5-tier VIX system, conditional aging by shock type, asymmetric hysteresis, stepped integration, NBFI liquidity overlay)

25 RETAIL SENTIMENT CONTRARIAN BIAS MODEL.docx — P25 v2.0 with IG offline notice, JPY special rules

10 RSI REVERSAL.docx — P10 v2.0 (3 methods: trend pullback, mean reversion, divergence)

12 TTM SQUEEZE PROTOCOL.docx — P12 v2.0 (BB inside KC compression detection)

13 PIVOT POINT PROTOCOL.docx — P13 v1.1 (instrument-specific session reset times)

16 REGIME CLASSIFICATION.docx — P16 v1.1 (3-layer sequential: ADX → SMA → BB)

1 SUPPORT and resistance protocol.docx — P1 v3.5 (dynamic R-multiples, asymmetrical scale-outs)

20 NEWS EVENT EXECUTION PLAYBOOK.docx — P20 v1.0 (3-layer macro bias, portfolio risk limits)

2 PSYCHOLOGICAL LEVEL LIQUIDITY PROTOCOL 2.docx — P2 v3.0 (sweep + reversal, ≥2 confluence)

3 CANDLESTICK REVERSAL PROTOCOL.docx — P3 v3.0 (8-filter convergence, volume >2× critical)

4 FIBONACCI TRADING SYSTEM PROTOCOL.docx — P4 v3.0 (Golden Zone + OTE, confluence ≥5)

5 MOVING AVERAGE TREND SYSTEM.docx — P5 v2.0 (EMA crossover, volume >150% on signal bar)

6 MAE DUAL.docx — P6 v2.0 (dual-mode: trend-following + mean reversion via EMA slope)

7 GMMA TREND PROTOCOL.docx — P7 v1.1 (dual-ribbon, excludes EUR/CHF, AUD/NZD, EUR/GBP)

8 BOLLINGER BANDS PROTOCOL.docx — P8 v2.0 (Bounce + Squeeze modes)

11 INDICATOR COMBINATION FRAMEWORK PROTOCOL.docx — P11 v2.0 (meta: BB+RSI ranging, EMA+MACD trending)

14 MASTER CHART PATTERNS PROTOCOL.docx — P14 v1.1 (RSI divergence mandatory, 0.5% max risk)

17 RETRACEMENT vs Reversals Identif.docx — P17 v1.0 (depth + pivot + Fib + structure consensus)

18 INTEREST RATE DIFFERENTIAL BIAS MODEL.docx — P18 v2.0 (2Y spread + carry viability 4-gate)

21 FISCAL POLICY BIAS MODEL.docx — P21 v2.0 (fiscal credibility, r-g differential, doom loop)

22 COT REPORT CONTRARIAN REVERSAL PROTOCOL.docx — P22 v1.0 (WillCo + %-L/S + OI gate)

23 REASSESSMENT CADENCE.docx — P23 v1.0 (decision fatigue toolkit, cadence violations)

24 CROSS PAIR RELATIVE STRENGTH SELECTION PROTOCOL.docx — P24 v1.0 (cross-pair filter)

26 GLOBAL LIQUIDITY REGIME BIAS MODEL.docx — P26 v1.0 (scoring dashboard, crisis phases)

ROLE.docx — Meta-strategist AI dispatcher prompt blueprint

Summary All Information.docx — Project synthesis (strategy feasibility, AI platform comparison)

Strategic guide, recommendations.docx — Operational playbook (3-layer framework, checklists)

Different paths Forex.docx — Strategic overview (copy trading, AI layer, sentiment bot, EOD execution)

Old protocols/ — Previous protocol versions (v1)

Protocols 1-26: Individual .docx files in root folder

Conventions
Protocols numbered 1-26, prefixed with number in filename

Version control in protocol headers (e.g., v3.4)

All strategies must be 100% mechanical (zero discretion)

Win rates documented per protocol (e.g., S&R: 55-65% bounces, 50-70% breaks)

Risk: 3% daily cap, position sizing per protocol rules

Engine versioning: v2.5.2 (Liquidity Scorer added)

Protocol creation pipeline: Meta-Strategist v4.7 → Stage 1 (Analyze) → Stage 2 (Classify into Pipeline A-E) → Stage 3 (Generate 3 prompts) → Protocol Created

Stage 2 research methodology: Each protocol's Stage 2 research was run through 3 INDEPENDENT deep search AIs (Gemini Deep Research, ChatGPT with browsing, Perplexity), then all 3 outputs were manually synthesized into one consolidated report. This means every parameter has been validated against 3 independent sources. Unusual-looking values are likely deliberate Stage 2 decisions — do not re-flag without strong mathematical or logical reason.

Protocol quality control: Protocol Consistency Auditor (logic/math) → Deep Searcher (research validation) → Revision Directive → Protocol Revision Master (executes revision)

What's Working
Protocol Engine v2.5.2 fully operational with 7 engines and HTML dashboard

All 26 protocol documents written

COT data pipeline working (disagg + tff + legacy, all CFTC codes matching correctly)

WillCo formula calculating for all 12 instruments

28-pair rate differentials with shift tracking and staleness detection

Forex Factory event calendar with country-aware matching

Instrument selection with regime-based permissions (5 risk tiers)

Conviction matrix with 6-layer SUPPORTS/OPPOSES/NEUTRAL classification

SEVERE_RISK_OFF 5-tier VIX system fully implemented in derive_risk_sentiment(), REGIME_PERMISSIONS, _map_regime(), classify_layer(), render_dashboard(), and InstrumentSelector (all 6 touchpoints)

AUTO risk sentiment thresholds correctly aligned with P19: <16 RISK_ON / 16-20 NEUTRAL / 20-30 MOD / 30-40 SEVERE / >40 EXTREME

Session state persistence (positions, P&L, risk tracking)

Pine Script Gauntlet v3.0 + S&R Volume Profile deployed on TradingView

Copy trading research completed (target: <10% drawdown accounts)

P16 Regime Classification v1.1 audit CLOSED — 9 doc changes, BBW N=200 (HAR-calibrated), classification completeness 100%

P19 Risk Sentiment v2.0 audit CLOSED — 5-tier VIX system doc/engine aligned, conditional aging, asymmetric hysteresis, stepped integration, NBFI liquidity overlay, BC priority resolution, JPY/EUR/Gold conditional rules

P18 Interest Rate Differential v2.0 audit CLOSED — hybrid model (shift for direction, absolute for carry), VIX>25 duration tracking added to engine, conflict resolution rule added, data source proxies documented, crowding gate lookback note added

P21 Fiscal Policy v2.0 audit CLOSED — derive_pair_fiscal() both-BEARISH inversion fixed, index BULLISH return path added, FISCAL_BIAS dict restructured with staleness tracking (30-day warning), _fb_get() backward-compatible helper

P20 News Event Execution Playbook v1.0 audit CLOSED — Wave 2 protocol de-jargonized, aligned with 5-tier VIX system, EIA Tier 2 overlap fixed, straddle warnings added.

P22 COT Contrarian Reversal v1.0 audit CLOSED — Wave 2 protocol engine alignment confirmed, COT %-Long/%-Short confirmation metric and lookback differentiation verified functional.

P23 Reassessment Cadence v1.0 audit CLOSED

P24 Cross Pair Relative Strength v1.0 audit CLOSED

P25 Retail Sentiment Contrarian Bias v2.0 audit CLOSED

P26 Global Liquidity Regime Partially automated via LiquidityScorer. Wave 2 Macro Protocols partially COMPLETE. (some retrieval of data is not working correctly)

P1 Support & Resistance v3.5 audit CLOSED — Fixed aggressive breakout expectancy leak with dynamic R-multiples, resolved breakeven paradox, and added asymmetrical scale-outs.

P2 Psychological Level Liquidity v3.0 audit CLOSED — Mechanized sweep boundaries (0.20-0.99 ATR), added 0.15 ATR entry offsets, implemented 1.5 ATR clustering noise-band invalidation, and fixed RSI cross-back logic.

What Needs Work
Deep Search macro refresh (currently stale, needs update)

FRED API reliability (VIX/TWI failures)

Foreign yield auto-fetch (currently manual, TradingView recommended for exact values)

More historical COT data (need 156+ weeks for secular WillCo)

Backtest validation for all 15 technical protocols (no documented results yet)

Protocol 15 TP1 ratio bug (always fails, needs TP2 check instead)

Multi-strategy conflict resolution rules not defined

Informed Flow Detection (P19 appendix) needs 10+ historical cases

Pine Script coding for protocols 11-15, 17, 24

Prop firm competition entry (The5ers, The Funded Trader)

Code vs Chat boundary formalization

P19 v2.0 engine sync — doc now specifies 5-tier position multipliers, VIX 45 Extreme threshold (engine uses 40), hysteresis rules, conditional aging — engine derive_risk_sentiment() needs update to match v2.0 spec

P19 regime aging automation — currently manual overlay; engine implementation deferred