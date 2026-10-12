# RUBRIC_SCORECARD — internal evidence matrix (not a prediction of the judges' scores) — updated 2026-10-12 06:50 IST

Rubric verbatim from https://www.kaggle.com/competitions/arc-prize-2026-paper-track/overview
(read 2026-10-12): "Submissions for Paper Awards are evaluated equally across the following six
criteria. Each criterion is scored on a scale from 0 (lowest) to 5 (highest), with the final score
calculated as the average of all six." Papers above 4.5/5 share a $375K pool; top three take
$50K/$20K/$5K. Judges: Mike Knoop, François Chollet. Ties go to the earlier submission.

| Criterion | Official wording | Provisional (today) | Evidence so far | Weakness | Next action |
|---|---|---|---|---|---|
| Accuracy | "How accurate is the submission based on its performance on the leaderboard? (you will be asked to provide your submission ID)" | 0 | public-25 dev score 0.28/100 (v4, `experiments/arc3_E2_v4_hud_contact1_a2000_s0`); LB top is 62.96 | no submission yet; absolute score will be low | Carson clicks Submit on the pushed kernel; two finals by Oct 30 |
| Universality | "How general and universal is the Submission approach beyond the competition? Does your submission translate to other similar problems?" | 2 | no per-game code; same agent on all 25 games; human-replay analysis shows which goal types the mechanism covers across games (E11) | public games only; hidden-set result pending | hidden-set submission |
| Progress | "How much does the paper increase the overall chance of anyone achieving a top score on ARC Prize?" | 2 | offline harness with toolkit-exact scorer; non-determinism test and hidden-counter detector found 3 representation defects that any agent hits (`RESEARCH_LOG.md` 07:45, 08:55) | tools not yet packaged/documented for others | README + `arc3/` tool docs; release |
| Theory | "How well does the paper describe why the Submission works (as opposed to merely describing how it works)?" | 3 | pre-registered mechanism; memory ablation (E3) shows identical level-1 cost and lower later-level cost; measured assumptions A1/A2 with per-game determinism and model accuracy; goal template class validated on 340 human replays (consistent in 6 games, empty in 12 click games, E11) | n = 2 games with ≥2 levels; bound is informal | tighten the sample-complexity statement; add the E11 table to the paper |
| Completeness | "How thoroughly and completely does the paper cover your submission to the leaderboard?" | 2 | every number traces to `experiments/*/results.json` + `EXPERIMENT_LOG.csv`; failure tables per run | no submission ID yet; paper is a skeleton | finish `paper/draft.md` from measured numbers only |
| Novelty | "How novel is the Submission relative to existing public research?" | 3 | no public Kaggle agent learns an effect model for planning with cross-level memory + goal inference (notebook survey, `LITERATURE_MAP.md` §7) | Twin/Tycho do executable world models with frontier LLMs; must position precisely | related-work paragraph with explicit deltas |

Update rule: a provisional score may rise only when a file in `experiments/` or `paper/` is named as
evidence in the row. Every edit is dated in `RESEARCH_LOG.md`.
