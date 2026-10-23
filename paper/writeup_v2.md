# What should an agent carry from one level to the next?

## Abstract

ARC-AGI-3 games keep their mechanics across levels and change their layout, so an agent that has solved
level k holds two different things it could reuse on level k+1: the **plan** it used, and the **mechanics**
it learned. The two leading families of entries each bet on one and neither tests the bet. LLM-in-REPL
harnesses carry the plan, replaying the previous level's winning sequence into the model's context; our
symbolic explorer carries the mechanics. We measure which transfers, three ways: in the 340 released human
replay sessions with no agent involved, in a controlled ablation of our own agent, and in paired hidden-set
draws of the harness with its level memory on and off. The human record is unambiguous and matches neither
bet. A winning sequence re-solves the next level in **0 of 1,237** testable pairs across **0 of 25** games,
positive control 95.6 percent, yet successive winning sequences are more alike than chance on 19 of 25
games: the plan carries real structure and is not executable. A mechanics model predicts the next level's
movement at 0.740 against a 0.301 null. On the hidden set we also show the metric prices first-level
efficiency and is nearly blind to later-level coverage, which is why memory moves it by 0.000 and a different
ablation moves it sevenfold.

## 1. The question, and why the metric makes it the paying one

A completed level earns 100·(human actions / agent actions)², capped at 115, weighted by level k. Squaring
pays for efficiency, not coverage, so clearing many levels slowly earns almost nothing. Level 1 must be
solved from nothing, so its cost is bounded below by discovery; later levels are where an agent can be cheap,
and only if something it already holds still applies. The paying question is not whether to carry state
across levels but **what** to carry.

## 2. Prior work: both families choose, neither measures

Kaggle entries fall into three families: LLM-in-REPL harnesses (Tufa Labs' Duck, Franzen's Milestone-2)
running a 27B to 75B model that writes Python against the frames; a "will the frame change" CNN (Stochastic
Goose) restarting each level; and white-box search, which reads public-game source the hidden games do not
expose. The published papers (Twin, Tycho, PRO-LONG) report 88 to 100 percent on the public games only, a set
AERA shows null strategies partly solve. The harnesses inject each solved level's winning sequence into the
model's context at level-up; our explorer carries a learned effect model instead. Both are plausible and
neither family publishes a controlled comparison against its own no-memory twin. That is the gap this paper
fills.

## 3. The two memories, stated precisely

**Plan memory** (`inference/utils/level_memory.py`, the harness fork): on completing level k it records
W_k, the actions since the last reset, resets excluded and click coordinates verbatim, and shows those
sequences to the model at level k+1.

**Mechanics memory** (`arc3/agents/model_based.py`, ours): per-action modal displacements of rigid object
groups, the colours that block a swept path, per-key reliability windows, and any goal predicate inferred
from the template class Gone / Count / Touch / Overlap / Appeared. Layout is discarded, the object vocabulary
is not.

These are not variants of one mechanism. A plan is a trajectory in action space and transfers only if the
next solution is nearly the same sequence; a mechanics model transfers if the next level obeys the same
rules, whatever its layout.

## 4. E21: what transfers in human play, with no agent involved

Settling this on human play puts it beyond any agent's weaknesses. Population: all 340 released human
sessions on the public 25, replayed in the same local game builds, pre-registered in `HYPOTHESES.md` on
2026-10-13 before any code ran.

- **F** fidelity gate: every recorded action is replayed and every frame compared; a session is usable to
  its first mismatch.
- **M1** plan transfer: from a snapshot at the moment level k completed, execute W_k and ask whether level
  k+1 completes within |W_k| actions. Controls: C1 W_k shuffled ×5, C2 the level's own W_{k+1} as a positive
  control, C3 uniform random actions of the same length ×5.
- **M2** plan similarity: 1 − Levenshtein(W_k, W_{k+1}) / max length, against shuffled W_k.
- **M3** mechanics transfer: each action's modal displacement learned on level k, scored on level k+1 steps
  where something moved; ceiling is that model scored on level k, the null the exact mean over all
  non-identity label permutations.

Predictions, filed before the run, and what all 340 sessions gave. 309 sessions replay frame-exactly; of
1,314 consecutive completed level pairs, 1,237 (94.1 percent) are reproducible and so testable.

| filed prediction | bar | measured | |
|---|---|---|---|
| **P21a** W_k completes level k+1 | ≤10% of pairs, 0 on ≥20 of 25 games | **0 of 1,237 pairs, 0 of 25 games** | met |
| P21a positive control C2 (own W_{k+1}) | ≥90% | **95.6%** | met |
| **P21b** M3 mechanics transfer, movement games | ≥0.8 | **0.740** (ceiling 0.906, 843 pairs) | failed |
| **P21b** M3 against its permuted null | ≥3x | **2.5x** (null 0.301) | failed |
| **P21c** M2 plan similarity beats shuffle | on <13 games | **on 19 of 25 games** | failed |

One of three met. The failures matter more than the pass. Replaying a plan completes nothing, anywhere, with
a working positive control, yet successive winning sequences are measurably more alike than chance on most
games. The plan is not empty and it is not executable. That is sharper than either prediction anticipated,
and it is exactly the position an LLM harness is placed in: `solved_levels()` hands the model a sequence that
genuinely resembles what will work next and cannot be run. The mechanics model transfers at 0.740 against a
0.301 null, short of our bar and far from nothing. Shuffled plans and random actions complete 0 percent.

**Caveats carried with these numbers.** The positive control fails on tn36 for all 51 of its pairs (and 3
lf52, 1 sc25), so tn36's M1 is uninformative rather than negative and is excluded wherever M1 is quoted; s5i5
has 43 pairs and no reproducible pair; six games record no movement steps, so M3 is silent on them. And 188
of 6,185 random-control runs (3.0 percent, all lf52) exceeded a 60-second budget and are reported as
unevaluable, not as failures: on that game a random sequence drives the environment into states whose
per-step cost grows without bound (0.7 s at step 47, 40.0 s at step 77) while the same session's winning
sequences replay in milliseconds. Counting them as failures would push the control toward zero, the direction
that flatters P21a, so they are excluded and counted. The budget was filed in `HYPOTHESES.md` before any
affected session was scored.

**A data defect only the full population exposed.** The released replays write the action id in two forms,
numeric ("6") and named ("ACTION6", "RESET"). The named form is 14,625 of 171,859 events, 8.5 percent, across
23 of the 340 sessions, and our first parser accepted digits only, so those actions silently became id −1. A
12-session pilot contained none of them. Had that sample been trusted, every rate above would have been
computed over a quietly truncated population.

## 5. The same question asked of two agents

**5a. Mechanics memory, controlled (ours, public 25).** Memory on scores 0.277 and clears 13 levels, memory
off 0.227 and 11. Level-1 cost is identical between the arms, as the mechanism predicts since nothing is
carried into the first level, and a second level is reached only with memory on.

**5b. What bounds that transfer.** A template-class predicate consistent across levels exists on 6 of 25
games and in 27.9 percent of multi-level human sessions; seven further predicate families lift this to 34
percent against a 10 percent null. The object vocabulary bounds the transfer term, not the template list.

**5c. Plan memory, controlled (LLM harness, hidden set).** Each level-memory variant was paired with its
own no-memory twin on the same base model, two draws each, on the 55 hidden games:

| variant | plan memory | draw 1 | draw 2 |
|---|---|---|---|
| v2-level-memory | on | 29.54 | 0.00 |
| v1-franzen-faithful | off | 29.93 | 0.00 |

The healthy draws differ by **0.39 points**, and the two-draw means by 0.20. The pre-registered rule claims an
effect only above 11 points, so **no effect is claimed**: giving the model the previous level's winning
sequence did not change what it scored. That is the same answer E21 gives from human play, reached on the
hidden set by a different agent family.

The two zeros are the stronger finding. Each is the **same kernel version** that scored ~29.7 the day
before, resubmitted and rerun by the competition, returning COMPLETE with 0.00. Run-to-run variation on the
hidden rerun therefore spans the entire range of the score, which makes the 11-point rule generous rather
than strict and makes any single-draw hidden comparison in this competition unsafe. We report it rather than
discarding it: our conclusion does not depend on which way the zeros are treated, since the gap is 0.39 with
them excluded and 0.20 with them included.

A Swift-based pair was started first and abandoned: v6 (Swift + level memory) drew 4.92 against Intel's
29.93, and every Swift smoke run cleared 2 to 4 levels where Intel cleared 5 to 9, so the comparison moved to
the Intel base before its control was drawn.

**5d. The claim rule, pre-registered.** Identical copies of the reference notebook score mean 25.77 with
standard deviation 3.93. A memory effect is therefore claimed only if a pair differs by more than 11 points.
Below that the draws are reported as the harness's performance with memory and not as evidence that memory
helped.

## 6. The floor, and what the hidden ranking is worth

Five submissions on the same 55 unseen games:

| submission | agent | public 25 | hidden 55 |
|---|---|---|---|
| 57095368 | explorer, build whose prediction path crashed into a cyclic fallback | n/a | 0.15 |
| 57170721 | random agent, 60 actions per game | n/a | 0.12 |
| 57123503 | explorer, cross-level memory **on** | 0.277 | 0.08 |
| 57199354 | explorer, cross-level memory **off** | 0.227 | 0.08 |
| 57248168 | explorer, contact curiosity **off** | 0.204 | **0.01** |

The obvious reading of the first four is that the hidden metric is insensitive to what the agent does: a
random agent outscores the working one, and a memory switch worth +0.050 on the public set is worth 0.000
here. The fifth submission shows that reading is too broad. Turning off contact curiosity, worth +0.080 on
the public set, moves the hidden score sevenfold, from 0.08 to 0.01.

So the metric is not blind. It is selective, and the decomposition says exactly how. A completed level pays
100 x (human actions / agent actions)^2, so efficiency is paid for and coverage is not: a first level at or
under the human action count is worth 1.8 to 4.8 game points, the same level at ten times human cost under
0.05. The two ablations differ in precisely that. Contact curiosity buys **first-level efficiency**, cutting
median level-1 cost from 21.2x to 8.6x human, and the metric pays for it. Memory buys **later-level
coverage**, reaching a second level on two more games, and the metric is nearly blind to it.

That is a narrower claim than "the hidden ranking is uninformative", and better supported. The ranking is
uninformative *about this paper's treatment*, because cross-level memory is the one thing the metric does not
price. Three public games supply 90 percent of our public 0.280 (lp85 2.78 points, tn36 2.40, vc33 1.14), the
hidden 0.08 is about 4.4 game points over 55 games, roughly one such level, and 1,087 of 4,233 teams sit in
the same (0.05, 0.23] band. The memory evidence in this paper therefore rests on the controlled experiments
and the human replays, and the hidden draws are reported as evidence about what the metric prices.

## 7. Limitations

The effect model expresses rigid displacements only, so click and recolour mechanics are memorised, not
planned toward, and where the goal lies outside the template class mechanics memory gives nothing. The LLM
arm has two draws per variant against a 3.93-point copy-to-copy spread, which is why its claim rule is a
threshold rather than a test. E21 measures human play, so it bounds what is *available* to transfer, not what
an agent manages to use.

*Disclosure.* The code, experiments and this text were produced by the author working with an AI coding
assistant; every reported number was generated by the released code and is traceable to a file in the
repository.
