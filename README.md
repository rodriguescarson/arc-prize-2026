# ARC Prize 2026 — ARC-AGI-3 model-based explorer (Paper Track workspace)

A training-free, CPU-only ARC-AGI-3 agent that learns an object-level model of what its actions do while
playing, plans in that model, and carries the model plus an inferred goal across the levels of a game.
Everything in the paper is reproducible from this repository; every number traces to a file under
`experiments/` and a row in `EXPERIMENT_LOG.csv`.

## Reproduce
```bash
uv sync                                                   # Python 3.12, numpy, arc-agi 0.9.9, arcengine 0.9.3
# public ARC-AGI-3 games: accept the Kaggle rules, then
kaggle competitions download -c arc-prize-2026-arc-agi-3 -p data/kaggle/arc-prize-2026-arc-agi-3 && unzip -q data/kaggle/arc-prize-2026-arc-agi-3/*.zip -d data/kaggle/arc-prize-2026-arc-agi-3
uv run arc3 --agent random      --max-actions 2000                    # floor
uv run arc3 --agent explorer    --max-actions 2000                    # novelty-seeking baseline
uv run arc3 --agent model_based --max-actions 2000 --kwargs '{"memory": true, "goals": true, "contact": true}'
uv run arc3 --agent model_based --max-actions 2000 --kwargs '{"memory": false}'   # ablation
# negative-result variants (kept, off by default): '{"click_model": true}' (E12), '{"sequences": true}' (E13); prior_explorer agent (E8)
uv run python -m arc_prize_2026.arc3.failure_table experiments/<run>/results.json
uv run python -m arc_prize_2026.arc3.figures --ladder a=... b=... --atlas experiments/arc3_E0_explorer_a2000_s0_logged/atlas.json
for t in tests/test_*.py; do uv run python $t; done
```
Scores use `arc3_score.py`, a line-by-line mirror of `arc_agi.scorecard` (100·(human/agent)² per level,
115 cap, level-index weights, completion-fraction cap, 0–100). Public-25 numbers are development numbers;
the Kaggle hidden set (110 games) is the only evaluation.

## Layout
| Path | What |
|---|---|
| `MISSION.md` | the full research brief |
| `RESEARCH_INVENTORY.md`, `LITERATURE_MAP.md`, `HYPOTHESES.md`, `EXPERIMENT_PLAN.md`, `IMPLEMENTATION_PLAN.md`, `RUBRIC_SCORECARD.md`, `NEXT_ACTIONS.md` | deliverables; `RESEARCH_LOG.md` is the append-only lab notebook |
| `EXPERIMENT_LOG.csv` | one row per run: hypothesis, commit, config, split, score, runtime, outcome |
| `src/arc_prize_2026/arc3/` | `perception.py` (objects, state key), `effects.py` (online effect model), `planner.py` (BFS in the model), `goals.py` (goal inference), `agents/` (random, explorer, model_based), `runner.py` + `cli.py` (offline harness), `atlas.py`, `volatility.py`, `failure_table.py`, `figures.py`, `human_replays.py`, `kaggle/build_notebook.py` |
| `src/arc_prize_2026/{data,score,submission,runner,solvers}` | ARC-AGI-2 pipeline (fallback track; pass@2 scorer, Kaggle layout validator, DSL-search floor) |
| `submission/kaggle/` | generated single-file agent + notebook + `BUILD.json` (sha256, commit) |
| `paper/` | draft and figures |

## Diagnostics others can reuse
- **State non-determinism test**: run the agent with memoised transitions and read `pred_by_source.memo`
  accuracy per game; anything below 1.0 means the state representation misses hidden state (we found
  hidden-counter progress bars this way).
- **Hidden-counter detector**: `agents/model_based.py::_update_volatility` (rate-based and thin-bar detectors).
- **Exploration atlas**: `arc3/atlas.py` (distinct states, no-op fraction per action, branching).

## Kaggle
`uv run python -m arc_prize_2026.arc3.kaggle.build_notebook --memory 1 --contact 1` writes
`submission/kaggle/submission.ipynb` (installs `arc-agi` from the competition wheelhouse, no internet)
and `kernel-metadata.json`; push with `kaggle kernels push -p submission/kaggle`. The offline bundle is
tested by `tests/test_kaggle_bundle.py`.

## Licence
Code: CC-BY 4.0 on submission per the competition rules (to be confirmed at release). Game environments,
wheels and human replays belong to the ARC Prize Foundation and are not redistributed here (`data/` is gitignored).
