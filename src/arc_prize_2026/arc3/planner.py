"""Breadth-first planning in the learned effect model.

Nodes carry (state_key, objs, grid). Edges: for every candidate action key, the model predicts the next
objects (memo edges are followed by key only, which is enough to recognise known states but not to
expand them further unless we also saw their objects; we keep an objs cache per state key for that).
Target: the nearest state holding an untried (state, key) pair whose key class is not a known no-op.
Returns the action-key path to that state plus the exploratory key to take there.
"""
from __future__ import annotations

from collections import deque

import numpy as np

from .effects import EffectModel
from .perception import Obj, background_colour, moved, render_move, state_key


def plan_to_information(model: EffectModel, objs: list[Obj], grid: np.ndarray, keys_for, tried: dict[int, set],
                        objs_cache: dict[int, tuple[list[Obj], np.ndarray]], max_depth: int = 12, max_nodes: int = 1500):
    """keys_for(objs) -> list of (key, class_key, action, data). Returns (path_keys, final_key) or (None, None)."""
    bg = background_colour(grid)
    start = state_key(objs)
    objs_cache.setdefault(start, (objs, grid))
    q = deque([(start, [])])
    seen = {start}
    nodes = 0
    best = None
    while q and nodes < max_nodes:
        sk, path = q.popleft()
        nodes += 1
        if sk not in objs_cache:
            continue
        o_list, g = objs_cache[sk]
        cands = keys_for(o_list)
        # exploratory keys available here?
        untried = [c for c in cands if c[0] not in tried.get(sk, set()) and not model.is_known_noop(c[1])]
        if untried and path:  # don't count the start node unless nothing else exists
            untried.sort(key=lambda c: (model.n_obs[c[1]], ))
            return path, untried[0]
        if untried and not path and best is None:
            untried.sort(key=lambda c: (model.n_obs[c[1]], ))
            best = ([], untried[0])
        if len(path) >= max_depth:
            continue
        for key, ckey, action, data in cands:
            nk = model.next_key(sk, key)
            if nk is not None:
                if nk not in seen:
                    seen.add(nk); q.append((nk, path + [(key, action, data)]))
                continue
            pred, src = model.predict(o_list, g, ckey)
            if pred is None:
                continue
            nk = state_key(pred)
            if nk == sk or nk in seen:
                continue
            # render the predicted grid for the moved objects
            g2 = g
            for a, b in zip(o_list, pred):
                if (a.y0, a.x0) != (b.y0, b.x0):
                    g2 = render_move(g2, a, b, bg)
            objs_cache.setdefault(nk, (pred, g2))
            seen.add(nk); q.append((nk, path + [(key, action, data)]))
    return best if best else (None, None)
