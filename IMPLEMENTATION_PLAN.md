# IMPLEMENTATION_PLAN — architecture, dependencies, milestones (2026-10-12)

## Architecture (`src/arc_prize_2026/`)
```
data.py / score.py / submission.py / runner.py / diagnostics.py   ARC-AGI-2 path (done; fallback track)
grids.py, solvers/{trivial,dsl_search}.py                           ARC-AGI-2 floor baselines (done)
registry.py                                                         EXPERIMENT_LOG.csv writer (done)
arc3_score.py                                                       toolkit-exact ARC-AGI-3 scorer (done, tested)
arc3/runner.py, arc3/cli.py                                         offline harness over environment_files (done)
arc3/agents/base.py, random_agent.py, explorer.py                   B0, B1 (done)
arc3/perception.py        frame -> objects (components, bbox, colour, mask hash), HUD/border crop, abstract state key
arc3/effects.py           effect model: (action_key, context) -> object-level diff distribution; conflict splitting
arc3/planner.py           BFS/A* in the learned model; info-gain targets; goal targets; plan execution + divergence check
arc3/goals.py             predicate template class; consistency filter at level transitions
arc3/agents/model_based.py  the H1 agent: perception -> effects -> planner/goals; flags memory=on/off, goals=on/off
arc3/atlas.py             E0 exploration atlas from run logs
arc3/kaggle/              build_notebook.py (splices the agent into the starter kit), kernel-metadata.json
```
Agents stay standard-library + numpy only, so the same file runs offline here and inside the
no-internet Kaggle kernel (T4×2 or CPU; RTX 6000 not needed).

## Dependencies
Python 3.12, numpy, arc-agi 0.9.9, arcengine 0.9.3 (uv-managed, `uv.lock` committed). Kaggle CLI 2.2.4
(from `~/Projects/gemma-swe-agent/.venv`) for pushes. Optional: torch for the Stochastic Goose
baseline rerun (B2) — not required by our agent.

## Milestones
| Date (IST) | Milestone | Gate |
|---|---|---|
| Oct 13 | perception + abstract state key; E0 atlas table | distinct-object-config counts for 25 games |
| Oct 15 | effect model + E1 accuracy logging | P4 measured |
| Oct 17 | planner with info-gain targets; E2 run | P1/P2 measured vs B1 |
| Oct 19 | goal predicates + cross-level memory; E3/E4 | P3 measured |
| **Oct 20** | first Kaggle submission (E5) via starter kit | non-zero hidden score; plumbing verified |
| Oct 22 | **H1 go/kill decision** | P1 & P2 |
| Oct 24 | replicates (E6), failure tables, figures 1–3 | noise floor known |
| Oct 27 | paper draft 1 (≤1,500 words) from measured numbers; code cleanup, README, tests | every number traces to `experiments/` |
| Oct 30 | code freeze; two final submissions (E7) chosen | |
| Nov 2 | ARC-AGI-3 submission deadline (23:59 UTC) | |
| Nov 4 | paper draft final + cover image + public notebook link | LLM-council refutation pass |
| **Nov 7** | submit Paper Track writeup (one day before the earlier of the two deadlines) | |

## Reproducibility
`uv sync && uv run arc3 --agent model_based --max-actions 2000 --seed 0` reproduces every public-25
number; `experiments/<run>/results.json` + `EXPERIMENT_LOG.csv` + git commit per row. The Kaggle
notebook is generated from the same agent file and its sha256 is recorded in `submission/`.
