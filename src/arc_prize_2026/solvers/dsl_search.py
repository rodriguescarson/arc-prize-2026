"""Enumerative DSL search baseline (CPU, no learning).

Programs are compositions of up to `depth` parameter-free transforms from a small library, with
shape parameters (scale/tile factors) inferred from the train pairs and an optional final learned
colour map. A program is accepted only if it reproduces EVERY train output exactly. Accepted
programs are ranked by length; the first two distinct test predictions become the two attempts.

This is a floor, not a contribution: it exists to anchor later deltas and to exercise the failure
diagnostics on real tasks.
"""
from __future__ import annotations

from itertools import product

import numpy as np

from ..data import Grid, Task
from ..grids import (DIHEDRAL, apply_colour_map, crop_component, crop_nonbg, downscale, gravity,
                     learn_colour_map, mirror_4, mirror_h, mirror_v, tile, to_list, to_np, upscale)

UNARY = {
    **{f"d:{k}": v for k, v in DIHEDRAL.items() if k != "id"},
    "crop_nonbg": crop_nonbg,
    "crop_largest": lambda a: crop_component(a, "largest"),
    "crop_smallest": lambda a: crop_component(a, "smallest"),
    "mirror_h": mirror_h,
    "mirror_v": mirror_v,
    "mirror_4": mirror_4,
    "grav_down": lambda a: gravity(a, "down"),
    "grav_up": lambda a: gravity(a, "up"),
    "grav_left": lambda a: gravity(a, "left"),
    "grav_right": lambda a: gravity(a, "right"),
}


def _shape_ops(task: Task) -> dict:
    """Scale/tile ops whose factors are consistent across all train pairs."""
    ops = {}
    ratios = set()
    for p in task.train:
        a, b = to_np(p["input"]), to_np(p["output"])
        ratios.add((b.shape[0] / a.shape[0], b.shape[1] / a.shape[1]))
    if len(ratios) != 1:
        return ops
    ry, rx = ratios.pop()
    if ry == rx and ry > 1 and float(ry).is_integer():
        k = int(ry)
        ops[f"upscale{k}"] = lambda a, k=k: upscale(a, k)
        ops[f"tile{k}x{k}"] = lambda a, k=k: tile(a, k, k)
    if ry > 1 and rx > 1 and float(ry).is_integer() and float(rx).is_integer() and ry != rx:
        ops[f"tile{int(ry)}x{int(rx)}"] = lambda a, ky=int(ry), kx=int(rx): tile(a, ky, kx)
    if ry == rx and ry < 1 and (1 / ry).is_integer():
        k = int(round(1 / ry))
        ops[f"downscale{k}"] = lambda a, k=k: downscale(a, k)
    return ops


def _run(program: list, a: np.ndarray, library: dict) -> np.ndarray | None:
    try:
        for name in program:
            a = library[name](a)
            if a.size == 0 or a.shape[0] > 30 or a.shape[1] > 30:
                return None
        return a
    except Exception:
        return None


def solve(task: Task, depth: int = 2, max_programs: int = 4000) -> list[list[Grid]]:
    library = {**UNARY, **_shape_ops(task)}
    names = list(library)
    train = [(to_np(p["input"]), to_np(p["output"])) for p in task.train]
    tests = [to_np(g) for g in task.test_inputs]

    accepted: list[tuple[int, list, dict | None]] = []  # (cost, program, colour_map)
    n_checked = 0
    for d in range(0, depth + 1):
        for prog in product(names, repeat=d):
            prog = list(prog)
            n_checked += 1
            if n_checked > max_programs:
                break
            outs = [_run(prog, a, library) for a, _ in train]
            if any(o is None for o in outs):
                continue
            if all(o.shape == b.shape and np.array_equal(o, b) for o, (_, b) in zip(outs, train)):
                accepted.append((d, prog, None))
                continue
            # try a learned colour map on top
            if all(o.shape == b.shape for o, (_, b) in zip(outs, train)):
                cm = learn_colour_map([(o, b) for o, (_, b) in zip(outs, train)])
                if cm is not None and any(u != v for u, v in cm.items()):
                    accepted.append((d + 1, prog, cm))
        if n_checked > max_programs:
            break

    accepted.sort(key=lambda t: t[0])
    result: list[list[Grid]] = []
    for t in tests:
        cands: list[Grid] = []
        for _, prog, cm in accepted:
            o = _run(prog, t, library)
            if o is None:
                continue
            if cm is not None:
                o = apply_colour_map(o, cm)
            g = to_list(o)
            if g not in cands:
                cands.append(g)
            if len(cands) >= 2:
                break
        if not cands:
            cands = [to_list(t)]
        result.append(cands)
    return result
