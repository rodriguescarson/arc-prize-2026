# Learning what actions do: object-level effect models with cross-level memory for ARC-AGI-3


## Abstract
Kaggle's ARC-AGI-3 agents either run a language model in a code REPL or explore blindly. We ask whether a
small, training-free agent can instead *learn what its actions do* while playing, plan in that model, and
carry what it learned across a game's levels. The agent segments each frame into objects, learns per-action displacements and blocking rules from frame
diffs, plans by breadth-first search in that model toward unexplored interactions, and after the first level
transition infers a goal predicate from a template class and plans toward it on later levels. On the 25 public games it clears 15 levels versus 5 for a novelty-seeking explorer and
3 for a random agent, one of them under the human action count and one within
1.25× of it. Where the goal is inferred, level 2 costs 0.4× level 1. On the hidden set it
scores 0.08, at the leaderboard floor: the metric counts near-human first levels, and ours came from three
public games. We release the agent, an offline harness with the competition's scoring formula, a non-determinism test
for state representations and a hidden-counter detector.

## 1. Problem and question
ARC-AGI-3 is interactive: the agent sees a 64×64 frame, chooses among up to seven actions, and must discover
rules, controls and goal from scratch across levels. A completed level earns 100·(human actions / agent
actions)², capped at 115, and level k weighs k, so later levels dominate. The strongest public-set paper concludes that "goal inference is the hard part". An agent must learn what the *state* is, what each *action does*, and what counts as *done*; we ask how far
one that learns all three online, with no language model and no training set, gets on the hidden set.

## 2. Prior work and gap
Kaggle entries come in three families. LLM-in-REPL harnesses (Tufa Labs' Duck, Franzen's Milestone-2) run a
27–75B model writing Python against the frames on a 96 GB GPU. A "will the frame change" CNN (Stochastic
Goose) restarts at every level. White-box search reads the public games' source, which hidden games don't expose. Papers (Twin, Tycho, PRO-LONG) build executable world models with frontier APIs and report 88–100% on the
public games only, which AERA shows null strategies partly solve. No public agent learns a non-LLM model of action effects, plans in it, keeps it across
levels and is evaluated on the hidden set.

## 3. Method
3.1 State: objects (colour, bbox, mask), terrain colours (≥20% coverage) used for collision only;
HUD rows masked by two measured detectors. 3.2 Effect model: rigid groups, modal displacement, swept-path
blocking/passable colour statistics, per-key reliability window. 3.3 Planner: BFS in the model; targets =
untried (state, action), rarely-contacted object classes, or goal predicates. 3.4 Goal inference: templates
Gone/Count/Touch/Overlap/Appeared, positive = model-predicted post-action state at the transition, negative
= level start, intersection across transitions. 3.5 Memory: model and goals persist across levels. 3.6 Goal proposer (development only): a decision model reads a ~350-word summary of the level (object
classes, the mover and its learned displacements) and picks one currently-false goal from the template menu
or "explore". With no plan to it, the agent walks toward a touch target along learned displacements. A goal
is dropped after 50 actions held without a transition or 80 steps without reaching it.

## 4. Why it should work (theory)
**A1 (determinism).** Games are deterministic given a correct state representation. Measured: memoised
next-state prediction is ≥ 0.95 accurate on 14 of 25 games and exactly 1.0 on 9; the rest expose hidden counters or animation-length state, where A1 fails and our two detectors
recover it.
**A2 (rigid dynamics).** Simple actions displace a rigid group by a fixed vector unless a colour in the
swept path blocks it. Measured: the generative model is ≥ 0.9 accurate on sp80 and su15 and ≥ 0.6 on dc22,
g50t, m0r0, ls20; click-driven games (ft09, r11l, s5i5, tn36, vc33) rely on memoisation.
**Bound.** Under A1 a planner pays at most once per unknown (state, action) pair, a model-free explorer
again on every revisit; with a median 983 abstract states in 2000 actions and |A| = 5, a
blind sweep cannot cover a level in budget.
**Transfer.** Levels share dynamics and goal by design, so learning pays on later levels: memory ON vs OFF
leaves level-1 cost identical and lowers later-level cost. In the 340 released human replays, a
template-class predicate consistent across levels exists on 6 of 25 games and in 27.9% of multi-level
sessions; seven further predicate families lift this only to 34% against a 10% null. The object
vocabulary bounds the transfer term; a longer template list does not move it. Otherwise the agent degrades to memoised exploration.

## 5. Experiments
Protocol: 25 public games, 2000 actions per game, fixed seeds, toolkit-exact scorer, paired per game;
public numbers are development; hidden is evaluation.

| agent | score (0–100) | levels | games ≥1 level | games ≥2 levels | median L1 actions/human | levels ≤ human | wall s |
|---|---|---|---|---|---|---|---|
| random | 0.192 | 3/183 | 3 | 0 | 10.3× | 1 | 34 |
| explorer | 0.038 | 5/183 | 5 | 0 | 6.4× | 0 | 113 |
| v4_contact_on | 0.284 | 15/183 | 11 | 3 | 8.6× | 1 | 1293 |
| v4_contact_off | 0.204 | 13/183 | 10 | 2 | 21.2× | 0 | 1811 |
| v5_memory_on | 0.277 | 13/183 | 11 | 2 | 10.4× | 1 | 2172 |
| v5_memory_off | 0.227 | 11/183 | 11 | 0 | 10.4× | 1 | 2475 |
| final_v7 | 0.280 | 15/183 | 12 | 2 | 11.0× | 1 | 1372 |
| greedy walk, no proposer | 0.280 | 15/183 | 12 | 2 | 11.0× | 1 | 926 |
| + Jev 1.13 proposer (not in the submission) | **0.296** | **16/183** | **13** | 2 | 7.1× | 1 | 2463 |
| + Nemotron-3 Super proposer, open-weight | 0.295 | 16/183 | 13 | 2 | 7.1× | 1 | 1011 |


Shared perception isolates the learned model and planning.
Contact curiosity raises coverage and efficiency (11 vs 10 games; median level-1 cost 8.6× vs 21.2× human).
Memory alone reaches a second level, at falling per-level cost (per-game prediction accuracy: fig. 3). Three seeds score 0.280, 0.276 and 0.278 and differ on 4 of 25 games;
differences under 2 games or 0.02 points are noise. The proposer is the one addition that passes its pre-registered gate: +0.015 to +0.016 over the greedy-only
control on three seeds, no game lost, g50t's first level in 240 actions instead of 1,159. The open-weight Nemotron-3 Super repeats it on three seeds when a
goal is a target only until first reached. Other chat models lose games. **On the hidden public half (55 unseen games) the agent scores 0.08**,
inside the (0.05, 0.23] band that holds 26% of 4,233 teams; an earlier submission whose bundle crashed in the
prediction path and played cyclic actions scored 0.15. The score explains why: a first
level at or under the human action count is worth 1.8–4.8 game points, one at 10× human cost under 0.05, so the
total counts near-human first levels. Three games (lp85, tn36, vc33) supply 90% of the public 0.280; the hidden
0.08 is about one such level in 55 games. Coverage of 15 levels is nearly invisible to this metric.

## 6. Failure analysis
Per game: no game dies in a loop (resets
≤ 4.3% of actions) or cycles through a few states (≥ 16% distinct frames): exploration itself is not what stalls. Five games are *model-blind* (generative accuracy < 0.3: bp35, cd82, ka59, sk48, tn36); the other 20 are
*no-progress*: the planner keeps finding untried transitions (median 1,973 of 2,000 steps planned) without
crossing a level boundary: a goal problem, not a search problem. A reached first level costs 0.9× (lp85) to
58× (m0r0) the human count. The repeat failures of the 75B Franzen harness in a published audit (sk48, bp35, lf52) stall here too.

## 7. Limitations, reproducibility, conclusion
**Limitations.** The generative model only expresses rigid displacements, so click and recolour mechanics
are memorised and never planned toward. Most first levels still cost hundreds of actions, which the
squared-efficiency metric turns into near-zero credit, so the hidden score sits at the leaderboard floor. Where
the goal lies outside the template class, transfer gives nothing. The proposer needs a decision model at
inference time; the offline rerun has none, so the submitted agent runs without it. Two pre-registered extensions failed: a human-habit exploration prior (paired level-1 ratio 1.0) and
click-effect prediction (accurate on 6 of 13 click games, coverage unchanged).
**Reproducibility.** CPU only, no training set, no per-game code. One command (`uv run arc3 --agent
model_based --max-actions 2000`) reproduces every public-25 number and the public notebook replays them inside
Kaggle's runtime; every
`EXPERIMENT_LOG.csv` row carries its commit.
**Conclusion.** Learning what actions do, planning in it and keeping it across levels turns a blind explorer
into an agent that clears first levels on 12 of 25 public games, with no language model, and a decision model
proposing targets adds a replicated step. None of it moves the hidden score. The metric pays for near-human first levels, and coverage at ten times the
human cost earns almost nothing, so first-level efficiency is what the next agent has to buy.

*Disclosure.* The code, experiments and this text were produced by the author working with an AI
coding assistant; every reported number was generated by the released code on the public games and
is traceable to a file in the repository.
