# RUBRIC_SCORECARD — internal evidence matrix (not a prediction of the judges' scores)

Rubric verbatim from https://www.kaggle.com/competitions/arc-prize-2026-paper-track/overview
(read 2026-10-12): "Submissions for Paper Awards are evaluated equally across the following six
criteria. Each criterion is scored on a scale from 0 (lowest) to 5 (highest), with the final score
calculated as the average of all six." Papers above 4.5/5 share a $375K pool; top three take
$50K/$20K/$5K. Judges: Mike Knoop, François Chollet. Ties go to the earlier submission.

| Criterion | Official wording | Provisional (today) | Evidence so far | Weakness | Next action |
|---|---|---|---|---|---|
| Accuracy | "How accurate is the submission based on its performance on the leaderboard? (you will be asked to provide your submission ID)" | 0 | no Kaggle submission yet; local floors 0/120 (ARC-AGI-2), 2 levels/25 games random (ARC-AGI-3) | no model yet | pick track, ship a first submission by 20 Oct |
| Universality | "How general and universal is the Submission approach beyond the competition? Does your submission translate to other similar problems?" | 0 | — | — | choose a mechanism that is solver-agnostic / environment-agnostic and test it on ≥2 families |
| Progress | "How much does the paper increase the overall chance of anyone achieving a top score on ARC Prize?" | 0 | — | — | release code + a diagnostic tool others can run |
| Theory | "How well does the paper describe why the Submission works (as opposed to merely describing how it works)?" | 0 | — | — | state the mechanism, its assumptions, and a falsifiable prediction before running |
| Completeness | "How thoroughly and completely does the paper cover your submission to the leaderboard?" | 1 | pipeline, registry, diagnostics exist; every number traces to `experiments/` | no results | keep the claims table (measured / derived / unvalidated) |
| Novelty | "How novel is the Submission relative to existing public research?" | 0 | — | 90 papers in 2025; crowded | `LITERATURE_MAP.md` gap analysis first |

Update rule: a provisional score may rise only when a file in `experiments/` or `paper/` is named as
evidence in the row. Every edit is dated in `RESEARCH_LOG.md`.
