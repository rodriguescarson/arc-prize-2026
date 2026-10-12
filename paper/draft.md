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
[Why ARC-AGI-3 differs from ARC-AGI-2; scoring = efficiency relative to human actions, level-index
weighted (toolkit formula); the organisers' failure taxonomy; "goal inference is the hard part".
Question: how much of the gap is representation (what is the state?), dynamics (what do actions do?),
and goal (what counts as done?), and can each be learned from interaction alone, without a language model?]

## 2. Prior work and gap
[LLM-in-REPL harnesses (Duck, Franzen); learned action-effect CNN (Stochastic Goose) that resets per level;
white-box search that imports game source (dead on hidden games); executable world models with frontier
APIs (Twin, Tycho, PRO-LONG) on the public set only; AERA on public-set saturation. Gap: a learned,
non-LLM model used for planning, with memory across levels, evaluated on the hidden set.]

## 3. Method
3.1 State: objects (colour, bbox, mask), terrain colours (≥20% coverage) kept for collision but not identity,
HUD rows masked by two measured detectors. 3.2 Effect model: rigid groups, modal displacement, swept-path
blocking/passable colour statistics, per-key reliability window. 3.3 Planner: BFS in the model; targets =
untried (state, action), rarely-contacted object classes, or goal predicates. 3.4 Goal inference: templates
Gone/Count/Touch/Overlap/Appeared, positive = model-predicted post-action state at the transition, negative
= level start, intersection across transitions. 3.5 Memory: model and goals persist across levels.

## 4. Why it should work (theory)
Deterministic factored dynamics: each real action resolves one unknown (state, action) pair; planning in
the model is free. Object identity by bbox collapses position-only differences into one mover state space.
Level-index weighting means later levels carry most of the score, so cross-level transfer, not level-1
speed, is where efficiency pays. [State the assumptions and where they fail: non-rigid effects, hidden
counters, goals outside the template class.]

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
