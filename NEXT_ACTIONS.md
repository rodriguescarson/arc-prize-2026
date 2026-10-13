# NEXT_ACTIONS — status, blockers, next steps (updated 2026-10-13 14:13 IST)

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
5. **Direction (asked 10-12 12:40, open):** keep the paper line only; add a fork of the Franzen plateau notebook on free Kaggle GPU quota (scheduling patch + object-level tools; one 4×25 A/B per week); or the LoRA route (needs paid multi-GPU, advised against: no transferable data, no measurable validation).
6. **Publishing at filing (Carson's call):** the Paper Track needs a public notebook; `carsonrodrigues/arc3-paper-reproduce-public25` v1 (reproduces 0.2797 / 15 levels on Kaggle CPU) is built and private. Making it and the repo public happens only on Carson's say-so.

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

## Decision-model goal proposer (E19–E20d, 10-12 evening) — design frozen
Jev 1.13 (OpenRouter Decisions API) proposes a currently-false "touch" goal from the symbolic level summary; the agent walks toward it with learned displacements when the planner has no goal path, dropping a goal after 50 held actions without a transition or 80 greedy steps (E20b). Public 25: **0.2955 / 16 levels / 13 games** vs v7 0.2797 / 15 / 12; **replicated on seeds 1–2 (+0.016 each, no losses)**. The free open-weight Nemotron-3 Super 120B-A12B reaches 0.2948 / 16 / 13 with the E20c guard, **replicated on seeds 1–2 (+0.015 each, no losses)** — the candidate for an offline port on the RTX PRO 6000 (vLLM pipeline in ~/Projects/gemma-swe-agent). Chat models without the guard hurt (Phi-4, Gemma 4 31B, Qwen3 32B); with the guard Gemma 4 31B still loses two games and Nemotron-Nano 30B is neutral, so **only Jev (API-only) and Nemotron-Super 120B-A12B (open-weight) work**; further bounding (E20d) hurt → design frozen by the kill rule. Cost ≈ $0.003 per Jev run; every call cached. **Not in the Kaggle submission** (no internet in the rerun); a port is a separate decision (GPU kernel, 9 h budget shared with 110 games).

## Next steps (in order)
1. **DONE 10-13 05:37 IST — submission 57123503 (mem1 v9): hidden score 0.08** (inside the low leaderboard band; the public 0.280 was 90% three near-human first levels and does not transfer). Was: submit the memory-ON kernel **v9** (v7 and every earlier version carried the `_moved` bundle defect; v8+ are verified bit-identical to the repo agent; v9 adds the frames-list trim that bounds the framework's RAM) (E15 vectorised planner, verified bit-identical on 24/25 public games; action cap 3,000 after E17; global 8.25 h; per-game *thread-CPU* budget 700 s — the rerun plays all 110 games as concurrent threads under one GIL, so a per-game wall budget starves games (v3) and no budget lets one pathological game eat the shared budget): `kaggle competitions submit -c arc-prize-2026-arc-agi-3 -k carsonrodrigues/arc3-model-based-explorer-mem1-c1 -v 9 -f submission.parquet -m "v7 agent (E15), memory ON, cap 3000, per-game thread-CPU 700 s, fixed bundle + frame trim (kernel v9)"`. Compare v3 (0.15) vs v7 against the E14 prediction in HYPOTHESES.md. Older kernel versions (v4 no limit, v5 CPU budget pre-speed-up, v6 cap 1,500) remain as fallbacks.
   E16 crons scheduled (2e2ad3d9 10-14, f5030151 10-15, e7198cea 10-16). Then the E16 hidden-set ablations, all at the same budget (cap 3,000, 8.25 h, 700 s/game): 10-14 `arc3-model-based-explorer-mem0-c1` **v9** (memory off), 10-15 `arc3-model-based-explorer-mem1-c0` **v4** (contact off), 10-16 `arc3-model-based-explorer-mem1-c1-g0` **v4** (goal inference off). All non-final; the two finals remain Carson's call.
2. E12 and E13 done and negative (both kept behind flags). The click games need a different object vocabulary (identity that survives size/colour changes across levels); treat as future work in the paper unless a cheap idea appears.
3. Seeds 2–3 on the final candidate (E6) and the E12 variant; per-game failure table refresh.
4. Paper: trim to ≤ 1,500 words (currently ~1,620), add the E11 table as a figure, final related-work deltas.
5. Two final Kaggle submissions (memory ON / OFF) by Oct 30; writeup submitted Nov 7.
