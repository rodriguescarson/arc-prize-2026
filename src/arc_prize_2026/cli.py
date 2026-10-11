"""CLI: uv run arc eval --solver trivial --data data/ARC-AGI-2 --split evaluation"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import load_task_dir, load_kaggle_split
from .registry import log_run
from .runner import run_solver
from .diagnostics import diagnose_run

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="arc")
    sp = ap.add_subparsers(dest="cmd", required=True)
    ev = sp.add_parser("eval", help="run a solver on a split and score it")
    ev.add_argument("--solver", required=True)
    ev.add_argument("--data", default="data/ARC-AGI-2", help="dataset root with data/<split>/*.json, or a Kaggle challenges .json")
    ev.add_argument("--solutions", default=None, help="Kaggle solutions .json (only with a challenges file)")
    ev.add_argument("--split", default="evaluation")
    ev.add_argument("--limit", type=int, default=None)
    ev.add_argument("--run-id", default=None)
    ev.add_argument("--hypothesis", default="")
    ev.add_argument("--kwargs", default="{}", help="JSON dict of solver kwargs")
    ev.add_argument("--no-log", action="store_true")
    a = ap.parse_args(argv)

    data = Path(a.data)
    if data.suffix == ".json":
        tasks = load_kaggle_split(data, a.solutions, source=data.stem)
        if a.limit:
            tasks = tasks[: a.limit]
        split_name = data.stem
    else:
        tasks = load_task_dir(data / "data" / a.split, limit=a.limit)
        split_name = f"{data.name}/{a.split}"
    kwargs = json.loads(a.kwargs)
    run_id = a.run_id or f"{a.solver}__{split_name.replace('/', '-')}"
    out_dir = ROOT / "experiments" / run_id
    sub, report, meta = run_solver(a.solver, tasks, out_dir, solver_kwargs=kwargs)
    print(json.dumps(meta, indent=1))
    if report:
        print('diagnostics:', json.dumps(diagnose_run(out_dir, tasks)))
    if report and not a.no_log:
        log_run(
            run_id=run_id, hypothesis=a.hypothesis, method=a.solver, config=kwargs,
            dataset_split=split_name, n_tasks=len(tasks), score=report.score,
            tasks_solved=report.tasks_fully_solved, runtime_s=meta["runtime_s"],
            outcome="baseline" if "baseline" in a.hypothesis.lower() or a.solver == "trivial" else "measured",
            interpretation="",
        )
        print(f"logged -> {ROOT / 'EXPERIMENT_LOG.csv'}")
    print(f"submission -> {out_dir / 'submission.json'}")


if __name__ == "__main__":
    main()
