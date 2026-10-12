# NEXT_ACTIONS — status, blockers, next steps (updated 2026-10-12 11:10 IST)

## Verified deadlines (all Kaggle times 23:59 UTC = 05:29 IST next day)
| Event | Date | IST | Note |
|---|---|---|---|
| Entry + team-merger deadline, ARC-AGI-2 and ARC-AGI-3 | 26 Oct 2026 23:59 UTC | 27 Oct 05:29 | must have joined + submitted-able by then |
| ARC-AGI-2 / ARC-AGI-3 final code submission | 2 Nov 2026 23:59 UTC | 3 Nov 05:29 | 1 submission/day, 2 finals |
| **Paper Track writeup** | **8 Nov (arcprize.org) / 9 Nov 23:59 UTC (Kaggle)** | 9 Nov / 10 Nov 05:29 | conflict unresolved → plan for **8 Nov** |
| Winners announced | 4 Dec 2026 | | |

Internal plan: code freeze **30 Oct**, first real Kaggle submission by **20 Oct**, paper draft complete **4 Nov**, submit paper **7 Nov**.

## Blockers needing Carson
1. **Kaggle**: joined ARC-AGI-3 + Paper Track (done 10-12). ARC-AGI-2 not joined; only needed if the fallback track is used.
2. **First competition submission**: a private kernel was pushed for a "Save & Run All" plumbing check
   (https://www.kaggle.com/code/carsonrodrigues/arc-agi-3-model-based-explorer-mem1). Clicking "Submit to Competition"
   on a green run (1 of 1 daily submissions) needs Carson's go-ahead; target by **Oct 20** to lock eligibility before the Oct 26 entry deadline.
3. **Disk**: 9.6 GB free. Not blocking the current CPU-only track.
4. **Paid compute**: none spent, none planned for H1.

## Current status (ARC-AGI-3, public 25 games, 2000 actions, seed 0, toolkit-exact 0–100 score)
| Agent | Score | Levels | Games with level 1 |
|---|---|---|---|
| random (B0) | 0.192 | 3/183 | 2 |
| novelty explorer (B1) | 0.038 | 5/183 | 5 |
| model-based v1 (memory ON) | 0.110 | 8/183 | 7 |
| **model-based v2** (bbox identity, rigid groups, swept-path blocking, terrain colours, reliability gating) | **0.246** | **11/183** | **9** |
| v3 contact curiosity (pre-HUD fix) | 0.255 | 15/183 | 11 |
| v4 thin-bar HUD detector, contact ON | 0.284 | 15/183 | 11 |
| v4 contact OFF (ablation) | 0.204 | 13/183 | 10 |
| v5 goals + decorations, memory ON | 0.277 | 13/183 | 11 |
| v5 memory OFF (E3 ablation) | 0.227 | 11/183 | 11 |
| v6 death-edge learning | running | | |

Pre-registered gates: P2 (≥2× explorer's level-1 coverage = 10 games) MET at 11/25 since v3; P1 paired efficiency mixed; P3 (within-game learning curve) supported on 2/2 games that reach level ≥2 with memory ON (tu93 10.4→4.8, vc33 6.1→2.6 actions/human), none without memory. H1 go/kill date Oct 22.
Faster-than-human levels so far: lp85 L1 15 actions (human 17), tn36 L1 43 (32), vc33 L1 43 (7) + L2 47 (18).

## Next steps (in order)
1. Read v3/v4 results; keep contact curiosity only if it beats v2 paired per game.
2. Goal inference at level transitions + goal-directed planning for levels ≥2 (H1 part 4; level-index weighting makes later levels worth most).
3. Memory ON vs OFF ablation (E3) and seeds 1–2 (E6 noise floor).
4. Ask Carson to click "Submit to Competition" once the pushed kernel's run is green (E5).
5. Human-replay prior (H2) needs the dataset: dub.link/vfwCqvb blocks curl (403/429); open it in a browser.
6. Paper skeleton from measured numbers only (`paper/`), figures: exploration atlas, prediction accuracy by game, learning curves.
