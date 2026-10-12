# NEXT_ACTIONS — status, blockers, next steps (updated 2026-10-12 13:41 IST)

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
2. **First competition submission MADE** (non-final): ID 57095368, kernel arc3-model-based-explorer-mem1-c1 v3, **COMPLETE, public score 0.15** (hidden public half). Eligibility locked. Daily quota used for 10-12. Carson's decisions remain: which two submissions to mark final before Nov 2, and whether to submit the memory-OFF twin on a later day for the paired comparison.
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
| v6 death-edge learning | 0.280 | 15/183 | 12 |
| **v7 (+bar exclusion; final candidate, = Kaggle kernels v2)** | **0.280** | **15/183** | **12** |
| explorer + human-habit prior (H2, E8) | 0.013 | 5/183 | 4 (negative) |
| E12 click-effect generalisation | 0.197 | 14/183 | 11 (negative; gate failed) |
| E13 click-sequence replay | — | — | inapplicable (classes do not persist across levels) |

Pre-registered gates: P2 (≥2× explorer's level-1 coverage = 10 games) MET at 11/25 since v3; P1 paired efficiency mixed; P3 (within-game learning curve) supported on 2/2 games that reach level ≥2 with memory ON (tu93 10.4→4.8, vc33 6.1→2.6 actions/human), none without memory. H1 go/kill date Oct 22.
Faster-than-human levels so far: lp85 L1 15 actions (human 17), tn36 L1 43 (32), vc33 L1 43 (7) + L2 47 (18).

## Next steps (in order)
1. On 10-13 (quota reset 05:30 IST; session cron at 05:37): submit the memory-ON kernel **v6** (E15 vectorised planner, verified bit-identical on 24/25 public games; per-game *thread-CPU* budget 700 s; the rerun plays all 110 games as concurrent threads under one GIL, so a per-game wall budget starves games (v3) and no budget lets one pathological game eat the shared 8.5 h): `kaggle competitions submit -c arc-prize-2026-arc-agi-3 -k carsonrodrigues/arc3-model-based-explorer-mem1-c1 -v 6 -f submission.parquet -m "v7 agent (E15 speed-up), memory ON, per-game thread-CPU budget 700 s (kernel v6)"`. Then on 10-14 the memory-OFF twin (mem0 v6) for the paired comparison (P5). Compare v3 (0.15) vs v6 against the E14 prediction in HYPOTHESES.md. Kernels v4 (no per-game limit) and v5 (CPU budget, pre-speed-up) remain as fallbacks.
2. E12 and E13 done and negative (both kept behind flags). The click games need a different object vocabulary (identity that survives size/colour changes across levels); treat as future work in the paper unless a cheap idea appears.
3. Seeds 2–3 on the final candidate (E6) and the E12 variant; per-game failure table refresh.
4. Paper: trim to ≤ 1,500 words (currently ~1,620), add the E11 table as a figure, final related-work deltas.
5. Two final Kaggle submissions (memory ON / OFF) by Oct 30; writeup submitted Nov 7.
