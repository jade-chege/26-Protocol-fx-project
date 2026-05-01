# PROJECT PLAYBOOK GAUNTLET — ORIENTATION REPORT
**Date:** 2026-04-10  
**Session Type:** Orientation & Planning (no audit work)  
**Files Read:** CLAUDE.md, TASKS.md, all 26 protocol .docx files, Text in protocols creation.docx, Questions and thoughts.docx, Prompts for forex.docx, Pine Scripts.docx, Protocol Consistency Checker SKILL.md + audit-categories.md + output-templates.md

---

# PART 1 — CURRENT STATE REPORT

## 1A. What Is Built and Confirmed Working

**Protocol Engine v2.3.4** — 7 engines, all operational:

1. **COTProcessor** — Downloads/caches CFTC data (disagg, tff, legacy). Maps all CFTC codes. Calculates WillCo percentile over 26-week rolling window. Tracks 12 instruments (7 forex, 3 commodities, 2 indices). Data pipeline functional with ~64 rows per instrument (~15 months).

2. **FREDDashboard** — Pulls VIX, HY OAS, US 2Y/10Y, TIPS, Breakeven, USD TWI from FRED API. Derives risk regime, carry status, yield curve shape. Works when FRED responds (intermittent failures on VIX and TWI).

3. **RateDiffEngine** — Calculates 28-pair interest rate differentials (7 majors + 21 crosses). JSON persistence for shift tracking. Staleness detection (>7 days). Functional but depends on manual FOREIGN_YIELDS input.

4. **EventCalendar** — Forex Factory API integration. Country-aware matching. ADP/NFP collision fix applied. Tiered blackout windows per P20 spec (FOMC 120/240min through Jobless 15/15min). Compound event detection.

5. **SessionState** — JSON persistence of positions, P&L, risk usage, liquidity regime, COT signals. Auto-loads most recent state on startup.

6. **ConvictionMatrix** — 6-layer scoring (liquidity, fiscal, rate_diff, risk_sentiment, retail, regime). **Status: CRITICAL DISCREPANCY** — see Section 1D below.

7. **InstrumentSelector** — Scores all 35 instruments in LONG and SHORT directions. Regime gates (4 tiers currently, 5th pending). Concentration limits. Minimum score threshold ≥3. Session compatibility checks.

**Protocol Documents** — All 26 written:
- Cat 1 Technical (P1-P15): versions range from v1.1 to v3.4
- Cat 2 Regime (P16): v1.1
- Cat 3 Retracement (P17): v1.0
- Cat 4A Macro Bias (P18, P19, P21, P22, P25, P26): v1.0–v2.0
- Cat 4B Events (P20): v1.0
- Cat 5 Meta (P23, P24): v1.0

**Pine Script — Deployed:**
- Phase 1 Gauntlet v3.0 (Pine Script v6) — multi-protocol dashboard with instrument modes (Gold/Silver/Oil/Default), ADX persistence engine, SMA alignment, BB zones, MACD, RSI
- P1 S&R Volume Profile v3.7 — audited PASS (exemplary)
- P9 MACD Crossover v3.0 standalone — audited PASS

**Infrastructure:**
- 3 Pine Script audits completed (all PASS)
- Protocol Consistency Checker skill built (3-phase workflow: Audit → Research → Revision)
- Forex Sentiment Monitor skill built
- Multi-chat architecture designed (Chief of Staff / Code Writer / Implementation Guide)
- 5 AI prompts written (Master, Helper, Auditor v2.1, Architect, Implementation Guide)
- Copy trading research completed

## 1B. Started But Incomplete

| Item | What Exists | What's Missing |
|------|-------------|----------------|
| SEVERE_RISK_OFF v2.4 | Spec approved, 6 code touchpoints identified | Not coded. Affects derive_risk_sentiment(), REGIME_PERMISSIONS, _map_regime(), classify_layer(), render_dashboard(), Implementation Guide prompt |
| COT %-Long/%-Short | WillCo percentile works | Secondary confirmation metric `Spec_Longs/(Longs+Shorts)×100` not coded |
| COT Lookback Differentiation | 26-week window for all | Spec requires 13-week for NAS/S&P/WTI; not implemented |
| P15 Divergence | Protocol written | TP1 ratio gate broken — always rejects (ratio=1.0 < 2.0 check). Architect flagged, unresolved |
| Foreign Yields | Manual FOREIGN_YIELDS dict | No auto-fetch. Last updated 2026-04-01, now stale (>7 days) |
| Gauntlet v3.1 | v3.0 audited | Dynamic alert() calls with regime name + ADX value not yet added |
| Informed Flow Detection | Concept validated, Iran case study, draft trigger rules (5 conditions), quantitative review done (7 findings) | Needs 10+ historical cases (currently n=14 but clustered, 5+ TPs and 3 FPs undocumented) |
| Multi-Strategy Conflict Resolution | Draft proposal in "Questions and thoughts" doc (trade count + time metrics) | No formal protocol or tiebreaker rules |
| Deep Search Macro Data | Last run 2026-03-27 | 14 days stale. Global Liquidity = EXPANSION (may have changed) |
| P25 Retail Sentiment | v2.0 written | IG/DailyFX permanently offline (Sept 2024). Now FXSSI single-source capped |

## 1C. Planned But Not Started

- Backtest validation for all 15 technical protocols (zero documented results)
- Pine Script coding for P11-P15, P16, P17, P24
- Master dashboard indicator (regime + bias + entry signals combined)
- Prop firm competition entry (The5ers, The Funded Trader)
- Paper trading with full Protocol Engine workflow (2-week target)
- Weekly Scanner Protocol (Sunday pair rotation automation)
- VIX term structure auto-fetch (currently manual vixcentral.com check)
- Formal Code vs Chat boundary document
- Trade journal / single Excel tracking file
- API integrations (TradingView, MT5, X.com)
- 4-wave protocol audit (Wave 1-4 structure designed, none started)

## 1D. CRITICAL DISCREPANCY: ConvictionMatrix Status

**What CLAUDE.md says:** ConvictionMatrix is "working" with v2.3.4 — the classify_layer fix was shipped. The conviction matrix uses 6-layer SUPPORTS/OPPOSES/NEUTRAL classification. It's listed under "What's Working."

**What "Text in protocols creation.docx" says:** The ConvictionMatrix has a CRITICAL BUG — it uses `Counter()` on raw string values from 6 layers that each output different vocabularies (EXPANSION vs BULLISH vs BULL_USD vs MODERATE_RISK_OFF vs CONTRARIAN_BULL vs TRENDING). Counter() never matches across layers. Result: "outputs DO NOT TRADE for ALL instruments." The doc prescribes a 3-part fix: (A) pass trade direction into ConvictionMatrix, (B) map all layer outputs to SUPPORTS/OPPOSES/NEUTRAL, (C) direction-aware evaluation.

**Reconciliation:** The most likely explanation is that the "Text in protocols creation" doc describes the **pre-v2.3.4** state — the bug that was then fixed. CLAUDE.md's Known Issue #4 confirms "Conviction Matrix Conservative" with only XAU/USD and GBP/USD tradeable at REDUCE SIZE, and several pairs at DO NOT TRADE. This is described as "working as designed" — meaning the fix WAS applied (layer outputs now map to SUPPORTS/OPPOSES/NEUTRAL), but the conservative behavior is due to rate diff opposition (USD strength creating OPPOSES on many pairs), not the Counter() vocabulary mismatch.

**However, this needs verification.** The Cowork-synced notebook is truncated (255 bytes). The actual running code on your Windows machine is ~1,500+ lines. Only running the engine or reading the real notebook can confirm whether the Counter() bug was truly fixed or is still present.

**Risk if unfixed:** The entire instrument selection pipeline produces garbage output — every trade blocked regardless of conviction.

## 1E. Open Issues — Full Inventory

### Known Issues (from CLAUDE.md, confirmed against protocol files)

| # | Issue | Status | Blocking? |
|---|-------|--------|-----------|
| 1 | FRED API intermittent failures (VIX, TWI) | Workaround: manual override | No — manual works |
| 2 | COT OI Gate mostly failing (only GBP/AUD/WTI pass) | Market-wide, not code bug | Limits P22 validity |
| 3 | WillCo edge cases (EUR/NZD at 0.0, WTI at 100.0) | By design — LOW_OI prevents | No |
| 4 | Conviction Matrix conservative | Working as designed | No (if fix shipped) |
| 5 | Foreign yield staleness (last: 2026-04-01) | Manual only | Yes — stale now |
| 6 | COT %-L/%-S confirmation not coded | Missing feature | Limits P22 confidence |
| 7 | COT lookback 26w for all (should be 13w for equities/commodities) | Not implemented | Dilutes signals |
| 8 | P15 TP1 ratio bug | Architect flagged, unresolved | P15 un-tradeable |
| 9 | Multi-strategy conflict resolution | Not built | Deferred |
| 10 | IG Client Sentiment offline | Permanent | P25 single-source cap |
| 11 | SEVERE_RISK_OFF v2.4 | Spec done, not coded | 6 touchpoints waiting |
| 12 | AUTO risk thresholds misalign with P19 | Known, fix bundled with v2.4 | VIX 16-25 zone unreliable |
| 13 | Informed Flow Detection | Pilot draft, needs validation | Deferred |
| 14 | Gauntlet Gold mode must match pair | Operational reminder | No |
| 15 | P12 numbering conflict | RESOLVED | — |

### Issues Found During This Orientation (New)

| # | Issue | Severity | Detail |
|---|-------|----------|--------|
| N1 | "14x ATR" systematic anomaly | INVESTIGATE | Protocols 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 all show "14x ATR" stop loss in extraction. P1 uses 0.5-2.5x ATR. This is almost certainly an extraction artifact (ATR period "14" being parsed as "14x ATR multiplier") but must be verified by reading the actual .docx formatted text, not just paragraph extraction |
| N2 | ConvictionMatrix fix verification needed | CRITICAL | See Section 1D — cannot confirm from Cowork-synced truncated notebook |
| N3 | P19 doc shows 4 VIX tiers, CLAUDE.md says 5 | KNOWN (doc update needed) | P19 doc needs SEVERE_RISK_OFF tier added after v2.4 ships |
| N4 | P20 win rate 5-8% | INVESTIGATE | Extremely low — may be intentional (fade/hedge playbook) but undocumented rationale |
| N5 | Multiple protocols have overlapping/ambiguous win rates | NOTE | P8 (60% vs 10-15% vs 5-8%), P10 (71-91% is outlier), P25 (55-85% range too wide). These need clarification during audits |
| N6 | InstrumentSelector has 4 regime tiers, not 5 | KNOWN | Aligned with v2.4 pending status |
| N7 | "Text in protocols creation" describes COT lookback as differentiated (26w forex, 13w equities) | CONTRADICTS CLAUDE.md | CLAUDE.md says all use 26w. The "Text in protocols" doc may describe the SPEC, while CLAUDE.md describes what's ACTUALLY coded. Need to check actual notebook code |

## 1F. Architecture Mapping: "Text in Protocols Creation" vs Reality

| Component Described | Implementation Status | Notes |
|--------------------|-----------------------|-------|
| COTProcessor (disagg/tff/legacy, WillCo, OI Gate) | **IMPLEMENTED** | Working. Missing %-L/%-S confirmation and lookback differentiation |
| FREDDashboard (VIX, yields, OAS, TWI) | **IMPLEMENTED** | Working with intermittent failures |
| RateDiffEngine (28 pairs, shift tracking) | **IMPLEMENTED** | Working. Manual FOREIGN_YIELDS bottleneck |
| EventCalendar (FF API, blackout windows) | **IMPLEMENTED** | Working. Country-aware matching + ADP/NFP fix |
| SessionState (JSON persistence) | **IMPLEMENTED** | Working |
| ConvictionMatrix (6-layer SUPPORTS/OPPOSES/NEUTRAL) | **IMPLEMENTED (v2.3.4 fix) — VERIFY** | Doc describes Counter() bug; CLAUDE.md says fixed. Verification needed |
| InstrumentSelector (35 instruments, regime gates) | **IMPLEMENTED** | Working. 4 of 5 regime tiers active |
| derive_pair_fiscal() | **IMPLEMENTED** | Part of conviction pipeline |
| derive_risk_sentiment() | **IMPLEMENTED** | AUTO mode + manual override |
| INSTRUMENT_DNA (35 instruments) | **IMPLEMENTED** | Static config |
| 3-environment architecture (Python/Pine/DeepSearch) | **IMPLEMENTED** | All three environments active |
| 10-section Session Handoff Protocol | **DESIGNED** | In Prompts doc, not formally tested |
| 3-tier Context Management | **DESIGNED** | In Prompts doc, Protocol Consistency Checker uses it |

---

# PART 2 — PRIORITIZED ACTION LIST

## Pre-Wave: Immediate Fixes (unblock everything)

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 0.1 | Verify ConvictionMatrix Counter() bug is actually fixed in v2.3.4 | If unfixed, entire instrument selection pipeline is broken. Nothing else matters until confirmed | COWORK (read notebook code) OR EDWIN (run engine, check output) | Nothing | Quick |
| 0.2 | Verify "14x ATR" extraction anomaly | Determines whether 14 protocols have a documentation error or if it's just an extraction artifact from ATR(14) period notation | COWORK (re-read .docx files with formatting context) | Nothing | Quick |
| 0.3 | Update FOREIGN_YIELDS dict | Stale since 2026-04-01 (9 days). Rate diff engine outputs unreliable | EDWIN (manual: get 7 currency 2Y yields from TradingView, update Cell 1) | Nothing | Quick |
| 0.4 | Refresh Deep Search macro data | Last run 2026-03-27 (14 days stale). Global Liquidity regime may have shifted | CLAUDE DEEP RESEARCH (Edwin runs manually) | Nothing | Medium |

## Wave 1 — Backbone Protocol Audits: P16, P18, P19, P21

These four protocols form the foundation that every other protocol depends on. P16 classifies market regime. P18/P19/P21 generate the macro bias layers that feed the conviction matrix. If these are inconsistent, everything downstream is wrong.

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 1.1 | Audit P16 (Regime Classification) | Universal ADX filter — every technical protocol depends on this | PROJECT (analysis) → COWORK (execute skill) | 0.1, 0.2 | Medium |
| 1.2 | Audit P19 (Risk Sentiment) | VIX tiers feed 10+ protocols; known code/spec misalignment | PROJECT → COWORK | 0.1 | Medium |
| 1.3 | Audit P18 (Interest Rate Differential) | Rate diff engine is working but doc/engine alignment unverified | PROJECT → COWORK | 0.1, 0.3 | Medium |
| 1.4 | Audit P21 (Fiscal Policy) | Fiscal credibility feeds conviction matrix; qualitative-heavy, needs operationalization check | PROJECT → COWORK | 0.1 | Medium |
| 1.5 | Implement SEVERE_RISK_OFF v2.4 | Spec complete, 6 touchpoints identified. Closes Known Issues #11 and #12 | COWORK (code changes in notebook) | 1.2 (P19 audit confirms spec) | Medium |
| 1.6 | Batch Wave 1 Deep Research prompts | Audits will generate Type B research questions. Batch all for one Deep Research session | PROJECT (compile prompts) | 1.1-1.4 | Quick |
| 1.7 | Run Wave 1 Deep Research | Validate findings from P16/P18/P19/P21 audits | CLAUDE DEEP RESEARCH (Edwin runs) | 1.6 | Heavy |
| 1.8 | Apply Wave 1 Revision Directives | Fix any CRITICAL/WARNING findings confirmed by research | COWORK | 1.7 | Medium |

## Wave 2 — Remaining Macro: P20, P22, P23, P24, P25, P26

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 2.1 | Audit P22 (COT Contrarian) | 3 known engine gaps (%-L/S, lookback, OI gate). Audit quantifies impact | PROJECT → COWORK | Wave 1 complete | Medium |
| 2.2 | Audit P25 (Retail Sentiment) | IG offline, single-source cap. Audit validates remaining viability | PROJECT → COWORK | Wave 1 complete | Medium |
| 2.3 | Audit P26 (Global Liquidity) | Liquidity is conviction modifier, not directional. Verify this is consistently applied | PROJECT → COWORK | Wave 1 complete, 0.4 | Medium |
| 2.4 | Audit P20 (News Event Execution) | Complex cross-protocol dependencies (P1, P5, P10, P18, P19, P21, P23). 5-8% win rate needs investigation | PROJECT → COWORK | Wave 1 complete | Medium |
| 2.5 | Audit P23 (Reassessment Cadence) | Meta-process — validates cadence rules and regime aging (Day 0-3 full → Day 10+ moderate) | PROJECT → COWORK | Wave 1 complete | Quick |
| 2.6 | Audit P24 (Cross-Pair Relative Strength) | Filter protocol — validates selection algorithm consistency with InstrumentSelector | PROJECT → COWORK | Wave 1 complete | Quick |
| 2.7 | Code COT %-Long/%-Short confirmation | Closes Known Issue #6 | COWORK | 2.1 (P22 audit) | Medium |
| 2.8 | Code COT lookback differentiation (13w/26w) | Closes Known Issue #7 | COWORK | 2.1 (P22 audit) | Quick |
| 2.9 | Batch Wave 2 Deep Research + run | Same pattern as Wave 1 | PROJECT → DEEP RESEARCH | 2.1-2.6 | Heavy |
| 2.10 | Apply Wave 2 Revision Directives | Fix confirmed findings | COWORK | 2.9 | Medium |

## Wave 3 — Technical Protocols: P1-P5, P6-P10, P11-P15

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 3.1 | Audit P1 (S&R v3.4) | Most mature protocol, highest cross-protocol reference count | PROJECT → COWORK | Waves 1-2 | Medium |
| 3.2 | Audit P2-P5 batch | Core technical suite: Psych Levels, Candlestick, Fibonacci, MA Trend | PROJECT → COWORK | Waves 1-2 | Heavy |
| 3.3 | Audit P6-P10 batch | MAE Dual, GMMA, Bollinger, MACD, RSI Reversal | PROJECT → COWORK | Waves 1-2 | Heavy |
| 3.4 | Audit P11-P15 batch | Indicator Combo, TTM Squeeze, Pivot, Chart Patterns, Divergence (includes P15 TP1 bug) | PROJECT → COWORK | Waves 1-2 | Heavy |
| 3.5 | Fix P15 TP1 ratio bug | Closes Known Issue #8. Likely needs TP2 check instead of TP1 | COWORK | 3.4 (P15 audit) | Quick |
| 3.6 | Audit P17 (Retracement vs Reversal) | Meta-classifier, no performance metrics — validate decision tree completeness | PROJECT → COWORK | Waves 1-2 | Quick |
| 3.7 | Batch Wave 3 Deep Research + run | Largest batch — 15 technical protocols | PROJECT → DEEP RESEARCH | 3.1-3.6 | Heavy |
| 3.8 | Apply Wave 3 Revision Directives | Fix confirmed findings | COWORK | 3.7 | Heavy |

## Wave 4 — Cross-Protocol Reconciliation

| # | Action | Why | Where | Depends On | Effort |
|---|--------|-----|-------|------------|--------|
| 4.1 | Cross-protocol consistency sweep | Check: same concept handled differently without justification, conflicting regime requirements, instrument adjustment inconsistencies, shared data sources with different interpretation rules | PROJECT → COWORK | Waves 1-3 | Heavy |
| 4.2 | Build Multi-Strategy Conflict Resolution protocol | Closes Known Issue #9. Formalize tiebreaker when 2+ protocols signal on same pair | PROJECT (design) → COWORK (write doc) | 4.1 | Medium |
| 4.3 | Update CLAUDE.md with all audit findings | Sync working memory with post-audit state | COWORK | 4.1-4.2 | Quick |
| 4.4 | Formalize Code vs Chat boundary | Document which computations belong in engine vs chat vs manual | PROJECT → COWORK | 4.1 | Quick |

## Post-Audit Pipeline (after all 4 waves)

| # | Action | Why | Where | Effort |
|---|--------|-----|-------|--------|
| 5.1 | Pine Script P11-P15, P16, P17, P24 | Code remaining protocols into TradingView indicators | COWORK | Heavy |
| 5.2 | Apply Gauntlet v3.1 (dynamic alerts) | Add alert() calls with regime name + ADX value | COWORK | Quick |
| 5.3 | Build master dashboard indicator | Combine regime + bias + entry signals | COWORK | Heavy |
| 5.4 | Backtest validation (all 15 technical protocols) | Document results with dates, sample sizes, stress tests | COWORK + EDWIN (manual TradingView) | Heavy |
| 5.5 | Paper trade 2 weeks | Full Protocol Engine workflow live | EDWIN | Heavy |
| 5.6 | Prop firm competition entry | The5ers, The Funded Trader | EDWIN | Medium |

---

# PART 3 — COWORK TASKS READY TO EXECUTE NOW

These tasks have zero dependencies on other actions and can be executed immediately.

---

## COWORK TASK 1: Verify "14x ATR" Extraction Anomaly

```
TASK: Determine whether the "14x ATR" stop loss appearing in protocols 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, and 16 is a real protocol parameter or an extraction artifact.

HYPOTHESIS: The "14" likely refers to the ATR PERIOD (ATR(14) is standard) being misread as a 14x MULTIPLIER during text extraction. Protocol 1 (the most mature, v3.4) uses 0.5-2.5x ATR multipliers, which is normal.

STEPS:
1. Read the following .docx files using python-docx, but this time extract the FULL formatted text including tables, headers, and any structured sections — not just paragraph text:
   - "2 PSYCHOLOGICAL LEVEL LIQUIDITY PROTOCOL 2.docx"
   - "5 MOVING AVERAGE TREND SYSTEM.docx"  
   - "9 MACD CROSSOVER PROTOCOL.docx"
   (These three are representative samples across the range)

2. For each file, search for:
   - Any mention of "14" near "ATR" — determine if it's "ATR(14)" (the period) or "14× ATR" (a multiplier)
   - The actual stop loss section — what multiplier is specified?
   - Any table that might contain "14" in a column that could be misread

3. Also read "1 SUPPORT and resistance protocol.docx" as a control — we know P1 uses 0.5-2.5× ATR, so it should NOT show "14x ATR"

OUTPUT: For each protocol sampled, state:
- The actual stop loss ATR multiplier specified in the protocol
- Whether "14" appears and in what context (period vs multiplier)
- Whether this is confirmed as an extraction artifact or a real concern

SUCCESS CRITERIA: Clear determination of artifact vs real issue, with quoted evidence from at least 3 protocols.
```

---

## COWORK TASK 2: Verify ConvictionMatrix v2.3.4 Fix Status

```
TASK: Determine whether the ConvictionMatrix Counter() vocabulary mismatch bug described in "Text in protocols creation.docx" has been fixed in Protocol Engine v2.3.4.

CONTEXT: The "Text in protocols creation" document describes a critical bug where Counter() is used on raw strings from 6 layers with different vocabularies (EXPANSION, BULLISH, BULL_USD, etc.), causing it to output "DO NOT TRADE" for ALL instruments. CLAUDE.md says the classify_layer fix was shipped in v2.3.4 and the conviction matrix now uses SUPPORTS/OPPOSES/NEUTRAL mapping.

PROBLEM: The Cowork-synced copy of the notebook is truncated (255 bytes). The real notebook on Windows is ~1,500+ lines.

STEPS:
1. First, check if the full notebook is accessible:
   - Read: /sessions/clever-funny-pasteur/mnt/forex learnings/Semi_automation/Code for macro analysis.ipynb
   - Check file size and whether it's the truncated version

2. If truncated (likely), search for ANY Python files in the Semi_automation directory that might contain the ConvictionMatrix code:
   - List all files in /sessions/clever-funny-pasteur/mnt/forex learnings/Semi_automation/
   - Check for .py files, exported scripts, or backup notebooks

3. If no full code is accessible, search CLAUDE.md and "Text in protocols creation.docx" for specific evidence:
   - Does CLAUDE.md describe the fix mechanism (direction-aware SUPPORTS/OPPOSES/NEUTRAL)?
   - Does the v2.3.4 changelog mention ConvictionMatrix?
   - Is there a session_state JSON file that shows conviction matrix output? (Would show actual layer values)

4. Check session state JSON files for evidence:
   - Read any session_state_*.json files in Semi_automation/
   - Look for conviction_matrix output — if layers show SUPPORTS/OPPOSES/NEUTRAL, fix was applied
   - If layers show raw values (EXPANSION, BULLISH, etc.), fix was NOT applied

OUTPUT:
- Confirmed FIXED / Confirmed UNFIXED / CANNOT DETERMINE (with explanation)
- Evidence used to reach conclusion
- If CANNOT DETERMINE: exactly what Edwin needs to check in his running Jupyter notebook

SUCCESS CRITERIA: Clear determination with evidence, or explicit instructions for what Edwin must verify manually.
```

---

## COWORK TASK 3: Update TASKS.md with Audit Wave Structure

```
TASK: Add the 4-wave audit plan to TASKS.md so the audit pipeline is tracked alongside existing tasks.

STEPS:
1. Read /sessions/clever-funny-pasteur/mnt/forex learnings/TASKS.md (full file)

2. Add a new section after the existing "Phase 3.5" section and before "Phase 4" with this content:

### Phase 3.75: Protocol Consistency Audit (4-Wave)
> Goal: Systematically audit all 26 protocols for mathematical viability, logical consistency, and cross-protocol contradictions

**Wave 1 — Backbone (P16, P18, P19, P21):**
- [ ] Audit P16 Regime Classification
- [ ] Audit P19 Risk Sentiment Bias Model
- [ ] Audit P18 Interest Rate Differential
- [ ] Audit P21 Fiscal Policy Bias Model
- [ ] Implement SEVERE_RISK_OFF v2.4 (after P19 audit confirms spec)
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

3. Do NOT modify any existing content in TASKS.md — only add the new section.

SUCCESS CRITERIA: New section appears in TASKS.md between Phase 3.5 and Phase 4, with all items as checkboxes.
```

---

## COWORK TASK 4: Generate Sentiment Monitor Briefing

```
TASK: Check if the forex-sentiment-monitor skill can produce a current briefing, and if a recent one exists, read it.

STEPS:
1. Check for existing sentiment reports:
   - List files in /sessions/clever-funny-pasteur/mnt/forex learnings/sentiment_reports/
   - Read the most recent report if one exists

2. Read the sentiment monitor skill:
   - Read /sessions/clever-funny-pasteur/mnt/forex learnings/forex-sentiment-monitor/SKILL.md
   - Read /sessions/clever-funny-pasteur/mnt/forex learnings/forex-sentiment-monitor/references/protocol-thresholds.md

3. Report what you find:
   - Is there a recent sentiment report? What date?
   - What does the skill do and what data sources does it use?
   - Is it operational or does it need setup?

OUTPUT: Summary of sentiment monitor status and any existing report content.

SUCCESS CRITERIA: Clear picture of whether this tool is producing actionable output.
```

---

# PART 4 — DECISIONS NEEDED FROM EDWIN

## Decision 1: ConvictionMatrix Verification Method
**Question:** How should we verify whether the Counter() bug fix shipped in v2.3.4?
**Options:**
- A) Edwin runs the engine in Jupyter and shares the conviction matrix output (fastest, most reliable)
- B) Edwin copies the full notebook to the Cowork-synced folder (enables code review but large file)
- C) Edwin exports just the ConvictionMatrix class + classify_layer function as a .py file
**Implications:** Option A confirms immediately but doesn't let me review code. Option C is the best balance.
**Blocks:** Action 0.1, and transitively everything in Waves 1-4 (if unfixed, audit findings would differ)

## Decision 2: FOREIGN_YIELDS Update
**Question:** Can you update the FOREIGN_YIELDS dict now? The 7 currency 2Y yields are 9 days stale.
**Options:**
- A) Update now from TradingView (3 minutes)
- B) Defer until Wave 1 P18 audit
**Implications:** If deferred, rate diff engine outputs during the audit will be based on stale data. Updating now is quick and unblocks P18 audit accuracy.
**Blocks:** Action 0.3, and P18 audit accuracy (1.3)

## Decision 3: Deep Search Macro Refresh Timing
**Question:** When do you want to run the overdue Global Liquidity deep search?
**Options:**
- A) Now, before audits start (ensures Wave 2 P26 audit uses current data)
- B) After Wave 1 completes (batch with Wave 2 Deep Research prompts)
- C) As a separate task this weekend
**Implications:** Global Liquidity was EXPANSION as of March 27. If it shifted to STABLE or CONTRACTION, that affects conviction matrix outputs and P26 audit findings.
**Blocks:** Action 0.4, and P26 audit accuracy (2.3)

## Decision 4: P20 Win Rate Intention
**Question:** Is P20's 5-8% win rate intentional? Is this a fade/hedge playbook rather than a primary trading strategy?
**Options:**
- A) Intentional — it's a protective/hedging playbook (document this rationale)
- B) Error — win rate was meant to be higher (investigate during audit)
- C) Unsure — needs investigation
**Implications:** If intentional, the audit treats it as OBSERVATION. If error, it's a CRITICAL finding.
**Blocks:** Nothing immediately, but informs P20 audit in Wave 2 (2.4)

## Decision 5: Audit Execution Model
**Question:** For each protocol audit, do you want me to:
- A) Run the full 3-phase workflow (Audit → Research Brief → Revision Directive) within Cowork, generating Deep Research prompts for you to run manually
- B) Run Phase 1 (Audit) only in Cowork, then bring findings here for discussion before generating research prompts
- C) Something else
**Implications:** Option A is faster but you review after the fact. Option B gives you decision points between phases.
**Blocks:** How we structure all Wave 1-3 audit tasks

## Decision 6: "Text in Protocols Creation" Document Status
**Question:** Is the "Text in protocols creation.docx" the current authoritative architecture reference, or is it outdated (pre-v2.3.4)?
**Options:**
- A) Current — treat it as the spec, and discrepancies with CLAUDE.md are CLAUDE.md errors
- B) Outdated — CLAUDE.md is more current, and the doc describes pre-fix state
- C) Mixed — some sections current, some outdated
**Implications:** Determines whether CLAUDE.md or the doc wins when they conflict (especially on ConvictionMatrix, COT lookback, and other items)
**Blocks:** How we interpret discrepancies throughout the audit

---

# PART 5 — CONTEXT GAPS

## Gap 1: Actual Protocol Engine Code (CRITICAL)
**Missing:** The running code in `C:\Users\Chege\Documents\forex\forex learnings\Semi_automation\Code for macro analysis.ipynb`. The Cowork-synced copy is truncated (255 bytes).
**Blocks:** ConvictionMatrix verification (0.1), SEVERE_RISK_OFF implementation (1.5), COT feature additions (2.7, 2.8), and any code-level audit finding verification.
**Resolution:** Edwin exports the notebook or key classes to a .py file and places it in the Cowork-synced folder. Alternatively, Edwin could copy the full .ipynb.

## Gap 2: Most Recent Engine Output
**Missing:** The actual output from the last Protocol Engine run — what did the conviction matrix show? What instruments were on the watchlist? What regime was detected?
**Blocks:** Confirms whether conviction matrix is producing SUPPORTS/OPPOSES/NEUTRAL or still broken. Also establishes baseline for audit.
**Resolution:** Edwin runs the engine and shares/screenshots the HTML dashboard output, or copies a recent session_state JSON.

## Gap 3: TradingView Current State
**Missing:** Which Pine Script indicators are currently loaded on which charts. Whether Gold mode is correctly toggled per-pair. Current ADX readings for key instruments.
**Blocks:** Nothing directly, but informs whether Gauntlet v3.1 fix is urgent.
**Resolution:** Edwin takes screenshots of TradingView setup, or just confirms verbally.

## Gap 4: Prop Firm Target Timeline
**Missing:** When Edwin plans to enter prop firm competitions. This determines how aggressively the audit pipeline needs to be compressed.
**Blocks:** Nothing technically, but affects prioritization. If prop firm entry is 2 weeks away, we skip Wave 3-4 and focus on getting 3-5 strongest protocols audit-clean.
**Resolution:** Edwin states target date.

## Gap 5: BabyPips Training Completion Status
**Missing:** TASKS.md mentions "remaining ~33%" of BabyPips training. Which sections remain? Do they inform any unwritten protocol refinements?
**Blocks:** Nothing directly.
**Resolution:** Edwin states which sections remain.

## Gap 6: Prior Session Conversation History
**Missing:** The conversation history from prior Claude/Cowork sessions that produced design decisions documented in CLAUDE.md. Some decisions (like "TRANSITIONAL counts as populated but generates NEUTRAL") have rationale that may only exist in those conversations.
**Blocks:** Nothing — CLAUDE.md captures the decisions well enough for audit purposes. But context on WHY certain decisions were made could prevent us from re-litigating them during audits.
**Resolution:** Not actionable unless Edwin has saved transcripts.

## Gap 7: Live Trading History
**Missing:** Whether Edwin has taken any live or demo trades using the system. If so, results and observations.
**Blocks:** Nothing directly, but live experience would inform audit priorities (e.g., "P8 Bounce mode gave 3 false signals last week on EUR/USD" would escalate P8 audit).
**Resolution:** Edwin shares any trading journal or experience notes.

## Gap 8: Current Market Regime
**Missing:** Current VIX level, current GLOBAL_RISK_SENTIMENT setting, current regime for key instruments.
**Blocks:** Useful context for determining whether current engine configuration is appropriate, but not blocking for audit work.
**Resolution:** Edwin checks TradingView or runs engine Cell 2.

---

# APPENDIX: PROTOCOL VERSION INVENTORY

| # | Protocol | Version | Strategy Type | Engine Component |
|---|----------|---------|---------------|-----------------|
| 1 | Support & Resistance | v3.4 | Multi-method | — (chart-based) |
| 2 | Psychological Level Liquidity | v3.0 | S&R breakout/sweep | — |
| 3 | Candlestick Reversal | v3.0 | Reversal | — |
| 4 | Fibonacci Trading System | v3.0 | Retracement | — |
| 5 | Moving Average Trend | v2.0 | Trend-following | — |
| 6 | MAE Dual | v2.0 | Dual-mode | — |
| 7 | GMMA Trend | v1.1 | Trend-following | — |
| 8 | Bollinger Bands | v2.0 | Mean-reversion + breakout | — |
| 9 | MACD Crossover | v2.0 | Trend-following | — |
| 10 | RSI Reversal | v2.0 | Mean-reversion | — |
| 11 | Indicator Combination Framework | v2.0 | Meta-strategy | — |
| 12 | TTM Squeeze | v2.0 | Volatility breakout | — |
| 13 | Pivot Points | v1.1 | S&R calculated | — |
| 14 | Master Chart Patterns | v1.1 | Pattern recognition | — |
| 15 | Divergence | v1.1 | Mean-reversion (BUGGED) | — |
| 16 | Regime Classification | v1.1 | Meta-filter | InstrumentSelector + Gauntlet |
| 17 | Retracement vs Reversal | v1.0 | Meta-classifier | — |
| 18 | Interest Rate Differential | v2.0 | Macro bias | RateDiffEngine |
| 19 | Risk Sentiment | v1.0 | Macro regime | FREDDashboard + derive_risk_sentiment |
| 20 | News Event Execution | v1.0 | Event playbook | EventCalendar |
| 21 | Fiscal Policy | v2.0 | Macro bias | FISCAL_BIAS + derive_pair_fiscal |
| 22 | COT Contrarian Reversal | v1.0 | Macro contrarian | COTProcessor |
| 23 | Reassessment Cadence | v1.0 | Meta-process | SessionState |
| 24 | Cross-Pair Relative Strength | v1.0 | Meta-filter | InstrumentSelector |
| 25 | Retail Sentiment Contrarian | v2.0 | Macro contrarian | RETAIL_SENTIMENT + classify_layer |
| 26 | Global Liquidity Regime | v1.0 | Macro regime | GLOBAL_LIQUIDITY + classify_layer |

---

*End of Orientation Report. No audit work performed. Next action: Edwin resolves Decisions 1-6 and Pre-Wave items 0.1-0.4, then Wave 1 audits begin.*
