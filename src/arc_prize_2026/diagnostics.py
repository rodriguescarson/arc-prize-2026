"""Per-test-output failure taxonomy for a submission vs ground truth.

Categories (first match wins):
  correct        - attempt_1 or attempt_2 exact
  shape_wrong    - neither attempt has the right shape
  near_miss      - right shape, >= 90% cells correct on the best attempt
  colours_wrong  - right shape, cell accuracy < 90% but the set of colours used is wrong
  content_wrong  - right shape, cell accuracy < 90%, colour set right
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from .data import Task
from .grids import to_np


def diagnose_one(attempts: dict, truth) -> dict:
    t = to_np(truth)
    best = None
    for k in ("attempt_1", "attempt_2"):
        g = attempts.get(k)
        if g is None:
            continue
        a = to_np(g)
        if a.shape != t.shape:
            cand = {"attempt": k, "shape_match": False, "cell_acc": 0.0, "colour_set_ok": False}
        else:
            acc = float((a == t).mean())
            cand = {"attempt": k, "shape_match": True, "cell_acc": acc,
                    "colour_set_ok": set(np.unique(a).tolist()) == set(np.unique(t).tolist())}
        if best is None or (cand["shape_match"], cand["cell_acc"]) > (best["shape_match"], best["cell_acc"]):
            best = cand
    if best is None:
        return {"category": "shape_wrong", "cell_acc": 0.0}
    if best["shape_match"] and best["cell_acc"] == 1.0:
        cat = "correct"
    elif not best["shape_match"]:
        cat = "shape_wrong"
    elif best["cell_acc"] >= 0.9:
        cat = "near_miss"
    elif not best["colour_set_ok"]:
        cat = "colours_wrong"
    else:
        cat = "content_wrong"
    return {"category": cat, "cell_acc": round(best["cell_acc"], 4), "best_attempt": best["attempt"],
            "truth_shape": list(t.shape)}


def diagnose(tasks: list[Task], submission: dict) -> dict:
    per = {}
    for t in tasks:
        per[t.task_id] = [diagnose_one(submission[t.task_id][i], out) for i, out in enumerate(t.test_outputs)]
    cats = Counter(d["category"] for ds in per.values() for d in ds)
    return {"counts": dict(cats), "per_task": per}


def diagnose_run(run_dir: Path, tasks: list[Task]) -> dict:
    sub = json.loads((Path(run_dir) / "submission.json").read_text())
    rep = diagnose(tasks, sub)
    (Path(run_dir) / "diagnostics.json").write_text(json.dumps(rep, indent=1, sort_keys=True))
    return rep["counts"]
