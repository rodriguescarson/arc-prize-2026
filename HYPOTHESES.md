# HYPOTHESES — competing ideas, predictions, selection (pre-registered 2026-10-12, 04:54 IST)

Written BEFORE any mechanism was implemented. Numbers below are predictions; the outcomes are
appended in dated sections at the bottom, never edited in place.

## Track decision: ARC-AGI-3 (primary), ARC-AGI-2 (fallback)

Evidence (`LITERATURE_MAP.md`, `RESEARCH_INVENTORY.md`, `data/kaggle/reference/` summaries):
- ARC-AGI-2 is saturated at the frontier (90–95%) and on Kaggle (public LB 88.06); 90 papers were
  submitted in 2025; any paper there needs a Kaggle submission in a field of full-time teams, and the
  only local vehicle we could run is someone else's notebook (NVARC port, ~24%), which fails Novelty.
- ARC-AGI-3 Kaggle LB tops at 62.96/100 with LLM-in-REPL harnesses on 96 GB GPUs. All published
  mechanism papers (Twin 93%, Tycho 88%, PRO-LONG 97%) use frontier APIs on the 25 public games only;
  the hidden set is OOD by design. The best non-LLM Kaggle entries score < 0.5/100 and only "work" by
  importing the public games' source code. In the strongest open entry (Franzen v3, 100 trajectories)
  50.88 of 53.51 missing points come from unfinished levels; 2.63 from inefficiency.
- Carson's assets fit ARC-AGI-3: CPU-only harness already runs all 25 games in 9 s; Kaggle starter kit
  exists; paired-stats and pre-registration tooling exist; no GPU is needed to iterate.
- The organisers' own failure taxonomy (blog 2026-05-01): "local effect / false world model", "wrong
  training analogy", "solved level, didn't learn game". Twin: "goal inference is the hard part".
- Unexplored in all of the above: a learned (non-LLM) action-effect model used for *planning*, with
  memory that survives level changes. Stochastic Goose discards everything at each level.

## H1 (PRIMARY) — Object-level action-effect models + cross-level memory

**Limitation addressed.** Model-free explorers (random, novelty, Stochastic Goose's "will the frame
change" CNN) spend hundreds of actions per level because they never represent *what* an action does;
LLM harnesses represent it in prose/code but need 27B models and 96 GB GPUs; and every Kaggle agent
restarts its knowledge at each level although levels of one game share the same dynamics and goal.

**Hypothesis.** ARC-AGI-3 games are deterministic, object-factored systems whose action effects can be
learned online from frame diffs as a small table of (action, local context) → object-level effect.
Planning in that learned model (toward unexplored abstract states, then toward an inferred goal
predicate) reduces the actions needed per level by a large constant factor, and carrying the model and
the goal predicate across levels produces a within-game learning curve that memoryless agents cannot.

**Mechanism.** (1) Perception: 64×64 frame → objects (same-colour connected components; HUD/border
cropped out of the state identity). (2) Effect model: for each action key (simple action, or click on
an object class), record the object-level diff (move Δ, appear, vanish, recolour) conditioned on local
context; conflicts split the context (e.g. "blocked when an object is adjacent in the move direction").
(3) Planner: BFS/A* over abstract states using the model; targets = information gain (untried
(state, action) pairs) until a level completes, then the goal predicate. On a prediction error, update
and replan. (4) Goal inference: at each level transition, keep the predicates from a fixed template
class (overlap/adjacency/colour-count/position-match between object classes) that are true at the
transition frame and false in all earlier frames of that level. (5) Memory: the model and surviving
predicates persist across levels; nothing persists across games.

**Theory.** In a deterministic MDP with |S| abstract states and |A| action keys, model-based
exploration needs at most |S|·|A| real actions to learn all transitions (each real action resolves one
unknown (s,a) pair), while planning is free; model-free novelty search re-traverses known transitions.
The object abstraction shrinks |S| from 16^4096 raw frames to the number of distinct object
configurations actually reachable, which the explorer runs will measure. Cross-level memory removes
the |S|·|A| learning cost for later levels when the dynamics are shared; the goal predicate converts
exploration into a shortest-path problem.

**Pre-registered predictions (ARC-AGI-3 public 25, seed 0, 2000 actions/game, paired per game).**
- P1 (efficiency): among games where both the novelty explorer and the model-based agent complete
  level 1, the model-based agent uses ≤ 0.5× the actions, median over games, with a paired bootstrap
  95% CI upper bound < 0.8.
- P2 (coverage): the model-based agent completes level 1 on ≥ 2× as many games as the novelty explorer
  (explorer today: 5/25 at 2000 actions).
- P3 (learning curve): with memory ON, actions(level k)/baseline(level k) decreases with k on ≥ 60% of
  games that reach level ≥ 3; with memory OFF (model reset at each level), the median slope is ≥ 0.
- P4 (learnability diagnostic): next-abstract-state prediction accuracy of the model > 0.8 after 200
  actions on ≥ 15/25 games; games below 0.5 are reported as the mechanism's stated limit.
- P5 (OOD): on the Kaggle hidden set, memory-ON scores ≥ memory-OFF (two final submissions), reported
  with the known run-to-run variance (±1.87 points on whole-run means in Franzen's audit).
- Kill rule: if P1 and P2 both fail by **Oct 22**, H1 is demoted to a negative result and H2 becomes
  primary. Public-set numbers are development numbers; only the Kaggle hidden score is "evaluation".

**Failure conditions.** Dynamics not object-factored (fluid fills, timers, randomness); click targets
that are not objects (empty-space clicks); goals outside the template class; games where level 1 cannot
be cleared without the goal (no information gain reaches the transition).

## H2 (SECONDARY) — Human replays as an exploration prior

**Limitation.** 342 released human replays on the 25 public games are used only to set baselines.
**Hypothesis.** Human first-run behaviour (which action types first, where clicks land, how often to
repeat) is a game-agnostic prior that cuts actions-to-first-level for any explorer.
**Predictions.** Explorer + prior uses ≤ 0.7× the actions to level 1 vs explorer alone (paired,
median over games, CI upper bound < 0.9); the prior learned on 20 games transfers to the 5 held-out
games (leave-games-out); hidden-set score ≥ explorer alone.
**Risk.** The dataset's format/licence are unverified; the prior may reduce to "click on objects",
which the explorer already does.

## H3 (FALLBACK TRACK, ARC-AGI-2) — Seed variance and selection noise of Kaggle-class TTT

**Limitation.** Only one published range exists (McGovern 3.33–6.67 semi-private); Kaggle teams
compare sub-2-point differences without CIs.
**Hypothesis.** Across 5 seeds of a fixed open pipeline (NVARC port) on the 120 public eval tasks,
≥ 25% of solved tasks churn and the per-run score SD exceeds 1.5 points; a selection-regret estimate
shows that picking the best of N seeds inflates the public score by > 2 points.
**Cost.** 5 × 12 h on Kaggle L4×4 (2 runs/week under quota) — 2.5 weeks; low Novelty on the
submission itself. Kept only as the fallback if ARC-AGI-3 produces nothing by Oct 22.

## Scoring (0–5 each; our estimates, not the judges')
| Criterion | H1 | H2 | H3 |
|---|---|---|---|
| Leaderboard improvement potential | 2 (low absolute score; new mechanism) | 1 | 1 (reuses NVARC) |
| Novelty vs public work | 4 (no non-LLM planning model with cross-level memory on Kaggle) | 3 | 3 |
| Generalisation to unseen tasks | 4 (hidden set is the test; no per-game code) | 3 | 2 |
| Theoretical explanatory power | 4 (sample-complexity argument, measurable |S|,|A|) | 2 | 3 |
| Feasibility before deadline | 3 (perception + planner in ~10 days) | 4 | 2 (GPU quota) |
| Reproducibility / open-source value | 5 (CPU, deterministic, harness released) | 4 | 4 |
| Compute cost and risk | 5 (CPU only) | 5 | 2 |
| **Mean** | **3.9** | 3.1 | 2.4 |

Decision: **H1 primary, H2 secondary add-on (if the data is accessible), H3 fallback track.**

## Outcomes (appended 2026-10-12 06:59 IST; evidence in EXPERIMENT_LOG.csv and experiments/)
- **P2 (coverage ≥ 2× explorer's 5 games): MET** — 11 games with level 1 from v3 onward (`arc3_E2_v4_hud_contact1_a2000_s0`).
- **P1 (level-1 cost ≤ 0.5× explorer, paired): NOT MET** — among games both finish, ratios are mixed (lp85 15 vs 109, ls20 353 vs 644 better; ft09 303 vs 119 worse); median level-1 cost vs human 8.6× (v4) vs 6.4× (explorer, on its 5 easier games).
- **P3 (within-game learning curve with memory): SUPPORTED on n = 2** — memory ON reaches level 2 on tu93 and vc33 with actions/human 10.4→4.8 and 6.1→2.6; memory OFF reaches no level 2 (`arc3_E3_v5_mem{1,0}_goals1_a2000_s0`). Needs more games reaching level ≥ 3 to test the ≥60% criterion.
- **P4 (generative accuracy > 0.8 after 200 actions on ≥ 15 games): NOT MET** — ≥ 0.9 on 2 games, ≥ 0.6 on 6; memoised determinism ≥ 0.95 on 14/25. The generative model is a displacement model; click-driven games are memo-only by design.
- **P5 (hidden set): pending** — kernel runs in Kaggle's runtime (self-test green); submission awaits Carson.
- Unplanned findings worth a paragraph each: hidden-counter progress bars (non-Markov state detected by memo accuracy < 1), rigid multi-part sprites with decorations, deadly-edge memoisation (tu93 resets 350 → 85).
- Decision at 06:59: H1 stays primary (P2 met, P3 supported, mechanism measurable); H2 data is now local for the next cycle.
- **H2 (human-habit prior) — 07:12: FAILED its pre-registered gate.** Paired level-1 ratio median 1.0 (CI [1.0, 11.5], n=3), coverage 4 vs 5 games, total 0.013 vs 0.038 (`arc3_E8_prior_explorer_a2000_s0`). Reported as a negative result; the replay data stays in use for E11 (goal-template consistency) and per-level human baselines.

## Next cycle — E12 pre-registration (07:44)
**Limitation measured:** 12 of 25 public games are click-driven; there the effect model is memo-only (generative accuracy < 0.3), the explorer cannot plan toward unseen click outcomes, and the goal template class is empty on human replays for those games (E11).
**Mechanism:** learn click effects by object class: for a click on class c, the modal object-level diff (recolour c→c′, vanish, appear at a relative offset, toggle) conditioned on the clicked object's class and its neighbours' classes; predict generatively for unseen objects of the same class; add "all objects of class c recoloured to c′" and "clicked-object sequence" templates to the goal class.
**Predictions (public 25, 2000 actions, seed 0, paired vs v7):** level-1 coverage on the 12 click-driven games rises from 4 to ≥ 7; generative accuracy ≥ 0.6 on ≥ 6 of them; no regression on the 13 movement games (same levels ± seed noise). Kill if coverage gain < 2 games by Oct 18.
