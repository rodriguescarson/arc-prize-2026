"""Build and validate Kaggle-layout submissions.

Layout (ARC Prize 2025 Kaggle format, to be re-verified against the 2026 page):
    {task_id: [{"attempt_1": Grid, "attempt_2": Grid}, ...one entry per test input...]}
Every task in the challenge file must appear, with exactly len(test) entries, each with both attempts.
"""
from __future__ import annotations

import json
from pathlib import Path

from .data import Grid, Task

FALLBACK: Grid = [[0]]


def _coerce_grid(g) -> Grid:
    """Make a prediction JSON-safe and in-spec; fall back to [[0]] if hopeless."""
    try:
        if g is None:
            return FALLBACK
        if hasattr(g, "tolist"):
            g = g.tolist()
        g = [[int(v) for v in row] for row in g]
        if not g or not g[0] or len(g) > 30 or len(g[0]) > 30:
            return FALLBACK
        w = len(g[0])
        if any(len(r) != w for r in g):
            return FALLBACK
        if any(not 0 <= v <= 9 for r in g for v in r):
            return FALLBACK
        return g
    except Exception:
        return FALLBACK


def build_submission(tasks: list[Task], predictions: dict[str, list[tuple[Grid, Grid]]]) -> dict:
    """predictions: {task_id: [(attempt_1, attempt_2) per test input]}; missing entries get fallbacks."""
    sub = {}
    for t in tasks:
        preds = predictions.get(t.task_id, [])
        entries = []
        for i in range(len(t.test)):
            a1, a2 = preds[i] if i < len(preds) else (None, None)
            entries.append({"attempt_1": _coerce_grid(a1), "attempt_2": _coerce_grid(a2)})
        sub[t.task_id] = entries
    return sub


def validate_submission(sub: dict, tasks: list[Task]) -> list[str]:
    """Return a list of problems (empty == valid)."""
    problems = []
    want = {t.task_id: len(t.test) for t in tasks}
    for tid, n in want.items():
        if tid not in sub:
            problems.append(f"missing task {tid}")
            continue
        entries = sub[tid]
        if not isinstance(entries, list) or len(entries) != n:
            problems.append(f"{tid}: expected {n} test entries, got {len(entries) if isinstance(entries, list) else type(entries)}")
            continue
        for i, e in enumerate(entries):
            for k in ("attempt_1", "attempt_2"):
                if k not in e:
                    problems.append(f"{tid}[{i}]: missing {k}")
                elif _coerce_grid(e[k]) != e[k]:
                    problems.append(f"{tid}[{i}].{k}: not a valid grid")
    extra = set(sub) - set(want)
    if extra:
        problems.append(f"{len(extra)} unexpected task ids, e.g. {sorted(extra)[:3]}")
    return problems


def write_submission(sub: dict, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sub, separators=(",", ":")))
    return path
