"""Pipeline-validation baseline. Expected score ~0. Exists to prove the end-to-end path works.

attempt_1: the test input unchanged (identity).
attempt_2: if every train output is the same grid, that grid; else the train output whose shape
           is most common, filled with the most common colour in train outputs.
"""
from __future__ import annotations

from collections import Counter

from ..data import Grid, Task


def _most_common_output_shape(task: Task) -> tuple[int, int]:
    shapes = Counter((len(p["output"]), len(p["output"][0])) for p in task.train)
    return shapes.most_common(1)[0][0]


def _most_common_colour(task: Task) -> int:
    c = Counter(v for p in task.train for row in p["output"] for v in row)
    return c.most_common(1)[0][0]


def solve(task: Task) -> list[list[Grid]]:
    outs = [p["output"] for p in task.train]
    constant = outs[0] if all(o == outs[0] for o in outs) else None
    h, w = _most_common_output_shape(task)
    fill = _most_common_colour(task)
    result = []
    for ti in task.test_inputs:
        a1 = [row[:] for row in ti]
        a2 = constant if constant is not None else [[fill] * w for _ in range(h)]
        result.append([a1, a2])
    return result
