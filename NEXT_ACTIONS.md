# NEXT_ACTIONS

> **The paper moved on 2026-10-23.** All research artifacts now live in
> `~/research/22-arc-agi3-level-transfer/` (Carson: "all research work should go in ~/research").
> That folder holds `paper/`, `HYPOTHESES.md`, `RUBRIC_SCORECARD.md` and the E21 result, and its
> README explains the split. This repo keeps the competition entry: agent code, tests, data, the
> Kaggle kernels, and the three files the daily recorder writes (`RESEARCH_LOG.md`,
> `EXPERIMENT_LOG.csv`, `submission/SUBMISSIONS.md`). Consolidate those after the 2 Nov freeze.
 — status, blockers, next steps (updated 2026-10-15 22:05 IST)

## IF THE SESSION DIED, START HERE
Session-only timers do not survive. Run by hand from `~/Projects/arc_prize_2026`:
- **2026-10-16 05:37 IST, last submission from this workspace** (check the slot is free for the UTC day first with
  `~/Projects/gemma-swe-agent/.venv/bin/kaggle competitions submissions -c arc-prize-2026-arc-agi-3 | head -4`):
  `~/Projects/gemma-swe-agent/.venv/bin/kaggle competitions submit -c arc-prize-2026-arc-agi-3 -k carsonrodrigues/arc3-model-based-explorer-mem1-c0 -v 4 -f submission.parquet -m "E16 noise draw: v7 agent contact curiosity OFF (kernel c0 v4), cap 3000, 700 s/game thread-CPU"`
  Then record the ID in `submission/SUBMISSIONS.md`, `RESEARCH_LOG.md`, `EXPERIMENT_LOG.csv`; read the score ~9 h later.
- **From 2026-10-17 this workspace never submits again.** The bot in `~/Projects/arc-agi-3` owns every slot.
- **Record a scored draw** (one command, local, safe to re-run; writes SUBMISSIONS.md + RESEARCH_LOG.md + EXPERIMENT_LOG.csv):
  `uv run python -m arc_prize_2026.arc3.record_scores --dry-run` to see it, `--commit` to write and push.
  Run it whenever a draw has been scored (the bot submits daily from 10-17; each score lands ~9 h later).
- **E21 (unfinished):** `uv run python -m arc_prize_2026.arc3.level_transfer data/human_replays --workers 3`
  (~25 min, needs the session to stay open). Killed five times so far by session end or system memory pressure, so
  the run now **resumes**: every finished session is appended to `experiments/human_replays/E21_level_transfer.jsonl`
  and the same command re-run skips what is already there. Give `--restart` only to throw that away and begin again.
  Close Chrome and the iOS simulators first; the two kills for memory both happened with those resident.

## Hidden-set results so far (all on the same 55 unseen games)
| submission | agent | score |
|---|---|---|
| 57095368 | explorer v7, defective bundle (near-random fallback) | 0.15 |
| 57170721 | random solver, 60 actions/game (sibling bot's pipeline test) | 0.12 |
| 57123503 | explorer v7, memory ON | 0.08 |
| 57199354 | explorer v7, **memory OFF** | **0.08** |
Memory is worth +0.050 on the public 25 (E3) and 0.000 here. The hidden metric does not separate these agents,
and a random agent outscores all of them. E16's reframe (pre-registered 10-13 14:13) is now measured, not argued.


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
5. **Direction: RESOLVED by the sibling workspace.** `~/Projects/arc-agi-3` (another session, repo rodriguescarson/arc-agi-3) already runs the Franzen/Duck-harness fork with automated daily submissions from 2026-10-17 00:01 UTC (GitHub Actions + Mac LaunchAgent + claude.ai routine; handover in its `docs/STATUS.md`). Slot plan (verified by its scheduler's dry-run 10-13): this workspace owns 10-14, 10-15, 10-16 (E16 at 00:07 UTC); the bot owns every day from 10-17. **Never push `arc3-duck-*` kernels or submit by hand after 10-16.** GPU quota from 10-17 is reserved for that pipeline; this workspace uses CPU kernels only.
6. **Publishing at filing (Carson's call):** the Paper Track needs a public notebook; `carsonrodrigues/arc3-paper-reproduce-public25` v1 (reproduces 0.2797 / 15 levels on Kaggle CPU) is built and private. Making it and the repo public happens only on Carson's say-so.
7. **Rules checked 10-13 on arcprize.org:** the paper must be "linked to a Kaggle code submission ... that demonstrates the approach detailed in the paper" (score not a gate; the page does not say it must be a selected final), so the writeup links to an explorer submission (57123503), never to a Duck-fork run. Code must be open-sourced under a permissive public-domain licence (CC0 / MIT-0) before private scores are released; the earlier CC-BY note applied to the Kaggle writeup text, not the code. **Finals recommendation (Carson's call):** final 1 = best Duck-fork draw from ~/Projects/arc-agi-3; final 2 = the explorer submission the paper cites, which removes any doubt about paper eligibility at no practical cost.

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
