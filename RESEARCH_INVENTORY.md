# RESEARCH_INVENTORY — what Carson already has that an ARC Prize 2026 entry can reuse

Written 2026-10-12 (IST) from a recursive read of `~/research`, `~/Projects/*`, and
`~/Projects/arc-white-box`. Nothing was modified. VERIFIED = read from disk this session.

## 0. Bottom line

1. **No ARC-AGI code exists anywhere on this machine.** `grep -ri "arc-agi|arcprize|arc prize"`
   over `~/research` returns zero hits. `~/Projects/arc-white-box` is the **Alignment Research
   Center's** White-Box Estimation Challenge (MLP cumulant propagation), a different "ARC". Its
   estimator code is irrelevant here; its *process* is not (see §3).
2. **What transfers is infrastructure and methodology, not models**: Kaggle offline-notebook
   packaging and a QLoRA trainer (gemma-swe-agent), paired-bootstrap / sign-test / Wilson-CI stats,
   pre-registration + provenance file formats, an LLM-council reviewer, and citation checkers.
3. **The competition tracker already decided the strategy on 2026-09-16** (`competition-tracker/
   briefs/07-research-track.md`): "enter ARC-AGI-3 (or -2) modestly so you are eligible, then
   compete on the paper. The paper must be linked to a real ARC-AGI-2 or ARC-AGI-3 Kaggle
   submission." Recorded deadlines: code submissions **Nov 2**, paper **Nov 8 (arcprize.org) /
   Nov 9 23:59 UTC (Kaggle)**. These are being re-verified against the live pages (see
   `NEXT_ACTIONS.md`).
4. **Compute on hand**: MacBook Pro M4, 16 GB, **9.6 GB disk free (98% full)**; system Python 3.9
   has torch 2.8 + MPS. Kaggle: `~/.kaggle/kaggle.json` present; CLI 1.7 default, 2.2.4 in
   `gemma-swe-agent/.venv`; 30 GPU-h/week quota (4×L4 kernels used before). RunPod account with
   prior 2×H100 usage ($6.98/h, ~$136 spent in Sept against a $500 cap). College lab RTX A6000
   48 GB (RDP only, WSL2, no SSH). A paid run needs Carson's approval (MISSION §10).

## 1. Assets worth reusing (exact paths)

### 1a. Kaggle offline inference + packaging — `~/Projects/gemma-swe-agent` (VERIFIED)
| Asset | Path | Why it matters for ARC |
|---|---|---|
| Notebook generator with wheelhouse install, interpreter-tag filtering, vLLM boot | `scripts/make_eval_kernel.py` | ARC Kaggle kernels run with internet off; same pattern |
| Kernel metadata template (`enable_internet:false`, `model_sources`, `dataset_sources`, `machine_shape`) | `kernels/*/kernel-metadata.json` | copy and edit |
| Deterministic bundle + sha256, base64 one-cell notebook | `scripts/pack_bundle.py`, `scripts/make_kernel.py` | reproducibility: paper cites the sha |
| Push + poll + fetch output | `scripts/kaggle_push_wait.sh` | needs Kaggle CLI 2.x for `--accelerator` |
| QLoRA trainer (NF4, r16/α32, chunked loss) + CPU-testable core | `train/qlora_train.py`, `train/qlora_lib.py` | test-time-training / fine-tuning path |
| Adapter packaging | `train/package_adapter.py` | ship LoRA weights as a Kaggle dataset |
| Paired comparison with Wilson 95% CIs + exact sign test | `eval/compare.py` | the per-task paired analysis ARC needs |
| sqlite experiment DB with failure-stage labels | `eval/expdb.py` | alternative registry pattern |
| Pre-registered decision rules as executable scripts | `scripts/keep_rule.py`, `scripts/ab_l4_decide.py` | freeze "keep/revert" rules before results |
| Failure forensics write-up pattern | `docs/a6000/FAILURE_FORENSICS.md` | template for error analysis section |
| 149 pytest files, "tests first, glue included" rule | `tests/`, `docs/PLAN_TO_FINISH.txt` | |

Caveat: all tied to Gemma 4 31B, vLLM 0.19.1 and the swegemma harness; adapt, do not import.

### 1b. Statistics and evaluation methodology — `~/research` (VERIFIED)
| Asset | Path |
|---|---|
| `bootstrap_acc_ci`, `paired_bootstrap_diff`, `mcnemar`, `fmt_ci` (164-line stdlib+numpy module) | `03-intent-detection-at-scale/data/stats.py` (same file in 04 and 20) |
| Paired t / Wilcoxon / bootstrap over (task, seed) units | `04-llm-optimization-tensorflow/data/significance.py` |
| Wilson interval, cluster bootstrap, AUROC, McNemar | `10-agentic-cad-reliability/scripts/stats.py` |
| Exact sign test, exact Wilcoxon, seed-level bootstrap, selection regret, best-of-N inflation | `15-silent-failure-automated-adaptation/code/reanalyze_job_level.py` |
| Permutation null, bootstrap CI, interaction test, with pytest suite | `13-neurotwin-brain-identifiability/src/neurotwin/stats.py`, `analysis/interaction_test.py` |
| ECE, reliability curves, temperature scaling, split-conformal, abstention | `07-dental-procedure-prediction/data/calibration.py`, `meps_conformal.py`, `abstention.py` |
| success@k, silent-failure rate, ECE for code-generating agents | `10-agentic-cad-reliability/benchmark/metrics.py` |

### 1c. Agent / generate-execute-verify loops (closest in shape to an ARC program-synthesis solver)
| Asset | Path |
|---|---|
| Generate code → run in subprocess → grade against reference; Mock/Anthropic/OpenAI/OpenRouter clients; dry-run with no keys | `10-agentic-cad-reliability/benchmark/{agents,executor,grader,runner,llm}.py` |
| LLM proposes configs, evaluator scores, confidence filter | `04-llm-optimization-tensorflow/data/llm_optflow_advisor.py` |
| Generator-vs-verifier-strength axis (four verifier levels) | `14-dreams-hallucinations-generative-reconstruction/vignette/run_popqa_axis.py` |
| Resumable per-run JSONL client with cost ledger and hard USD cap | `20-labeled-examples-intent-gap/data/revision-2026-10/code/orclient.py` |
| Idempotent queue runner, daemonize, harvest, audit/reconcile | `~/Projects/adaption-hackathon/polychart/{queue_runner,daemonize,harvest,audit,reconcile}.py` |
| Relaunch-dead-jobs with `start_new_session`, STOP/HOLD files, `RESUME.md` handoff | `~/Projects/adaption-leaderboard/relaunch.py`, `RESUME.md` |
| Spend guard and launch guard | `~/Projects/adaption-leaderboard/spend_guard.py`, `launch_guard.py` |

### 1d. Retrieval (Prism) — `~/Projects/prism/prism_memory` (VERIFIED, deprecated project)
Dense (Qwen3-Embedding-0.6B) + BM25 + RRF + cross-encoder rerank, lane routing by prototype
similarity, golden-set eval with stage ablation and miss classification (RERANKABLE vs RETRIEVAL).
Dependency-free parts: `chunker.py`, `decay.py`, `provenance.py`, `consolidate.py`, the `eval.py`
pattern. **Relevance to ARC is low** (no obvious retrieval problem), except as a pattern for
retrieving similar *training tasks* as in-context demonstrations, which prior ARC work has tried.

### 1e. Process assets
- Pre-registration format: `04-.../heldout-validation-2026-10-10/PROTOCOL.md`, `16-.../PROTOCOL.md`,
  `20-.../decisions/PROTOCOL.md`; GO/NO-GO plans `13-.../PLAN.md`, `17-.../DESIGN.md`.
- Provenance: `15-.../data/PROVENANCE.md` + `numbers.tex` + `check_mlj_numbers.py` (every paper
  number traces to a file).
- `~/research/MANUSCRIPT-REVISION-PLAYBOOK.md` (claim strength at full precision, disclose failed
  hypotheses). `~/research/CLAUDE.md` writing + citation rules.
- LLM council review: `12-.../scripts/review_council.py`, `~/Projects/gemma-swe-agent/scripts/llm_council.py`.
- Citation checkers: `references/verify_dois.py` (05, 07, 08, 09, 12, 13, 14, 17), `crossref_audit.py`.
- Multi-agent review workflow: `~/research/.claude/wf-audit-paper4.js`.

### 1f. ARC White-Box (`~/Projects/arc-white-box`) — process only
`harness/evalsuite.py` (per-item paired runner, bootstrap CIs, locked HOLDOUT needing an explicit
flag, ledger of every look), `PLAN.md` structure (baseline ladder B0–B4, pre-registered PASS/KILL
with dates, "Not pursued, with reasons", claims table tagged measured/derived/unvalidated). Copy
the structure, not the code.

## 2. Potential research directions grounded in these assets
(Scored and selected in `HYPOTHESES.md` once the literature map lands.)
- **Candidate selection / verification as the contribution.** Carson's strongest demonstrated
  skill is measurement: silent-failure detection (10, 15), calibration and conformal (07),
  generator-vs-verifier analysis (14), selection-regret and best-of-N inflation (15). Any ARC
  solver that produces multiple candidates needs a selector for its two attempts; the
  augmentation-vote and product-of-probabilities heuristics in the TTT lineage are measurable and
  improvable, and the analysis generalises across solver families (universality).
- **Test-time training audit.** Project 15's "automated adaptation can silently fail" framing
  applied to TTT on ARC: when does per-task fine-tuning help, when does it hurt, and can that be
  predicted before spending the compute? Reuses the QLoRA trainer and the paired-stats toolkit.
- **Generate-execute-verify program synthesis** (project 10's loop) with a self-contained small
  model inside a Kaggle kernel. Feasible mechanically; the open question is whether a ≤8B
  open model reaches a non-trivial ARC-AGI-2 score without API access.

## 3. Missing capabilities and their cost
| Capability | Status | Cost to build |
|---|---|---|
| ARC task loader, pass@2 scorer, Kaggle submission writer/validator, experiment registry | **DONE 2026-10-12** (`src/arc_prize_2026/`), trivial baseline runs end-to-end | — |
| Verified 2026 submission format (attempt_1/attempt_2 layout re-check) | pending rules agent | 0.5 h |
| A non-trivial local baseline (DSL search on CPU) | next | 0.5 day |
| A GPU baseline (small-LM TTT or TRM-style) reproducing a public number | needs Kaggle GPU quota or RunPod (Carson approves spend) | 2–4 days + compute |
| Kaggle notebook that runs offline within the compute limit and produces `submission.json` | adapt gemma-swe-agent scripts | 1–2 days |
| Disk: 9.6 GB free | **blocker for any local model** (`~/.cache/g4` is 34 GB live Gemma data, do not touch) | Carson's call |

## 4. Relevant prior work and competing approaches
See `LITERATURE_MAP.md` (in progress).

## 5. Highest-value first experiments
1. Reproduce one public baseline number on ARC-AGI-2 public eval under the competition protocol
   (pass@2, 120 tasks) so every later delta has a comparable anchor.
2. Measure the selection gap: oracle-pick-from-N candidates vs the baseline's own top-2. The size
   of that gap bounds what any selector contribution can be worth.
3. Per-task failure taxonomy on the public eval (wrong shape / wrong colours / partial), paired
   across solver families, to pick the failure mode worth attacking.
