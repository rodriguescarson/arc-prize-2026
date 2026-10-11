"""Append-only experiment registry -> EXPERIMENT_LOG.csv at the workspace root.

One row per run. Nothing is ever edited in place; corrections are new rows with outcome=retraction.
"""
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / "EXPERIMENT_LOG.csv"
FIELDS = [
    "run_id", "timestamp_ist", "hypothesis", "method", "commit", "config",
    "dataset_split", "n_tasks", "score", "tasks_solved", "runtime_s", "outcome", "interpretation",
]
IST = timezone(timedelta(hours=5, minutes=30))


def git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        sha = out.stdout.strip() or "nogit"
        return sha + ("-dirty" if dirty else "")
    except Exception:
        return "nogit"


def log_run(*, run_id: str, hypothesis: str, method: str, config: dict, dataset_split: str,
            n_tasks: int, score: float, tasks_solved: int, runtime_s: float, outcome: str,
            interpretation: str) -> None:
    new = not LOG.exists()
    with LOG.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({
            "run_id": run_id,
            "timestamp_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M"),
            "hypothesis": hypothesis,
            "method": method,
            "commit": git_commit(),
            "config": json.dumps(config, sort_keys=True),
            "dataset_split": dataset_split,
            "n_tasks": n_tasks,
            "score": f"{score:.6f}",
            "tasks_solved": tasks_solved,
            "runtime_s": f"{runtime_s:.1f}",
            "outcome": outcome,
            "interpretation": interpretation,
        })
