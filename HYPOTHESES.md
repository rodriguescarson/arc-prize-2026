# HYPOTHESES — competing ideas, predictions, selection (pre-registered 2026-10-12, 05:20 IST)

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
