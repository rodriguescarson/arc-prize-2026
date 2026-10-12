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
from .perception import Obj, background_colour, ident, moved, render_move, state_key


def adjacent_classes(members: list[Obj], objs: list[Obj]) -> set:
    """Classes of non-member objects whose bbox touches (8-neighbourhood) any member's bbox."""
    out = set()
    for m in members:
        for o in objs:
            if o in members:
                continue
            if o.y0 <= m.y1 and m.y0 <= o.y1 and o.x0 <= m.x1 and m.x0 <= o.x1:
                out.add(ident(o))
    return out


def plan_to_information(model: EffectModel, objs: list[Obj], grid: np.ndarray, keys_for, tried: dict[int, set],
                        objs_cache: dict[int, tuple[list[Obj], np.ndarray]], max_depth: int = 12, max_nodes: int = 1500,
                        mover_idents: frozenset | None = None, contacted: dict | None = None, goal_test=None):
    """keys_for(objs) -> list of (key, class_key, action, data). Returns (path_keys, final_key) or (None, None).

    Target priority: (1) a reachable state where the mover group touches an object class contacted fewer
    times than any other (contact-driven curiosity), taking an untried key there; (2) the nearest state with
    an untried, non-no-op key, preferring keys with the fewest observations."""
    bg = background_colour(grid)
    start = state_key(objs)
    objs_cache.setdefault(start, (objs, grid))
    q = deque([(start, [])])
    seen = {start}
    nodes = 0
    best = None
    contact_best = None  # (contact_count, depth, path, key)
    min_contact = min(contacted.values()) if contacted else 0
    while q and nodes < max_nodes:
        sk, path = q.popleft()
        nodes += 1
        if sk not in objs_cache:
            continue
        o_list, g = objs_cache[sk]
        if goal_test is not None and path and goal_test(o_list):
            return path, None  # goal state reached in the model: execute the path, no exploratory key needed
        cands = keys_for(o_list)
        untried = [c for c in cands if c[0] not in tried.get(sk, set()) and not model.is_known_noop(c[1])]
        if untried:
            untried.sort(key=lambda c: (model.n_obs[c[1]], ))
        # contact-driven target: mover touches a rarely-contacted class
        if mover_idents and contacted is not None and untried:
            members = [o for o in o_list if ident(o) in mover_idents]
            if members:
                adj = adjacent_classes(members, o_list)
                if adj:
                    cc = min(contacted.get(c, 0) for c in adj)
                    if contact_best is None or cc < contact_best[0]:
                        contact_best = (cc, len(path), path, untried[0])
                        if cc <= min_contact and path:
                            return path, untried[0]
        if untried and path and contact_best is None and best is None:
            best = (path, untried[0])
        if untried and not path and best is None:
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
            if pred is None or src == "unreliable":
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
    if contact_best is not None and contact_best[2]:
        return contact_best[2], contact_best[3]
    return best if best else (None, None)
