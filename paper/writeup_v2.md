# What should an agent carry from one level to the next?

*Draft v2, restructured per `paper/OUTLINE_v2.md`. Sections marked PENDING hold a placeholder until the
file named beside them exists. Nothing is written into this draft before its number has been produced.*

## Abstract

ARC-AGI-3 games keep their mechanics across levels and change their layout. An agent that has just solved
level k therefore holds two different things it could reuse on level k+1: the **plan** it used, and the
**mechanics** it learned. The two leading families of entries each bet on one of these and neither tests the
bet. The LLM-in-REPL harnesses carry the plan, replaying the previous level's winning action sequence into
the model's context. Our symbolic explorer carries the mechanics, keeping per-action displacements, blocking
colours and an inferred goal predicate. We measure which one transfers, three ways. In the 340 released human
replay sessions, with no agent involved. In a controlled ablation of our own agent on the 25 public games.
And in paired hidden-set draws of the LLM harness with its level memory switched on and off. We also report a
result that constrains all three: on the 55 hidden games our agent scores 0.08 with memory on and 0.08 with
it off, while a random 60-action agent scores 0.12 and a defective build of our own agent scores 0.15. At
this score level the hidden metric does not separate these agents, so we take the memory evidence from the
controlled experiments and report the hidden draws as evidence about the metric.

## 1. The question, and why the metric makes it the paying one

A completed level earns 100·(human actions / agent actions)², capped at 115, and level k carries weight k.
Squaring the ratio means efficiency, not coverage, is what is paid for: a first level solved at or under the
human action count is worth 1.8 to 4.8 game points, and the same level solved at ten times human cost is
worth under 0.05. Clearing many levels slowly earns almost nothing.

That turns cross-level transfer into the central question rather than a refinement. Level 1 of a game has to
be solved from nothing, so its cost is bounded below by discovery. Every later level is where an agent can be
cheap, and it can only be cheap if something it already holds still applies. So the paying question is not
whether to carry state across levels. It is **what** to carry.

## 2. Prior work: both families choose, neither measures

Kaggle entries fall into three families. LLM-in-REPL harnesses (Tufa Labs' Duck, Franzen's Milestone-2) run a
27B to 75B model writing Python against the frames. A "will the frame change" CNN (Stochastic Goose) restarts
at every level. White-box search reads the public games' source, which the hidden games do not expose. The
published papers (Twin, Tycho, PRO-LONG) report 88 to 100 percent on the public games only, a set AERA shows
null strategies partly solve.

The LLM harnesses carry level memory in a function that returns, for each solved level, the action sequence
that completed it, and inject it into the model's context at level-up. Our explorer carries a learned effect
model instead. Both choices are plausible and neither family publishes a controlled comparison against its own
no-memory twin. That is the gap this paper fills.

## 3. The two memories, stated precisely

**Plan memory** (`inference/utils/level_memory.py` in the harness fork). On completing level k, the harness
records W_k, the actions from the last reset that preceded the completion, resets excluded, click coordinates
verbatim. At level k+1 those sequences are shown to the model.

**Mechanics memory** (`arc3/agents/model_based.py`, ours). The agent keeps per-action modal displacements of
rigid object groups, the colours that block a swept path, per-key reliability windows, and any goal predicate
it has inferred from the template class Gone / Count / Touch / Overlap / Appeared. Layout is discarded; the
object vocabulary is not.

The two are not variants of one mechanism. Plan memory is a trajectory in action space and transfers only if
the next level's solution is nearly the same sequence. Mechanics memory is a model of the environment and
transfers if the next level obeys the same rules, whatever its layout.

## 4. E21: what transfers in human play, with no agent involved

If a winning sequence does not re-solve the next level in human play, while a mechanics model does predict
that level's moves, then the choice between the two memories is settled on data no agent's weaknesses can
explain away.

Population: all 340 released human sessions on the public 25, replayed in the same local game builds.
Pre-registered in `HYPOTHESES.md` at 2026-10-13 19:28, before any code ran.

- **F**, fidelity gate: each session's recorded actions are replayed and every frame compared with the
  recorded one. A session is usable up to its first mismatch.
- **M1**, plan transfer: from a snapshot taken the moment the human completed level k, execute W_k and ask
  whether level k+1 completes within |W_k| actions. Controls: C1 W_k shuffled, five times; C2 the level's own
  W_{k+1} as a positive control; C3 uniform random actions of the same length, five times.
- **M2**, plan similarity on the recorded data: 1 − Levenshtein(W_k, W_{k+1}) / max length, against shuffled
  W_k.
- **M3**, mechanics transfer: each action's modal displacement learned on level k, scored on level k+1 steps
  where something moved. Ceiling is the same model scored on level k itself. The null is the exact mean over
  all non-identity permutations of the action labels.

Predictions, filed before the run: **P21a** W_k completes at most 10 percent of pairs and zero pairs on at
least 20 of 25 games, while C2 completes at least 90 percent. **P21b** on movement games M3 is at least 0.8
and at least three times its null. **P21c** M2 beats shuffle on fewer than 13 games.

**Full-population result: PENDING** (`experiments/human_replays/E21_level_transfer.json`). A 12-session smoke
sample reproduced 65 of 65 pairs frame-exactly, with C2 at 100 percent, M1, C1 and C3 all at zero, and M3
transfer 0.87 against a 0.30 null. Those are 12 sessions, reported here only to show the measurement
runs. The filed claim is the 340-session figure, whichever way it falls.

**A data defect the full population exposed.** The released replays write the action id in two forms, numeric
("6") and named ("ACTION6", "RESET"). The named form is 14,625 of 171,859 events, 8.5 percent, across 23 of
the 340 sessions. Our first parser accepted digits only, so those actions silently became id −1. The 12-session
smoke contained none of them, and the defect surfaced only when the full set ran. An unknown id now ends that
session's usable prefix explicitly. Had the sample been trusted,
every rate in this section would have been computed over a quietly truncated population.

## 5. The same question asked of two agents

**5a. Mechanics memory, controlled (ours, public 25).** Memory on scores 0.277 and clears 13 levels; memory
off scores 0.227 and clears 11. Level-1 cost is identical between the arms, which is what the mechanism
predicts, since nothing is carried into the first level. A second level is reached only with memory on.

**5b. What bounds that transfer.** A template-class predicate consistent across levels exists on 6 of 25 games
and in 27.9 percent of multi-level human sessions. Seven further predicate families lift this to 34 percent
against a 10 percent null. The object vocabulary bounds the transfer term; a longer template list does not
move it.

**5c. Plan memory, controlled (LLM harness, hidden set). PENDING.** Each level-memory variant is paired with
its own no-memory twin on the shared daily submission slot: v6-swift-level-memory against v3-swift, then
v2-level-memory against v1-franzen-faithful, two draws each from 2026-10-17.

**5d. The claim rule, pre-registered.** Identical copies of the reference notebook score mean 25.77 with
standard deviation 3.93. A memory effect is therefore claimed only if a pair differs by more than 11 points.
Below that the draws are reported as the harness's performance with memory and not as evidence that memory
helped.

## 6. The floor, and what the hidden ranking is worth

Four submissions on the same 55 unseen games: our explorer with memory on, 0.08; the same agent with memory
off, 0.08; a random agent taking 60 actions per game, 0.12; and an earlier build of our own agent whose
prediction path crashed, leaving it playing a cyclic fallback, 0.15. On the public 25 the memory switch is
worth +0.050. On the hidden 55 it is worth 0.000, and a random agent outscores the working one.

The decomposition explains it rather than excusing it. Three public games supply 90 percent of our public
0.280: lp85 at 2.78 points, tn36 at 2.40, vc33 at 1.14. The hidden 0.08 is about 4.4 game points over 55
games, roughly one such level. 1,087 of 4,233 teams, 25.7 percent, sit in the same (0.05, 0.23] band. At this
level the hidden ranking does not measure what these agents differ in. That is why the memory claims here
rest on the controlled experiments and the human replays.

## 7. Limitations

The effect model expresses rigid displacements only, so click and recolour mechanics are memorised rather than
planned toward. Where the goal lies outside the template class, mechanics memory gives nothing. The LLM arm
has two draws per variant against a 3.93-point copy-to-copy spread, which is why the claim rule is a
threshold rather than a test. E21 measures human play, so it bounds what is available to transfer, not what a
particular agent manages to use.

*Disclosure.* The code, experiments and this text were produced by the author working with an AI coding
assistant; every reported number was generated by the released code and is traceable to a file in the
repository.
