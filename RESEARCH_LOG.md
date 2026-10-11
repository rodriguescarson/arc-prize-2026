# RESEARCH_LOG — concise, append-only, survives context resets

All times IST. Newest at the bottom.

## 2026-10-12
- 04:27 Mission brief saved to `MISSION.md` (the `/goal` command caps at 4000 chars; the full brief lives here).
- 04:28 `~/Projects/arc-white-box` identified as the Alignment Research Center's White-Box challenge, NOT ARC-AGI. Process reusable, code not.
- 04:29 Workspace created as its own uv project (Python 3.11, numpy). Datasets cloned to `data/`: ARC-AGI-2 (1000 train / 120 eval, HEAD f3283f7), ARC-AGI-1 (400/400), ARC-AGI-3-Agents (HEAD 4743e7d, 2026-08-03; supports local environments via the `arc-agi` package).
- 04:30 Disk at 98% (9.6 GB free). `~/.cache/g4` = 34 GB live Gemma data (never clean, per memory). No local model downloads until Carson frees space.
- 04:32 Core pipeline written: `data.py`, `score.py` (pass@2, per-task mean), `submission.py` (Kaggle layout + validator), `runner.py`, `registry.py` (-> `EXPERIMENT_LOG.csv`), `cli.py` (`uv run arc eval ...`), `solvers/trivial.py`. Trivial baseline: 0/120 on ARC-AGI-2 eval, 167 test outputs; 1 attempt-2 hit on the first 200 training tasks (constant-output task). Pipeline validated end to end.
- 04:35 Inventory agents returned: zero ARC code on the machine; reusable = gemma-swe-agent Kaggle packaging + QLoRA, research stats helpers, pre-reg/provenance formats. `RESEARCH_INVENTORY.md` written.
- 04:36 competition-tracker (2026-09-16) recorded: code deadline Nov 2, paper Nov 8 (arcprize.org) vs Nov 9 23:59 UTC (Kaggle); paper must link to a real ARC-AGI-2/3 Kaggle submission; open-source before private scores; no internet at eval. Awaiting live verification.
- Open: rules agent + literature agent still running.
- 04:36 Kaggle API (CLI 2.2.4, Carson's creds): three live competitions — arc-prize-2026-arc-agi-3 (deadline 2026-11-02 23:59, $850k, 4,169 teams), arc-prize-2026-arc-agi-2 (2026-11-02 23:59, $700k, 2,747 teams), arc-prize-2026-paper-track (2026-11-09 23:59, $450k, 247 teams). `userHasEntered: False` on all three. ARC-AGI-2 files: arc-agi_{training,evaluation}_{challenges,solutions}.json, arc-agi_test_challenges.json (1.0 MB, hidden set), sample_submission.json. Paper track ships only NOTE.md. ARC-AGI-3 ships ARC-AGI-3-Agents repo + `arc_agi_3_wheels/` (cp312 wheels: arc_agi 0.9.8, arcengine 0.9.3) + `environment_files/<game>/<hash>/<game>.py` local game environments.
- 04:38 `kaggle competitions download` -> **403 Forbidden on all three**: Carson must accept the rules / join each competition on kaggle.com first (BLOCKER for official data + any submission; public data is already local from GitHub).
- 04:38 DSL-search floor baseline (CPU, depth-2 compositions of 19 transforms + learned colour map): ARC-AGI-2 eval **0/120** (3.8 s), ARC-AGI-1 eval 5/400 = 1.25% (11 s), ARC-AGI-2 train 37/1000 = 3.75% (21 s). Diagnostics on ARC-AGI-2 eval: shape_wrong 48, content_wrong 46, near_miss 39, colours_wrong 34 of 167 test outputs. Logged in EXPERIMENT_LOG.csv.
