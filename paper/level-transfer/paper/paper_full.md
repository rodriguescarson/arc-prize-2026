---
title: "What should an agent carry from one level to the next?"
subtitle: "ARC Prize 2026 Paper Track entry"
author: "Carson Rodrigues"
date: "2 November 2026"
---

## Abstract

ARC-AGI-3 games reuse and extend their mechanics across levels and change their layout, so an agent that has
solved level $k$ holds two things it could reuse on level $k{+}1$: the **plan** it used, or the **mechanics** it
learned. Entries carry a plan, a rule or both from level to level, and none we found measures which helps on
hidden games. We measure which transfers, three ways: in the 340 released human replay sessions, in a
controlled ablation of our own agent, and in paired hidden-set draws of a large language model (LLM) harness
with its `solved_levels()` helper on and off. A winning sequence re-solves the next level in 0 of 1,186
testable pairs (23 games with a working positive control, 144 distinct level transitions, so a 95 percent upper
bound of 2.5 percent; control 99.7 percent), and successive winning sequences are only slightly more alike than
a shuffle (0.446 against 0.431). A mechanics model predicts the next level's movement at 0.740 (pair mean over
10 movement games) against a 0.301 null, short of our 0.8 bar. The harness comparison is too coarse to confirm
or refute anything: two hidden draws per arm average 24.65 with the helper and 27.89 without, a 3.2-point gap
inside the 11 points the design resolves. One draw per arm is consistent with a hidden metric that
rewards first-level efficiency and barely registers later-level coverage.

## 1. The question

The benchmark scores agents by RHAE, relative human action efficiency. In the technical report [1], a completed
level earns $100 \times \min(1.15, (\text{human actions} / \text{agent actions})^2)$, weighted by level number.
Squaring the ratio rewards efficiency far more than coverage, so clearing many levels slowly earns almost
nothing. Level 1 is bounded below by discovery; later levels are where an agent can be cheap, and only if
something it holds still applies. The question is what to carry across levels.

## 2. Prior work

Entries fall into three families. Harnesses let a language model work in a Python read-eval-print loop (REPL)
against the game frames: the Duck [2] and Franzen's Milestone-2 solution [3]. Franzen's level-up prompt tells
the model to plan afresh and reuse the previous level's mechanics; rellik13's fork [4] pins each cleared
level's rule and last 30 winning actions. StochasticGoose [5] is a convolutional neural network (CNN) that
predicts whether an action changes the frame and resets at each level. Some notebooks [6] search the public
games' source, which the hidden games do not expose. Papers report RHAE of 93 to 100 on the 25 public games
with their best frontier-model configurations (Tycho [7], Twin [8], PRO-LONG [9], Schema [10], VISTA [11],
Memento 3 [12], Kepler [13]), a set that the study introducing AERA, the Adaptive Epistemic Reasoning Agent [14],
finds reachable by non-intelligent strategies. The memory ablations we found are on public games: PRO-LONG gains
18.0 points on average across frontier models over a baseline agent without its log, NVIDIA's Object-Oriented
Agents (NOOA) [15] 11.8 over plain markdown files, and Tracing [16] finds that scripts an agent writes for one
task are almost never called on a later one (33 of 630 references cross a task boundary; a task there is a level). We found no paired
hidden-set comparison of what to carry across levels.

This paper is a measurement study whose predictions were filed in `HYPOTHESES.md`. The track has placed empirical
studies before: the 2024 second-place paper examined test-time training [17].

## 3. The two memories

**Plan memory** (the `solved_levels()` helper in `inference/utils/level_memory.py`, our harness fork): on
completing level $k$ it records $W_k$, the actions since the last reset (resets excluded, click coordinates
verbatim), and shows the last 60 of them to the model at level $k{+}1$.

**Mechanics memory** (`arc3/agents/model_based.py`, our explorer): per-action modal displacements of rigid
object groups, the colours that block a swept path, per-key reliability windows, and any goal predicate inferred
from the template class Gone / Count / Touch / Overlap / Appeared. Layout is discarded and the object
vocabulary is kept.

A plan is a trajectory through one layout, so it transfers only if the next solution is nearly the same sequence; a mechanics model transfers if the next level obeys the same rules, whatever its layout. Tracing [16] fits this: most of its scripts embed the state of the current level.

## 4. Human replays (E21)

E21 is the twenty-first experiment in our hypotheses log. Its population is all 340 sessions in the
public release mirror [18] (the release post counts 342), on the public 25 games, replayed in the same local
builds. The tests and bars are fixed in `HYPOTHESES.md` (pushed 15 October 03:05 UTC, after a 12-session smoke
that already showed plan transfer (M1, defined below) at 0 of 65, before any full result). The full run
completed on 16 October.

- **F** fidelity gate: every recorded action is replayed and every frame compared; a session is testable up to
  its first mismatch.
- **M1** plan transfer: from a snapshot at the moment level $k$ completed, execute $W_k$ and ask whether level
  $k{+}1$ completes within $|W_k|$ actions (a budget at least as long as the next human solution in only 469 of the 1,237 testable pairs, 452 of the 1,186 without tn36; replay completes none of them). Controls: C1 $W_k$ shuffled $\times 5$, C2 the level's own $W_{k+1}$ as a positive
  control, C3 uniform random actions of the same length $\times 5$.
- **M2** plan similarity: $1 - \text{Levenshtein}(W_k, W_{k+1}) / \text{max length}$, computed over action ids,
  against shuffled $W_k$.
- **M3** mechanics transfer: each action's modal displacement learned on level $k$, scored on level $k{+}1$ steps
  where something moved; the ceiling is that model scored on level $k$, the null the exact mean over all
  non-identity label permutations. A movement game is one of the 12 games that are not click-driven.

309 sessions replay frame-exactly; of 1,314 completed level pairs, 1,237 (94.1 percent) are testable. Games are
named by their four-character environment id [1]. The positive control fails on every pair of one game (tn36), so
M1 is quoted on the other 1,186 pairs (23 games); the caveats give the filed figures with tn36 included. Table 1
gives the filed predictions and Figure 1 plots them.

| filed prediction | bar | measured | verdict |
|:-------------------------|:-------------------|:------------------------------------------|:-------|
| **P21a** $W_k$ completes level $k{+}1$ | at most 10 percent, 0 on at least 20 games | 0 of 1,186 pairs, 0 of 23 games (0 of 144 distinct transitions) | met |
| P21a control C2 (own $W_{k+1}$) | at least 90 percent | 99.7 percent | met |
| **P21b** M3 transfer, movement games | at least 0.8 | 0.740 (ceiling 0.906; pair mean over 431 pairs in 10 movement games; per game 0.00 to 0.99) | failed |
| **P21b** M3 against its permuted null | at least 3 times | 2.5 times (null 0.301 over 421 pairs; 0.757 on those 421) | failed |
| **P21c** M2 similarity beats shuffle | fewer than 13 games | 17 of 20 games (19 of 25 under the filed rule) | failed |

: E21 results against the filed predictions.

![E21 results, drawn from `experiments/E21_level_transfer.json` by `paper/make_fig_e21.py`. Panel A: the share of testable pairs in which level $k{+}1$ is completed, over 1,186 pairs from 23 games (tn36 excluded because its positive control fails). Replaying $W_k$, a shuffled $W_k$ and random actions complete none; the level's own $W_{k+1}$ completes 99.7 percent. Panel B: the action-effect accuracy of a mechanics model learned on level $k$ and scored on level $k{+}1$ (431 pairs in 10 movement games), against its permuted null (over the 421 of those pairs that have one; the mean on those 421 is 0.757) and its in-sample ceiling, with the 0.8 bar filed in advance, which it did not clear.](figures/fig6_e21_transfer.png){width=100%}

One of three predictions was met, and the failures matter more. Replaying a plan completes nothing, with a
working positive control. The 1,186 pairs rest on only 144 distinct (game, level) transitions, about eight
sessions each, so the interval is quoted at both units: the Clopper-Pearson 95 percent upper bound on the replay
success rate is 0.31 percent treating pairs as independent and 2.5 percent at transition level (0 of 144). Both
are far below the 10 percent bar. Successive winning sequences are only slightly more alike than a shuffle
(0.446 against 0.431, pooled over all 1,314 pairs) and are above it on 17 of the 20 games where a shuffle can
differ; on five games (lp85, r11l, s5i5, tn36, vc33) a shuffle leaves the score unchanged in every pair, and on
three (ls20, m0r0, tu93) similarity sits below it. The plan has structure but cannot be replayed. That is what
our harness fork's `solved_levels()` hands its model. Shuffled plans and random actions also complete 0 percent. Replay fails alike in the 12 click-driven and the 11 movement-driven games of the 23.

**Caveats.** The positive control fails on all 51 tn36 pairs (and 3 lf52, 1 sc25), so M1 is quoted without tn36
(with it: 0 of 1,237, control 95.6 percent, the filed run); s5i5 has no testable pair; six other games
record no movement, so M3 is silent there. 188 of 6,185 random-control runs (3.0 percent, all lf52) exceeded a
60-second budget, filed before any affected session was scored: random sequences drive lf52 into states whose
step cost grows without bound. They are reported as unevaluable, because counting them as failures would
flatter P21a. M3 has data on 10 of the 12 movement games; three of them (tu93, wa30, re86) hold 48 percent
of its 431 pairs, which rest on 56 distinct transitions. Per game, M3 is 0.99 on dc22, 0.97 on g50t, 0.90 on re86, 0.89 on ls20 and tu93, and 0.75 on sp80 and wa30, but 0.36 on tr87, 0.30 on m0r0 and 0.00 on cd82 (one transition, 10 pairs); we have not diagnosed the three low games.

## 5. Two agents

**5a. Mechanics memory on and off (our explorer, public 25 development set, one seed).** Memory on scores 0.277
and clears 13 levels, off 0.227 and 11, on our local scorer, from one seed pair with no interval. Level-1 cost is
identical, as it must be since nothing is carried into a first level, and a second level is reached only with
memory on.

**5b. `solved_levels()` on and off (LLM harness, hidden 55).** The model is
Intel/Qwen3.8-Flash-Next-W4A16-AutoRound (the Intel base) in Franzen's Milestone-2 harness. A draw is one scored
rerun of a notebook on the 55 hidden games. The helper variant (v2) was paired with its twin without the helper
(v1), two draws each, taken from 19 to 25 October (Table 2); a pair on the Swift base (UkisAI Swift1.5 post-train)
was dropped after its first draw scored 4.92. v2 differs from v1 in two ways: it adds an optional REPL call,
`solved_levels()`, that the level-up message mentions once, and it rewords the budget-bar line of the prompt
(`ARC3_BAR_GUIDANCE=budget`). Both arms keep Franzen's level-transfer guidance, which already tells the model to
reuse the previous level's mechanics. We do not know how often v2's model called the helper: the call counts in
the logs of its two scored draws (57477157 and 57575322) are not tallied. The comparison therefore tests the
helper together with the reworded line.

| variant | helper | draw 1 | draw 2 | draw 3 | mean | kernel versions |
|:--------------------|:-----|-----:|-----:|-----:|-----:|:------|
| v2-level-memory | on | 29.54 | 19.75 | | 24.65 | 2, 4 |
| v1-franzen-faithful | off | 29.93 | 25.85 | | 27.89 | 2, 5 |
| v1f (v1 code, faster model load) | off | 29.44 | 21.86 | 28.19 | 26.50 | 1 |

: Hidden-set draws (55 games each) by variant.

Leaderboard scores of first-time copies of the reference notebook (hundreds of teams, one draw each; the thread
gives no sample size and does not say whether every copy was unedited or whether failed runs were dropped) have
mean 25.77, standard deviation (SD) 3.93 [19], and an independent study reports SD 3.99 over ten evaluations of
one frozen harness on twenty public games [20]; two single draws therefore differ with SD about 5.5. The
rule filed before any pair ran claims an effect only above 11 points, twice that, and predicted none. The means
of the v2 and v1 arms differ by 3.2 (0.8 SD, where 3.93 is the SD of a difference between two-draw means), the
helper arm lower. No effect is claimed; two draws per arm resolve only 11 points (the 95 percent interval for
off minus on runs from $-4.5$ to $+10.9$), so the data leave an effect of either sign open. Pooling the three
v1f draws with v1 gives five draws without the helper: mean 27.05, SD 3.30, 2.4 points above the helper arm. As of 2 November, all thirteen valid Intel draws, across five variants (v1, v1f, v2, v8i, which is v1 plus a slot-priority rule called D' in our logs, and v10, which is v1f plus start-up hardening and three harness fixes: a guarded RESET, a notice after cut-off replies, and attempt-loss stops), average 26.35 (SD 3.18), indistinguishable from an unmodified copy of the notebook we forked. The draws not in Table 2 are 24.95 and 26.47 (v8i, kernel versions 1 and 3) and 24.51, 29.78, 27.60 and 24.72 (v10, version 1).

Two earlier draws, one per arm (22 and 23 October), returned 0.00 and are excluded from every count and mean.
We attribute them to the platform ending a rerun after 15 minutes without a game move, together with slower
model loading, so they say nothing about either arm. Both arms were redrawn after a keepalive fix: a game
reset sent every five minutes until the model server is ready.

## 6. The floor and the hidden ranking

Contact curiosity is a term in the explorer's planner that prefers states where the mover touches a rarely
contacted object class. Table 3 sets the hidden score of each explorer submission beside the public-set score of
its nearest measured twin.

| submission | agent | public 25 (nearest measured twin) | hidden 55 |
|:--------|:-------------------------------|:---------------|:-----|
| 57095368 | explorer, crashed to cyclic fallback | n/a | 0.15 |
| 57170721 | random, 60 actions/game | n/a | 0.12 |
| 57123503 | explorer, memory on | 0.280 | 0.08 |
| 57199354 | explorer, memory off | 0.227 (v5 twin) | 0.08 |
| 57248168 | explorer, contact curiosity off | 0.204 (v4 twin) | 0.01 |

: Explorer submissions, hidden score against the nearest measured public-set score.

The first four rows suggest the hidden metric ignores the agent: a random agent outscores the working one, and a
memory switch worth $+0.050$ publicly (the v5 pair, 0.277 against 0.227) is worth 0.000 here. The fifth row
differs by about one level: with contact curiosity off, the explorer scores 0.01 against 0.08 on the hidden 55 in
one draw each (0.07 $\times$ 55 = 3.9 points). Contact curiosity is worth $+0.080$ publicly on the v4 pair, all of
it from one game, lp85; without lp85 the contact-on agent scores lower than the contact-off agent on the public 25.

Contact curiosity is consistent with a gain in first-level efficiency: it cuts median level-1 cost from 21.2 to
8.6 times the human cost (medians over 10 and 11 games; on the nine games the two sets share, 21.95 against 8.59
times; `experiments/level1_cost_check.out`), and the hidden metric squares that ratio. Memory is consistent with
later-level coverage, a second level on two more games, which the metric nearly ignores. Here the hidden ranking
says little about this paper's treatment. Three public games supply 90 percent of our public 0.280, the hidden
0.08 sums to 4.4 points over 55 games (0.08 $\times$ 55), roughly one such level, and on 13 October 1,087 of 4,233
teams sat in the (0.05, 0.23] band that contains our 0.08.

## 7. Limitations and scope

Scope: one benchmark (ARC-AGI-3), human replays on the public 25 games only, one LLM base model (a second pair
was dropped); nothing here tests transfer outside ARC-AGI-3. The replay test (M1) needs only recorded multi-level sessions, a deterministic replayable build and a level-completion signal, so it could be repeated on other game suites whose levels reuse mechanics; we ran it on one.

The effect model expresses only rigid displacements, so the explorer memorises click and recolour mechanics and
cannot plan toward them; outside the template class, mechanics memory gives nothing. The LLM arm has two draws
per variant against a 3.93-point copy spread, its second draws ran with slower model loading, and the two draws of
each arm ran on different kernel versions. E21 measures human play, so it bounds what is available to transfer and
says nothing about what an agent uses. M1 tests a verbatim replay within the budget $|W_k|$. A model that adapts a
plan it is shown can do things M1 does not test, and 330 of the 1,237 sequences $W_k$ are longer than the 60
actions the harness shows.

Other filed predictions mostly failed. The explorer's level-1 efficiency (P1) and next-state accuracy (P4)
predictions were not met. The click-effect (E12), ordered-goal (E13) and first goal-proposer (E19) extensions
were negative. The proposer follow-ups gained about 0.015 on the public 25 and replicated (E20 and E20b with one
proposer, E20c with another). E20c with the first proposer lost a game, and E20d failed its gate. All are in
`HYPOTHESES.md`.

## 8. Conclusion

Replaying a winning plan completes no next level in human play, and a helper that returns plans moved our
harness's hidden score by less than its draw noise. Mechanics predict next-level movement at 0.740, short of the bar we filed, though predicting a move is not solving a level. For anyone aiming at 85 percent, later levels must be cheap, and verbatim replay did not supply them; a replay that adapts the plan is untested. Next entrants should log that a feature is used before crediting it, and report several draws
against the copy spread.

## Linked submission

57477157 (`v2-level-memory`, kernel version 2): Franzen's Milestone-2 harness plus `solved_levels()` and a
reworded budget-bar line; 29.54 hidden, the better of two draws and one SD above our 13-draw Intel mean, so expect a private score nearer 26.

## Code and data

Code, data and every experiment log are released with the paper.

## Disclosure

Claude Code (Anthropic) wrote most of the code, ran the experiments and drafted this text under the author's
direction. The author set the hypotheses and the filed predictions, reviewed every change and approved each claim;
every reported number comes from the released code or the Kaggle submission list and traces to a file in the
repository.

## References

1. ARC Prize Foundation. ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence. arXiv:2603.24621, <https://arxiv.org/abs/2603.24621>, 2026.
2. Tufa Labs. The Duck harness, winning solution to ARC-AGI-3 Milestone 1. <https://github.com/Tufalabs/duck-harness>, 2026.
3. D. Franzen. ARC-AGI-3 Milestone 2 solution. <https://github.com/da-fr/arc-agi-3-solution>, 2026 (Kaggle notebook <https://www.kaggle.com/code/dfranzen/arc-agi-3-milestone-2-solution>).
4. rellik13 (Kaggle user sirikilohit). arc-agi-3-duck-18-1gc-submit. Kaggle notebook, <https://www.kaggle.com/code/sirikilohit/arc-agi-3-duck-18-1gc-submit>, 2026.
5. D. Smit. StochasticGoose. <https://github.com/DriesSmit/ARC3-solution>, 2025.
6. nihilisticneuralnet. [0.46] ARC-AGI-3: Persistent Memory BFS ARC Solver. Kaggle notebook, <https://www.kaggle.com/code/nihilisticneuralnet/0-46-arc-agi-3-persistent-memory-bfs-arc-solver>, 2026.
7. J. Lehmann, A. Aioanei, S. Vahdati. Tycho: Active Abstraction with Programmatic World Models for ARC-AGI-3. arXiv:2607.28287, <https://arxiv.org/abs/2607.28287>, 2026.
8. A. Skoutnev et al. Twin: Playing an Unknown Game with a Test-Time Digital Twin. arXiv:2608.14490, <https://arxiv.org/abs/2608.14490>, 2026.
9. A. Fox et al. PRO-LONG: Programmatic Memory Enables Long-Horizon Reasoning. arXiv:2607.20064, <https://arxiv.org/abs/2607.20064>, 2026.
10. G. Zeng et al. Schema: Discovering Unknown Environments via Agentic Program Induction. arXiv:2609.39140, <https://arxiv.org/abs/2609.39140>, 2026.
11. Q. Han et al. VISTA: A Visual Harness for Reasoning in an Interactive World. arXiv:2610.02200, <https://arxiv.org/abs/2610.02200>, 2026.
12. H. Zhao et al. Memento 3: Model-Based Recursive Self-Improvement through Reflective Rulebooks. arXiv:2610.11794, <https://arxiv.org/abs/2610.11794>, 2026.
13. W. Wu. Kepler: Auditable World Models for ARC-AGI-3. arXiv:2610.00834, <https://arxiv.org/abs/2610.00834>, 2026.
14. K. H. Liew. Explore Before You Solve: The Speed-Depth Trade-off in Epistemic Agents for ARC-AGI-3. arXiv:2605.25931, <https://arxiv.org/abs/2605.25931>, 2026.
15. P. Furgale et al. NVIDIA-labs OO Agents: Native Python Object-Oriented Agents. arXiv:2607.20709, <https://arxiv.org/abs/2607.20709>, 2026.
16. C. Wu, J. Passenger, Y. Song. Tracing the Thoughts of a Coding Agent Playing ARC-AGI-3: Lessons for Continual Learning. arXiv:2610.11450, <https://arxiv.org/abs/2610.11450>, 2026.
17. E. Akyürek et al. The Surprising Effectiveness of Test-Time Training for Few-Shot Learning (the ARC Prize 2024 results list it as "... for Abstract Reasoning"). arXiv:2411.07279, <https://arxiv.org/abs/2411.07279>, 2024.
18. G. Kamradt (ARC Prize). Measuring Human Performance on ARC-AGI-3. <https://arcprize.org/blog/arc-agi-3-human-dataset>, 14 April 2026 (Hugging Face mirror by magic-sword: <https://huggingface.co/datasets/magic-sword/arc_agi_3_public_demo_human_testing>).
19. S. Pham. Incredible notebook performance variation (Daniel Franzen's copies data analysis). Kaggle discussion 745062, <https://www.kaggle.com/discussions/general/745062>, October 2026.
20. J. Lehmann, S. Vahdati. Can LLMs Improve Their Own Harness? A Controlled Study on ARC-AGI-3. arXiv:2610.30499, <https://arxiv.org/abs/2610.30499>, 2026.
