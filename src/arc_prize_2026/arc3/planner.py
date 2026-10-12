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

from .effects import DEATH, EffectModel
from .perception import Obj, background_colour, ident, moved, render_move, state_key


def _eq_key(o: Obj) -> tuple:
    """The tuple the frozen dataclass compares on (mask is compare=False), so set membership == `o in list`."""
    return (o.colour, o.y0, o.x0, o.y1, o.x1, o.area, o.shape)


def adjacent_classes(members: list[Obj], objs: list[Obj]) -> set:
    """Classes of non-member objects whose bbox touches (8-neighbourhood) any member's bbox.

    Vectorised: the pairwise bbox test is an (M x N) boolean matrix; membership uses the dataclass equality
    tuple. Same result as the former double loop, which was quadratic in Python and dominated bp35."""
    if not members or not objs:
        return set()
    mem = {_eq_key(m) for m in members}
    others = [o for o in objs if _eq_key(o) not in mem]
    if not others:
        return set()
    mb = np.array([(m.y0, m.x0, m.y1, m.x1) for m in members], dtype=np.int32)
    ob = np.array([(o.y0, o.x0, o.y1, o.x1) for o in others], dtype=np.int32)
    touch = ((ob[None, :, 0] <= mb[:, None, 2]) & (mb[:, None, 0] <= ob[None, :, 2])
             & (ob[None, :, 1] <= mb[:, None, 3]) & (mb[:, None, 1] <= ob[None, :, 3]))
    hit = touch.any(axis=0)
    return {ident(o) for o, h in zip(others, hit) if h}


def plan_to_information(model: EffectModel, objs: list[Obj], grid: np.ndarray, keys_for, tried: dict[int, set],
                        objs_cache: dict[int, tuple[list[Obj], np.ndarray]], max_depth: int = 12, max_nodes: int = 1500,
                        mover_idents: frozenset | None = None, contacted: dict | None = None, goal_test=None,
                        click_model: bool = False, adj_cache: dict | None = None):
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
    pred_cache: dict[tuple, tuple] = {}
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
        cands = keys_for(o_list, len(path))
        untried = [c for c in cands if c[0] not in tried.get(sk, set()) and not model.is_known_noop(c[1]) and not model.is_deadly(sk, c[0])]
        if untried:
            untried.sort(key=lambda c: (model.n_obs[c[1]], ))
        # contact-driven target: mover touches a rarely-contacted class
        if mover_idents and contacted is not None and untried:
            members = [o for o in o_list if ident(o) in mover_idents]
            if members:
                ck = (sk, mover_idents)
                if adj_cache is not None and ck in adj_cache:
                    adj = adj_cache[ck]
                else:
                    adj = adjacent_classes(members, o_list)
                    if adj_cache is not None:
                        adj_cache[ck] = adj
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
            if nk == DEATH:
                continue
            if nk is not None:
                if nk not in seen:
                    seen.add(nk); q.append((nk, path + [(key, action, data)]))
                continue
            ck = (sk, key)
            if ck in pred_cache:
                pred, src = pred_cache[ck]
            elif click_model and isinstance(key, tuple) and key[0] == "click" and key[1] != "lattice":
                clicked = next((o for o in o_list if (o.colour, o.h, o.w, o.y0, o.x0) == (key[1], key[2], key[3], key[4], key[5])), None)
                pred, src = model.predict_click(o_list, ckey, clicked) if clicked is not None else (None, "unknown")
                pred_cache[ck] = (pred, src)
            else:
                pred, src = model.predict(o_list, g, ckey)
                pred_cache[ck] = (pred, src)
            if pred is None or src == "unreliable":
                continue
            nk = state_key(pred)
            if nk == sk or nk in seen:
                continue
            # render the predicted grid: moved objects for movement predictions; recolour/erase for clicks
            g2 = g
            if len(pred) == len(o_list):
                for a, b in zip(o_list, pred):
                    if (a.y0, a.x0) != (b.y0, b.x0):
                        g2 = render_move(g2, a, b, bg)
                    elif a.colour != b.colour:
                        g2 = g2.copy(); sub = g2[a.y0:a.y1, a.x0:a.x1]; m = np.frombuffer(a.mask, dtype=bool).reshape(a.h, a.w) if a.mask else np.ones((a.h, a.w), bool); sub[m] = b.colour
            else:
                g2 = g2.copy()
                gone = [a for a in o_list if a not in pred]
                for a in gone:
                    sub = g2[a.y0:a.y1, a.x0:a.x1]; m = np.frombuffer(a.mask, dtype=bool).reshape(a.h, a.w) if a.mask else np.ones((a.h, a.w), bool); sub[m] = bg
            objs_cache.setdefault(nk, (pred, g2))
            seen.add(nk); q.append((nk, path + [(key, action, data)]))
    if contact_best is not None and contact_best[2]:
        return contact_best[2], contact_best[3]
    return best if best else (None, None)
