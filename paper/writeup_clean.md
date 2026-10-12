# Learning what actions do: object-level effect models with cross-level memory for ARC-AGI-3


## Abstract
Kaggle's ARC-AGI-3 agents either run a language model in a code REPL or explore blindly. We ask whether a
small, training-free agent can instead *learn what its actions do* while playing, plan in that model, and
carry what it learned across a game's levels. The agent segments each frame into objects, learns per-action displacements and blocking rules from frame
diffs, plans by breadth-first search in that model toward unexplored interactions, and after the first level
transition infers a goal predicate from a template class and plans toward it on later levels. On the 25 public games it clears 15 levels versus 5 for a novelty-seeking explorer and
3 for a random agent, one of them under the human action count and one within
1.25× of it. Where the goal is inferred, level 2 costs 0.4× level 1. We release the agent, an offline harness with the competition's scoring formula, a non-determinism test
for state representations and a hidden-counter detector.

## 1. Problem and question
ARC-AGI-3 is interactive: the agent sees a 64×64 frame, chooses among up to seven actions, and must discover
rules, controls and goal from scratch across levels. A completed level earns 100·(human actions / agent
actions)², capped at 115, and level k weighs k, so later levels dominate. The organisers' failure taxonomy names false world models and "solved the level, didn't learn the game";
the strongest public-set paper concludes that "goal inference is the hard part". An agent must learn what the *state* is, what each *action does*, and what counts as *done*; we ask how far
one that learns all three online, with no language model and no training set, gets on the hidden set.

## 2. Prior work and gap
Kaggle entries come in three families: LLM-in-REPL harnesses (Tufa Labs' Duck, Franzen's Milestone-2), a
27–75B model writing Python against the frames on a 96 GB GPU; a "will the frame change" CNN (Stochastic
Goose) re-initialised at every level; and white-box search over the public games' source, impossible on hidden
games. Papers (Twin, Tycho, PRO-LONG) build executable world models with frontier APIs and report 88–100% on the 25
public games only, which AERA shows null strategies partly solve. No public agent learns a non-LLM model of action effects, plans in it, keeps it across
levels and is evaluated on the hidden set.

## 3. Method
3.1 State: objects (colour, bbox, mask), terrain colours (≥20% coverage) kept for collision, not identity;
HUD rows masked by two measured detectors. 3.2 Effect model: rigid groups, modal displacement, swept-path
blocking/passable colour statistics, per-key reliability window. 3.3 Planner: BFS in the model; targets =
untried (state, action), rarely-contacted object classes, or goal predicates. 3.4 Goal inference: templates
Gone/Count/Touch/Overlap/Appeared, positive = model-predicted post-action state at the transition, negative
= level start, intersection across transitions. 3.5 Memory: model and goals persist across levels. 3.6 Goal proposer (development only): a decision model
reads a ~350-word summary of the level (object classes with colour, size, count, positions; the mover and its
learned displacements) and picks one currently-false goal from the template menu or "explore"; with no plan to
it, the agent walks toward a touch target along learned displacements, dropping a goal after 50 actions held
without a transition or 80 steps without reaching it.

## 4. Why it should work (theory)
**A1 (determinism).** Games are deterministic given a correct state representation. Measured: memoised
next-state prediction is ≥ 0.95 accurate on 14 of 25 games and exactly 1.0 on 9; the rest expose hidden counters or animation-length state, where A1 fails and our two detectors
recover it.
**A2 (rigid dynamics).** Simple actions displace a rigid group by a fixed vector unless a colour in the
swept path blocks it. Measured: the generative model is ≥ 0.9 accurate on sp80 and su15 and ≥ 0.6 on dc22,
g50t, m0r0, ls20; click-driven games (ft09, r11l, s5i5, tn36, vc33) rely on memoisation.
**Bound.** Under A1 a model-free explorer pays again for every revisited transition; a planner pays at most
once per unknown (state, action) pair. The explorer reaches a median 983 abstract states in 2000 actions with
|A| = 5, so a blind sweep cannot cover a level in budget; the planner resolves only the pairs
it chooses.
**Transfer.** Levels share dynamics and goal by design, so learning pays on later levels: memory ON vs OFF
leaves level-1 cost identical and lowers later-level cost. In the 340 released human replays, a
template-class predicate consistent across levels exists on 6 of 25 games and in 27.9% of multi-level
sessions; seven further predicate families lift this only to 34% against a 10%
null, so the bound on the transfer term is the object vocabulary, not the template list. Where A2 fails or the goal lies outside the template class, the agent degrades to
memoised exploration, which we report.

## 5. Experiments
Protocol: 25 public games, 2000 actions per game, fixed seeds, toolkit-exact scorer, paired per game;
public numbers are development; hidden is evaluation.

| agent | score (0–100) | levels | games ≥1 level | games ≥2 levels | median L1 actions/human | levels ≤ human | wall s |
|---|---|---|---|---|---|---|---|
| random | 0.192 | 3/183 | 3 | 0 | 10.3× | 1 | 34 |
| explorer | 0.038 | 5/183 | 5 | 0 | 6.4× | 0 | 113 |
| explorer_human_prior | 0.013 | 5/183 | 4 | 1 | 14.7× | 0 | 552 |
| v4_contact_on | 0.284 | 15/183 | 11 | 3 | 8.6× | 1 | 1293 |
| v4_contact_off | 0.204 | 13/183 | 10 | 2 | 21.2× | 0 | 1811 |
| v5_memory_on | 0.277 | 13/183 | 11 | 2 | 10.4× | 1 | 2172 |
| v5_memory_off | 0.227 | 11/183 | 11 | 0 | 10.4× | 1 | 2475 |
| final_v7 | 0.280 | 15/183 | 12 | 2 | 11.0× | 1 | 1372 |
| greedy walk, no proposer | 0.280 | 15/183 | 12 | 2 | 11.0× | 1 | 926 |
| + Jev 1.13 proposer (not in the submission) | **0.296** | **16/183** | **13** | 2 | 7.1× | 1 | 2463 |


Explorer and model-based agent share perception, so the table isolates the learned model and planning.
Contact curiosity raises coverage and efficiency (11 vs 10 games; median level-1 cost 8.6× vs 21.2× human).
Memory alone reaches a second level, at falling per-level cost (per-game prediction accuracy: fig. 3). Three seeds score 0.280, 0.276 and 0.278 and differ on 4 of 25 games;
differences under 2 games or 0.02 points are noise. The proposer is the one addition that passes its
pre-registered gate: +0.015 to +0.016 over the greedy-only control on all three seeds, no game lost, g50t's
first level in 240 actions instead of 1,159 and r11l's first level reached; two chat models in the same role (Phi-4, Nemotron) lose tu93, so the choice of model matters. Our first hidden-set submission scored **0.15**; its bundle later proved to
raise an exception in the movement-prediction path and fall back to cyclic actions, so it measures a crippled
agent. Fixed-bundle submissions follow; the leading LLM harness scores 62.96.

## 6. Failure analysis
Per game: no game dies in a loop (resets
≤ 4.3% of actions) or cycles through a few states (≥ 16% distinct frames): exploration itself is not what stalls. Five games are *model-blind* (generative accuracy < 0.3: bp35, cd82, ka59, sk48, tn36); the other 20 are
*no-progress*: the planner keeps finding untried transitions (median 1,973 of 2,000 steps planned) without
crossing a level boundary: a goal problem, not a search problem. A reached first level costs 0.9× (lp85) to
58× (m0r0) the human count. A published 100-trajectory audit of the 75B-parameter
Franzen harness lists sk48 as never clearing level 1 and bp35 and lf52 as stopping after one level; our
agent matches all three.

## 7. Limitations, reproducibility, conclusion
**Limitations.** The generative model only expresses rigid displacements, so click and recolour
mechanics are memorised, not planned toward; exploration still pays hundreds of actions on most first
levels, which the squared-efficiency metric turns into near-zero credit; where the small goal template
class misses the true goal, cross-level transfer gives nothing; absolute scores are far below the LLM-harness leaders; the proposer needs a decision model at
inference time, which the offline rerun does not have, so the submitted agent runs without it. Two pre-registered extensions failed their gates: a human-habit exploration prior (paired level-1 ratio 1.0)
and class-level click-effect prediction (≥ 0.6 accuracy on 6 of 13 click games, coverage unchanged): click
effects are learnable, but those games' goals are click sequences outside our template class.
**Reproducibility.** CPU only, no training set, no per-game code. One command (`uv run arc3 --agent
model_based --max-actions 2000`) reproduces every public-25 number and the public notebook replays them inside
Kaggle's runtime; every
`EXPERIMENT_LOG.csv` row carries its commit.
**Conclusion.** Learning what actions do, planning in that model and keeping it across levels turns a blind
explorer into an agent that clears first levels on 12 of 25 public games and plays later levels several
times more efficiently, with no language model; a decision model proposing targets adds a measured, replicated
step more. The measured failures name what the next representation must express.

*Disclosure.* The code, experiments and this text were produced by the author working with an AI
coding assistant; every reported number was generated by the released code on the public games and
is traceable to a file in the repository.
