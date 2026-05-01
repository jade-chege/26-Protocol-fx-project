# PROJECT PLAYBOOK GAUNTLET — ORIENTATION REPORT (REVISED)
**Date:** 2026-04-11
**Session Type:** Orientation & Planning (no audit work)
**Revision:** Incorporates Edwin's corrections re: ConvictionMatrix confirmed fixed, 14×ATR is extraction artifact (ATR period 14), 3-source Stage 2 methodology, SEVERE_RISK_OFF fully implemented, full notebook accessible

**Files Read:** CLAUDE.md, TASKS.md, all 26 protocol .docx files, Text in protocols creation.docx, Questions and thoughts.docx, Prompts for forex.docx (including Meta-Strategist v4.7 pipeline), Pine Scripts.docx (including full Protocol Engine v2.3.4 Python code), Protocol Consistency Checker SKILL.md + audit-categories.md + output-templates.md

---

# PART 1 — CURRENT STATE REPORT

## 1A. What Is Built and Confirmed Working

**Protocol Engine v2.3.4** — 7 engines, all operational and verified:

1. **COTProcessor** — Downloads/caches CFTC data (disagg, tff, legacy). Maps all CFTC codes. WillCo percentile over 26-week rolling window. 12 instruments (7 forex, 3 commodities, 2 indices). ~64 rows per instrument (~15 months).

2. **FREDDashboard** — Pulls VIX, HY OAS, US 2Y/10Y, TIPS, Breakeven, USD TWI from FRED API. Derives risk regime, carry status, yield curve shape. Intermittent failures on VIX and TWI (workaround: manual GLOBAL_RISK_SENTIMENT override).

3. **RateDiffEngine** — 28-pair interest rate differentials (7 majors + 21 crosses). JSON persistence for shift tracking. Staleness detection (>7 days). Functional but depends on manual FOREIGN_YIELDS input.

4. **EventCalendar** — Forex Factory API integration. Country-aware matching. ADP/NFP collision fix. Tiered blackout windows per P20 spec (FOMC 120/240min through Jobless 15/15min). Compound event and Tier 1 overlap detection.

5. **SessionState** — JSON persistence of positions, P&L, risk usage, liquidity regime, COT signals. Auto-loads most recent state on startup.

6. **ConvictionMatrix** — **CONFIRMED FIXED (v2.3.4).** The old Counter() vocabulary mismatch is gone. `classify_layer()` normalizes all 6 layers (liquidity, fiscal, rate_diff, risk_sentiment, retail, regime) to SUPPORTS/OPPOSES/NEUTRAL per trade direction using INSTRUMENT_DNA risk characters. Permission cascade: ≥2 OPPOSES → DO NOT TRADE (0%); 1 OPPOSES → REDUCE SIZE (50-75%); ≥3 SUPPORTS + ≥4 populated → FULL CONVICTION (100%). Liquidity contraction override reduces sizing further. Currently conservative output (only XAU/USD and GBP/USD tradeable at REDUCE SIZE) is working as designed — USD strength via MAX/STRONG rate diff spreads correctly generates OPPOSES on many pairs.

7. **InstrumentSelector** — Scores all 35 instruments in LONG and SHORT directions. 5 regime tiers fully implemented (RISK_ON, NEUTRAL, MODERATE_RISK_OFF, SEVERE_RISK_OFF, EXTREME_RISK_OFF). Concentration limits (per-currency, carry_cross, commodity_metals, index). Minimum score ≥3.

**SEVERE_RISK_OFF — FULLY IMPLEMENTED (all 6 touchpoints):**
- `derive_risk_sentiment()`: VIX <16=RISK_ON, 16-20=NEUTRAL, 20-30=MODERATE, 30-40=SEVERE, >40=EXTREME ✓
- `REGIME_PERMISSIONS`: favored=[RISK_OFF, ANTI_FIAT], permitted=[NEUTRAL, MILD_RISK_OFF], blocked=[RISK_ON, MILD_RISK_ON], max_instruments=6, forced_includes=[XAU/USD] ✓
- `_map_regime()`: Explicit SEVERE_RISK_OFF mapping ✓
- `classify_layer()`: Risk-off logic includes SEVERE_RISK_OFF (identical to MODERATE/EXTREME for SUPPORTS/OPPOSES) ✓
- `render_dashboard()`: SEVERE color added to regime_colors ✓
- `InstrumentSelector`: Uses REGIME_PERMISSIONS[regime_key] ✓

**Note for CLAUDE.md:** Known Issues #11 (SEVERE_RISK_OFF not coded) and #12 (AUTO thresholds misalign with P19) are both RESOLVED in the current engine code. These should be marked as closed.

**Protocol Documents** — All 26 written, each through a rigorous creation pipeline:

**Protocol Creation Pipeline (Meta-Strategist v4.7):**
Stage 1 (Analyze) → Stage 2 (Classify into Pipeline A-E) → Stage 3 (Route) → Stage 4 (Generate 3 production prompts)

Five Pipelines:
- **A: Edge Extraction** — Mechanical strategies (P1-P15). 6-point research: modern application, failure points, optimal conditions, confluence, quantitative evidence, institutional perspective
- **B: Risk System** — Risk management principles. 6-point: professional implementation, common mistakes, edge cases, quantitative tools, academic evidence, institutional standards
- **C: Mindset & Psychology** — Psychological heuristics (P23 partially). 6-point: behavioral finance evidence, evidence-based interventions, cross-domain applications, behavior change science, success case studies, tracking
- **D: Market Bias** — Ongoing macro relationships (P18, P19, P21, P22, P25, P26). 6-point: correlation strength, institutional consensus, structural regime analysis, breakdown conditions, lead-lag dynamics, quantitative research
- **E: Macro Event** — Time-bound events (P20). 6-point: historical case studies, theory vs reality, confounding variables, timing/lag, modern institutional view, tradability analysis

**Critical: 3-Source Stage 2 Validation.** Each protocol's Stage 2 research was run through 3 INDEPENDENT deep search AIs (Gemini Deep Research, ChatGPT with browsing, Perplexity), then all 3 outputs were manually synthesized into one consolidated report. This means every parameter has been cross-validated against 3 independent sources. Unusual-looking values are far more likely to be deliberate Stage 2 decisions than errors. The audit must give significant deference to validated parameters — only flag with strong mathematical or logical reason, not because a value "looks unusual."

**Protocol Versions:**
- v3.4: P1 (most mature)
- v3.0: P2, P3, P4
- v2.0: P5, P6, P8, P9, P10, P11, P12, P18, P21, P25 (10 protocols)
- v1.1: P7, P13, P14, P15, P16
- v1.0: P17, P19, P20, P22, P23, P24, P26

**Pine Script — Deployed:**
- Phase 1 Gauntlet v3.0 (Pine Script v6) — multi-protocol dashboard with instrument modes (Gold: 0.75 fan-out, 3-bar persist; Silver: Gold + 4-bar Transitional; Oil: ADX 28, 3-bar; Default: 0.50 fan-out, 2-bar)
- P1 S&R Volume Profile v3.7 — audited PASS (exemplary: proper array guards, dynamic alerts, silver merge)
- P9 MACD Crossover v3.0 standalone — audited PASS (clean)

**Quality Control Toolchain:**
```
Meta-Strategist v4.7 → Stage 1 → Stage 2 (3-source research) → Stage 3 → Stage 4 → Protocol Created
                                                                                          ↓
Protocol Consistency Auditor v1.2 (logic/math) ← THIS IS NEXT
  ↓ (if issues found)
Deep Searcher (research validation, Type B prompts)
  ↓ (research returned)
Revision Directive produced
  ↓
Protocol Revision Master (executes revision)
```

**Additional Infrastructure:**
- 3 Pine Script audits completed (all PASS)
- Protocol Consistency Checker skill built (3-phase: Audit → Research Brief → Revision Directive)
- Forex Sentiment Monitor skill built
- Multi-chat architecture designed (Chief of Staff / Code Writer / Implementation Guide) with 10-section Session Handoff Protocol + 3-tier Context Management
- 5 AI prompts written (Master, Helper, Auditor v1.2, Architect, Implementation Guide)
- Copy trading research completed (target: <10% drawdown accounts)

## 1B. Started But Incomplete

| Item | What Exists | What's Missing |
|------|-------------|----------------|
| COT %-Long/%-Short | WillCo percentile works | Secondary confirmation metric `Spec_Longs/(Longs+Shorts)×100` not coded |
| COT Lookback Differentiation | 26-week window for all | Spec requires 13-week for NAS/S&P/WTI; not implemented |
| P15 Divergence | Protocol written | TP1 ratio gate broken — always rejects. Architect flagged, unresolved |
| Foreign Yields | Manual FOREIGN_YIELDS dict | No auto-fetch. Last updated 2026-04-01, now stale (10 days) |
| Gauntlet v3.1 | v3.0 audited PASS | Dynamic alert() calls with regime name + ADX value not yet added |
| Informed Flow Detection | Concept validated, Iran case study, draft trigger rules, quant review (7 findings) | Needs 10+ historical cases (n=14 but clustered, 5+ TPs and 3 FPs undocumented) |
| Multi-Strategy Conflict Resolution | Draft proposal in "Questions and thoughts" doc | No formal protocol or tiebreaker rules |
| Deep Search Macro Data | Last run 2026-03-27 | 15 days stale. Global Liquidity was EXPANSION — may have changed |
| P25 Retail Sentiment | v2.0 written | IG/DailyFX permanently offline. FXSSI single-source capped |
| Deep Search Skills (Prompts A-D) | Prompt specifications exist in Text in protocols creation.docx | Not yet built as Cowork skills for repeatable execution |

## 1C. Planned But Not Started

- Backtest validation for all 15 technical protocols (zero documented results)
- Pine Script coding for P11-P15, P16, P17, P24
- Master dashboard indicator (regime + bias + entry signals combined)
- Prop firm competition entry (The5ers, The Funded Trader)
- Paper trading with full Protocol Engine workflow (2-week target)
- Weekly Scanner Protocol (Sunday pair rotation automation)
- VIX term structure auto-fetch
- Formal Code vs Chat boundary document
- Trade journal / single Excel tracking file

## 1D. Open Issues — Updated Inventory

### Active Issues

| # | Issue | Status | Impact |
|---|-------|--------|--------|
| 1 | FRED API intermittent failures (VIX, TWI) | Workaround: manual override | Low — manual works |
| 2 | COT OI Gate mostly failing | Market-wide low participation | Limits P22 setup validity |
| 3 | WillCo edge cases (EUR/NZD at 0.0, WTI at 100.0) | LOW_OI prevents execution | By design |
| 4 | Conviction Matrix conservative (few pairs tradeable) | Working as designed | No fix needed |
| 5 | Foreign yield staleness (last: 2026-04-01) | **10 DAYS STALE** | Rate diff outputs unreliable |
| 6 | COT %-L/%-S confirmation not coded | Missing feature | P22 single-metric reliance |
| 7 | COT lookback 26w for all (should be 13w for equities/commodities) | Not implemented | Dilutes equity/commodity signals |
| 8 | P15 TP1 ratio bug | Architect flagged, unresolved | P15 un-tradeable as written |
| 9 | Multi-strategy conflict resolution | Not built | Deferred |
| 10 | IG Client Sentiment offline | Permanent (Sept 2024) | P25 single-source cap |
| 13 | Informed Flow Detection (P23 appendix) | Pilot draft, needs validation | Deferred |
| 14 | Gauntlet Gold mode must match pair | Operational reminder | — |

### Resolved Issues (update CLAUDE.md)

| # | Issue | Resolution |
|---|-------|------------|
| 11 | SEVERE_RISK_OFF not coded | **RESOLVED** — all 6 touchpoints confirmed in v2.3.4 code |
| 12 | AUTO risk thresholds misalign with P19 | **RESOLVED** — derive_risk_sentiment() uses correct 5-tier (<16/16-20/20-30/30-40/>40) |
| 15 | P12 numbering conflict | **RESOLVED** — P11=Indicator Combo, P12=TTM Squeeze |

### Note for P19 Doc Update
P19 document still shows 4 VIX tiers. The engine has 5 (including SEVERE_RISK_OFF). The protocol document should be updated to match the implemented 5-tier system after the Wave 1 P19 audit.

---

# PART 2 — PRIORITIZED ACTION LIST

## Pre-Wave: Immediate Actions (no dependencies)

| # | Action | Why | Where | Effort |
|---|--------|-----|-------|--------|
| 0.1 | Update FOREIGN_YIELDS dict | 10 days stale. Rate diff engine unreliable. 3-minute TradingView update | EDWIN (manual) | Quick |
| 0.2 | Refresh Deep Search macro data | 15 days stale. Global Liquidity regime may have shifted | CLAUDE DEEP RESEARCH (Edwin runs manually) | Medium |
| 0.3 | Update CLAUDE.md — close resolved issues #11, #12 | Working memory is stale — says SEVERE not coded when it is | COWORK | Quick |
| 0.4 | Update TASKS.md — add 4-wave audit structure + Wave 5 | Track audit progress alongside existing tasks | COWORK | Quick |

## Wave 1 — Backbone Protocol Audits: P16, P18, P19, P21

These four form the foundation every other protocol depends on. P16 classifies market regime. P18/P19/P21 generate macro bias layers feeding the conviction matrix.

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 1.1 | Audit P16 (Regime Classification) | Universal ADX filter — every technical protocol depends on this | PROJECT → COWORK (skill) | Pre-Wave | Medium |
| 1.2 | Audit P19 (Risk Sentiment) | VIX tiers feed 10+ protocols; doc needs 5-tier update | PROJECT → COWORK | Pre-Wave | Medium |
| 1.3 | Audit P18 (Interest Rate Differential) | Rate diff engine operational; verify doc/engine alignment | PROJECT → COWORK | 0.1 (yields fresh) | Medium |
| 1.4 | Audit P21 (Fiscal Policy) | Fiscal credibility feeds conviction matrix; qualitative-heavy | PROJECT → COWORK | Pre-Wave | Medium |
| 1.5 | Batch Wave 1 Deep Research prompts | Collect all Type B findings from 1.1-1.4 for one Deep Research session. Check with Edwin first: does he have Stage 2 consolidated reports for P16/P18/P19/P21? | PROJECT | 1.1-1.4 | Quick |
| 1.6 | Run Wave 1 Deep Research | Validate Type B findings not resolvable from Stage 2 reports | CLAUDE DEEP RESEARCH (Edwin runs) | 1.5 | Heavy |
| 1.7 | Apply Wave 1 Revision Directives | Fix confirmed CRITICAL/WARNING findings | COWORK | 1.6 | Medium |

## Wave 2 — Remaining Macro: P20, P22, P23, P24, P25, P26

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 2.1 | Audit P22 (COT Contrarian) | 3 known engine gaps. Audit quantifies impact | PROJECT → COWORK | Wave 1 | Medium |
| 2.2 | Audit P25 (Retail Sentiment) | IG offline, single-source cap. Validate remaining viability | PROJECT → COWORK | Wave 1 | Medium |
| 2.3 | Audit P26 (Global Liquidity) | Verify liquidity is conviction modifier only, not directional signal | PROJECT → COWORK | Wave 1, 0.2 | Medium |
| 2.4 | Audit P20 (News Event Execution) | Complex cross-protocol deps (7 protocols referenced). 5-8% win rate context | PROJECT → COWORK | Wave 1 | Medium |
| 2.5 | Audit P23 (Reassessment Cadence) | Validate cadence rules and regime aging (Day 0-3 → Day 10+) | PROJECT → COWORK | Wave 1 | Quick |
| 2.6 | Audit P24 (Cross-Pair Relative Strength) | Validate selection algorithm vs InstrumentSelector consistency | PROJECT → COWORK | Wave 1 | Quick |
| 2.7 | Code COT %-Long/%-Short confirmation | Closes Known Issue #6 | COWORK | 2.1 | Medium |
| 2.8 | Code COT lookback differentiation (13w/26w) | Closes Known Issue #7 | COWORK | 2.1 | Quick |
| 2.9 | Batch Wave 2 Deep Research + run | Same pattern: check Stage 2 reports first, then Type B for gaps | PROJECT → DEEP RESEARCH | 2.1-2.6 | Heavy |
| 2.10 | Apply Wave 2 Revision Directives | Fix confirmed findings | COWORK | 2.9 | Medium |

## Wave 3 — Technical Protocols: P1-P5, P6-P10, P11-P15, P17

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 3.1 | Audit P1 (S&R v3.4) | Most mature protocol, highest cross-protocol reference count | PROJECT → COWORK | Waves 1-2 | Medium |
| 3.2 | Audit P2-P5 batch | Core technical: Psych Levels, Candlestick, Fibonacci, MA Trend | PROJECT → COWORK | Waves 1-2 | Heavy |
| 3.3 | Audit P6-P10 batch | MAE Dual, GMMA, Bollinger, MACD, RSI Reversal | PROJECT → COWORK | Waves 1-2 | Heavy |
| 3.4 | Audit P11-P15 batch | Indicator Combo, TTM Squeeze, Pivot, Chart Patterns, Divergence (includes P15 TP1 bug) | PROJECT → COWORK | Waves 1-2 | Heavy |
| 3.5 | Fix P15 TP1 ratio bug | Closes Known Issue #8. Likely needs TP2 check instead of TP1 | COWORK | 3.4 | Quick |
| 3.6 | Audit P17 (Retracement vs Reversal) | Meta-classifier, validate decision tree completeness | PROJECT → COWORK | Waves 1-2 | Quick |
| 3.7 | Batch Wave 3 Deep Research + run | Largest batch — 16 protocols. Check Stage 2 reports first | PROJECT → DEEP RESEARCH | 3.1-3.6 | Heavy |
| 3.8 | Apply Wave 3 Revision Directives | Fix confirmed findings | COWORK | 3.7 | Heavy |

## Wave 4 — Cross-Protocol Reconciliation

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 4.1 | Cross-protocol consistency sweep | Same concept handled differently without justification? Conflicting regime requirements? Instrument adjustment inconsistencies? Shared data sources with different interpretation rules? | PROJECT → COWORK | Waves 1-3 | Heavy |
| 4.2 | Build Multi-Strategy Conflict Resolution protocol | Closes Known Issue #9. Formalize tiebreaker when 2+ protocols signal on same pair | PROJECT → COWORK | 4.1 | Medium |
| 4.3 | Update CLAUDE.md with all audit findings | Sync working memory with post-audit reality | COWORK | 4.1-4.2 | Quick |
| 4.4 | Formalize Code vs Chat boundary | Document which computations belong in engine vs chat vs manual | PROJECT → COWORK | 4.1 | Quick |

## Wave 5 — Build Deep Search Operational Skills (Prompts A-D)

These are the weekly/daily macro research prompts from "Text in protocols creation.docx" that feed the 4 config dictionaries in the engine. Building them as Cowork skills makes them repeatable and consistent.

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 5.1 | Build Prompt A skill: Risk Sentiment Assessment | Feeds GLOBAL_RISK_SENTIMENT. VIX + term structure + VVIX + HY spreads + breakdown codes. Currently manual | COWORK (skill-creator) | Waves 1-4 (audit may refine inputs) | Medium |
| 5.2 | Build Prompt B skill: Foreign Yields & Rate Differentials | Feeds FOREIGN_YIELDS dict. TradingView exact yields + CB tone analysis | COWORK (skill-creator) | Waves 1-4 | Medium |
| 5.3 | Build Prompt C skill: Fiscal & Liquidity Assessment | Feeds FISCAL_BIAS and GLOBAL_LIQUIDITY. r-g differentials, fiscal credibility, CB balance sheets | COWORK (skill-creator) | Waves 1-4 | Medium |
| 5.4 | Build Prompt D skill: COT & Retail Sentiment Update | Feeds RETAIL_SENTIMENT + COT interpretation layer. FXSSI/Myfxbook data + COT positioning context | COWORK (skill-creator) | Waves 1-4 | Medium |
| 5.5 | Test all 4 skills end-to-end | Run each skill, verify output feeds correctly into engine config | COWORK + EDWIN | 5.1-5.4 | Medium |

## Post-Audit Pipeline

| # | Action | Why | Where | Effort |
|---|--------|-----|-------|--------|
| 6.1 | Pine Script P11-P15, P16, P17, P24 | Code remaining protocols into TradingView | COWORK | Heavy |
| 6.2 | Apply Gauntlet v3.1 (dynamic alerts) | Add alert() calls with regime + ADX | COWORK | Quick |
| 6.3 | Build master dashboard indicator | Combine regime + bias + entry signals | COWORK | Heavy |
| 6.4 | Backtest validation (all 15 technical protocols) | Document results: dates, sample sizes, stress tests | COWORK + EDWIN | Heavy |
| 6.5 | Paper trade 2 weeks | Full Protocol Engine workflow live | EDWIN | Heavy |
| 6.6 | Prop firm competition entry | The5ers, The Funded Trader | EDWIN | Medium |

---

# PART 3 — COWORK TASKS READY TO EXECUTE NOW

---

## COWORK TASK 1: Update CLAUDE.md — Close Resolved Issues

```
TASK: Update CLAUDE.md to reflect that Known Issues #11 and #12 are 
RESOLVED, and correct the notebook truncation note.

STEPS:
1. Read /sessions/clever-funny-pasteur/mnt/forex learnings/CLAUDE.md

2. Make these specific edits:

   a) In Known Issue #11 (SEVERE_RISK_OFF), change the Status line from:
      "Status: Spec approved, awaiting implementation as v2.4"
      To:
      "Status: RESOLVED in v2.3.4 — all 6 code touchpoints confirmed 
      implemented (derive_risk_sentiment, REGIME_PERMISSIONS, _map_regime, 
      classify_layer, render_dashboard, InstrumentSelector)"

   b) In Known Issue #12 (AUTO Risk Sentiment Thresholds), change:
      "Will be fixed when SEVERE_RISK_OFF tier is implemented (v2.4)"
      To:
      "RESOLVED — derive_risk_sentiment() now uses correct 5-tier: 
      <16=RISK_ON, 16-20=NEUTRAL, 20-30=MODERATE, 30-40=SEVERE, >40=EXTREME"

   c) Find the line about the Cowork-synced notebook copy. It currently says:
      "Note: The Cowork-synced copy is truncated (255 bytes). The real file 
      on Windows is ~1,500+ lines and fully functional."
      Change to:
      "The notebook is ~324KB and fully synced to the Cowork folder. A full 
      copy of the engine code also exists in Pine Scripts.docx."

   d) In the "What Needs Work" section, remove the line:
      "Implement SEVERE_RISK_OFF v2.4 — spec approved, 6 code touchpoints 
      identified, not yet coded"
      (Because it IS coded.)

   e) Also remove "Fix AUTO risk sentiment thresholds to align with P19" 
      from the "What Needs Work" section (also resolved).

   f) Update the engine versioning note: change
      "Engine versioning: v2.3.4 (SEVERE_RISK_OFF + classify_layer fix)"
      To:
      "Engine versioning: v2.3.4 (SEVERE_RISK_OFF fully implemented + 
      classify_layer fix shipped)"

3. Do NOT change anything else in CLAUDE.md.

SUCCESS CRITERIA: 
- Known Issues #11 and #12 marked as RESOLVED with evidence
- Notebook truncation note corrected
- "What Needs Work" no longer lists SEVERE_RISK_OFF or AUTO thresholds
- All other content unchanged
```

---

## COWORK TASK 2: Add Audit Wave Structure to TASKS.md

```
TASK: Add the 4-wave audit plan plus Wave 5 (deep search skills) to 
TASKS.md so the audit pipeline is tracked.

STEPS:
1. Read /sessions/clever-funny-pasteur/mnt/forex learnings/TASKS.md

2. Add a new section AFTER "Phase 3.5" and BEFORE "Phase 4" with 
   this exact content:

### Phase 3.75: Protocol Consistency Audit (4-Wave + Skill Build)
> Goal: Audit all 26 protocols for math, logic, cross-protocol 
> consistency, then build operational deep search skills

**Pre-Wave — Immediate:**
- [ ] Update FOREIGN_YIELDS dict (10 days stale)
- [ ] Refresh Deep Search macro data (15 days stale)
- [x] Close CLAUDE.md Known Issues #11, #12 (SEVERE_RISK_OFF confirmed)

**Wave 1 — Backbone (P16, P18, P19, P21):**
- [ ] Audit P16 Regime Classification
- [ ] Audit P19 Risk Sentiment Bias Model
- [ ] Audit P18 Interest Rate Differential
- [ ] Audit P21 Fiscal Policy Bias Model
- [ ] Batch + run Wave 1 Deep Research prompts
- [ ] Apply Wave 1 Revision Directives

**Wave 2 — Remaining Macro (P20, P22, P23, P24, P25, P26):**
- [ ] Audit P22 COT Contrarian Reversal
- [ ] Audit P25 Retail Sentiment Contrarian
- [ ] Audit P26 Global Liquidity Regime
- [ ] Audit P20 News Event Execution
- [ ] Audit P23 Reassessment Cadence
- [ ] Audit P24 Cross-Pair Relative Strength
- [ ] Code COT %-Long/%-Short confirmation (after P22 audit)
- [ ] Code COT lookback differentiation 13w/26w (after P22 audit)
- [ ] Batch + run Wave 2 Deep Research prompts
- [ ] Apply Wave 2 Revision Directives

**Wave 3 — Technical (P1-P15, P17):**
- [ ] Audit P1 Support & Resistance v3.4
- [ ] Audit P2-P5 (Psych Levels, Candlestick, Fibonacci, MA Trend)
- [ ] Audit P6-P10 (MAE Dual, GMMA, Bollinger, MACD, RSI Reversal)
- [ ] Audit P11-P15 (Indicator Combo, TTM Squeeze, Pivot, Chart Patterns, Divergence)
- [ ] Fix P15 TP1 ratio bug (after P15 audit)
- [ ] Audit P17 Retracement vs Reversal
- [ ] Batch + run Wave 3 Deep Research prompts
- [ ] Apply Wave 3 Revision Directives

**Wave 4 — Cross-Protocol Reconciliation:**
- [ ] Cross-protocol consistency sweep (all 26)
- [ ] Build Multi-Strategy Conflict Resolution protocol
- [ ] Update CLAUDE.md with all audit findings
- [ ] Formalize Code vs Chat boundary document

**Wave 5 — Deep Search Operational Skills:**
- [ ] Build Prompt A skill: Risk Sentiment Assessment
- [ ] Build Prompt B skill: Foreign Yields & Rate Differentials
- [ ] Build Prompt C skill: Fiscal & Liquidity Assessment
- [ ] Build Prompt D skill: COT & Retail Sentiment Update
- [ ] Test all 4 skills end-to-end

3. Also update the existing TASKS.md entries:
   - In Phase 1, mark these as DONE:
     "Implement SEVERE_RISK_OFF v2.4" → [x] (already implemented)
     "Fix AUTO risk sentiment thresholds to align with P19" → [x] (already aligned)

4. Do NOT modify any other existing content.

SUCCESS CRITERIA: New Phase 3.75 section with all checkboxes. 
SEVERE_RISK_OFF and AUTO thresholds marked as done in Phase 1.
```

---

## COWORK TASK 3: Generate Current Sentiment Briefing Status

```
TASK: Check the forex-sentiment-monitor skill status and any existing 
reports.

STEPS:
1. List files in:
   /sessions/clever-funny-pasteur/mnt/forex learnings/sentiment_reports/

2. Read the most recent report if one exists

3. Read:
   /sessions/clever-funny-pasteur/mnt/forex learnings/forex-sentiment-monitor/SKILL.md
   /sessions/clever-funny-pasteur/mnt/forex learnings/forex-sentiment-monitor/references/protocol-thresholds.md
   /sessions/clever-funny-pasteur/mnt/forex learnings/forex-sentiment-monitor/references/instrument-sensitivity.md

4. Report:
   - Is there a recent sentiment report? What date and what does it say?
   - What does the skill do, what data sources, is it operational?
   - Does it align with P19's 5-tier VIX system?

SUCCESS CRITERIA: Clear picture of sentiment monitor operational status.
```

---

## COWORK TASK 4: Verify Protocol Document Stop Loss Parameters

```
TASK: For 3 representative protocols, extract the ACTUAL stop loss ATR 
multipliers from the .docx files to establish the correct baseline for 
audits. (The earlier extraction showed "14x ATR" which was confirmed 
as misreading ATR period 14 — this task confirms the real multipliers.)

STEPS:
1. Using python-docx, read these 3 protocol files and extract the 
   FULL text including any tables:
   - /sessions/clever-funny-pasteur/mnt/forex learnings/5 MOVING AVERAGE TREND SYSTEM.docx
   - /sessions/clever-funny-pasteur/mnt/forex learnings/9 MACD CROSSOVER PROTOCOL.docx
   - /sessions/clever-funny-pasteur/mnt/forex learnings/12 TTM SQUEEZE PROTOCOL.docx

2. For each, find and quote the EXACT text that specifies:
   - Stop loss distance (ATR multiplier or pip distance)
   - Take profit targets (TP1/TP2/TP3 with position percentages)
   - R:R ratio stated in any "Reality Check" section
   
3. Also extract from tables — use doc.tables to get table content, 
   as stop/target parameters often live in tables not paragraphs.

4. Produce a clean summary: Protocol → Stop → Targets → R:R

SUCCESS CRITERIA: Exact quoted stop/target parameters for 3 protocols, 
confirming the real multipliers (expected: 0.5x-2.0x ATR range).
```

---

# PART 4 — DECISIONS NEEDED FROM EDWIN

## Decision 1: FOREIGN_YIELDS Update
**Question:** Can you update the FOREIGN_YIELDS dict now? 10 days stale.
**Options:** A) Update now from TradingView (3 min) | B) Defer until Wave 1 P18 audit
**Implications:** Stale yields mean rate diff engine outputs are unreliable during audits.
**Blocks:** P18 audit accuracy (1.3)

## Decision 2: Deep Search Macro Refresh Timing
**Question:** When do you want to run the overdue Global Liquidity deep search?
**Options:** A) Now, before audits | B) After Wave 1 (batch with Wave 2) | C) This weekend
**Implications:** If Global Liquidity shifted from EXPANSION, affects conviction matrix and P26 audit.
**Blocks:** P26 audit accuracy (2.3)

## Decision 3: P20 Win Rate Context
**Question:** The 5-8% win rate in P20 (News Event Execution) — is this intentional?
**Options:** A) Intentional — it's a protective/hedging playbook (I'll document the rationale) | B) Error — investigate during audit | C) Unsure
**Implications:** Determines whether audit treats this as OBSERVATION vs CRITICAL.
**Blocks:** Nothing immediately; informs Wave 2 P20 audit (2.4)

## Decision 4: Audit Execution Model
**Question:** For each protocol audit, preferred workflow:
**Options:**
A) Full 3-phase in Cowork (Audit → Research Brief → Revision Directive), with Type B prompts for you to run in Deep Research. Before generating Type B prompts, I ask whether you have the Stage 2 consolidated report for that protocol.
B) Phase 1 only in Cowork, then bring findings here for discussion before research prompts
C) Something else
**Implications:** Option A is faster, treats Stage 2 reports as first-line resolution. Option B gives you more control.
**Blocks:** How we structure all Wave 1-4 tasks

## Decision 5: Stage 2 Consolidated Reports Availability
**Question:** Which protocols do you have Stage 2 consolidated reports for? You mentioned approximately half.
**Options:** N/A — just need the list so I know when to ask vs when to generate Type B
**Implications:** For protocols WITH reports: flagged parameters can potentially be resolved immediately. For protocols WITHOUT: Type B Deep Research prompts generated.
**Blocks:** Efficiency of the audit process

## Decision 6: Prop Firm Timeline
**Question:** When do you plan to enter prop firm competitions?
**Options:** This affects whether we compress the audit timeline or run methodically.
**Implications:** If 2 weeks away → focus on 3-5 strongest protocols only. If 2+ months → run full 4-wave audit.
**Blocks:** Overall prioritization

---

# PART 5 — CONTEXT GAPS

## Gap 1: Stage 2 Consolidated Reports (Which Protocols?)
**Missing:** Specific list of which protocols have accessible Stage 2 consolidated research reports.
**Blocks:** Audit efficiency — determines Type A resolution vs Type B prompt generation per finding.
**Resolution:** Edwin provides the list (Decision 5 above).

## Gap 2: Current Market Regime
**Missing:** Current VIX level, GLOBAL_RISK_SENTIMENT setting, regime for key instruments.
**Blocks:** Useful context for audit prioritization but not technically blocking.
**Resolution:** Edwin checks TradingView or runs engine.

## Gap 3: Deep Search Prompt Specifications (Prompts A-D)
**Missing:** The exact prompt text for the 4 operational deep search prompts that feed the engine. These are referenced in "Text in protocols creation.docx" but I need to locate the exact specifications to build them as Cowork skills (Wave 5).
**Blocks:** Wave 5 skill building.
**Resolution:** Read the relevant sections of "Text in protocols creation.docx" or "Prompts for forex.docx" more carefully — the prompts may already be there. Or Edwin provides them.

## Gap 4: TradingView Current Setup
**Missing:** Which Pine Script indicators loaded on which charts, Gold mode toggle state, current ADX readings.
**Blocks:** Nothing directly.
**Resolution:** Edwin confirms verbally or screenshots.

## Gap 5: Live Trading Experience
**Missing:** Whether Edwin has taken any live/demo trades with the system. Results and observations.
**Blocks:** Nothing directly, but would inform audit priorities.
**Resolution:** Edwin shares if relevant.

## Gap 6: Prop Firm Target Timeline
**Missing:** When Edwin plans to enter competitions.
**Blocks:** Determines audit compression vs methodical pace (Decision 6).
**Resolution:** Edwin states target.

## Gap 7: BabyPips Completion Status
**Missing:** Which sections of the remaining ~33% are incomplete. Whether they inform unwritten refinements.
**Blocks:** Nothing directly.
**Resolution:** Edwin states which sections remain.

---

*End of Revised Orientation Report. No audit work performed. Next actions: Edwin resolves Decisions 1-6 and Pre-Wave items 0.1-0.2, then Cowork executes Tasks 1-4 in parallel, then Wave 1 audits begin.*
