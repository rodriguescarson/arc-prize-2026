# What should an agent carry from one level to the next?

The full paper (PDF) is the main submission; this is its summary.

## Abstract

ARC-AGI-3 games reuse and extend their mechanics across levels and change their layout, so an agent that has solved
level k can reuse on level k+1 either the **plan** it used or the **mechanics** it learned. Entries carry a plan, a
rule or both from level to level, and none we found measures which helps on hidden games. We measure which
transfers, three ways: in the 340 released human replay sessions, in a controlled ablation of our own agent, and in
paired hidden-set draws of a large language model (LLM) harness with its `solved_levels()` helper on and off. A
winning sequence re-solves the next level in 0 of 1,186 testable pairs (23 games with a working positive control,
144 distinct level transitions; control 99.7 percent), and successive winning sequences are only slightly more alike
than a shuffle (0.446 against 0.431). A mechanics model predicts the next level's movement at 0.740 against a 0.301
null, short of our 0.8 bar. The harness comparison is too coarse to confirm or refute anything: two hidden draws per
arm average 24.65 with the helper and 27.89 without, a 3.2-point gap inside the 11 points the design resolves. One draw per arm is consistent with a hidden metric that rewards first-level efficiency and barely
registers later-level coverage.

## 1. The question

A completed level earns 100 * (human actions / agent actions)^2, capped per level, weighted by level k. Squaring
rewards efficiency far more than coverage, so clearing many levels slowly earns almost nothing.

## 2. Prior work

Harnesses let a language model write Python against the frames: the Duck and Franzen's Milestone-2 solution.
Franzen's level-up prompt tells the model to plan afresh and reuse the previous level's mechanics; rellik13's fork
pins each cleared level's rule and last 30 winning actions. Papers report scores of 93 to 100 on the 25 public games with their
best configurations (Tycho, Twin, PRO-LONG), a set that the study introducing AERA (Adaptive Epistemic Reasoning
Agent) reports reachable by non-intelligent strategies. The memory ablations we found are on public games: PRO-LONG
gains 18.0 points on average over a no-log baseline, NVIDIA's NOOA 11.8 over plain files. We found no paired
hidden-set comparison of what to carry across levels. Citations: see the full paper.

## 3. The two memories

Plan memory (`solved_levels()`, our harness fork) shows the model the last 60 actions of W_k, the sequence that
completed level k, at level k+1. Mechanics memory (our explorer) keeps per-action displacements and goal predicates,
and discards layout. A plan is a trajectory through one layout, so it transfers only if the next solution is nearly the same sequence; mechanics transfer if the next level obeys the same rules. A coding-agent trace study (Tracing) fits this: most scripts embed their level's state, and only 33 of 630 references cross a level.

## 4. Human replays (E21)

E21 uses all 340 sessions in the public release mirror (the post counts 342). The bars are
fixed in HYPOTHESES.md (pushed 15 Oct 03:05 UTC, after a 12-session smoke that already showed M1 (below) at 0 of 65,
before any full result).

- **M1** plan transfer: from a snapshot where level k completed, execute W_k and ask whether level k+1 completes
  within |W_k| actions (only 452 of 1,186 next human solutions fit; none of those completes). Shuffled W_k and random actions also complete 0 percent; the level's own W_{k+1} is the
  positive control.
- **M2** plan similarity: 1 - Levenshtein(W_k, W_{k+1}) / max length, over action ids, against a shuffle.
- **M3** mechanics transfer: displacements learned on level k, scored on level k+1, against a permutation null.

309 sessions replay frame-exactly; 1,237 of 1,314 completed level pairs are testable up to each session's first
mismatch. M1 is quoted on 1,186 of them (23 games), without tn36 (see Caveats).

| filed prediction | bar | measured | |
|---|---|---|---|
| **P21a** W_k completes level k+1 | <=10%, 0 on >=20 games | 0 of 1,186 pairs, 0 of 23 games; control 99.7% | met |
| **P21b** M3 transfer, against null | >=0.8, >=3x | 0.740 (431 pairs, 10 games), 2.5x (null 0.301) | failed |
| **P21c** M2 beats shuffle | <13 games | 17 of 20 games (19 of 25 under the filed rule) | failed |

One of three met. The pairs rest on 144 distinct transitions, so the Clopper-Pearson 95 percent upper bound is 0.31
percent treating pairs as independent and 2.5 percent at transition level (0 of 144), both below the 10 percent bar.
Successive winning sequences are only slightly more alike than a shuffle (0.446 against 0.431): the plan has
structure but cannot be replayed.

**Caveats.** The positive control fails on all 51 tn36 pairs, so M1 is quoted without tn36 (with it: 0 of 1,237,
control 95.6 percent, the filed run); s5i5 has no testable pair.

## 5. Two agents

**5a. Mechanics memory on and off (our explorer, public 25 development set, one seed).** Memory on scores 0.277 and
clears 13 levels, off 0.227 and 11, on our local scorer. A second level is reached only with memory on.

**5b. `solved_levels()` on and off (LLM harness, hidden 55).** The model is
Intel/Qwen3.8-Flash-Next-W4A16-AutoRound; a draw is one scored rerun on the 55 hidden games. The helper variant (v2)
drew 29.54 and 19.75 (kernel versions 2 and 4); its twin without the helper (v1) drew 29.93 and 25.85 (versions 2 and 5). v2 also rewords the budget-bar line of the prompt, and both arms keep Franzen's
level-transfer guidance. How often v2's model called the helper is unknown. Three more no-helper draws (v1f, same
code, faster loading: 29.44, 21.86, 28.19) bring the no-helper mean to 27.05 over five draws, 2.4 above the helper
arm.

First-time copies of the reference notebook (hundreds of teams, one draw each) score mean 25.77, standard deviation
3.93, so two single draws differ with SD about 5.5. The rule filed before any pair ran claims an effect only above
11 points and predicted none. The means differ by 3.2 (0.8 SD), the helper arm lower; two draws per arm resolve only
11 points, so no effect is claimed and the data leave an effect of either sign open. As of 2 November, all thirteen valid Intel draws, across five variants, average 26.35 (SD 3.18), indistinguishable from an unmodified copy of the
notebook we forked.

Two earlier 0.00 draws, one per arm, are excluded; we attribute them to the platform ending a rerun after 15 minutes
without a game move, plus slow model loading.

## 6. The floor and the hidden ranking

Hidden-55 scores (public 25 nearest twin in brackets): crashed explorer 0.15, random agent 0.12, explorer with
memory on 0.08 (0.280) and off 0.08 (0.227, v5 twin), contact curiosity off 0.01 (0.204, v4 twin). The first four
suggest the hidden metric ignores the agent: a random agent outscores the working one, and a memory switch worth
+0.050 publicly (the v5 pair, 0.277 against 0.227) is worth 0.000 here. The fifth is a level lower: contact
curiosity (the planner prefers states that touch rarely contacted objects; +0.080 publicly on the v4 pair, all lp85)
scores 0.01 off against 0.08 on in one draw, about one level. It is consistent with first-level efficiency (median
level-1 cost 21.2x to 8.6x human), and memory with later-level coverage, which the metric nearly ignores.

## 7. Limitations and scope

Scope: one benchmark (ARC-AGI-3), human replays on the public 25 games only, one LLM base model (a second pair was
dropped); nothing here tests transfer outside ARC-AGI-3. E21 measures human play, so it bounds what is available to
transfer and says nothing about what an agent uses.

## 8. Conclusion

Replaying a winning plan completes no next level in human play, and a helper that returns plans moved our harness's
hidden score by less than its draw noise. Mechanics predict next-level movement at 0.740, short of the bar we filed, though predicting a move is not solving a level. For 85 percent, later levels must be cheap; verbatim replay did not supply them, and a replay that adapts the plan is untested. Next entrants should log that a feature is used before crediting it, and report several draws against the copy
spread.

*Linked submission.* 57477157 (`v2-level-memory`, kernel version 2): Franzen's Milestone-2 harness plus
`solved_levels()` and a reworded budget-bar line; 29.54 hidden, the better of two draws, so expect a private score
nearer 26. Code, data and every experiment log are released with the paper.

*Disclosure.* Claude Code (Anthropic) wrote most of the code, ran the experiments and drafted this text under the
author's direction. The author set the hypotheses and the filed predictions, reviewed every change and approved each
claim; every reported number comes from the released code or the Kaggle submission list and traces to a file in the
repository.
