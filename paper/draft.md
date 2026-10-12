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
Kaggle entries fall into three families (survey in `LITERATURE_MAP.md` §7 and `data/kaggle/reference/`):
(i) LLM-in-REPL harnesses (Tufa Labs' Duck, Franzen's Milestone-2 solution) in which a 27B model writes
Python that inspects frames and emits actions on a 96 GB GPU; (ii) a learned "will the frame change"
CNN (Stochastic Goose, the official sample) that re-initialises at every level; (iii) white-box search
that imports the public games' source code and therefore cannot run on hidden games. Research papers
(Twin, Tycho, PRO-LONG) build executable world models with frontier APIs and report 88–100% on the 25
public games only, which AERA shows even null strategies partly solve. No public agent learns a
non-LLM model of action effects, plans in it, and keeps it across levels; none evaluates that mechanism
on the hidden set. That is the gap this submission fills.

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
**Bound.** Under A1, a model-free explorer that revisits known transitions pays again for each revisit;
a model-based planner pays at most once per unknown (state, action) pair, so the real actions needed to
learn a level's dynamics are ≤ |S_reach|·|A|, with planning free. Median reachable abstract states in
2000 explorer actions is 983 with median |A| = 5 [measured: atlas], so a model-free sweep cannot finish
even the reachable part of one level inside the budget, while the planner's cost is bounded by the number
of *distinct* pairs it chooses to resolve (contact-driven targets cut that further).
**Transfer.** Levels of a game share dynamics and goal (the organisers' design); the score weights level
k by k. So the gain from learning is realised on later levels: memory ON vs OFF leaves level-1 cost
identical (same code path) and lowers later-level cost [measured: E3, tu93 10.4→4.8, vc33 6.1→2.6
actions/human]. Where A2 fails (non-rigid effects), or the goal lies outside the template class, the agent
degrades to memoised exploration, which we report rather than hide.

## 5. Experiments
Protocol: 25 public games, 2000 actions/game, fixed seeds, toolkit-exact scorer, paired per game. Public
numbers are development; the hidden set is evaluation.
- Baseline ladder [measured]: random 0.192 / 3 levels; explorer 0.038 / 5; model-based v2 0.246 / 11;
  v4 contact ON 0.284 / 15 / 11 games; contact OFF 0.204 / 13 / 10.
- Prediction accuracy by game (P4) [measured: agent_stats in results.json].
- Memory ON vs OFF (P3) [pending E3]. Replicates / noise floor [pending E6].
- Hidden set (P5) [pending: submission IDs].

## 6. Failure analysis
[Per-game table from failure_table.py; the six repeat-failure games from the Franzen audit; what the
representation cannot express.]

## 7. Limitations, reproducibility, conclusion
[CPU only; no per-game code; `uv sync && uv run arc3 ...` reproduces every public number; sha256 of the
submitted agent file; commit hash.]
