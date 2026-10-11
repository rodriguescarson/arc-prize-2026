"""Online object-level action-effect model.

Observations are (objects_before, action_key, objects_after). We learn, per action key:
  * `moves[key]`      : Counter of (colour, shape) -> Counter of displacement (dy, dx) — which object class
                        moves and by how much when this action is taken (per-object deltas from `diff`).
  * `blocked[key]`    : Counter of colours seen immediately ahead (in the learned move direction) of the
                        moving object on steps where it did NOT move (no-op for that object).
  * `passable[key]`   : Counter of colours ahead on steps where it DID move.
  * `transitions`     : exact memo (state_key, action_key) -> next state_key (deterministic games).
  * `effects[key]`    : Counter of coarse effect signatures (moved/recoloured/appeared/vanished counts),
                        used to decide whether an action does anything at all in general.
`predict(objs, key)` returns the predicted object list (or None if unknown), by applying the modal
displacement to the modal moving class when the cells ahead are background-or-passable; it returns the
same objects (no-op) when the cells ahead are in the blocked set. Only movement effects are predicted
generatively; recolour/appear/vanish are memorised through `transitions` and otherwise count as unknown.
"""
from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np

from .perception import Obj, diff, ident, moved as _moved, state_key

Key = object  # action key: int action id, or ("click", y//4, x//4)


def _ahead_cells(o: Obj, dy: int, dx: int, grid: np.ndarray, members: list[Obj] | None = None) -> list[int]:
    """Colours of every cell the object sweeps through when displaced by (dy, dx) in unit steps,
    excluding cells currently occupied by any member of its rigid group. [-1] marks the world edge."""
    H, W = grid.shape
    occupied = members or [o]
    steps = max(abs(dy), abs(dx))
    if steps == 0:
        return []
    sy, sx = (dy > 0) - (dy < 0), (dx > 0) - (dx < 0)
    cells: list[int] = []
    for k in range(1, steps + 1):
        ty0, tx0 = o.y0 + sy * k, o.x0 + sx * k
        ty1, tx1 = ty0 + o.h, tx0 + o.w
        if ty0 < 0 or tx0 < 0 or ty1 > H or tx1 > W:
            return [-1]
        for y in range(ty0, ty1):
            for x in range(tx0, tx1):
                if any(m.y0 <= y < m.y1 and m.x0 <= x < m.x1 for m in occupied):
                    continue
                cells.append(int(grid[y, x]))
    return cells


class EffectModel:
    def __init__(self) -> None:
        self.moves: dict[Key, Counter] = defaultdict(Counter)          # key -> Counter[((colour, shape), (dy, dx))]
        self.blocked: dict[Key, Counter] = defaultdict(Counter)
        self.passable: dict[Key, Counter] = defaultdict(Counter)
        self.transitions: dict[tuple[int, Key], int] = {}
        self.effects: dict[Key, Counter] = defaultdict(Counter)
        self.n_obs: Counter = Counter()
        self.n_pred = 0
        self.n_pred_correct = 0
        self.key_pred: dict[Key, list[int]] = defaultdict(lambda: [0, 0])  # key -> [n, correct] for generative predictions
        self.min_reliability = 0.5

    # ---- learning -------------------------------------------------------------------------------
    def observe(self, before: list[Obj], grid_before: np.ndarray, key: Key, after: list[Obj]) -> dict:
        d = diff(before, after)
        sk_b, sk_a = state_key(before), state_key(after)
        self.transitions[(sk_b, key)] = sk_a
        self.n_obs[key] += 1
        sig = (len(d["moved"]), len(d["recoloured"]), len(d["appeared"]), len(d["vanished"]))
        self.effects[key][sig] += 1
        for o, p, delta in d["moved"]:
            self.moves[key][(ident(o), delta)] += 1
            self.passable[key].update(_ahead_cells(o, *delta, grid_before))
        if not d["moved"] and sig == (0, 0, 0, 0):
            # nothing moved: if we know what this key usually moves, record what was ahead of it
            group = self.modal_group(key)
            if group is not None:
                idents, (dy, dx) = group
                members = [o for o in before if ident(o) in idents]
                for o in members:
                    self.blocked[key].update(_ahead_cells(o, dy, dx, grid_before, members))
        return d

    def modal_group(self, key: Key):
        """(set of idents that move together, modal displacement) or None."""
        if not self.moves[key]:
            return None
        by_delta = Counter()
        for (cls, delta), n in self.moves[key].items():
            by_delta[delta] += n
        delta, _ = by_delta.most_common(1)[0]
        counts = {cls: n for (cls, d), n in self.moves[key].items() if d == delta}
        top = max(counts.values())
        idents = frozenset(cls for cls, n in counts.items() if n >= 0.5 * top)
        return idents, delta

    def is_known_noop(self, key: Key) -> bool:
        c = self.effects[key]
        return sum(c.values()) >= 3 and c[(0, 0, 0, 0)] / sum(c.values()) > 0.9

    # ---- prediction -----------------------------------------------------------------------------
    def predict(self, objs: list[Obj], grid: np.ndarray, key: Key) -> tuple[list[Obj] | None, str]:
        """Return (predicted objects or None, source in {memo, model, unknown})."""
        sk = state_key(objs)
        if (sk, key) in self.transitions:
            return None, "memo"
        group = self.modal_group(key)
        if group is None:
            return None, "unknown"
        n, c = self.key_pred[key]
        if n >= 10 and c / n < self.min_reliability:
            return None, "unreliable"  # this key's mechanic is not a rigid move; memo-only from here on
        idents, (dy, dx) = group
        members = [o for o in objs if ident(o) in idents]
        if not members:
            return None, "unknown"
        bl, pa = self.blocked[key], self.passable[key]
        blocked = False
        for o in members:
            for c in _ahead_cells(o, dy, dx, grid, members):
                if c == -1 or (bl[c] > 0 and bl[c] >= pa[c]):
                    blocked = True; break
            if blocked:
                break
        if blocked:
            return list(objs), "model"
        out = [_moved(o, dy, dx) if ident(o) in idents else o for o in objs]
        return out, "model"

    def next_key(self, sk: int, key: Key) -> int | None:
        return self.transitions.get((sk, key))

    def record_prediction(self, predicted_key: int | None, observed_key: int, key: Key | None = None) -> None:
        if predicted_key is None:
            return
        self.n_pred += 1
        ok = int(predicted_key == observed_key)
        self.n_pred_correct += ok
        if key is not None:
            self.key_pred[key][0] += 1; self.key_pred[key][1] += ok

    @property
    def accuracy(self) -> float | None:
        return self.n_pred_correct / self.n_pred if self.n_pred else None
