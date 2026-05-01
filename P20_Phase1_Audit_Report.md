# PROTOCOL CONSISTENCY AUDIT — PHASE 1

**Protocol:** P20 — Master News & Event Trading System
**Version:** v1.0
**Date:** 2026-04-23
**Strategy Type:** Multi-event execution playbook (10 event sections + universal rules)
**Instruments:** All (forex majors/minors, gold, silver, oil, indices)

══════════════════════════════════
## Audit Summary
══════════════════════════════════

| Category | Findings | Critical | Warning | Note | Observation |
|---|---|---|---|---|---|
| A: Mathematical | 2 | 0 | 1 | 1 | 0 |
| B: Logical | 3 | 0 | 2 | 0 | 1 |
| C: Cross-Section | 4 | 1 | 2 | 1 | 0 |
| D: Instrument | 1 | 0 | 0 | 1 | 0 |
| E: Claims vs Evidence | 1 | 0 | 0 | 0 | 1 |
| F: Structural | 3 | 0 | 2 | 1 | 0 |
| **Total** | **14** | **1** | **7** | **4** | **2** |

**Overall Assessment:** FAIL — REVISION REQUIRED (1 Critical finding)

---

══════════════════════════════════
## Detailed Findings
══════════════════════════════════

---

### Finding 1: P19 VIX tier reference shows only 4 tiers — missing SEVERE_RISK_OFF
**Severity:** CRITICAL
**Category:** C1 — Cross-Section / Cross-Protocol Consistency
**Location:** Section 0, Step 0 — Protocol 19 reference

**The Issue:**
Section 0 states:

> "Protocol 19 — Risk Sentiment Bias. Classify regime: **Extreme Risk-Off (VIX >30–40)** = full override, only regime-aligned trades. **Moderate Risk-Off (VIX >20)** = reduce counter-regime conviction. **Neutral (VIX 16–20)** = no filter. **Risk-On (VIX <16, falling)** = growth-linked longs supported."

This describes **4 tiers**: Risk-On, Neutral, Moderate Risk-Off, Extreme Risk-Off. The approved P19 v2.0 defines **5 tiers** with SEVERE_RISK_OFF (VIX 30–40) as a distinct tier between Moderate (20–30) and Extreme (>40).

P20's reference collapses Severe and Extreme into "VIX >30–40" which:
- Misrepresents the Extreme threshold (should be >40, not >30–40)
- Omits the SEVERE_RISK_OFF tier entirely
- Creates a gap: trader following P20 would apply Moderate rules (VIX 20–30) then jump to Extreme (>30) — skipping Severe's distinct position multipliers

**Why This Matters:**
P19's 5-tier system is a universal rule across all 26 protocols. Engine v2.4.0 implements 5 tiers. P20 referencing only 4 tiers means a trader following P20 alone would apply wrong risk sizing when VIX is 30–40.

**Evidence:**
CLAUDE.md Known Issue #12 (now RESOLVED): "derive_risk_sentiment() now uses the correct 5-tier P19-aligned thresholds: <16 RISK_ON / 16-20 NEUTRAL / 20-30 MOD_RISK_OFF / 30-40 SEVERE_RISK_OFF / >40 EXTREME_RISK_OFF"

P20 Section 0 references VIX >30–40 as Extreme, contradicting the approved spec.

**Preliminary Recommendation:**
Update Section 0 P19 reference to reflect 5-tier system:
- Risk-On (VIX <16)
- Neutral (16–20)
- Moderate Risk-Off (20–30)
- Severe Risk-Off (30–40)
- Extreme Risk-Off (>40)

**Research Needed:** No — this is a known, resolved cross-protocol alignment issue. The fix is mechanical text replacement.

---

### Finding 2: NFP Method A (Straddle) has zero-to-negative expectancy
**Severity:** WARNING
**Category:** A1 — R:R Validation
**Location:** Section 2, Method A

**The Issue:**
Method A states:

> "Target: 1.5× range width" and "Win rate 25–55%. Both legs can trigger in V-shape. Advanced/high-risk only."

At the midpoint win rate (40%), R:R of 1.5:1 yields:
- Breakeven WR = 40.0%
- Gross expectancy = 0.00R
- Net expectancy (after ~0.15R friction for straddle + wider spreads) = **-0.15R**
- Verdict: **NON-VIABLE**

Even at the high end (55% WR), net expectancy = +0.17R — marginal after accounting for the double-stop-out scenario where both legs trigger.

**Why This Matters:**
The protocol already flags this as "Advanced/high-risk only" and notes both legs can trigger. The double-whipsaw scenario (max loss = 2× range) further degrades expectancy. However, P20 doesn't explicitly state the expectancy is negative — a trader seeing "1.5× range width" target might assume positive edge.

**Evidence:**
E = (0.40 × 1.5) − (0.60 × 1.0) = 0.60 − 0.60 = 0.00R (gross)
Friction (wider spreads at 8:30 ET, straddle structure): ~0.15R
Net = −0.15R → NON-VIABLE at midpoint

**Preliminary Recommendation:**
Add explicit expectancy warning: "Method A has negative-to-marginal expected value when accounting for spread widening and double-whipsaw risk. Use only as a volatility trade when directional uncertainty is high and you accept the probability of loss."

The protocol already marks this appropriately as secondary/advanced. This is a transparency fix, not a removal.

**Research Needed:** No — math is deterministic from stated parameters.

---

### Finding 3: FOMC blackout window — protocol vs. engine mismatch
**Severity:** WARNING
**Category:** C1 — Cross-Section Consistency (Protocol vs. Engine)
**Location:** Section 1, Execution; Engine EventCalendar

**The Issue:**
P20 Section 1 states:

> "Technical blackout window: 2 hours pre-announcement through **2–4 hours post-press-conference.**"

Press conference starts at 2:30 PM ET. "2–4 hours post-press-conference" = approximately 4:30 PM – 6:30 PM ET → total post-announcement window = **150–270 min**.

Engine EventCalendar sets:
```python
{'event': 'FOMC Decision', 'tier': 1, 'pre': 120, 'post': 240, 'instruments': ['ALL']}
```
Pre = 120 min (2h) ✅ matches.
Post = 240 min (4h) — measured from **2:00 PM ET statement**, not press conference end. So blackout ends at 6:00 PM ET.

The ambiguity: P20 says "post-press-conference" (which starts ~2:30 PM, runs ~60 min, so ends ~3:30 PM). 2–4 hours post-presser = 5:30–7:30 PM. Engine measures 4h from statement (2:00 PM) = 6:00 PM.

Result: Engine's 6:00 PM end falls within the protocol's 5:30–7:30 PM range, so functional alignment is acceptable. But the measurement anchor differs (statement vs. presser end).

**Why This Matters:**
If engine clock starts at statement but protocol says "post-press-conference," a delayed or extended presser could create a gap where the engine lifts the blackout before the protocol would.

**Evidence:**
Engine: `'post': 240` from statement at 2:00 PM → blackout ends 6:00 PM ET
Protocol: "2–4 hours post-press-conference" → press conf ends ~3:30 PM → 5:30–7:30 PM ET

**Preliminary Recommendation:**
Standardize P20 language to anchor from statement time (2:00 PM ET), matching the engine. E.g.: "Technical blackout window: 2 hours pre-statement (12:00 PM ET) through 4 hours post-statement (6:00 PM ET)."

**Research Needed:** No — alignment fix.

---

### Finding 4: BoE decision — two EVENT_MAP entries with different post windows
**Severity:** WARNING
**Category:** C1 — Cross-Section Consistency (Protocol vs. Engine)
**Location:** Section 5; Engine EventCalendar

**The Issue:**
Engine has two BoE entries:
```python
(['BOE Monetary Policy Report'], {'event': 'BoE Decision + MPR', 'tier': 1, 'pre': 30, 'post': 120, ...})
(['Official Bank Rate'], {'event': 'BoE Decision', 'tier': 1, 'pre': 30, 'post': 60, ...})
```

P20 Section 5 states:
> "No entry before 15 minutes — spreads normalise" and "On MPR days... extend wait to 45–60 min"

The engine correctly differentiates MPR (post: 120 min) vs non-MPR (post: 60 min). However, P20 doesn't specify a "technical blackout window" for BoE in explicit minutes the way it does for FOMC. The 15-min and 45–60 min waits are execution guidance, not blackout definitions.

The mismatch: Engine blocks technical entries for 60–120 min post. Protocol says wait 15–60 min for entry. A trader could attempt entry at T+45 on MPR days while the engine still shows BLACKOUT for another 75 min.

**Why This Matters:**
The engine's blackout is a conservative safety net. P20's execution timing is the tactical layer. But a trader using both will see conflicting signals — engine says BLACKOUT, protocol says ENTER.

**Evidence:**
Engine BoE+MPR: post = 120 min (blackout until T+120)
Protocol: "extend wait to 45–60 min" on MPR days (entry at T+45 to T+60)

**Preliminary Recommendation:**
Two options:
1. Align engine post window to protocol (reduce MPR post to 60 min), or
2. Add explicit blackout windows to P20 Section 5 matching engine values and clarify that execution entry is within the post-blackout portion.

This is a doc/engine alignment question, not a math error. The conservative engine setting is the safer default.

**Research Needed:** No — design decision.

---

### Finding 5: CPI instrument list — Silver explicitly excluded in P20 but engine maps CPI to limited set anyway
**Severity:** NOTE
**Category:** C1 — Cross-Section Consistency
**Location:** Section 3, Instruments table; Engine EventCalendar

**The Issue:**
P20 CPI Instruments table explicitly lists Silver as "Not recommended" and Oil as "Not recommended." The engine CPI entry instruments are:

```python
['EUR/USD', 'GBP/USD', 'USD/JPY', 'XAU/USD', 'NAS100', 'SPX500', 'US30']
```

This excludes Silver (XAG/USD) and Oil — correctly aligned with P20's recommendation. Gold (XAU/USD) is included. ✅ Consistent.

However, P20 Section 3 does not include a standalone "Instruments" subsection header with instrument entries — the table appears but the section label "Instruments" has no content after it (line 274 is blank). The table exists later in the document.

**Why This Matters:**
Minor structural issue. The table content is present and correct. The empty subsection header is cosmetic.

**Preliminary Recommendation:**
Move the Instruments table directly under the "Instruments" header in Section 3 for scannability.

**Research Needed:** No — editorial.

---

### Finding 6: Event Overlap Rule priority list incomplete
**Severity:** WARNING
**Category:** B1 — Logical Consistency
**Location:** Section 0, Event Overlap Rule

**The Issue:**
P20 states:

> "Priority: FOMC > NFP > CPI > ECB / BoE / BoJ > OPEC > all others."

This omits:
- **Core PCE** (Tier 1 in the engine, separate from CPI)
- **Minor CBs** (BoC, RBA, RBNZ — all Tier 1 in the engine)
- **EIA** (Tier 1 in the engine)

Where does Core PCE rank? It's arguably equivalent to CPI. Where do BoC/RBA/RBNZ rank? Between major CBs and OPEC? And EIA — before or after OPEC?

**Why This Matters:**
If two Tier 1 events overlap within 48h and one is PCE + BoC, the trader has no priority rule to resolve. The "all others" catch-all is insufficient for Tier 1 events.

**Evidence:**
Engine EVENT_MAP shows Core PCE, BoC, RBA, RBNZ, and EIA all as tier: 1.

**Preliminary Recommendation:**
Expand priority list:
FOMC > NFP > CPI/PCE > ECB/BoE/BoJ > BoC/RBA/RBNZ > OPEC > EIA > all others.

**Research Needed:** No — logical completeness.

---

### Finding 7: Catalyst Decay — P19 VIX thresholds don't match 5-tier system
**Severity:** WARNING
**Category:** C1 — Cross-Section / Cross-Protocol
**Location:** Section 0, Catalyst Decay, Magnitude Adjustment

**The Issue:**
The Catalyst Decay section states:

> "VIX < 15 or GVZ below 52-week 25th percentile → compress all windows 25%. **VIX > 25** → extend 25%."

P19 v2.0 defines tiers at: <16, 16–20, 20–30, 30–40, >40.
The VIX <15 threshold in decay doesn't match P19's <16 Risk-On boundary.
The VIX >25 threshold sits in the middle of the Moderate tier (20–30).

These decay thresholds may be intentionally different from P19's regime thresholds (decay window adjustment vs. risk regime classification are different functions). But the inconsistency could confuse a trader switching between systems.

**Why This Matters:**
Stage 2 Deference Rule applies — these thresholds may be deliberately calibrated for decay-specific purposes. However, the mismatch with P19's boundaries should be flagged for awareness.

**Evidence:**
P19 Risk-On: VIX <16. Decay compression: VIX <15.
P19 Moderate Risk-Off: VIX 20–30. Decay extension: VIX >25.

**Preliminary Recommendation:**
Classify as OBSERVATION if intentional. If unintentional, align to P19 boundaries (<16 for compression, >30 for extension). Requires clarification.

**Research Needed:** Yes (Type A) — is the VIX <15 / >25 distinction intentional for catalyst decay timing, or should it align with P19's <16 / >30 boundaries?

---

### Finding 8: BoE scale-out timing unvalidated
**Severity:** WARNING
**Category:** E1 / F2 — Claims vs Evidence / Time Logic
**Location:** Section 5, Execution

**The Issue:**
P20 Section 5 states:

> "Scale-out: 70% before London Close (~16:00 GMT). ⚠️ Timing not statistically validated, but NY-overlap reversal logic is sound as conservative default."

The protocol explicitly acknowledges this is **not validated**. The 70% exit before London Close is a heuristic, not a researched parameter.

**Why This Matters:**
This is commendably honest — the protocol flags its own uncertainty. But a 70% exit at a specific time is a significant parameter affecting blended R:R. If the true optimal exit is 50% or 90%, or if the timing should be 15:00 GMT or 17:00 GMT, the expected return changes materially.

**Evidence:**
Protocol self-flags: "Timing not statistically validated."

**Preliminary Recommendation:**
Add to Phase 2 research queue: optimal partial exit timing and percentage for BoE event trades relative to London Close.

**Research Needed:** Yes (Type B) — what is the empirically optimal partial exit timing and percentage for GBP/USD event trades on BoE days? Does the NY-overlap reversal pattern hold consistently?

---

### Finding 9: No cross-event narrative continuity framework
**Severity:** OBSERVATION
**Category:** F3 — Structural Completeness
**Location:** Section 0 (and Footnote 5)

**The Issue:**
Footnote 5 states:

> "None of the protocols address how one event's outcome should adjust the next event's scenario probabilities (e.g., hot NFP should adjust CPI expectations). This wasn't in any source material, so the synthesizer correctly did not fabricate it."

> "Recommendation: This is a genuine gap but belongs in a future revision, not a synthesis fix. Flag for v2.0: add a brief 'Event Chain' note to Section 0 covering the NFP → CPI → FOMC sequence."

The protocol itself identifies this gap and defers to v2.0.

**Why This Matters:**
This is a known, acknowledged gap. Not a finding per se — included for completeness and to track the v2.0 backlog item.

**Preliminary Recommendation:**
Carry forward to v2.0 backlog. No action needed for current audit.

**Research Needed:** No.

---

### Finding 10: OPEC Section — high aggregate exposure cap (5–8%) vs universal 3% cap
**Severity:** WARNING
**Category:** B2 — Logical Consistency
**Location:** Section 9, Execution & Risk; vs Section 0, Portfolio Risk Limits

**The Issue:**
Section 0 states:

> "Maximum concurrent event exposure: **3% of account** across all open event-driven positions. **Exception: OPEC multi-day holds may reach 5–8% including hedges** (Section 9)."

Section 9 confirms:

> "Total event cap **5–8% including hedges**"

While the exception is explicitly documented, 5–8% is 2–3× the universal 3% cap. OPEC positions are in WTI — one of the highest-volatility instruments in the system. The justification ("multi-day holds with hedges") is stated but thin.

**Why This Matters:**
A 5–8% concentration in a single commodity with weekend gap risk (P20 notes "1–8% for A/B/C, 10–25%+ for D") means a worst-case scenario could generate 0.5–2.0% account loss from gap alone, even with hedges. The hedges themselves (OTM puts at ≤0.25%) provide minimal downside protection against a 10–25% gap.

**Evidence:**
Worst case: 5% position × 10% weekend gap = 0.5% loss (manageable)
Extreme: 8% position × 25% gap (Scenario D) = 2.0% loss before stops
Puts at 0.25% cover only partial downside

**Preliminary Recommendation:**
Not necessarily wrong — OPEC is a multi-day macro event with hedging structure. But the gap between 3% universal and 8% OPEC maximum should be justified with a risk analysis. The protocol should specify: what percentage of the 5–8% must be hedged, and what residual directional exposure is permissible.

**Research Needed:** Yes (Type A) — what is the historical distribution of weekend gaps following OPEC decisions? Does the 5–8% cap with OTM put hedges produce acceptable tail risk?

---

### Finding 11: EIA Crude Inventory — engine assigns Tier 1 but P20 treats as selective
**Severity:** NOTE
**Category:** C1 — Cross-Section Consistency
**Location:** Section 10; Engine EventCalendar

**The Issue:**
Engine EventCalendar:
```python
({'event': 'EIA Crude Inventory', 'tier': 1, 'pre': 60, 'post': 30, 'instruments': ['WTI']})
```

P20 Section 10 describes EIA as a "confirmation tool, not a trade initiation signal" with a ~90% no-trade rate. The 60-min pre / 30-min post blackout is appropriate for WTI only.

The engine assigns Tier 1, which triggers the Tier 1 overlap warning logic (within 48h of another Tier 1). This means EIA appearing within 48h of, say, FOMC would trigger an overlap warning — but EIA only affects WTI, not the FOMC instruments.

**Why This Matters:**
False overlap warnings. EIA is WTI-only. FOMC is ALL instruments. A same-week occurrence (common: FOMC on Wednesday, EIA also on Wednesday) would trigger a spurious TIER1_OVERLAP warning. The engine's `_detect_compound_and_overlap` checks `base_event` to deduplicate same-event overlaps but doesn't check instrument intersection for different-event overlaps.

**Evidence:**
Engine overlap detection:
```python
if tier1[i].get('base_event', '') == tier1[j].get('base_event', ''):
    continue  # skip same base_event
```
This skips same-event dedup but allows EIA + FOMC overlap warning even though instruments don't intersect (except WTI is not in FOMC's set).

**Preliminary Recommendation:**
Two options:
1. Downgrade EIA to Tier 2 in the engine (matches P20's "confirmation tool" philosophy)
2. Add instrument-intersection check to overlap detection (only warn if instruments overlap)

Option 1 is simpler and more aligned with P20's intent.

**Research Needed:** No — design decision.

---

### Finding 12: BoJ — no hard stops recommended during liquidity vacuum
**Severity:** OBSERVATION
**Category:** F1 — Entry-Exit Alignment
**Location:** Section 6, Risk

**The Issue:**
P20 Section 6 states:

> "**No hard stops during 11:00–12:30 JST** — liquidity vacuum. Use mental stops or options."

This explicitly recommends mental stops during the BoJ window. Mental stops in a liquidity vacuum are high-risk — the trader must manually execute during peak volatility with thin depth.

**Why This Matters:**
This is a deliberate design choice, not an error. BoJ announcements have no fixed time, spreads explode, and hard stops will gap. The protocol correctly identifies the tradeoff. Options as an alternative stop are sound.

The concern: mental stops rely on discipline. The protocol addresses this by recommending 50% of normal sizing on event day, which is the correct risk-management response to unexecutable stops.

**Preliminary Recommendation:**
No change needed. The protocol correctly handles this edge case. Consider adding: "If unable to use options for downside protection, reduce position to 25% of normal."

**Research Needed:** No.

---

### Finding 13: Decay window instrument multiplier table — missing Oil (WTI)
**Severity:** NOTE
**Category:** D1 / F3 — Instrument Consistency / Completeness
**Location:** Section 0, Catalyst Decay, Instrument Adjustments table

**The Issue:**
The decay window instrument multiplier table shows:
- Forex Majors: 1.0×
- Forex Minors/Exotics: 1.5×
- XAUUSD: 1.25×
- XAGUSD: 1.25×
- NAS100: 0.75×
- SPX500/US30: 0.75×

**WTI (USOIL) is missing** from the multiplier table. OPEC (Section 9) and EIA (Section 10) both have WTI as primary instrument with specific decay behavior. Section 9 specifies "hold T+3 to T+5" for bullish drift and "within 24–48h" for bearish — but no explicit multiplier for the universal decay formula.

**Why This Matters:**
A trader applying catalyst decay to a WTI OPEC position would have no multiplier. Default = 1.0× (forex major baseline), which may be too short for oil's validated 3–5 day bullish drift.

**Evidence:**
Section 9: "hold T+3 to T+5 to capture validated bullish underreaction drift" (Scenario A)
Decay table: No WTI row.

**Preliminary Recommendation:**
Add WTI to the decay multiplier table. Based on Section 9's T+3–5 day hold guidance, a multiplier of 1.5–2.0× for T1 events would be consistent.

**Research Needed:** Yes (Type A) — is WTI's absence from the decay table an oversight or intentional (because OPEC/EIA have their own decay rules that supersede the universal table)?

---

### Finding 14: Minor CBs — BoE indices (UK100, UK250) not in engine instrument mappings
**Severity:** NOTE
**Category:** C1 — Cross-Section Consistency
**Location:** Section 5 vs Engine COUNTRY_INSTRUMENTS

**The Issue:**
P20 Section 5 lists instruments: "GBP/USD, EUR/GBP, **UK100, UK250**"

Engine COUNTRY_INSTRUMENTS for GBP: `['GBP/USD', 'EUR/GBP', 'GBP/JPY']`
Engine BoE EVENT_MAP instruments: `['GBP/USD', 'EUR/GBP', 'GBP/JPY']`

Neither UK100 nor UK250 appear in the engine's BoE instrument list. Also, GBP/JPY is in the engine but not prominent in P20 Section 5's header (though it's mentioned in scenarios).

**Why This Matters:**
UK100/UK250 are CFD indices that may not be in the engine's tracked universe at all. The engine is forex/commodity/index CFD focused. If UK indices aren't tracked, the blackout won't apply to them — but P20 recommends trading them on BoE days (with heavy caveats). Also, P20 Section 5 explicitly downgraded FTSE trades to "Opportunistic Only."

**Preliminary Recommendation:**
Low priority. UK100/UK250 are downgraded to opportunistic in P20, so missing blackout coverage is acceptable. Add GBP/JPY to the P20 Section 5 header instrument list for completeness (it's already in engine and scenarios).

**Research Needed:** No.

---

══════════════════════════════════
## Expectancy Analysis
══════════════════════════════════

P20 is a multi-event playbook, not a single-entry protocol. Each section has distinct risk parameters. Expectancy varies by event and method.

**Key principle:** P20 is an execution playbook — it defines HOW to trade events, not a standalone strategy with one R:R. Expectancy must be assessed per method.

| Section | Method | R:R | Win Rate (claimed) | BE WR | Net Expectancy | Verdict |
|---|---|---|---|---|---|---|
| S1: FOMC | Phase 5 drift | 2.0:1 | ~60% | 33.3% | +0.68R | VIABLE |
| S2: NFP | Method A (straddle) | 1.5:1 | 25–55% (mid: 40%) | 40.0% | −0.15R | ⚠ NON-VIABLE |
| S2: NFP | Method B (fade) | 1.25:1 | 45–65% (mid: 55%) | 44.4% | +0.12R | VIABLE |
| S2: NFP | Method C (post-settle) | 1.67:1 | 55–75% (mid: 65%) | 37.5% | +0.64R | VIABLE ✅ |
| S3: CPI | Scenario A/B | 2.0:1 | 70–85% (mid: ~77%) | 33.3% | +1.13R | VIABLE ✅ |
| S4: ECB | Presser entry | 2.5:1 | ~60% | 28.6% | +0.98R | VIABLE ✅ |
| S5: BoE | Surprise entry | 2.0:1 | ~60% | 33.3% | +0.68R | VIABLE |
| S6: BoJ | Confirmed entry | 2.5:1 | ~55% | 28.6% | +0.81R | VIABLE |
| S7: Minor CBs | Conditional entry | 2.0:1 | ~55% | 33.3% | +0.53R | VIABLE |
| S8: US Secondary | Decision Gate | 2.5:1 | ~55% | 28.6% | +0.81R | VIABLE |
| S9: OPEC | Scenario A | 2.5:1 | ~55% | 28.6% | +0.78R | VIABLE |
| S10: EIA | Strategy 5 | 2.0:1 | ~55% | 33.3% | +0.50R | VIABLE |
| S10: EIA | Strategy 1 | 2.0:1 | ~50% | 33.3% | +0.35R | VIABLE |

**Notes:**
- Win rates are estimated from protocol claims and strategy-type benchmarks (event-driven + confirmation filters typically 50–70%).
- NFP Method A is the only non-viable method. Protocol already flags it as "Advanced/high-risk only" with explicit double-whipsaw warning.
- CPI has the highest stated confidence (~75–85%) which produces the strongest expectancy. Stage 2 deference applies — these came from 3-source validated research.
- EIA Strategy 2 (Fade) and Strategy 3 (Straddle) are correctly excluded/banned.

══════════════════════════════════
## Research Required
══════════════════════════════════

**Total research questions generated:** 3

| Finding | Type | Question |
|---|---|---|
| F7 | Type A | Are VIX <15 / >25 decay thresholds intentional or should they align with P19's <16 / >30? |
| F8 | Type B | Optimal partial exit timing/% for GBP/USD on BoE days relative to London Close |
| F10 | Type A | Historical distribution of weekend gaps after OPEC decisions + residual risk with OTM puts |
| F13 | Type A | Is WTI's absence from decay multiplier table intentional (OPEC/EIA have own rules)? |

**Recommendation:** Resolve Type A questions (F7, F10, F13) inline. Queue F8 for Phase 2 Deep Research if warranted after Edwin/Gemini review.

---

══════════════════════════════════
## SESSION WORK LOG
══════════════════════════════════

- [Ex 1] — PROTOCOL RECEIVED: P20 v1.0, Master News & Event Trading System, ~8,000 words, 10 event sections + universal rules
- [Ex 1] — ENGINE CODE READ: EventCalendar class, EVENT_MAP (19 entries), blackout logic, overlap detection
- [Ex 1] — AUDIT COMPLETED: 14 findings (1 CRITICAL, 7 WARNING, 4 NOTE, 2 OBSERVATION) — FAIL
- [Ex 1] — EXPECTANCY CALCULATED: 12 methods assessed, 11 viable, 1 non-viable (NFP Method A)
- [Ex 1] — FINDING DOCUMENTED: F1 CRITICAL C1 — P19 4-tier reference missing SEVERE_RISK_OFF, no research needed
- [Ex 1] — FINDING DOCUMENTED: F2 WARNING A1 — NFP Method A negative expectancy, no research needed
- [Ex 1] — FINDING DOCUMENTED: F3 WARNING C1 — FOMC blackout anchor mismatch (statement vs presser), no research needed
- [Ex 1] — FINDING DOCUMENTED: F4 WARNING C1 — BoE engine blackout vs P20 entry timing conflict, no research needed
- [Ex 1] — FINDING DOCUMENTED: F5 NOTE C1 — CPI instruments aligned but empty subsection header, no research needed
- [Ex 1] — FINDING DOCUMENTED: F6 WARNING B1 — Event overlap priority incomplete (missing PCE, minor CBs, EIA), no research needed
- [Ex 1] — FINDING DOCUMENTED: F7 WARNING C1 — Decay VIX thresholds (<15/>25) don't match P19 (<16/>30), Type A research
- [Ex 1] — FINDING DOCUMENTED: F8 WARNING E1/F2 — BoE 70% scale-out unvalidated, Type B research
- [Ex 1] — FINDING DOCUMENTED: F9 OBSERVATION F3 — No cross-event narrative continuity, deferred to v2.0
- [Ex 1] — FINDING DOCUMENTED: F10 WARNING B2 — OPEC 5-8% cap vs universal 3%, Type A research
- [Ex 1] — FINDING DOCUMENTED: F11 NOTE C1 — EIA Tier 1 in engine but P20 treats as confirmation tool, no research needed
- [Ex 1] — FINDING DOCUMENTED: F12 OBSERVATION F1 — BoJ mental stops during liquidity vacuum, deliberate design choice
- [Ex 1] — FINDING DOCUMENTED: F13 NOTE D1/F3 — WTI missing from decay multiplier table, Type A research
- [Ex 1] — FINDING DOCUMENTED: F14 NOTE C1 — UK100/UK250 not in engine BoE instruments, low priority
