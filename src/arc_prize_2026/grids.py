"""Grid primitives on numpy arrays. All functions are pure and return new arrays."""
from __future__ import annotations

from collections import Counter

import numpy as np

A = np.ndarray


def to_np(g) -> A:
    return np.asarray(g, dtype=np.int8)


def to_list(a: A) -> list[list[int]]:
    return [[int(v) for v in row] for row in a]


def background(a: A) -> int:
    vals, counts = np.unique(a, return_counts=True)
    return int(vals[counts.argmax()])


# --- dihedral group -------------------------------------------------------------------------
DIHEDRAL = {
    "id": lambda a: a,
    "rot90": lambda a: np.rot90(a, 1),
    "rot180": lambda a: np.rot90(a, 2),
    "rot270": lambda a: np.rot90(a, 3),
    "flipud": np.flipud,
    "fliplr": np.fliplr,
    "transpose": lambda a: a.T,
    "antitranspose": lambda a: np.rot90(a, 2).T,
}
DIHEDRAL_INVERSE = {
    "id": "id", "rot90": "rot270", "rot180": "rot180", "rot270": "rot90",
    "flipud": "flipud", "fliplr": "fliplr", "transpose": "transpose", "antitranspose": "antitranspose",
}


# --- shape-changing ops ----------------------------------------------------------------------
def crop_nonbg(a: A) -> A:
    bg = background(a)
    ys, xs = np.where(a != bg)
    if len(ys) == 0:
        return a
    return a[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1]


def upscale(a: A, k: int) -> A:
    return np.kron(a, np.ones((k, k), dtype=a.dtype))


def downscale(a: A, k: int) -> A:
    h, w = a.shape
    if h % k or w % k:
        raise ValueError("not divisible")
    return a[::k, ::k]


def tile(a: A, ky: int, kx: int) -> A:
    return np.tile(a, (ky, kx))


def mirror_h(a: A) -> A:  # [a | fliplr(a)]
    return np.hstack([a, np.fliplr(a)])


def mirror_v(a: A) -> A:
    return np.vstack([a, np.flipud(a)])


def mirror_4(a: A) -> A:
    top = np.hstack([a, np.fliplr(a)])
    return np.vstack([top, np.flipud(top)])


def gravity(a: A, direction: str) -> A:
    """Push non-background cells to one side, column-wise (down/up) or row-wise (left/right)."""
    bg = background(a)
    out = np.full_like(a, bg)
    if direction in ("down", "up"):
        for x in range(a.shape[1]):
            col = a[:, x]
            vals = col[col != bg]
            if direction == "down":
                out[a.shape[0] - len(vals):, x] = vals
            else:
                out[: len(vals), x] = vals
    else:
        for y in range(a.shape[0]):
            row = a[y]
            vals = row[row != bg]
            if direction == "right":
                out[y, a.shape[1] - len(vals):] = vals
            else:
                out[y, : len(vals)] = vals
    return out


# --- connected components ---------------------------------------------------------------------
def components(a: A, bg: int | None = None, diag: bool = False) -> list[dict]:
    """Return connected components of non-bg cells (same-colour adjacency)."""
    if bg is None:
        bg = background(a)
    h, w = a.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    nbrs = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (1, -1), (-1, 1), (-1, -1)] if diag else [])
    for y in range(h):
        for x in range(w):
            if seen[y, x] or a[y, x] == bg:
                continue
            colour = a[y, x]
            stack = [(y, x)]
            seen[y, x] = True
            cells = []
            while stack:
                cy, cx = stack.pop()
                cells.append((cy, cx))
                for dy, dx in nbrs:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and a[ny, nx] == colour:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            ys = [c[0] for c in cells]; xs = [c[1] for c in cells]
            comps.append({"colour": int(colour), "cells": cells, "size": len(cells),
                          "bbox": (min(ys), min(xs), max(ys) + 1, max(xs) + 1)})
    return comps


def crop_component(a: A, which: str) -> A:
    comps = components(a)
    if not comps:
        return a
    key = {"largest": lambda c: c["size"], "smallest": lambda c: -c["size"]}[which]
    c = max(comps, key=key)
    y0, x0, y1, x1 = c["bbox"]
    return a[y0:y1, x0:x1]


# --- colour maps ------------------------------------------------------------------------------
def learn_colour_map(pairs: list[tuple[A, A]]) -> dict[int, int] | None:
    """Consistent cellwise colour substitution across same-shape pairs, or None."""
    m: dict[int, int] = {}
    for a, b in pairs:
        if a.shape != b.shape:
            return None
        for u, v in zip(a.ravel(), b.ravel()):
            u, v = int(u), int(v)
            if m.setdefault(u, v) != v:
                return None
    return m


def apply_colour_map(a: A, m: dict[int, int]) -> A:
    out = a.copy()
    for u, v in m.items():
        out[a == u] = v
    return out
