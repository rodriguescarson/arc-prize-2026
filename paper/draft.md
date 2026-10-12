# Learning what actions do: object-level effect models with cross-level memory for ARC-AGI-3

*Working draft, 2026-10-12. ≤1,500 words at submission. Every number below is tagged
[measured: file] or [pending]. Nothing is reported from the Kaggle leaderboard until a submission ID exists.*

## Abstract (draft)
ARC-AGI-3 agents on Kaggle either run a 27B-parameter language model in a code REPL or explore blindly.
We ask whether a small, training-free agent can instead *learn what its actions do* while playing,
plan in that learned model, and carry what it learned across the levels of a game. The agent segments
each 64×64 frame into objects, learns per-action object displacements with blocking rules from frame
diffs, plans by breadth-first search in the learned model toward unexplored interactions, and, after the
first level transition, infers a goal predicate from a fixed template class and plans toward it on later
levels. On the 25 public games it clears [pending E3] levels versus 5 for a novelty-seeking explorer and
3 for a random agent [measured: experiments/arc3_E2_v4_hud_contact1_a2000_s0, arc3_explorer_a2000_s0,
arc3_random_a2000_s0], solving two levels at human efficiency [measured: lp85 15 vs 17, tn36 37 vs 32].
Where the goal is inferred, level 2 costs a fraction of level 1 [measured: tu93 198 → 77 actions,
smoke_deco2]. We release the agent, an offline harness that reproduces the competition's scoring
formula, and two diagnostics that we found necessary and that others can reuse: a non-determinism test
for state representations and a hidden-counter detector.

## 1. Problem and question
ARC-AGI-3 replaces ARC-AGI-2's single input-output guess with an interactive game: the agent sees a 64×64
frame, chooses among up to seven actions (four directions, two buttons, a click), and must discover the
rules, the controls and the goal from scratch across several levels of increasing difficulty. The score is
efficiency: a completed level earns 100·(human actions / agent actions)², capped at 115, and a game's score
weights level k by k, so later levels dominate. The organisers' own failure taxonomy for frontier models
names "local effect / false world model", "wrong training analogy" and "solved the level, didn't learn
the game"; the strongest public-set paper concludes that "goal inference is the hard part". We separate
three things an agent must learn from interaction alone: what the *state* is (which pixels matter), what
each *action does*, and what counts as *done*, and we ask how far an agent that learns all three online,
with no language model and no training set, gets on the hidden Kaggle set.

## 2. Prior work and gap
Kaggle entries fall into three families: LLM-in-REPL harnesses (Tufa Labs' Duck, Franzen's Milestone-2)
where a 27B model writes Python against the frames on a 96 GB GPU; a "will the frame change" CNN
(Stochastic Goose) that re-initialises at every level; and white-box search that imports the public games'
source and cannot run on hidden games. Research papers (Twin, Tycho, PRO-LONG) build executable world
models with frontier APIs and report 88–100% on the 25 public games only, a set AERA shows null strategies
partly solve. No public agent learns a non-LLM model of action effects, plans in it, keeps it across
levels, and is evaluated on the hidden set. That is the gap.

## 3. Method
3.1 State: objects (colour, bbox, mask), terrain colours (≥20% coverage) kept for collision but not identity,
HUD rows masked by two measured detectors. 3.2 Effect model: rigid groups, modal displacement, swept-path
blocking/passable colour statistics, per-key reliability window. 3.3 Planner: BFS in the model; targets =
untried (state, action), rarely-contacted object classes, or goal predicates. 3.4 Goal inference: templates
Gone/Count/Touch/Overlap/Appeared, positive = model-predicted post-action state at the transition, negative
= level start, intersection across transitions. 3.5 Memory: model and goals persist across levels.

## 4. Why it should work (theory)
**Assumption A1 (determinism).** ARC-AGI-3 games are deterministic given a correct state representation.
Measured: with memoised transitions, next-state prediction is ≥ 0.95 accurate on 14 of 25 games and
exactly 1.0 on 9 [measured: v4 agent_stats, atlas table]; the remaining games expose hidden counters
(progress bars that advance on a hidden modulo) or animation-length state, which is where A1 fails and
where our two detectors recover it.
**Assumption A2 (factored, rigid dynamics).** Simple actions displace a rigid group of objects by a fixed
vector unless blocked by a colour in the swept path. Measured: the generative model is ≥ 0.9 accurate on
sp80 and su15 and ≥ 0.6 on dc22, g50t, m0r0, ls20 [measured: fig3]; it fails on click-driven games where
effects are not displacements (ft09, r11l, s5i5, tn36, vc33 rely on memoisation).
**Bound.** Under A1 a model-free explorer pays again for every revisited transition; a planner pays at
most once per unknown (state, action) pair, so real actions ≤ |S_reach|·|A| with planning free. The
explorer reaches a median 983 abstract states in 2000 actions with median |A| = 5 [measured: atlas], so a
model-free sweep cannot cover one level inside the budget, while the planner resolves only the distinct
pairs it chooses (contact-driven targets cut that further).
**Transfer.** Levels of a game share dynamics and goal (the organisers' design); the score weights level
k by k. So the gain from learning is realised on later levels: memory ON vs OFF leaves level-1 cost
identical (same code path) and lowers later-level cost [measured: E3, tu93 10.4→4.8, vc33 6.1→2.6
actions/human]. Where A2 fails (non-rigid effects), or the goal lies outside the template class, the agent
degrades to memoised exploration, which we report rather than hide.

## 5. Experiments
Protocol: 25 public games, 2000 actions per game, fixed seeds, toolkit-exact scorer, paired per game. Public
numbers are development; the hidden set is evaluation. [measured: `paper/results_table.md`, regenerated by
`arc3/assemble_results.py` from `experiments/*/results.json`]

| agent | score (0–100) | levels | games ≥1 level | games ≥2 levels | median L1 actions/human | levels ≤ human | wall s |
|---|---|---|---|---|---|---|---|
| random | 0.192 | 3/183 | 3 | 0 | 10.3× | 1 | 34 |
| explorer | 0.038 | 5/183 | 5 | 0 | 6.4× | 0 | 113 |
| explorer_human_prior | 0.013 | 5/183 | 4 | 1 | 14.7× | 0 | 552 |
| v4_contact_on | 0.284 | 15/183 | 11 | 3 | 8.6× | 1 | 1293 |
| v4_contact_off | 0.204 | 13/183 | 10 | 2 | 21.2× | 0 | 1811 |
| v5_memory_on | 0.277 | 13/183 | 11 | 2 | 10.4× | 1 | 2172 |
| v5_memory_off | 0.227 | 11/183 | 11 | 0 | 10.4× | 1 | 2475 |
| v5_seed1 | 0.283 | 14/183 | 12 | 2 | 9.3× | 1 | 1737 |
| final_v7 | 0.280 | 15/183 | 12 | 2 | 11.0× | 1 | 1372 |


Reading the table: the explorer and the model-based agent share perception; the difference is the learned
model and planning. Contact-driven curiosity raises both coverage and efficiency (11 vs 10 games, 8.6× vs
21.2× median level-1 cost). The memory ablation changes nothing on level 1 by construction and is the only
configuration that reaches a second level, with falling per-level cost. Per-game prediction accuracy is in
fig. 3. Replicate variance is small because the agent is near-deterministic: three seeds of the final
configuration score 0.280, 0.276 and 0.278 (13–15 levels, 11–12 games with a first level) and differ
on 4 of 25 games [measured: E6], so we treat differences under 2 games or 0.02 points as noise. Hidden-set score [pending submission].

## 6. Failure analysis
[Per-game table from failure_table.py; the six repeat-failure games from the Franzen audit; what the
representation cannot express.]

## 7. Limitations, reproducibility, conclusion
**Limitations.** The generative model only expresses rigid displacements, so click-driven and
recolouring mechanics are learned by memorisation and cannot be planned toward before they are seen;
exploration still pays hundreds of actions on most first levels, which the squared-efficiency metric
turns into near-zero credit; the goal template class is small and, where it does not contain the true
goal, cross-level transfer gives nothing; absolute scores are far below the LLM-harness leaders. Two
pre-registered extensions did not pass their gates and are reported as such: a human-habit exploration
prior (median paired level-1 ratio 1.0) and class-level click-effect prediction, which reached ≥ 0.6
accuracy on 6 of 13 click games yet left coverage unchanged and slowed lp85 from 15 to 774 actions:
click effects are learnable but the goals in those games are click sequences outside our template class.
**Reproducibility.** CPU only, no training set, no per-game code. `uv sync && uv run arc3 --agent
model_based --max-actions 2000` reproduces every public-25 number from `experiments/`; each run row in
`EXPERIMENT_LOG.csv` carries its commit; the submitted notebook embeds `my_agent.py` whose sha256 and
commit are in `submission/kaggle/BUILD.json`. Seeds change outcomes on 2 of 25 games.
**Conclusion.** Learning what actions do, planning in that model, and keeping it across levels is
enough to turn a blind explorer into an agent that clears first levels on 12 of 25 public games and
plays later levels several times more efficiently than its own first level, with no language model.
The measured failures, hidden-counter state, non-rigid effects, and goals outside the template class,
name exactly what the next representation has to express.

*Disclosure.* The code, experiments and this text were produced by the author working with an AI
coding assistant; every reported number was generated by the released code on the public games and
is traceable to a file in the repository.
