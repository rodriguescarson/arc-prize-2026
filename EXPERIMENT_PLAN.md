# EXPERIMENT_PLAN — prioritised experiments, baselines, metrics (2026-10-12)

Protocol for every ARC-AGI-3 experiment: offline harness (`uv run arc3`), 25 public games, fixed
seeds, 2000 actions/game unless stated, scores by `arc3_score.py` (toolkit formula, 0–100), paired
per game against the named baseline with a 2000-resample bootstrap CI on the median ratio.
Public-25 results are DEVELOPMENT numbers (the set is saturated and non-discriminative, AERA 2026);
the Kaggle hidden set is the only EVALUATION number and each hidden-set run costs one of 1 daily
submission, so every public experiment must pre-state what hidden-set decision it informs.

## Baseline ladder (all measured, `EXPERIMENT_LOG.csv`)
| ID | Agent | Public-25, 2000 actions, seed 0 | Levels |
|---|---|---|---|
| B0 | random (RESET on GAME_OVER) | 0.192 | 3/183 |
| B1 | novelty explorer (object-centroid clicks, no-op avoidance, frontier) | 0.038 | 5/183 |
| B2 | Stochastic Goose (Kaggle sample CNN) — to run locally, needs torch | pending | |
| B3 | best public non-LLM Kaggle agent (claimed 0.46 LB, white-box) — reference only, not re-run | — | |

## Experiments, in priority order
| ID | Question | Design | Metric / gate | Compute | Target date |
|---|---|---|---|---|---|
| E0 | Exploration atlas: how big is each game's reachable abstract state space? | run B1 with logs; count distinct frames, distinct object configurations, no-op fraction per action, branching factor | descriptive table, figure 1 of the paper | CPU, 2 min | Oct 13 |
| E1 | Does the learned effect model predict? (P4) | model-based agent, log predicted vs observed abstract next-state | accuracy after 200 actions per game; ≥ 0.8 on ≥ 15 games | CPU | Oct 16 |
| E2 | Does planning in the model cut actions to level 1? (P1, P2) | model-based agent vs B1, paired, seeds 0–2 | median ratio ≤ 0.5 (CI < 0.8); level-1 coverage ≥ 2× | CPU | Oct 18 |
| E3 | Does cross-level memory create a learning curve? (P3) | memory ON vs OFF, same agent | slope of actions/baseline over levels; ≥ 60% negative with ON | CPU | Oct 20 |
| E4 | Goal-predicate ablation | goal inference ON vs OFF (memory ON) | levels completed, actions per level ≥ 2 | CPU | Oct 21 |
| E5 | First hidden-set run | package memory-ON agent in the starter kit, submit | any non-zero score; confirms plumbing | 1 Kaggle submission | **Oct 20** |
| E6 | Replicates | 3 seeds × public-25 for the final agent and B1 | per-game SD, whole-run SD | CPU | Oct 24 |
| E7 | Hidden-set paired finals (P5) | memory-ON and memory-OFF as the two final submissions | score difference vs ±1.87 run noise | 2 submissions | Oct 30 |
| E8 (H2) | Human-replay prior | explorer ± prior, leave-5-games-out | ratio ≤ 0.7 (CI < 0.9) | CPU | Oct 23 if data accessible |
| E9 (fallback) | ARC-AGI-2 seed variance | 5 seeds of the NVARC port | churn ≥ 25%, SD > 1.5 | 60 GPU-h Kaggle | only if H1 killed Oct 22 |

## Failure analysis to run after every experiment
Per game: levels reached, actions per level vs baseline, model accuracy, cause of stall (no state
change found / predicate not in class / plan execution diverged / GAME_OVER loop). Tabulated in
`experiments/<run>/failure_table.md`; the six repeat-failure games from Franzen's audit (sk48, lf52,
bp35, wa30, g50t, sp80) are tracked explicitly.

## Noise floor
Before any claim, two seeds of the same agent must be compared to establish per-game and whole-run
replicate SD (the Franzen audit found 1.87-point spans on whole-run means, 40-point spans per game).
A difference smaller than 2× the replicate SD is reported as "within noise".

## Outcomes so far (appended 2026-10-12 06:56 IST; details in RESEARCH_LOG.md and EXPERIMENT_LOG.csv)
| ID | Outcome |
|---|---|
| E0 | done: atlas (`experiments/arc3_E0_explorer_a2000_s0_logged/atlas.json`); median 983 distinct states in 2000 actions, median |A| 5 |
| E1 | measured: generative accuracy ≥0.9 on 2 games, ≥0.6 on 6, memo accuracy ≥0.95 on 14/25 after HUD detectors (P4 threshold ≥0.8 on ≥15 games NOT met for the generative model; met for memoised determinism on 14) |
| E2 | model-based vs explorer: 15 vs 5 levels, 11 vs 5 games with L1 (P2 met since v3); P1 paired L1 ratio mixed |
| E-contact (added) | contact curiosity ON 0.284/15 vs OFF 0.204/13; kept ON |
| E3 | memory ON 0.277/13 vs OFF 0.227/11; L1 identical, L2 only with memory (tu93, vc33), ratios fall 10.4→4.8 and 6.1→2.6 (P3 direction confirmed on n=2) |
| E10 (added) | death-edge learning: tu93 resets 350→85, 3 levels; full run v6 pending |
| E11 (added) | human-replay goal-template consistency across levels (340 sessions) — running |
| E5 | kernel pushed and green in "Save & Run All"; competition submission awaits Carson |
| E6 | seed-1 replicate of v5 running |
