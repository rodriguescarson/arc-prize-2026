# NEXT_ACTIONS — status, blockers, next steps (updated 2026-10-12 04:45 IST)

## Verified deadlines (all Kaggle times 23:59 UTC = 05:29 IST next day)
| Event | Date | IST | Note |
|---|---|---|---|
| Entry + team-merger deadline, ARC-AGI-2 and ARC-AGI-3 | 26 Oct 2026 23:59 UTC | 27 Oct 05:29 | must have joined + submitted-able by then |
| ARC-AGI-2 / ARC-AGI-3 final code submission | 2 Nov 2026 23:59 UTC | 3 Nov 05:29 | 1 submission/day, 2 finals |
| **Paper Track writeup** | **8 Nov (arcprize.org) / 9 Nov 23:59 UTC (Kaggle)** | 9 Nov / 10 Nov 05:29 | conflict unresolved → plan for **8 Nov** |
| Winners announced | 4 Dec 2026 | | |

Internal plan: code freeze **30 Oct**, first real Kaggle submission by **20 Oct**, paper draft complete **4 Nov**, submit paper **7 Nov**.

## Blockers needing Carson
1. **Kaggle rules**: accepted for the Paper Track (download now works). ARC-AGI-2 and ARC-AGI-3 data still 403 at 04:40 IST → accept rules on those two pages too (https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-2/rules and .../arc-prize-2026-arc-agi-3/rules). The paper must document a real submission on one of them.
2. **Disk**: 9.6 GB free. Any local model work needs ~20 GB. Candidates to move/delete are Carson's call.
3. **Paid compute**: nothing spent yet. Kaggle's free quota (30 GPU-h/week) is the default; a RunPod run needs explicit approval with a quoted price.

## Current status
- Pipeline (loader, pass@2 scorer, Kaggle-layout submission writer + validator, registry, diagnostics) done and committed.
- Baselines measured on ARC-AGI-2 public eval: trivial 0/120; DSL search 0/120 (1.25% on ARC-AGI-1 eval, 3.75% on ARC-AGI-2 train).
- ARC-AGI-3 engine runs offline on this Mac (ls20: 7 levels, random agent 0 levels in 30 actions).
- Literature map in progress (agent running). Hypotheses + track choice follow it.

## Next steps (in order)
1. Finish `LITERATURE_MAP.md`, then `HYPOTHESES.md` with three scored hypotheses and the track decision.
2. Build the chosen track's end-to-end Kaggle notebook path (ARC-AGI-3 starter kit cloned at `data/ARC-AGI-3-Kaggle-Starter`; ARC-AGI-2 path reuses gemma-swe-agent packaging).
3. First real Kaggle submission (any score) to lock eligibility before 26 Oct.
