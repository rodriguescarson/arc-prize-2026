"""Frame -> objects -> abstract state key.

An ARC-AGI-3 frame is a 64x64 grid of colours 0..15. We segment it into same-colour 4-connected
components. The background is the largest component (by area). Objects carry colour, bbox, area and a
shape hash (mask relative to its bbox), so a moved object keeps its identity and a recoloured object
keeps its shape. The abstract state key is the sorted tuple of (colour, y0, x0, shape_hash) for all
non-background objects; two frames with the same key are the same abstract state.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

H = W = 64


@dataclass(frozen=True)
class Obj:
    colour: int
    y0: int
    x0: int
    y1: int  # exclusive
    x1: int
    area: int
    shape: int  # hash of the boolean mask inside the bbox
    mask: bytes = field(default=b"", compare=False, hash=False, repr=False)  # packed bool mask, for rendering

    @property
    def h(self) -> int:
        return self.y1 - self.y0

    @property
    def w(self) -> int:
        return self.x1 - self.x0

    @property
    def centre(self) -> tuple[int, int]:
        return ((self.y0 + self.y1 - 1) // 2, (self.x0 + self.x1 - 1) // 2)


def label_components(grid: np.ndarray) -> tuple[np.ndarray, int]:
    """4-connected same-colour labelling. Returns (labels, n) with labels in 1..n."""
    h, w = grid.shape
    labels = np.zeros((h, w), dtype=np.int32)
    n = 0
    for y in range(h):
        row = grid[y]
        for x in range(w):
            if labels[y, x]:
                continue
            n += 1
            c = row[x]
            stack = [(y, x)]
            labels[y, x] = n
            while stack:
                cy, cx = stack.pop()
                if cy > 0 and not labels[cy - 1, cx] and grid[cy - 1, cx] == c:
                    labels[cy - 1, cx] = n; stack.append((cy - 1, cx))
                if cy < h - 1 and not labels[cy + 1, cx] and grid[cy + 1, cx] == c:
                    labels[cy + 1, cx] = n; stack.append((cy + 1, cx))
                if cx > 0 and not labels[cy, cx - 1] and grid[cy, cx - 1] == c:
                    labels[cy, cx - 1] = n; stack.append((cy, cx - 1))
                if cx < w - 1 and not labels[cy, cx + 1] and grid[cy, cx + 1] == c:
                    labels[cy, cx + 1] = n; stack.append((cy, cx + 1))
    return labels, n


def segment(grid: np.ndarray, drop_background: bool = True) -> list[Obj]:
    grid = np.asarray(grid, dtype=np.int16)
    labels, n = label_components(grid)
    objs = []
    flat = labels.ravel()
    order = np.argsort(flat, kind="stable")
    sorted_labels = flat[order]
    bounds = np.searchsorted(sorted_labels, np.arange(1, n + 2))
    ys_all, xs_all = np.divmod(order, grid.shape[1])
    for k in range(n):
        idx = slice(bounds[k], bounds[k + 1])
        ys, xs = ys_all[idx], xs_all[idx]
        y0, y1, x0, x1 = int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1
        mask = np.zeros((y1 - y0, x1 - x0), dtype=bool)
        mask[ys - y0, xs - x0] = True
        objs.append(Obj(int(grid[ys[0], xs[0]]), y0, x0, y1, x1, int(len(ys)), hash(mask.tobytes()) ^ (mask.shape[0] << 20) ^ mask.shape[1], mask.tobytes()))
    if drop_background and objs:
        bg = max(objs, key=lambda o: o.area)
        objs = [o for o in objs if o is not bg]
    objs.sort(key=lambda o: (o.y0, o.x0, o.colour, o.shape))
    return objs


def ident(o: Obj) -> tuple[int, int, int]:
    """Object class used for learning effects: colour and bbox size (robust to small occlusions)."""
    return (o.colour, o.h, o.w)


def state_key(objs: list[Obj]) -> int:
    """Identity by colour + bbox; a hole carved into a floor by a sprite does not change the floor."""
    return hash(tuple((o.colour, o.y0, o.x0, o.y1, o.x1) for o in objs))


def frame_key(grid) -> int:
    return hash(np.asarray(grid, dtype=np.int8).tobytes())


def diff(before: list[Obj], after: list[Obj], max_disp: int = 32) -> dict:
    """Object-level diff. same = equal colour+bbox; moved = same class (colour,h,w), nearest within max_disp;
    recoloured = equal bbox, different colour; the rest appeared/vanished."""
    b_left, a_left = list(before), list(after)
    same, moved_, recol = [], [], []
    a_index = {(p.colour, p.y0, p.x0, p.y1, p.x1): p for p in a_left}
    for o in list(b_left):
        p = a_index.get((o.colour, o.y0, o.x0, o.y1, o.x1))
        if p is not None and p in a_left:
            same.append(o); b_left.remove(o); a_left.remove(p)
    for o in list(b_left):
        best = None
        for p in a_left:
            if ident(o) == ident(p):
                d = abs(p.y0 - o.y0) + abs(p.x0 - o.x0)
                if d <= max_disp and (best is None or d < best[0]):
                    best = (d, p)
        if best is not None:
            p = best[1]; moved_.append((o, p, (p.y0 - o.y0, p.x0 - o.x0))); b_left.remove(o); a_left.remove(p)
    for o in list(b_left):
        for p in list(a_left):
            if (o.y0, o.x0, o.y1, o.x1) == (p.y0, p.x0, p.y1, p.x1):
                recol.append((o, p)); b_left.remove(o); a_left.remove(p); break
    return {"same": same, "moved": moved_, "recoloured": recol, "vanished": b_left, "appeared": a_left}

def moved(o: Obj, dy: int, dx: int) -> Obj:
    return Obj(o.colour, o.y0 + dy, o.x0 + dx, o.y1 + dy, o.x1 + dx, o.area, o.shape, o.mask)


def render_move(grid: np.ndarray, o: Obj, new: Obj, bg: int) -> np.ndarray:
    """Return a copy of grid with object o erased (filled with bg) and redrawn at new's position."""
    g = grid.copy()
    m = np.frombuffer(o.mask, dtype=bool).reshape(o.h, o.w) if o.mask else np.ones((o.h, o.w), dtype=bool)
    sub = g[o.y0:o.y1, o.x0:o.x1]; sub[m] = bg
    H, W = g.shape
    if 0 <= new.y0 and new.y1 <= H and 0 <= new.x0 and new.x1 <= W:
        sub2 = g[new.y0:new.y1, new.x0:new.x1]; sub2[m] = o.colour
    return g


def background_colour(grid: np.ndarray) -> int:
    vals, counts = np.unique(grid, return_counts=True)
    return int(vals[counts.argmax()])
