# Learning what actions do: object-level effect models with cross-level memory for ARC-AGI-3


## Abstract
ARC-AGI-3 agents on Kaggle either run a large language model in a code REPL or explore blindly.
We ask whether a small, training-free agent can instead *learn what its actions do* while playing,
plan in that learned model, and carry what it learned across the levels of a game. The agent segments
each 64×64 frame into objects, learns per-action object displacements with blocking rules from frame
diffs, plans by breadth-first search in the learned model toward unexplored interactions, and, after the
first level transition, infers a goal predicate from a fixed template class and plans toward it on later
levels. On the 25 public games it clears 15 levels versus 5 for a novelty-seeking explorer and
3 for a random agent, one of them under the human action count and one within
1.25× of it. Where the goal is inferred, level 2 costs 0.4× level 1. We release the agent, an offline harness that reproduces the competition's scoring
formula, and two reusable diagnostics: a non-determinism test for state representations and a
hidden-counter detector.

## 1. Problem and question
ARC-AGI-3 is interactive: the agent sees a 64×64 frame, chooses among up to seven actions, and must discover rules, controls and goal from scratch across levels
of increasing difficulty. The score is
efficiency: a completed level earns 100·(human actions / agent actions)², capped at 115, and a game's score
weights level k by k, so later levels dominate. The organisers' failure taxonomy for frontier
models names false world models and "solved the level, didn't learn the game"; the strongest public-set
paper concludes that "goal inference is the hard part". An agent must learn three things from interaction
alone: what the *state* is, what each *action does*, and what counts as *done*. We ask how far one that
learns all three online, with no language model and no training set, gets on the hidden Kaggle set.

## 2. Prior work and gap
Kaggle entries fall into three families: LLM-in-REPL harnesses (Tufa Labs' Duck, Franzen's Milestone-2)
where a 27–75B model writes Python against the frames on a 96 GB GPU; a "will the frame change" CNN
(Stochastic Goose) that re-initialises at every level; and white-box search that imports the public games'
source and cannot run on hidden games. Research papers (Twin, Tycho, PRO-LONG) build executable world
models with frontier APIs and report 88–100% on the 25 public games only, which AERA shows null strategies
partly solve. No public agent learns a non-LLM model of action effects, plans in it, keeps it across
levels and is evaluated on the hidden set.

## 3. Method
3.1 State: objects (colour, bbox, mask), terrain colours (≥20% coverage) kept for collision, not identity;
HUD rows masked by two measured detectors. 3.2 Effect model: rigid groups, modal displacement, swept-path
blocking/passable colour statistics, per-key reliability window. 3.3 Planner: BFS in the model; targets =
untried (state, action), rarely-contacted object classes, or goal predicates. 3.4 Goal inference: templates
Gone/Count/Touch/Overlap/Appeared, positive = model-predicted post-action state at the transition, negative
= level start, intersection across transitions. 3.5 Memory: model and goals persist across levels.

## 4. Why it should work (theory)
**Assumption A1 (determinism).** ARC-AGI-3 games are deterministic given a correct state representation.
Measured: with memoised transitions, next-state prediction is ≥ 0.95 accurate on 14 of 25 games and
exactly 1.0 on 9; the rest expose hidden counters (progress bars
on a hidden modulo) or animation-length state, where A1 fails and our two detectors recover it.
**Assumption A2 (factored, rigid dynamics).** Simple actions displace a rigid group of objects by a fixed
vector unless blocked by a colour in the swept path. Measured: the generative model is ≥ 0.9 accurate on
sp80 and su15 and ≥ 0.6 on dc22, g50t, m0r0, ls20; it fails on click-driven games whose
effects are not displacements (ft09, r11l, s5i5, tn36, vc33 rely on memoisation).
**Bound.** Under A1 a model-free explorer pays again for every revisited transition; a planner pays at
most once per unknown (state, action) pair, so real actions ≤ |S_reach|·|A|. The explorer reaches a
median 983 abstract states in 2000 actions with |A| = 5, so a blind sweep cannot cover a
level in budget; the planner resolves only the pairs it chooses, and contact-driven targets cut
that further.
**Transfer.** Levels share dynamics and goal by design and the score weights level k by k, so learning
pays on later levels: memory ON vs OFF leaves level-1 cost identical (same code path) and lowers
later-level cost. In the 340 released human replays, a
template-class predicate consistent across levels exists on 6 of 25 games and in 27.9% of multi-level sessions, which bounds the
transfer term. Where A2 fails or the goal lies outside the template class, the agent degrades to
memoised exploration, which we report.

## 5. Experiments
Protocol: 25 public games, 2000 actions per game, fixed seeds, toolkit-exact scorer, paired per game;
public numbers are development, the hidden set is evaluation.

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


The explorer and the model-based agent share perception, so the table isolates the learned model and
planning. Contact-driven curiosity raises coverage and efficiency (11 vs 10 games; median level-1 cost
8.6× vs 21.2× human). Memory changes nothing on level 1 by construction and is the only setting that
reaches a second level, at falling per-level cost; fig. 3 gives per-game prediction accuracy. Three seeds
of the final configuration score 0.280, 0.276 and 0.278 and differ on 4 of 25 games;
differences under 2 games or 0.02 points are noise. On the hidden public half (55 unseen games) the
memory-on agent scores **0.15**; the leading LLM harness scores 62.96 and most entries 0. The memory-off twin follows for the paired
hidden-set test.

## 6. Failure analysis
Per game: no game dies in a loop (resets
≤ 4.3% of actions) or cycles through a few states (≥ 16% distinct frames), so exploration itself is not
what stalls. Five games are *model-blind* (generative accuracy < 0.3: bp35,
cd82, ka59, sk48, tn36), where effects are memorised but never predicted; the other 20 are *no-progress*:
the planner keeps finding untried transitions (median 1,973 of 2,000 steps planned) without crossing a
level boundary, which is a goal problem, not a search problem. A reached first level costs 0.9× (lp85) to
58× (m0r0) the human count. A published 100-trajectory audit of the 75B-parameter
Franzen harness lists sk48 as never clearing level 1 and bp35 and lf52 as stopping after one level; our
agent matches all three.

## 7. Limitations, reproducibility, conclusion
**Limitations.** The generative model only expresses rigid displacements, so click and recolour
mechanics are memorised, not planned toward; exploration still pays hundreds of actions on most first
levels, which the squared-efficiency metric turns into near-zero credit; where the small goal template
class misses the true goal, cross-level transfer gives nothing; absolute scores are far below the
LLM-harness leaders. Two
pre-registered extensions failed their gates: a human-habit exploration prior (paired level-1 ratio 1.0)
and class-level click-effect prediction (≥ 0.6 accuracy on 6 of 13 click games, coverage unchanged, lp85
slowed from 15 to 774 actions): click effects are learnable, but those games' goals are click sequences
outside our template class.
**Reproducibility.** CPU only, no training set, no per-game code. One command (`uv run arc3 --agent
model_based --max-actions 2000`) reproduces every public-25 number; each `EXPERIMENT_LOG.csv` row carries
its commit; the submitted notebook embeds `my_agent.py` with its sha256 and commit in `BUILD.json`.
**Conclusion.** Learning what actions do, planning in that model and keeping it across levels turns a
blind explorer into an agent that clears first levels on 12 of 25 public games and plays later levels
several times more efficiently, with no language model. The measured failures (hidden counters, non-rigid
effects, goals outside the template class) name what the next representation must express.

*Disclosure.* The code, experiments and this text were produced by the author working with an AI
coding assistant; every reported number was generated by the released code on the public games and
is traceable to a file in the repository.
