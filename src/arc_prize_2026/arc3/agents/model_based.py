"""H1 agent: learn an object-level effect model online, plan in it toward information gain, keep the
model across levels (memory=True) or reset it at each level (memory=False)."""
from __future__ import annotations

import numpy as np
from arcengine import FrameData, GameAction, GameState

from ..effects import EffectModel
from ..perception import Obj, ident, segment, state_key
from ..planner import plan_to_information
from .base import ACTION_BY_ID, BaseAgent


class ModelBasedAgent(BaseAgent):
    def __init__(self, game_id: str, seed: int = 0, memory: bool = True, max_depth: int = 12, max_nodes: int = 1500,
                 click_lattice: int = 8, **kwargs):
        super().__init__(game_id, seed)
        self.memory = memory
        self.max_depth, self.max_nodes, self.click_lattice = max_depth, max_nodes, click_lattice
        self.model = EffectModel()
        self.tried: dict[int, set] = {}
        self.objs_cache: dict[int, tuple[list[Obj], np.ndarray]] = {}
        self.plan: list = []
        self.predicted_next: int | None = None
        self.prev: tuple[list[Obj], np.ndarray, object, object] | None = None  # objs, grid, key, ckey
        self.levels_seen = 0
        self.n_plans = 0; self.n_plan_steps = 0; self.n_replans_on_error = 0; self.n_fallback = 0
        self.pred_by_source = {"memo": [0, 0], "model": [0, 0]}
        self.row_changes = np.zeros(64, dtype=np.int32); self.row_steps = 0; self.prev_grid: np.ndarray | None = None
        self.volatile_rows: np.ndarray = np.zeros(64, dtype=bool)

    def _update_volatility(self, grid: np.ndarray, after_reset: bool) -> None:
        if self.prev_grid is not None and not after_reset:
            self.row_changes += (grid != self.prev_grid).any(axis=1); self.row_steps += 1
            if self.row_steps >= 20:
                self.volatile_rows = (self.row_changes / self.row_steps) > 0.8
        self.prev_grid = grid

    def perceive(self, grid: np.ndarray) -> list[Obj]:
        objs = segment(grid)
        if self.volatile_rows.any():
            objs = [o for o in objs if not self.volatile_rows[o.y0:o.y1].all()]
        return objs

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
        sk = state_key(objs)
        self.objs_cache[sk] = (objs, grid)

        # level transition bookkeeping
        if latest.levels_completed > self.levels_seen:
            self.levels_seen = latest.levels_completed
            self.tried = {}; self.plan = []; self.predicted_next = None
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
                self.model.record_prediction(self.predicted_next, sk)
                if self.predicted_next != sk:
                    self.plan = []; self.n_replans_on_error += 1
            self.predicted_next = None

        keys_for = self._keys_for(latest)
        if not self.plan:
            path, final = plan_to_information(self.model, objs, grid, keys_for, self.tried, self.objs_cache,
                                              self.max_depth, self.max_nodes)
            if path is not None:
                self.plan = list(path) + [final[:1] + (final[2], final[3])] if final else list(path)
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
                self.predicted_next, self._pred_src = state_key(pred), "model"
        self.prev = (objs, grid, key, ckey)
        if action.is_complex():
            action.set_data(data)
        return action

    def stats(self) -> dict:
        return {"memory": self.memory, "plans": self.n_plans, "plan_steps": self.n_plan_steps,
                "replans_on_error": self.n_replans_on_error, "fallback_steps": self.n_fallback,
                "pred_total": self.model.n_pred, "pred_acc": None if self.model.accuracy is None else round(self.model.accuracy, 3),
                "pred_by_source": {k: (v[0], round(v[1] / v[0], 3) if v[0] else None) for k, v in self.pred_by_source.items()},
                "movers": {str(k): [sorted(map(str, g[0])), list(g[1])] for k in self.model.moves if (g := self.model.modal_group(k))},
                "volatile_rows": [int(i) for i in np.where(self.volatile_rows)[0]],
                "known_noops": [str(k) for k in self.model.effects if self.model.is_known_noop(k)]}
