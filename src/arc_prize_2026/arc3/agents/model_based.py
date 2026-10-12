"""H1 agent: learn an object-level effect model online, plan in it toward information gain, keep the
model across levels (memory=True) or reset it at each level (memory=False)."""
from __future__ import annotations

import numpy as np
from arcengine import FrameData, GameAction, GameState

from ..effects import EffectModel
from ..goals import GoalMemory, candidate_predicates
from ..perception import Obj, ident, segment, state_key
from ..planner import adjacent_classes, plan_to_information
from .base import ACTION_BY_ID, BaseAgent


class ModelBasedAgent(BaseAgent):
    def __init__(self, game_id: str, seed: int = 0, memory: bool = True, max_depth: int = 12, max_nodes: int = 1500,
                 click_lattice: int = 8, contact: bool = True, goals: bool = True, **kwargs):
        super().__init__(game_id, seed)
        self.memory = memory
        self.contact = contact
        self.goals = goals
        self.goal_memory = GoalMemory()
        self.level_init_objs: list[Obj] | None = None
        self.level_init_grid: np.ndarray | None = None
        self.n_goal_plans = 0
        self.max_depth, self.max_nodes, self.click_lattice = max_depth, max_nodes, click_lattice
        self.model = EffectModel()
        self.tried: dict[int, set] = {}
        self.objs_cache: dict[int, tuple[list[Obj], np.ndarray]] = {}
        self.plan: list = []
        self.predicted_next: int | None = None
        self.prev: tuple[list[Obj], np.ndarray, object, object] | None = None  # objs, grid, key, ckey
        self.levels_seen = 0
        self.n_plans = 0; self.n_plan_steps = 0; self.n_replans_on_error = 0; self.n_fallback = 0
        self.pred_by_source = {"memo": [0, 0], "model": [0, 0], "unreliable": [0, 0]}
        self.row_changes = np.zeros(64, dtype=np.int32); self.row_steps = 0; self.prev_grid: np.ndarray | None = None
        self.row_px = np.zeros(64, dtype=np.int64); self.row_maxpx = np.zeros(64, dtype=np.int64); self.mover_rows = np.zeros(64, dtype=bool)
        self.volatile_rows: np.ndarray = np.zeros(64, dtype=bool)
        self.terrain_colours: set[int] = set()
        self.contacted: dict = {}  # object class -> number of steps the mover group has touched it

    def _update_volatility(self, grid: np.ndarray, after_reset: bool) -> None:
        """Two HUD detectors feed `volatile_rows`:
        (a) rows changing on >80% of effective steps (step counters, animations);
        (b) thin progress bars: rows whose changes are tiny (<= 1 px per changing step, averaged), have
            occurred on >= 4 steps, and are never rows where the learned mover group has been seen.
        Both are measured, not assumed; `stats()` reports which rows were masked."""
        if self.prev_grid is not None and not after_reset:
            d = grid != self.prev_grid
            changed_rows = d.any(axis=1)
            if changed_rows.any():
                self.row_changes += changed_rows; self.row_steps += 1
                px = d.sum(axis=1)
                self.row_px += px
                self.row_maxpx = np.maximum(self.row_maxpx, px)
            if self.row_steps >= 10:
                rate_rows = (self.row_changes / self.row_steps) > 0.8
            else:
                rate_rows = np.zeros(64, dtype=bool)
            # thin bars: every change in the row is exactly 1 px, seen >= 6 times, never a mover row, and the
            # flagged rows form bands of at most 2 adjacent rows (a 1-px sprite wandering over many rows is not a bar)
            cand = (self.row_changes >= 6) & (self.row_maxpx <= 1) & ~self.mover_rows
            bar_rows = np.zeros(64, dtype=bool)
            y = 0
            while y < 64:
                if cand[y]:
                    y2 = y
                    while y2 + 1 < 64 and cand[y2 + 1]:
                        y2 += 1
                    if y2 - y + 1 <= 2 and (y2 <= 5 or y >= 50):  # HUD bars live at the frame edges
                        bar_rows[y:y2 + 1] = True
                    y = y2 + 1
                else:
                    y += 1
            self.volatile_rows = rate_rows | bar_rows
        self.prev_grid = grid

    TERRAIN_FRAC = 0.20  # a colour covering >= 20% of the frame is terrain (background, floor): kept in the grid for
                         # blocking checks but its objects are excluded from the state key

    def perceive(self, grid: np.ndarray) -> list[Obj]:
        objs = segment(grid, drop_background=False)
        counts = np.bincount(grid.ravel(), minlength=16)
        terrain = {int(c) for c in np.where(counts >= self.TERRAIN_FRAC * grid.size)[0]}
        if not terrain:
            terrain = {int(counts.argmax())}
        self.terrain_colours = terrain
        if self.volatile_rows.any():
            objs = [o for o in objs if not self.volatile_rows[o.y0:o.y1].all()]
        return [o for o in objs if o.colour not in terrain]

    # ---- candidate actions ---------------------------------------------------------------------
    def _keys_for(self, latest: FrameData):
        legal = self.legal_actions(latest)

        def keys(objs: list[Obj]):
            out = []
            for a in legal:
                if a.is_complex():
                    seen_cls = set()
                    for o in objs:
                        cy, cx = o.centre
                        cls = ("click",) + ident(o)
                        out.append((("click",) + ident(o) + (o.y0, o.x0), cls, a, {"x": int(cx), "y": int(cy)}))
                        seen_cls.add(cls)
                    step = 64 // self.click_lattice
                    for y in range(step // 2, 64, step):
                        for x in range(step // 2, 64, step):
                            out.append((("click", "lattice", y, x), ("click", "lattice"), a, {"x": x, "y": y}))
                else:
                    out.append((a.value, a.value, a, {}))
            return out
        return keys

    # ---- main -------------------------------------------------------------------------------------
    def choose_action(self, frames: list[FrameData], latest: FrameData) -> GameAction:
        if latest.state in (GameState.NOT_PLAYED, GameState.GAME_OVER) or not latest.frame:
            self.prev = None; self.plan = []; self.predicted_next = None
            return GameAction.RESET
        grid = np.asarray(latest.frame[-1], dtype=np.int16)
        self._update_volatility(grid, after_reset=self.prev is None)
        objs = self.perceive(grid)
        early_movers = frozenset().union(*[g[0] for k in self.model.moves if (g := self.model.modal_group(k))]) if self.model.moves else frozenset()
        if early_movers:
            members = [o for o in objs if ident(o) in early_movers]
            # decorations (direction markers, eyes) fully inside a mover member's bbox are part of the mover: drop them
            objs = [o for o in objs if o in members or not any(m.y0 <= o.y0 and o.y1 <= m.y1 and m.x0 <= o.x0 and o.x1 <= m.x1 for m in members)]
        sk = state_key(objs)
        if self.level_init_objs is None:
            self.level_init_objs = objs; self.level_init_grid = grid
        self.objs_cache[sk] = (objs, grid)

        # level transition bookkeeping
        if latest.levels_completed > self.levels_seen:
            if self.goals and self.prev is not None and self.level_init_grid is not None:
                mover = frozenset().union(*[g[0] for k in self.model.moves if (g := self.model.modal_group(k))]) if self.model.moves else frozenset()
                # positive example = the state the winning action produced in the model (the pre-transition
                # frame does not yet show the mover on the target); negative = level start, both re-perceived
                # under the current HUD/terrain mask so stale bar objects cannot become "goals"
                p_objs, p_grid, p_key, p_ckey = self.prev
                pre = self.perceive(p_grid)
                post, _src = self.model.predict(pre, p_grid, p_ckey)
                if post is None or state_key(post) == state_key(pre):
                    post = self.model.predict_unchecked(pre, p_ckey)
                positive = post if post is not None else pre
                init = self.perceive(self.level_init_grid)
                self.goal_memory.update(candidate_predicates(init, positive, mover))
            self.level_init_objs = objs; self.level_init_grid = grid
            self.levels_seen = latest.levels_completed
            self.tried = {}; self.plan = []; self.predicted_next = None; self.contacted = {}
            if not self.memory:
                self.model = EffectModel(); self.objs_cache = {sk: (objs, grid)}
            self.prev = None

        # learn from the last transition
        if self.prev is not None:
            p_objs, p_grid, p_key, p_ckey = self.prev
            self.model.observe(p_objs, p_grid, p_ckey, objs)
            self.model.transitions[(state_key(p_objs), p_key)] = sk
            if self.predicted_next is not None:
                src = self._pred_src
                self.pred_by_source[src][0] += 1
                self.pred_by_source[src][1] += int(self.predicted_next == sk)
                self.model.record_prediction(self.predicted_next, sk, p_ckey if src in ("model", "unreliable") else None)
                if self.predicted_next != sk and src != "unreliable":
                    self.plan = []; self.n_replans_on_error += 1
            self.predicted_next = None

        mover_idents = frozenset().union(*[g[0] for k in self.model.moves if (g := self.model.modal_group(k))]) if self.model.moves else frozenset()
        if mover_idents:
            members = [o for o in objs if ident(o) in mover_idents]
            for m in members:
                self.mover_rows[m.y0:m.y1] = True
            for c in adjacent_classes(members, objs):
                self.contacted[c] = self.contacted.get(c, 0) + 1
            for o in objs:
                self.contacted.setdefault(ident(o), 0)
        keys_for = self._keys_for(latest)
        if not self.plan:
            goal_test = None
            if self.goals:
                active = self.goal_memory.active(objs)
                if active:
                    mi = mover_idents
                    goal_test = lambda o, _a=active, _m=mi: any(p.holds(o, _m) for p in _a)
            path, final = plan_to_information(self.model, objs, grid, keys_for, self.tried, self.objs_cache,
                                              self.max_depth, self.max_nodes, mover_idents or None,
                                              self.contacted if (mover_idents and self.contact) else None, goal_test)
            if path is not None:
                if final is None:
                    self.n_goal_plans += 1
                self.plan = list(path) + ([final[:1] + (final[2], final[3])] if final else [])
                # normalise entries to (key, action, data)
                self.plan = [(e[0], e[-2], e[-1]) for e in self.plan]
                self.n_plans += 1
        if self.plan:
            key, action, data = self.plan.pop(0)
            self.n_plan_steps += 1
        else:
            self.n_fallback += 1
            cands = keys_for(objs)
            untried = [c for c in cands if c[0] not in self.tried.get(sk, set())]
            pool = untried or cands
            key, ckey, action, data = self.rng.choice(pool)
        ckey = key if not isinstance(key, tuple) else (("click",) + tuple(key[1:4]) if key[1] != "lattice" else ("click", "lattice"))
        self.tried.setdefault(sk, set()).add(key)
        # predict for accuracy accounting
        nk = self.model.next_key(sk, key)
        if nk is not None:
            self.predicted_next, self._pred_src = nk, "memo"
        else:
            pred, src = self.model.predict(objs, grid, ckey)
            if pred is not None:
                self.predicted_next, self._pred_src = state_key(pred), src
        self.prev = (objs, grid, key, ckey)
        if action.is_complex():
            action.set_data(data)
        return action

    def stats(self) -> dict:
        return {"memory": self.memory, "contact": self.contact, "goals": self.goals, "plans": self.n_plans, "goal_plans": self.n_goal_plans,
                "surviving_goals": sorted(map(str, self.goal_memory.surviving)) if self.goal_memory.surviving else None, "plan_steps": self.n_plan_steps,
                "replans_on_error": self.n_replans_on_error, "fallback_steps": self.n_fallback,
                "pred_total": self.model.n_pred, "pred_acc": None if self.model.accuracy is None else round(self.model.accuracy, 3),
                "pred_by_source": {k: (v[0], round(v[1] / v[0], 3) if v[0] else None) for k, v in self.pred_by_source.items()},
                "movers": {str(k): [sorted(map(str, g[0])), list(g[1])] for k in self.model.moves if (g := self.model.modal_group(k))},
                "volatile_rows": [int(i) for i in np.where(self.volatile_rows)[0]], "terrain_colours": sorted(self.terrain_colours),
                "known_noops": [str(k) for k in self.model.effects if self.model.is_known_noop(k)],
                "key_reliability": {str(k): [len(v), round(sum(v) / len(v), 2)] for k, v in self.model.key_pred.items() if len(v)}}
