# SESSION SUMMARY — 2026-05-05
**Topic:** Protocol Architecture Review + Automation Strategy Brainstorm
**Status:** IN PROGRESS — resuming tomorrow

---

## What Was Discussed

### Question 1: Should protocols be combined?
**Answer: No. Keep all 15 technical protocols separate. Fix three specific things instead.**

**Reasoning:**
- Each protocol has a different PRIMARY signal (the thing that creates the trade opportunity)
- Shared confirmation filters (candlesticks, RSI, Fibonacci) are intentional — they reduce false positives at different price structures
- Combining protocols destroys individual performance attribution, which you need to pick 3-5 strongest for prop firm
- P11 already IS the combination framework

**Three structural fixes required:**

1. **Fix P10 vs P15 overlap (genuine duplication)**
   - P10 Method 3 = "RSI divergence" = same trade as P15 (Divergence protocol)
   - Resolution: Remove Method 3 from P10. Add rule in P10: "if divergence present, defer to P15"
   - P10 becomes a pure RSI extremes protocol

2. **Promote P11 from "protocol" to "Protocol Router"**
   - P11 (Indicator Combination Framework) doesn't generate a trade — it tells you WHICH protocol to run based on regime
   - Rename it "Protocol Selection Router" and treat it as session prep, not a standalone signal

3. **Formalize Multi-Strategy Conflict Resolution (Wave 4 work)**
   - When P1 (S/R) and P13 (Pivots) fire simultaneously on same pair = doubled conviction or one trade?
   - This is the real answer to the "combining" question — not merging protocols, but building the tiebreaker rule
   - Already flagged as Known Issue #7 in CLAUDE.md

---

### Question 2: Best automation approach?
**Goal confirmed:** Maximum automation, full protocol compliance, full documentation for testing/iteration.
**Sequence confirmed:** Prop firm first (semi-auto) → then full automation on live account.

**Three options evaluated:**

| Option | Description | Verdict |
|--------|-------------|---------|
| A: Pine Scripts only | Extend current approach, manual execution always | Too limited for Phase 2 |
| B: MT5 Expert Advisors | Recode everything in MQL5 | Wastes all existing work, wrong sequencing |
| **C: Staged Hybrid (RECOMMENDED)** | TradingView alerts → Python → MT5 API | Reuses all existing work, clean Phase 1→2 transition |

**Recommended Stack (Option C):**

```
Python Engine (macro gate)          Pine Scripts (chart signal detection)
     ↓                                        ↓
Conviction Matrix                    TradingView Alerts
Pair watchlist                       (S/R, Fib, MACD, RSI, BBands, etc.)
     ↓                                        ↓
         PHASE 1 (prop firm): Trader reviews alert → manual MT4 execution
         PHASE 2 (live account): Python webhook listener → MT5 Python API auto-execute
```

**Key insight:** Phase 1 → Phase 2 transition is ADDITIVE. Same Pine Scripts, same Python engine. Just add the webhook listener + MT5 API execution layer. No rebuild.

**Claude Skills role:** Research/audit tools ONLY (Wave 5 Deep Search Prompts A-D). NOT for real-time signal detection or execution. Wrong tool for that.

**Priority order:**
1. Fix P10 Method 3 → defer to P15
2. Complete Pine Scripts for P11-P15, P17, P24
3. Build master dashboard Pine Script (all signals in one view)
4. Build conflict resolution rule (Wave 4)
5. Prop firm phase: Python Sunday prep + TradingView alerts + manual MT4
6. Document every trade by protocol (backtest evidence)
7. Post-funding: Add Python webhook listener + MT5 API execution layer

---

## Where We Left Off

**Last question asked (unanswered):**
> "Is there a specific reason you chose Pine Script as the charting platform vs. something like a Python charting library connected directly to a broker API? This affects whether Option C is truly the best path or whether a pure-Python approach (Python detects patterns + executes) could be better for Phase 2."

**Tomorrow: Answer this question, then move to:**
- Proposing 2-3 final design approaches (Task #3)
- Presenting the design for approval (Task #4)
- Writing the spec doc to `docs/superpowers/specs/2026-05-05-protocol-architecture-design.md`

---

## Key Decisions Already Made
- All 15 technical protocols stay separate (no combining)
- P11 gets promoted to Protocol Router (not a standalone trade signal)
- P10 Method 3 divergence → defer to P15
- Staged hybrid automation (Pine Script → Python webhook → MT5 API)
- Prop firm first, full auto after funding
- Claude Skills = research/prep only, never execution

---

## Session Context
- Files read: CLAUDE.md, TASKS.md, ORIENTATION_REPORT_2026-04-11_REVISED.md, P20_Phase1_Audit_Report.md, wave 3 audit/SYSTEM.MD
- Brainstorming skill active — following: Explore → Clarify → Propose approaches → Design → Spec doc → writing-plans
- Tasks created in session: #1 (context exploration ✓), #2 (clarifying questions ✓), #3 (propose approaches — in progress), #4 (design + spec)
