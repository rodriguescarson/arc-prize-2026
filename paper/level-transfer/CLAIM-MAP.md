# Claim map: where each number of our own in the paper comes from

State of 2 November 2026. Paths are relative to `paper/level-transfer/` unless they start with `repo:` (the root of this
repository) or `arc-agi-3:` (the root of <https://github.com/rodriguescarson/arc-agi-3>).

Regenerate the logs. Each command prints to the terminal; `diff` against the committed `.out` shows nothing.

    # from the repository root
    uv run python paper/level-transfer/experiments/e21_numbers.py | diff - paper/level-transfer/experiments/e21_numbers.out
    python3 -I paper/level-transfer/experiments/hidden_draws.py | diff - paper/level-transfer/experiments/hidden_draws.out
    python3 -I paper/level-transfer/experiments/budget_check.py | diff - paper/level-transfer/experiments/budget_check.out
    python3 -I paper/level-transfer/experiments/level1_cost_check.py | diff - paper/level-transfer/experiments/level1_cost_check.out
    uv run python paper/level-transfer/paper/make_fig_e21.py paper/level-transfer/experiments/E21_level_transfer.json paper/level-transfer/paper/figures

`e21_numbers.py` needs numpy; it gave identical output with numpy 2.0.2 on Python 3.9 and numpy 2.5.4 on Python 3.12.
The other three scripts use only the standard library. None of them replays a game: the E21 replay itself is
`repo:src/arc_prize_2026/arc3/level_transfer.py` (tests: `repo:tests/test_level_transfer.py`), and its output is the raw
file `experiments/E21_level_transfer.json` (full run log: `experiments/E21_level_transfer.out`).

## Human replays (E21), sections 4 and the abstract

| claim (paper) | where | script | raw file |
|---|---|---|---|
| 340 sessions, 309 frame-exact, 1,314 level pairs, 1,237 testable (94.1%) | section 4 | `experiments/e21_numbers.py` | `experiments/E21_level_transfer.json` |
| replay completes the next level in 0 of 1,186 pairs on 23 games (12 click-driven, 11 movement-driven); control C2 99.7%; 144 distinct transitions; 95% upper bounds 0.31% over pairs and 2.5% over transitions | abstract, Table 1, Figure 1A | same | same |
| the positive control fails on tn36 (51 pairs), lf52 (3) and sc25 (1); with tn36 included: 0 of 1,237, control 95.6% | section 4, caveats | same | same |
| the budget \|W_k\| is at least the next human solution in 469 of 1,237 pairs and 452 of 1,186; those 452 rest on 113 transitions, 0 successes, upper bounds 0.81% over pairs and 3.2% over transitions | abstract, section 4 | `experiments/e21_numbers.py`, `experiments/budget_check.py` | same |
| 330 of the 1,237 sequences \|W_k\| are longer than 60 actions | section 7 | `experiments/e21_numbers.py` | same |
| 188 of 6,185 random-control runs unevaluable (3.0%, all lf52); they exceeded the 60-second budget | section 4, caveats | same | same; the run log `experiments/E21_level_transfer.out` ("C3 188/6185") |
| M2 similarity 0.446 against shuffle 0.431 (difference 0.015, session-cluster interval 0.012 to 0.019); above shuffle on 17 of 20 games where a shuffle can differ, 19 of 25 under the filed rule; five tied games, three below | abstract, Table 1, section 4 | same | same |
| M3 0.740 over 431 pairs in 10 movement games (session-cluster interval 0.687 to 0.791, 99 sessions); ceiling 0.906; null 0.301 over 421 pairs, 0.757 on those, 2.5 times; 56 distinct transitions; game-weighted mean 0.682 (game-cluster interval 0.462 to 0.864); leave-one-game-out 0.704 to 0.787; three games hold 48% of the pairs; per-game values 0.99 (dc22) to 0.00 (cd82, one transition, 10 pairs) | abstract, Table 1, Figure 1B, section 4 | same | same |
| Figure 1 | section 4 | `paper/make_fig_e21.py` | `experiments/E21_level_transfer.json` |
| the tests and bars were filed before any full result (`HYPOTHESES.md`, commit `ec242a3`, 15 Oct 2026 03:05 UTC, after a 12-session smoke that showed M1 at 0 of 65); one of three predictions met | section 4, Table 1 | none | `HYPOTHESES.md` ("E21 pre-registration", "E21 erratum"); `git show ec242a3` |
| other filed predictions mostly failed: P1 and P4 not met; E12, E13, E19 negative; the proposer follow-ups gained about 0.015 on the public 25; E20c lost a game with one proposer; E20d failed its gate | section 7 | none | `HYPOTHESES.md` (the pre-registration and outcome entries of those names) and the matching rows of `repo:EXPERIMENT_LOG.csv` |

## LLM harness on the hidden 55 games, section 5b and the linked submission

| claim (paper) | where | script | raw file |
|---|---|---|---|
| 16 hidden-set LLM draws in the submission list: 13 kept, 3 excluded (Swift pair 4.92; two zeros on 22 and 23 October, attributed to a platform kill) | section 5b | `experiments/hidden_draws.py` (cross-checks every row) | `experiments/hidden_draws.csv`, copy of rows 6 to 21 of `repo:submission/SUBMISSIONS.md` |
| Table 2: v2 24.65 (29.54, 19.75; kernel versions 2, 4), v1 27.89 (29.93, 25.85; 2, 5), v1f 26.50 (29.44, 21.86, 28.19; 1); the draws not in Table 2: v8i 24.95, 26.47, v10 24.51, 29.78, 27.60, 24.72 | section 5b | same | same |
| helper arm 3.2 below its twin; 95% interval for off minus on -4.5 to +10.9; 0.8 SD; 11 points | abstract, section 5b | same | same, with the copy SD 3.93 (see below) |
| five no-helper draws (v1 + v1f) 27.05, SD 3.30, 2.4 above the helper arm | section 5b | same | same |
| 13 valid Intel draws across 5 variants: 26.35, SD 3.18 | section 5b, linked submission | same | same |
| submission 57477157 scored 29.54, one SD above the 13-draw mean | linked submission | same | `repo:submission/SUBMISSIONS.md` row 9 |
| one submission per day: the 16 draws fall on 16 distinct UTC days (two share the IST date 21 October) | section 5b | same | same |
| v2 differs from v1 in two settings, `ARC3_LEVEL_MEMORY=1` and `ARC3_BAR_GUIDANCE=budget` | section 5b | none (a diff of two files) | `arc-agi-3:kaggle/variants/v1-franzen-faithful.json`, `arc-agi-3:kaggle/variants/v2-level-memory.json` |
| the helper itself | section 3 | none | `arc-agi-3:harness/ARC3-Inference/inference/utils/level_memory.py` |
| copies of the unmodified notebook: mean 25.77, SD 3.93; an independent study: SD 3.99 | section 5b | none | external, references [19] and [20]; not re-fetched here, the Kaggle thread is JavaScript-rendered |

## Our explorer, sections 5a and 6

| claim (paper) | where | script | raw file |
|---|---|---|---|
| memory on 0.277 and 13 levels, off 0.227 and 11 (public 25, one seed pair) | section 5a | none | `repo:EXPERIMENT_LOG.csv` rows `arc3_E3_v5_mem1_goals1_a2000_s0` and `arc3_E3_v5_mem0_goals1_a2000_s0` ("levels 13/183", "levels 11/183") |
| four further memory-on runs 0.283, 0.280, 0.276, 0.278 | section 5a | none | `repo:EXPERIMENT_LOG.csv` rows `arc3_E6_v5_mem1_goals1_a2000_s1`, `arc3_E3_v7_bars_mem1_a2000_s0`, `arc3_E6_v7_mem1_a2000_s2`, `arc3_E6_v7_mem1_a2000_s3` |
| Table 3 hidden scores 0.15, 0.12, 0.08, 0.08, 0.01 | section 6 | none | `repo:submission/SUBMISSIONS.md` rows 1 to 5 |
| Table 3 public-25 twins 0.280, 0.227, 0.204 | section 6 | none | `repo:EXPERIMENT_LOG.csv` rows `arc3_E3_v7_bars_mem1_a2000_s0`, `arc3_E3_v5_mem0_goals1_a2000_s0`, `arc3_E2_v4_hud_contact0_a2000_s0` |
| contact curiosity +0.080 on the v4 pair, more than all of it from lp85 (+0.111; the other 24 games sum to -0.031) | section 6 | none | `repo:experiments/arc3_E2_v4_hud_contact1_a2000_s0/results.json` and `..._contact0_...` |
| median level-1 cost 21.2 and 8.6 times the human cost (21.95 and 8.59 on the nine shared games) | section 6 | `experiments/level1_cost_check.py` | the two `results.json` files above (sha256 in `experiments/level1_cost_check.out`) |
| three public games (lp85, tn36, vc33) supply 90% of the public 0.280 | section 6 | none | `repo:experiments/arc3_E3_v7_bars_mem1_a2000_s0/results.json` (90.4%) |
| 1,087 of 4,233 teams in the (0.05, 0.23] band on 13 October | section 6 | none | a public leaderboard download that this repository does not redistribute |
| arithmetic: 0.07 x 55 = 3.9 points; 0.08 x 55 = 4.4 points | section 6 | none | none |

## Numbers that are not ours

The RHAE formula (reference [1]); RHAE of 93 to 100 on the public 25 games (references [7] to [13]); PRO-LONG +18.0
points (reference [9]); NOOA +11.8 points (reference [15]); 33 of 630 references cross a task boundary (reference [16]);
SD 3.99 over ten evaluations (reference [20]); 342 sessions in the release post (reference [18]). They are cited, not
measured here, and are not reproduced by any file in this repository.

## Every experiment attempted

`repo:EXPERIMENT_LOG.csv` (the experiment log, 12 October onward) and `repo:submission/SUBMISSIONS.md` (the hidden-set
submission list, including the failed and the excluded ones).
