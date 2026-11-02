# What should an agent carry from one level to the next?

ARC Prize 2026 Paper Track entry by Carson Rodrigues. The main paper is
[`paper/paper_full.pdf`](paper/paper_full.pdf) (source: `paper/paper_full.md`); the Kaggle writeup body is
`paper/writeup_v2.md`.

## The result

| evidence | result |
|---|---|
| E21, all 340 released human replay sessions, no agent involved | a winning sequence re-solves the next level in 0 of 1,186 testable pairs on 23 games with a working positive control (control 99.7%; 144 distinct level transitions) |
| E21, same data | successive winning sequences are only slightly more alike than a shuffle (0.446 against 0.431) |
| E21, mechanics | a model learned on level k predicts level k+1 movement at 0.740 against a 0.301 permuted null, short of the 0.8 bar filed in advance |
| LLM harness, hidden 55, two draws per arm | `solved_levels()` on 24.65, off 27.89: a gap inside the 11 points the design resolves, so no effect is claimed |

One of three predictions filed in advance was met. They are in `HYPOTHESES.md`, an append-only file first pushed
on 15 Oct 2026 03:05 UTC (commit `ec242a3` in this repository).

## Files

- `paper/paper_full.pdf`, `paper/paper_full.md`: the main paper.
- `paper/writeup_v2.md`: the Kaggle writeup body.
- `paper/figures/fig6_e21_transfer.png`, built by `paper/make_fig_e21.py` from `experiments/E21_level_transfer.json`.
- `paper/figures/card_560x280.png`, built by `paper/make_card_560x280.py`.
- `HYPOTHESES.md`: every filed prediction, each outcome recorded against it.
- `experiments/E21_level_transfer.{json,out}`: the full-population E21 result and its run log.
- `experiments/level1_cost_check.{py,out}`: re-derives the level-1 cost medians quoted in section 6.
- `experiments/budget_check.{py,out}`: how often M1's budget |W_k| covers the next human solution (452 of the
  1,186 pairs) and that replay completes none of those; descriptive, computed after the E21 outcome.
- `experiments/e21_numbers.{py,out}`: every E21 number quoted in section 4 and the abstract, with the
  session-cluster intervals, from `experiments/E21_level_transfer.json` (needs numpy).
- `experiments/hidden_draws.{py,csv,out}`: Table 2 and the draw statistics of section 5b; the CSV holds rows 6 to 21
  of `submission/SUBMISSIONS.md` (13 valid draws, 3 excluded with their reason), state of 2 November 2026.
- `CLAIM-MAP.md`: the script and raw file behind each number of our own in the paper.
- `arxiv/`: the arXiv version (text, LaTeX source, built PDF); its README lists how it differs from the Paper Track
  text.
- `paper/pdf_header.tex`: the LaTeX header used to build the PDF.

The figure was re-rendered on 2 November with larger tick and bar labels for the arXiv version; the Paper Track
PDF carries the earlier rendering of the same data.

## Code the paper refers to

| path in the paper | where it is |
|---|---|
| `inference/utils/level_memory.py` (`solved_levels()`, the plan memory) | `harness/ARC3-Inference/inference/utils/level_memory.py` in [rodriguescarson/arc-agi-3](https://github.com/rodriguescarson/arc-agi-3) |
| `arc3/agents/model_based.py` (the explorer's mechanics memory) | `src/arc_prize_2026/arc3/agents/model_based.py` in this repository |
| the E21 replay experiment | `src/arc_prize_2026/arc3/level_transfer.py` in this repository (its full output also sits at `experiments/human_replays/`) |
| the hidden-set draws, one row per submission | `submission/SUBMISSIONS.md` in this repository |

Every other path in the paper is relative to this folder.

## Reproduce

From the repository root, with the environment from `pyproject.toml` (`uv sync`):

    uv run python paper/level-transfer/paper/make_fig_e21.py paper/level-transfer/experiments/E21_level_transfer.json paper/level-transfer/paper/figures
    python3 -I paper/level-transfer/experiments/level1_cost_check.py | diff - paper/level-transfer/experiments/level1_cost_check.out
    python3 -I paper/level-transfer/experiments/budget_check.py | diff - paper/level-transfer/experiments/budget_check.out
    uv run python paper/level-transfer/experiments/e21_numbers.py | diff - paper/level-transfer/experiments/e21_numbers.out
    python3 -I paper/level-transfer/experiments/hidden_draws.py | diff - paper/level-transfer/experiments/hidden_draws.out

The PDF is built with pandoc 3.9 and tectonic 0.15, from `paper/level-transfer/paper/`:

    pandoc paper_full.md -o paper_full.pdf --pdf-engine=tectonic --resource-path=. -H pdf_header.tex \
      -V geometry:margin=1in -V fontsize=11pt -V colorlinks=true -V urlcolor=blue -V linkcolor=black

## Licence

The author's code and text are MIT-0 (see `LICENSE` at the repository root). The human replay data the
experiments read come from the ARC Prize release and keep their source's terms (see
`data/human_replays_packed/NOTICE`).
