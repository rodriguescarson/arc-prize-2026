# What should an agent carry from one level to the next? ARC-AGI-3, ARC Prize 2026 Paper Track

Paper, code and data for Carson Rodrigues' ARC Prize 2026 Paper Track entry on agent memory in ARC-AGI-3. An agent
that has solved level k of a game can reuse on level k+1 either the plan it used or the mechanics it learned. In the
340 released human replay sessions, a winning plan replayed verbatim completes the next level in 0 of 1,186 testable
pairs (23 games, 144 distinct transitions; positive control 99.7 percent), while a mechanics model learned on level k
predicts level k+1's movement at 0.740 (431 pairs, 10 movement games, short of the 0.8 bar filed in advance) against a
0.301 permuted null. Two hidden-set draws per arm of an LLM harness with and without a helper that returns the
previous level's plan differed by 3.2 points (24.65 against 27.89), inside the 11 points the design resolves, so no
effect is claimed.

By [Carson Rodrigues](https://carsonrodrigues.com) ([Kaggle](https://www.kaggle.com/carsonrodrigues), [ORCID](https://orcid.org/0009-0001-7195-6742)), sole author of the paper, the analysis and the code here. The paper and its public parts are listed at [carsonrodrigues.com/research](https://carsonrodrigues.com/research#paper-22).

- Paper: [`paper/level-transfer/paper/paper_full.pdf`](paper/level-transfer/paper/paper_full.pdf), also filed as a
  writeup in the [ARC Prize 2026 Paper Track](https://www.kaggle.com/competitions/arc-prize-2026-paper-track)
- Every number in the paper, with the scripts that regenerate it: [`paper/level-transfer/`](paper/level-transfer/)
- The LLM harness and the Kaggle notebooks: [rodriguescarson/arc-agi-3](https://github.com/rodriguescarson/arc-agi-3)
- How to cite: [`CITATION.cff`](CITATION.cff). The code is MIT-0; the packed human replays in
  `data/human_replays_packed/` keep the terms of the ARC Prize release (see its `NOTICE`).

## The model-based explorer

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
uv run arc3 --agent model_based --max-actions 4000 --time-budget 900     # E17: levels vs action budget
uv run python -m arc_prize_2026.arc3.swarm_sim --game-budget-s 30600 --game-cpu-s 155 --max-actions 3000   # the rerun's 110-thread concurrency, simulated
uv run python -m arc_prize_2026.arc3.human_replays data/human_replays --family extended --tag e18        # E11/E18 goal-template coverage (+ --null control)
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
| `src/arc_prize_2026/arc3/` | `perception.py` (objects, state key), `effects.py` (online effect model), `planner.py` (BFS in the model), `goals.py` (goal inference), `agents/` (random, explorer, model_based), `runner.py` + `cli.py` (offline harness), `atlas.py`, `volatility.py`, `failure_table.py`, `figures.py`, `human_replays.py`, `swarm_sim.py` (rerun concurrency simulator), `kaggle/build_notebook.py` (competition kernel), `kaggle/build_repro.py` (public reproduction notebook) |
| `src/arc_prize_2026/{data,score,submission,runner,solvers}` | ARC-AGI-2 pipeline (fallback track; pass@2 scorer, Kaggle layout validator, DSL-search floor) |
| `submission/kaggle/` | generated single-file agent + notebook + `BUILD.json` (sha256, commit) |
| `paper/level-transfer/` | the Paper Track entry: main paper (PDF), writeup, figures, filed predictions, E21 result |

## Diagnostics others can reuse
- **State non-determinism test**: run the agent with memoised transitions and read `pred_by_source.memo`
  accuracy per game; anything below 1.0 means the state representation misses hidden state (we found
  hidden-counter progress bars this way).
- **Hidden-counter detector**: `agents/model_based.py::_update_volatility` (rate-based and thin-bar detectors).
- **Exploration atlas**: `arc3/atlas.py` (distinct states, no-op fraction per action, branching).

## Kaggle
`uv run python -m arc_prize_2026.arc3.kaggle.build_notebook --memory 1 --contact 1 --goals 1 --max-actions 3000 --budget-h 8.25 --game-cpu-s 700`
writes `submission/kaggle/submission.ipynb` (installs `arc-agi` from the competition wheelhouse, no internet)
and `kernel-metadata.json`; push with `kaggle kernels push -p submission/kaggle`. The rerun plays all 110
games as concurrent threads under one GIL, so the shim budgets each game by its own thread-CPU time
(`ARC3_GAME_CPU_S`), keeps a global wall budget, caps actions, and trims the framework's frame list in place.
`tests/test_kaggle_bundle.py` calls the bundled agent directly *and* through the shim and asserts its action
sequence is bit-identical to the repo agent (a dropped import alias once crashed every shipped kernel behind
the shim's exception fallback; nothing that only tests through the fallback can see that).
`uv run python -m arc_prize_2026.arc3.kaggle.build_repro` builds the Paper-Track reproduction notebook
(`carsonrodrigues/arc3-paper-reproduce-public25`), which replays the public-25 table inside Kaggle's runtime.

## Author and citation

[Carson Rodrigues](https://carsonrodrigues.com). GitHub's "Cite this repository" button reads `CITATION.cff`; in BibTeX:

```bibtex
@misc{rodrigues2026carry,
  author       = {Rodrigues, Carson},
  title        = {What should an agent carry from one level to the next?},
  year         = {2026},
  howpublished = {ARC Prize 2026 Paper Track entry, Kaggle},
  url          = {https://github.com/rodriguescarson/arc-prize-2026/blob/main/paper/level-transfer/paper/paper_full.pdf}
}
```

## Licence
Code and text authored by Carson Rodrigues: MIT-0 (`LICENSE`), the permissive public-domain licence arcprize.org requires for prize eligibility. Third-party code keeps its own open-source licence. Game environments and wheels belong to the ARC Prize Foundation and are not redistributed here. `data/human_replays_packed/` is a packed derivative of the ARC Prize human replay release; it keeps the terms of that release, not MIT-0 (see its `NOTICE`).
