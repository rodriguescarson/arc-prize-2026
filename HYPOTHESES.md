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
**E12 gate fixed before the result (08:03):** "click-driven" = has ACTION6 and v7 generative accuracy < 0.3 → 13 games: ar25, bp35, cn04, ft09, ka59, lf52, lp85, r11l, s5i5, sb26, sc25, sk48, vc33; v7 clears level 1 on 5 of them (bp35, lf52, lp85, s5i5, vc33). Gate: E12 clears level 1 on ≥ 8 of the 13 (≥ +3), generative accuracy ≥ 0.6 on ≥ 6 of them, and no loss of levels on the other 12 games beyond seed noise (≤ 1 game).
- **E12 — 08:45: FAILED** (coverage 5 → 5 vs ≥ 8 required; accuracy criterion met on 6/13; total 0.197 vs 0.280). Kept as a negative result with the "learnable but not plannable" reading; flag `click_model` off by default.

## Next cycle — E13 pre-registration (08:52): ordered goal templates for click games
**Limitation measured:** E11 found no consistent single-state predicate on 12 click-driven games; E12 showed click effects are learnable but planning on them does not find levels. Humans solve these games by *sequences* (toggle all of class c, then press d; click objects in an order).
**Mechanism:** extend the goal class with two ordered templates inferred from the level-1 trajectory: (a) AllRecoloured(c→c′) then Click(d) — the last k distinct click classes before the transition, in order, with the state predicate "all objects of class c have colour c′" as the precondition; (b) ClickSequence of classes [c1..ck] (k ≤ 4) — replay by class on the next level regardless of positions. Transfer: on level ≥2, execute the inferred sequence first (planning is not needed), then fall back to exploration.
**Predictions (public 25, 2000 actions, seed 0, paired vs v7):** on the 12 click-driven games with ≥2 levels in human data, the agent reaches level 2 on ≥ 3 games where v7 reaches it on 1 (vc33); no regression on movement games (≤ 1 game lost); total ≥ 0.30. Kill if < 2 games gain a level 2 by Oct 19. The human-replay check (E11-style) must show the ordered template is consistent across levels on ≥ 4 of the 12 click games before the agent run is trusted.
- **E13 — 09:01: FAILED / inapplicable** (replay fired on 1 of 5 smoke games; no level gained). Kept behind `sequences=True`.

## Next cycle — E14 pre-registration (12:27): is the hidden-set gap starvation or generalisation?
**Observation:** kernel v3 scored 0.15 on the hidden public half vs 0.280 on the public 25. Two explanations: (a) the rerun's 110 concurrent threads under one GIL, with the shim's 600 s per-game *wall* budget, gave each game only a fraction of its 1,500 actions (the 25-thread simulation already truncated 23/25 games; Kaggle's CPU is ≈4.5× slower and runs 4.4× more games); (b) the hidden games are simply harder for this agent.
**Change under test (kernel v5, agent identical to v7):** per-game budget measured in the game's own thread CPU time (700 s ≈ 2.5× the 278 s fair share of 8.5 h / 110), global 8.5 h wall and 1,500-action cap unchanged. The 25-thread simulation with the equivalent cap (155 s on this Mac) is the local control.
**Predictions, fixed before the 10-13 submission:** if (a) dominates, v5 scores ≥ 0.25 (≥ 1.65× v3); if (b) dominates, v5 scores within ±0.05 of 0.15. A result between 0.20 and 0.25 means both. The memory-OFF twin (10-14) then tests P5 on the hidden set under the same budget. The local control must stay within seed noise of 0.280 (≥ 0.274) or the cap is too tight and the prediction is void.
- **E14 control (12:36): MET** — the 25-thread simulation with the equivalent cap scores 0.280 / 14 levels (uncapped 0.280 / 14; seed band 0.276–0.280), so the cap costs nothing locally and the prediction for the 10-13 submission stands.

## Next cycle — E16 pre-registration (13:53): hidden-set ablations, one submission per day
**Question:** do the components' public-25 gains transfer to the hidden public half (55 unseen games)? Kernels, all with the v6 agent code and the 700 s thread-CPU budget: mem1 (full), mem0 (memory off), mem1-c0 (contact curiosity off), mem1-c1-g0 (goal inference off). Schedule (non-final, standing authorisation): 10-13 mem1 v6, 10-14 mem0 v6, 10-15 mem1-c0 v1, 10-16 mem1-c1-g0 v1.
**Predictions, fixed before any of them runs:** ordering full ≥ goals-off ≥ memory-off on the hidden set (goal inference only acts after a transition; memory-off also loses it); contact-off < full by at least the public-25 margin ratio (0.204/0.284 = 0.72×) if the contact mechanism transfers, within noise otherwise. Noise on the hidden set is unknown for our agent (near-deterministic locally; the rerun's scheduling may vary) — the public plateau notebook's identical reruns differed by 6.8 points of 27.8 (24%), so we treat ratios inside 0.8–1.25 as inconclusive and report them as such.

## Next cycle — E17 pre-registration (13:55): action-budget sensitivity
**Observation:** the Kaggle kernels cap each game at 1,500 actions, chosen when a game cost up to 7,000 s; after E15 the whole public set costs 451 s of CPU at 1,500 actions, ≈ 29% of the rerun's budget. Locally m0r0 reaches level 1 at action 1,725, which a 1,500 cap forfeits. A completed level scores > 0 however late it comes; an uncompleted one scores 0.
**Experiment:** one public-25 run at 4,000 actions (seed 0, same agent, 900 s per-game time budget); levels completed as a function of budget are read from the cumulative level-action counts at 500 / 1,000 / 1,500 / 2,000 / 3,000 / 4,000.
**Predictions:** levels at 2,000 = 15 (replicates E3); ≥ 2 further levels between 2,000 and 4,000. Decision rule fixed now: the Kaggle cap moves to the largest budget whose extrapolated CPU (110 games × mean thread-CPU × 4.5) stays under 60% of 30,600 s, provided the per-game 700 s thread-CPU cap remains; otherwise it stays at 1,500. If fewer than 2 levels are gained past 2,000, the cap moves to 2,000 only (to keep m0r0).
- **E17 (14:26): prediction MET** — 15 levels at 2,000 (replicates E3), 17 at 3,000 and 4,000 (ft09 2,672; sk48 2,863). Cap decision pending the thread-CPU measurement at 3,000 actions.
- **E17 decision (14:41):** thread-CPU at 3,000 actions = 886 s / 25 games → 57% of the rerun budget < 60% → cap = 3,000 for every kernel from now on (global wall 8.25 h, per-game 700 s thread-CPU). **E16 amendment (14:41, before any hidden-set run):** all four ablation kernels use cap 3,000: mem1 v7, mem0 v7, mem1-c0 v2, mem1-c1-g0 v2.

## Next cycle — E18 pre-registration (14:46): is the goal-template class the bottleneck?
**Limitation measured:** 20 of 25 public games are *no-progress* (§6): the planner keeps finding untried transitions but never crosses a level boundary; E11 found a cross-level-consistent goal predicate from our five templates (Gone/Count/Touch/Overlap/Appeared) in only 73 of 262 multi-level human sessions (27.9%) and on 6 of 25 games.
**Question:** would a broader predicate family explain more human level completions, i.e. is the template class the bottleneck, or is it the object representation / positive-example construction?
**Extended family (added to the analysis only; the agent is unchanged):** touch2(c, d) (two non-mover classes touch), inside(c, d) (c's bbox inside d's), aligned(c, d) (share a row or column), same_colour_all(h, w) (every object of that size has one colour), count_colour(colour, k), gone_colour(colour), appeared_colour(colour).
**Control:** the same analysis with a *random non-transition frame* of each level as the positive example (fixed seed): any cross-level consistency found there is spurious, and the extended family must beat its own null by the same margin the base family beats its null.
**Predictions, fixed before the run:** the base family reproduces 73/262 and 6 games; the extended family raises the session fraction to ≥ 40% and the consistent-game count (≥ 50% of a game's multi-level sessions) to ≥ 10 of 25, with the null control under 10%. If fewer than 2 games become consistent, the template class is not the bottleneck (reported as such; no agent change). If the prediction holds, the families responsible are added to the agent and tested on the public 25 with the standing gate (level ≥ 2 reached on ≥ 2 more games, no loss beyond seed noise).
- **E18 (15:08): NEGATIVE** — base family reproduces 73/262 (27.9%) and 6 games; extended family 89/262 (34.0%) and 7 games vs the ≥ 40% / ≥ 10 required; null controls 10/262 (3.8%) base and 26/262 (9.9%) extended. The only new consistent game, sb26 (appeared_colour(3), 6/10), is matched by its own null (9/10), so it is spurious; bp35 gains a real but sub-threshold aligned((7,3,3),(9,4,2)) on 5/11 sessions. Twelve games (lp85 0/32, r11l, sc25, sp80, su15, tn36, tr87, vc33 among them) stay at zero under every family: their goals are not single-state predicates over (colour, h, w) classes. No agent change.

- **E14 restated (15:15), before the 10-13 run:** the 0.15 baseline came from a bundle whose movement-prediction path raised an exception on every call and fell back to a cyclic action (bundle defect found 15:15, fixed in the kernels built after commit 92516a5). The 10-13 submission therefore changes two things at once (bundle fix + budget), so a rise cannot be attributed to the budget alone. Revised reading: if the fixed, budgeted agent scores ≥ 0.25 the hidden set is reachable by the v7 agent as measured locally; the budget-only effect can no longer be isolated without spending a daily slot on a fixed-bundle/600 s-wall kernel, which we do not plan. The as-submitted public-25 score of the broken bundle is measured for the record (`experiments/as_submitted_v3.out`).
- **E14 premise withdrawn (15:16):** the broken v3 bundle scores 0.096 / 1 level on the public 25 with 85% of its actions being exception fallbacks, so the hidden 0.15 was a near-random cycler, not starvation of the v7 agent. The budget mechanism stays (measured independently in the threaded simulations); the 10-13 submission is now simply the first hidden-set measurement of the agent. Prediction kept for the record only: fixed agent ≥ 0.25 would show the public-25 behaviour transfers; ≤ 0.15 would mean it does not.

## Next cycle — E19 pre-registration (17:46): a decision model as goal proposer over the symbolic state
**Limitation measured:** 20 of 25 public games are no-progress; the agent cannot guess a goal before the first level transition (§6), and E18 showed the template list is not the bottleneck. LLM harnesses solve the goal problem from pixels at ~175k tokens per game.
**Mechanism:** keep perception, the effect model, the planner and memory unchanged; add a goal *proposer*: at each level start (and every 300 actions while no transition has been seen) the agent writes a ~600-token summary of the level — object classes (colour, size, count, positions), the mover class and its learned displacements, what the last transition changed (if any) — plus a numbered menu of concrete, currently-false goal predicates from the template families (touch, overlap, gone, aligned, inside). A decision model picks one; the planner plans toward it exactly as it does for inferred goals. A chosen goal that is reached without a level transition is reported back and excluded on the next ask. Models (OpenRouter, responses cached on disk, temperature 0): google/gemma-4-31b-it:free, nvidia/nemotron-3-super-120b-a12b:free, microsoft/phi-4 (paid, cents), typesafe/jev-1.13 if reachable. The Kaggle rerun has no internet, so this is a development experiment; a positive result would be ported to an offline small model from Kaggle Models on the RTX 6000.
**Predictions (public 25, 2,000 actions, seed 0, paired vs v7 = 0.280 / 15 levels / 12 games with level 1):** the best model lifts games-with-level-1 to ≥ 14 (+2) or total to ≥ 0.30, with no loss beyond seed noise (≤ 1 game) on games v7 already solves. A stub proposer that always answers "explore" must reproduce v7 exactly (control). Kill if the best model gains < 1 game: report as negative (the summary is not enough for goal guessing) and keep the module off by default.
**Cost cap fixed now:** ≤ $2 of OpenRouter credit in total (free models first); every call cached in `experiments/llm_cache/`.
- **E19 (18:11): NEGATIVE** — no proposer gains a game (gate: ≥ +2 games or total ≥ 0.30); Jev −0.002, Phi-4 ±0, Nemotron unparsed. 24 of Jev's 31 accepted goals were never reached: the bottleneck moved from *guessing* the goal to *reaching* it in a partial model. Module stays off by default.

## Next cycle — E20 pre-registration (18:11): goal-directed exploration toward a proposed target
**Limitation measured:** E19's proposed goals are mostly unreachable by the planner (24/31 never reached) because the learned model does not yet contain a path; the agent then ignores the proposal and explores by curiosity.
**Mechanism:** when a *touch(c)* goal is active (proposed by the decision model, or inferred from a transition) and the planner returns no path, take the single action whose learned mover displacement most reduces the bbox distance between the mover group and the nearest object of class c, provided the model does not predict a block, the edge is not deadly and the key is not a known no-op; otherwise fall back to the curiosity target as before. Nothing else changes; the stub-"explore" control must stay bit-identical to v7.
**Predictions (public 25, 2,000 actions, seed 0, paired vs v7):** with Jev as proposer, level-1 cost falls by ≥ 25% on ≥ 3 of the 12 games v7 solves, or ≥ 1 new game reaches level 1; no game lost beyond seed noise (≤ 1). Kill if neither holds; then the proposal path is closed and the paper reports E19/E20 together as the measured limit of "LLM proposes, symbolic planner executes" in this agent.
- **E20 (18:55): gate MET for Jev on the new-game clause, marginally** — Jev+greedy 0.2954 (+0.0151 vs the greedy-only control 0.2803; seed SD 0.0014), gains r11l, loses ls20 (165 greedy steps toward a wrong `touch((9,3,3))` burned its budget), g50t 1,159 → 240. Nemotron and Phi-4 lose tu93. Replication on seeds 1–2 running before any port.

## E20b pre-registration (18:55): bound the walk
**Limitation measured:** a wrong proposed target can absorb the level's budget by greedy walking (ls20).
**Change:** reject a proposed goal after `greedy_cap` = 80 greedy steps without it holding ("not reachable by walking"), exclude it and ask again. Nothing else changes.
**Prediction (seed 0, paired vs E20 Jev+greedy):** ls20 recovers its level (353 ± noise) while r11l and g50t keep theirs; total ≥ 0.295. Kill if ls20 is not recovered or any other game is lost.
- **E20b (19:37): MET** — 0.2955 / 16 levels / 13 games, no loss; ls20 recovered (826). Mechanism = Jev proposes touch goals from the symbolic summary; the agent walks toward them with learned displacements when the planner has no goal path; a goal is dropped after 50 actions held without a transition or 80 greedy steps without reaching it.
- **E20 replication (19:40): CONFIRMED** on seeds 1–2 (Δ +0.0158 both; +g50t, +r11l; ls20 degraded) — the proposer effect is ~11 seed-SDs.
- **E20b replication (20:25): CONFIRMED** — Δ +0.015/+0.016/+0.016 over greedy-only on seeds 0–2, +1/+2/+2 games, no losses. Open question for the submission: an offline proposer (Gemma 4 31B / Qwen3 32B runs in progress).

## E20c pre-registration (23:08): a proposed goal is a target only until first reached
**Limitation measured:** with a chat proposer, tu93 loses all three levels (0 greedy steps): the accepted `touch((14,3,3))` goal is satisfiable, the planner keeps returning paths to goal-satisfying states, the agent shuttles between them (goal_plans 43, distinct frames 3,115 vs 6,508) and never finds the real transition. Jev avoided it by answering "explore" there (it declines in 51 of 107 cached decisions; median confidence 0.22).
**Change:** the proposed goal is used as a planning/greedy target only while it has never held on this level; once reached, normal exploration resumes and the 50-action patience decides whether to drop it. Nothing else changes; the stub control stays bit-identical.
**Predictions (seed 0, paired):** Nemotron-Super keeps tu93's three levels (≥ 2) while keeping ka59 and g50t; Jev's result stays within ±0.003 of E20b (0.2955). Kill if tu93 is still lost or Jev drops a game.
- **E20c (23:30): split** — Nemotron-Super + guard 0.2948 / 16 / 13, no loss (met); Jev + guard 0.2831, tu93 lost: Jev (sampled API; new prompt, new answer) proposed the *right* but far target `touch((14,3,3))` at action 4; never reached, so the patience never started, and the goal stayed active for 2,000 actions while the perturbed trajectory missed the transition (fallback 1,816).

## E20d pre-registration (23:30): bound a never-reached goal and the asks per level
**Change:** a proposed goal not reached within 150 level-actions is dropped and excluded; at most 3 asks per level. E20b cap (80 greedy steps) and E20c guard (target only until first reached) stay. Nothing else changes; the stub control is bit-identical.
**Predictions (seed 0, paired vs v7 0.2797 / 15 / 12):** Jev and Nemotron-Super both ≥ 0.29 with no game lost; tu93 keeps ≥ 2 levels under both. Kill if either proposer loses a game; then the proposer line is reported with E20b/E20c as its measured best (Nemotron-Super 0.2948, Jev 0.2955) and the tu93 fragility stated.
- **E20d (23:58): FAILED** — Jev 0.2830 (tu93 lost), Nemotron-Super 0.2806 (s5i5 lost). Kill rule applied: proposer design frozen at E20b (Jev, replicated ×3) / E20c (Nemotron-Super, open-weight, replication pending). The paper reports E19–E20d together.
- **E20c with Nemotron-Super (00:38): REPLICATED ×3** (+0.015 each, no losses). Proposer line final: Jev/E20b and Nemotron-Super/E20c, both replicated; chat models without the guard negative (Phi-4, Gemma 4 31B, Qwen3 32B, Nemotron-Nano).
- **Port candidates (01:44):** Gemma 4 31B + guard −0.011 (lost g50t, tu93); Nemotron-Nano 30B + guard ±0 (neutral). Only Jev and Nemotron-Super work. Proposer line closed for design; port = Carson's call.

- **E14 outcome (14:13): the public-25 result does NOT transfer.** Fixed-bundle agent (submission 57123503, kernel mem1 v9) scores **0.08** on the hidden public half, below the 0.15 of the defective cyclic bundle and inside the 0.05–0.23 band that holds 25.7% of the 4,233 teams (leaderboard 2026-10-13). Mechanism, measured on the public 25: the squared-efficiency score counts first levels solved near the human action count (worth 100/Σ1..L = 1.8–4.8 game points each; a level at 10× human cost is worth < 0.05). Three such games (lp85, tn36, vc33) supply 90% of the public 0.280; without them it is 0.027. The hidden 0.08 = 4.4 game points over 55 games ≈ one such level. So both hidden numbers (0.15 cyclic, 0.08 real) are draws from the same floor, separated by roughly one lucky level.
- **E16 reframed (14:13, before any E16 result):** at this floor a single near-human level moves the hidden score by 0.03–0.09, so the memory/contact/goals ablations cannot be distinguished from the full agent; the pre-registered ratio test is void. The three remaining submissions still run as scheduled and are reported as a **noise estimate** of the hidden score for near-identical agents (four draws: mem1, mem0, c0, g0), not as ablations. P5 is untestable on the hidden set at this score level and is reported as such.

## Scope decision (2026-10-13 19:28 IST, Carson): the paper covers cross-level memory in two agents
The rubric averages six 0–5 criteria and Accuracy is the leaderboard score of the linked submission; with the explorer's 0.08 (Accuracy ≈ 1) the average cannot exceed (1 + 25)/6 = 4.33, below the 4.5 bar of the Outstanding Papers pool (arcprize.org/competitions/2026/paper). Decision: the paper studies *what an agent should carry from one level to the next* in the symbolic explorer (controlled ablations, mechanism) and in the LLM harness of `~/Projects/arc-agi-3` (level memory = `solved_levels()`, variants v2 and v6, scheduled there from 10-17), and links the best level-memory LLM draw. Most of that draw's score is Franzen's harness, and the paper says so.

## E21 pre-registration (19:28): plans or mechanics — what carries over between levels?
**Question:** the LLM harness's memory shows the previous level's *winning action sequence*; the explorer's memory carries *mechanics* (action → displacement, blocking, deaths). Which content transfers to the next level? Measured on the public 25 with all 340 human sessions (full population), no agent involved.
**Data gate (F):** replay every session's recorded actions in the local environment (same game builds) and compare each frame with the recorded frame. A session is usable for in-environment tests up to its first mismatch. Report the match rate; if < 80% of consecutive completed level pairs are reproducible, M1 is reported as invalid.
**M1 plan transfer (in environment):** for every consecutive pair of levels (k, k+1) completed in one session: restore the start of level k+1 by replaying the human's actions, then execute W_k (the last attempt that completed level k, resets excluded, as `compute_solved_levels` returns it; click coordinates verbatim). Outcome: level k+1 completed within |W_k| actions. Controls: C1 W_k shuffled (same multiset, 5 shuffles); C2 W_{k+1} itself (positive control, must complete); C3 uniform random actions from the available set, same length (5 draws).
**M2 plan similarity (recorded data):** 1 − Levenshtein(W_k, W_{k+1}) / max length over action-id tokens, against the same with W_k shuffled.
**M3 mechanics transfer (recorded data, movement actions 1–5):** learn each action's modal mover displacement on level k; on level k+1, over steps with that action where something moved, the fraction whose observed displacements include the level-k prediction. Ceiling: the same model scored on level k (in sample). Null: the action labels of the level-k model permuted.
**Predictions:** (P21a) W_k completes level k+1 in ≤ 10% of pairs overall and in 0 pairs on ≥ 20 of 25 games; C2 ≥ 90%. (P21b) the level-k mechanics model predicts level-k+1 moves with accuracy ≥ 0.8 on movement games and ≥ 3× its permuted null. (P21c) M2 similarity exceeds its shuffle control on fewer than half the games.
**What changes on the outcome:** if P21a and P21b hold, the paper states that a level memory should carry mechanics rather than plans, and proposes (does not claim) a mechanics summary for the LLM harness. If W_k completes level k+1 in > 25% of pairs, verbatim plan memory is strong and the paper says so. Either way the result is reported.

## Hidden-set pre-registration for the LLM-harness draws (19:28, before any of them run)
Identical copies of Franzen's notebook score mean 25.8, SD 3.9 (sibling `docs/STATUS.md`). The difference of two single draws then has SD ≈ 5.5, so a hidden-set effect of level memory (v2 − v1, v6 − v3) is claimed only if it exceeds 11 points. Prediction: no such difference (|Δ| < 11 for both pairs). The paper reports the draws as performance of the harness with memory, not as evidence for memory; the memory effect is argued from E3 (explorer ablation) and E21.
- E21 definitions fixed before the run (19:40): "movement games" = the 12 games not in `CLICK_GAMES` of `human_sequences.py`; a game "exceeds its shuffle control" in M2 when the mean over its pairs of (similarity − mean shuffled similarity) is > 0; M3's permuted null is the exact mean over all non-identity permutations of the learned action labels.

### E21 deviation, recorded 2026-10-16 15:05 IST (before the affected sessions were scored)

The C3 control is pre-registered as five uniform-random sequences of the same length as W_k. On three games
(lf52, ar25, re86) a random sequence drives the environment into states whose per-step cost explodes. Measured
on one lf52 pair: step 47 took 0.7 s, step 64 10.1 s, step 77 40.0 s, with the worker process reaching 8.5 GB.
Human action sequences never do this; the same session's nine winning sequences are 11 to 157 actions and
replay in milliseconds. Six workers each holding one such replay exhausted a 16 GB machine and the run made
no progress for 70 minutes.

A 60-second wall-clock budget per control replay is therefore applied, which is about 200x a normal replay.
A run that exceeds it is recorded as **unevaluable** (`end="budget"`, with the actions executed and the
sequence length), is **excluded from the C1 and C3 rates**, and is **never counted as a failure to complete
the level**. Counting it as a failure would push the control rates toward zero, which is the direction that
favours P21a, so the conservative choice is to exclude and report. The number of unevaluable runs, and the
median point at which they were cut, are printed in the result summary and will be stated in the paper.

Re-running three already-scored sessions under the budget reproduces their stored results exactly, with zero
unevaluable runs, so the 327 sessions scored before this change are unaffected.
