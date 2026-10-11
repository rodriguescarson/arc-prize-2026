"""Run a solver over a task list, build + validate a submission, score it, log the run."""
from __future__ import annotations

import importlib
import json
import time
import traceback
from pathlib import Path

from .data import Grid, Task
from .score import ScoreReport, score_submission
from .submission import FALLBACK, build_submission, validate_submission, write_submission


def _two_distinct(cands: list[Grid]) -> tuple[Grid, Grid]:
    seen: list[Grid] = []
    for c in cands:
        if c is not None and c not in seen:
            seen.append(c)
        if len(seen) == 2:
            break
    if not seen:
        return FALLBACK, FALLBACK
    if len(seen) == 1:
        return seen[0], seen[0]
    return seen[0], seen[1]


def run_solver(solver_name: str, tasks: list[Task], out_dir: Path, *, per_task_timeout_s: float | None = None,
               solver_kwargs: dict | None = None) -> tuple[dict, ScoreReport | None, dict]:
    """Returns (submission, score_report_or_None, run_meta). Per-task failures become fallbacks, never crashes."""
    mod = importlib.import_module(f"arc_prize_2026.solvers.{solver_name}")
    solver_kwargs = solver_kwargs or {}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions: dict[str, list[tuple[Grid, Grid]]] = {}
    per_task: dict[str, dict] = {}
    t0 = time.time()
    for t in tasks:
        ts = time.time()
        try:
            cands = mod.solve(t, **solver_kwargs) if solver_kwargs else mod.solve(t)
            predictions[t.task_id] = [_two_distinct(c) for c in cands]
            err = None
        except Exception as e:  # noqa: BLE001 - a solver bug must not kill the run
            predictions[t.task_id] = [(FALLBACK, FALLBACK) for _ in t.test]
            err = f"{type(e).__name__}: {e}"
            (out_dir / "errors.log").open("a").write(f"{t.task_id}\n{traceback.format_exc()}\n")
        per_task[t.task_id] = {"seconds": round(time.time() - ts, 3), "error": err}
    runtime = time.time() - t0

    sub = build_submission(tasks, predictions)
    problems = validate_submission(sub, tasks)
    if problems:
        raise RuntimeError("invalid submission: " + "; ".join(problems[:5]))
    write_submission(sub, out_dir / "submission.json")

    report = None
    if all(t.has_solutions() for t in tasks):
        report = score_submission(tasks, sub)
        for r in report.task_results:
            per_task[r.task_id].update({"score": r.score, "attempt_hits": r.attempt_hits})
    meta = {
        "solver": solver_name,
        "solver_kwargs": solver_kwargs,
        "n_tasks": len(tasks),
        "runtime_s": round(runtime, 2),
        "errors": sum(1 for v in per_task.values() if v["error"]),
        "summary": report.summary() if report else None,
    }
    (out_dir / "per_task.json").write_text(json.dumps(per_task, indent=1, sort_keys=True))
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=1))
    return sub, report, meta
