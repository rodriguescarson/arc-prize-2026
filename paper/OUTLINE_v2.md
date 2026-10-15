# Writeup v2 outline — "what should an agent carry from one level to the next?"

Decision of 2026-10-13 19:28 IST (Carson): the paper covers cross-level memory in **two** agents and links
the best level-memory LLM draw. Reason in NEXT_ACTIONS.md (Accuracy = the linked submission's leaderboard
score; 0.08 caps the six-criterion average at 4.33, under the 4.5 bar of the Outstanding Papers pool).

Budget 1,500 words. Every row below names the file the number comes from, or says PENDING. Nothing is
written into the draft before its file exists.

## The question
ARC-AGI-3 games repeat their mechanics across levels and change their layout. So an agent that has solved
level k holds two different things it could reuse on level k+1: **the plan** (the action sequence that
worked) and **the mechanics** (what each action does, what blocks it, what ends a level). Which one
transfers? The two leading agent families each bet on one without testing it:

| agent | what its memory holds | where |
|---|---|---|
| LLM-in-REPL harness (Franzen Milestone-2 fork) | the previous level's winning action sequence, shown to the model at level-up (`solved_levels()`) | `~/Projects/arc-agi-3`, variants v2 and v6 |
| symbolic explorer (ours) | per-action displacements, blocking colours, goal predicate | `~/Projects/arc_prize_2026`, v7 |

## Evidence map

| § | claim | evidence | state |
|---|---|---|---|
| 1 | the question above, and why the metric makes it the paying question | RESEARCH_LOG 10-13 14:13 decomposition | have |
| 2 | prior work: neither family tests its memory choice | LITERATURE_MAP §7 | have |
| 3 | the two memories, stated precisely | `arc3/agents/model_based.py`; sibling `inference/utils/level_memory.py` | have |
| 4a | **E21** human replays, full population (340 sessions): does W_k solve level k+1? do level-k mechanics predict level-k+1 moves? | `experiments/human_replays/E21_level_transfer.*` | RUNNING |
| 4b | fidelity gate: human sessions replay frame-exactly in the local games | same run, F column | smoke 65/65 |
| 5a | explorer, controlled: memory ON 0.277 / 13 levels vs OFF 0.227 / 11; level-1 cost identical, level-2 only with memory | `arc3_E3_*`, EXPERIMENT_LOG | have |
| 5b | goal transfer is bounded by the object vocabulary, not the template list (E11/E18 + nulls) | `experiments/human_replays/coverage_*` | have |
| 5c | LLM harness, plan memory: v2 − v1 and v6 − v3 hidden draws | sibling bot, from 10-17 | PENDING |
| 5d | pre-registered rule: identical copies SD 3.9 → claim an effect only above 11 points | HYPOTHESES 10-13 19:28 | have |
| 6 | the floor: explorer 0.08, random 60-action solver 0.12, defective cyclic bundle 0.15, all on the same hidden half | SUBMISSIONS rows 1–4 | have (0.12 is new, 10-14) |
| 6b | E16 noise draws: mem1 0.08, mem0 PENDING, c0 PENDING | SUBMISSIONS | partial |
| 7 | limitations: n of games with ≥2 levels; one draw per variant; the proposer is development-only | as now | have |

## What changes from v1
- The title and abstract lead with the memory question, not with the effect model.
- §5 becomes two controlled comparisons (mechanics memory in the explorer, plan memory in the LLM harness)
  plus E21 as the agent-free measurement that explains both.
- The hidden-score discussion keeps the metric decomposition but adds the random-solver floor, which is the
  blunt version of the same point: at this score level the public ranking does not separate agents.
- The linked submission changes from 57123503 (explorer, 0.08) to the best level-memory draw. The explorer
  submissions stay in the table as the controlled arm.

## Risk
If no level-memory draw completes before 2026-11-02, the paper links the explorer submission and the
Accuracy cap stands. The draws are the sibling bot's, on the shared account; this workspace does not submit
after 10-16.
