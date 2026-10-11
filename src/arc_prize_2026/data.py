"""Task loading for ARC-AGI-1/2 (GitHub layout) and the Kaggle challenge/solution JSON layout.

A task is a dict with keys "train" (list of {input, output}) and "test" (list of {input[, output]}).
Grids are lists of lists of ints 0-9. We keep plain Python lists at the boundary so the same
objects can be serialised straight into a Kaggle submission.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

Grid = list[list[int]]


@dataclass
class Task:
    task_id: str
    train: list[dict]  # [{"input": Grid, "output": Grid}, ...]
    test: list[dict]  # [{"input": Grid, "output": Grid | None}, ...]
    source: str = ""  # e.g. "ARC-AGI-2/evaluation"
    meta: dict = field(default_factory=dict)

    @property
    def test_inputs(self) -> list[Grid]:
        return [p["input"] for p in self.test]

    @property
    def test_outputs(self) -> list[Grid | None]:
        return [p.get("output") for p in self.test]

    def has_solutions(self) -> bool:
        return all(p.get("output") is not None for p in self.test)


def _validate_grid(g, where: str) -> None:
    if not isinstance(g, list) or not g or not all(isinstance(r, list) and r for r in g):
        raise ValueError(f"{where}: grid must be a non-empty list of non-empty rows")
    w = len(g[0])
    if any(len(r) != w for r in g):
        raise ValueError(f"{where}: ragged grid")
    if len(g) > 30 or w > 30:
        raise ValueError(f"{where}: grid larger than 30x30 ({len(g)}x{w})")
    for r in g:
        for v in r:
            if not isinstance(v, int) or not 0 <= v <= 9:
                raise ValueError(f"{where}: cell value {v!r} outside 0-9")


def load_task_file(path: Path, source: str = "") -> Task:
    d = json.loads(path.read_text())
    t = Task(task_id=path.stem, train=d["train"], test=d["test"], source=source)
    for i, p in enumerate(t.train):
        _validate_grid(p["input"], f"{t.task_id} train[{i}].input")
        _validate_grid(p["output"], f"{t.task_id} train[{i}].output")
    for i, p in enumerate(t.test):
        _validate_grid(p["input"], f"{t.task_id} test[{i}].input")
        if p.get("output") is not None:
            _validate_grid(p["output"], f"{t.task_id} test[{i}].output")
    return t


def load_task_dir(directory: Path, source: str | None = None, limit: int | None = None) -> list[Task]:
    """Load every *.json task in a directory (ARC-AGI GitHub layout), sorted by id."""
    directory = Path(directory)
    files = sorted(directory.glob("*.json"))
    if limit is not None:
        files = files[:limit]
    src = source if source is not None else f"{directory.parent.parent.name}/{directory.name}"
    return [load_task_file(f, src) for f in files]


def load_kaggle_split(challenges_path: Path, solutions_path: Path | None = None, source: str = "kaggle") -> list[Task]:
    """Load the Kaggle ARC Prize layout.

    challenges: {task_id: {"train": [...], "test": [{"input": ...}, ...]}}
    solutions:  {task_id: [Grid, ...]}  (one output per test input, same order)
    """
    ch = json.loads(Path(challenges_path).read_text())
    sol = json.loads(Path(solutions_path).read_text()) if solutions_path else {}
    tasks = []
    for tid in sorted(ch):
        d = ch[tid]
        test = [dict(p) for p in d["test"]]
        if tid in sol:
            outs = sol[tid]
            if len(outs) != len(test):
                raise ValueError(f"{tid}: {len(outs)} solutions for {len(test)} test inputs")
            for p, o in zip(test, outs):
                p["output"] = o
        tasks.append(Task(task_id=tid, train=d["train"], test=test, source=source))
    return tasks


def iter_grids(task: Task) -> Iterator[Grid]:
    for p in task.train:
        yield p["input"]
        yield p["output"]
    for p in task.test:
        yield p["input"]
        if p.get("output") is not None:
            yield p["output"]


def task_dir_to_kaggle(tasks: list[Task]) -> tuple[dict, dict]:
    """Convert loaded tasks into (challenges, solutions) dicts in the Kaggle layout.

    Used to build a local dev set that is byte-for-byte shaped like the competition input.
    """
    challenges, solutions = {}, {}
    for t in tasks:
        challenges[t.task_id] = {
            "train": t.train,
            "test": [{"input": p["input"]} for p in t.test],
        }
        if t.has_solutions():
            solutions[t.task_id] = [p["output"] for p in t.test]
    return challenges, solutions
