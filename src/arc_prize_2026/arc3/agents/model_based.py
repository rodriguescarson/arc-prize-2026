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
                 click_lattice: int = 8, contact: bool = True, goals: bool = True, click_model: bool = False,
                 llm_goals: str | None = None, llm_every: int = 300, llm_patience: int = 50, greedy: bool = False, greedy_cap: int = 0,
                 llm_unreached_cap: int = 0, llm_max_asks: int = 0, **kwargs):
        super().__init__(game_id, seed)
        self.memory = memory
        self.contact = contact
        self.goals = goals
        self.click_model = click_model  # E12: generative click effects in planning (failed its gate; off by default)
        self.sequences = kwargs.get("sequences", False)  # E13: replay the level-1 clicked-class sequence on later levels
        self.seq_k = kwargs.get("seq_k", 4)
        self.level_clicks: list = []      # clicked classes in the current level (consecutive repeats compressed)
        self.learned_seq: list | None = None
        self.seq_queue: list = []          # classes still to click on this level
        self.n_seq_steps = 0
        self.goal_memory = GoalMemory()
        self.level_init_objs: list[Obj] | None = None
        self.level_init_grid: np.ndarray | None = None
        self.n_goal_plans = 0
        self.max_depth, self.max_nodes, self.click_lattice = max_depth, max_nodes, click_lattice
        self.model = EffectModel()
        self.tried: dict[int, set] = {}
        self.objs_cache: dict[int, tuple[list[Obj], np.ndarray]] = {}
        self.adj_cache: dict = {}  # (state_key, mover_idents) -> adjacent classes
        # E19: decision model as goal proposer (None = off; 'stub' = control that must reproduce the plain agent)
        from ..llm_goal import make_proposer
        self.llm_goals = llm_goals; self.llm_every = llm_every; self.llm_patience = llm_patience
        self.proposer = make_proposer(llm_goals)
        self.llm_goal = None            # Predicate chosen by the proposer for the current level
        self.llm_goal_reached_at = None  # level-action index when it first held
        self.llm_excluded: set = set()   # goals reached without a transition on this level
        self.llm_asks = 0; self.llm_accepted = 0; self.llm_rejected = 0; self.llm_log: list = []
        self.llm_last_ask_n = None      # level-action index of the last ask on this level
        self._plan_is_goal = False      # the current plan reaches a goal predicate (vs a curiosity target)
        self.level_actions_n = 0        # actions taken on the current level
        self.greedy = greedy; self.n_greedy = 0   # E20: step toward a touch-goal target when no plan exists
        self.greedy_cap = greedy_cap; self.n_greedy_goal = 0  # E20b: greedy steps spent on the current proposed goal (0 = no cap)
        self.llm_unreached_cap = llm_unreached_cap; self.llm_max_asks = llm_max_asks  # E20d: drop a never-reached goal after N actions; cap asks per level
        self.llm_goal_accepted_n = None; self.llm_asks_level = 0
        self.transition_note = None     # text describing what the last transition changed
        self.plan: list = []
        self.predicted_next: int | None = None
        self.prev: tuple[list[Obj], np.ndarray, object, object] | None = None  # objs, grid, key, ckey
        self.levels_seen = 0
        self.n_plans = 0; self.n_plan_steps = 0; self.n_replans_on_error = 0; self.n_fallback = 0; self.n_deaths = 0
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
    MAX_CLICK_OBJECTS = 16  # per node: clicks on at most this many objects (largest first), lattice only if no objects

    def _keys_for(self, latest: FrameData):
        legal = self.legal_actions(latest)

        def keys(objs: list[Obj], depth: int = 0):
            out = []
            for a in legal:
                if a.is_complex():
                    # v7 behaviour (click_model off): every object at every depth; E12: cap look-ahead nodes for speed
                    cands = list(objs) if (depth == 0 or not self.click_model) else sorted(objs, key=lambda o: -o.area)[: self.MAX_CLICK_OBJECTS]
                    for o in cands:
                        cy, cx = o.centre
                        out.append((("click",) + ident(o) + (o.y0, o.x0), ("click",) + ident(o), a, {"x": int(cx), "y": int(cy)}))
                    if not cands or depth == 0 or not self.click_model:
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
            if latest.state is GameState.GAME_OVER and self.prev is not None:
                p_objs, p_grid, p_key, p_ckey = self.prev
                self.model.record_death(state_key(p_objs), p_key)   # never take this edge again
                self.n_deaths += 1
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

        # E13: level transition -> remember the clicked-class sequence of the level just finished
        if self.sequences and latest.levels_completed > self.levels_seen:
            if self.level_clicks:
                self.learned_seq = self.level_clicks[-self.seq_k:]
            self.level_clicks = []
            self.seq_queue = list(self.learned_seq or [])
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
            if self.proposer is not None:
                surv = sorted(map(str, self.goal_memory.surviving)) if self.goal_memory.surviving else []
                self.transition_note = ("predicates true at the transition and false at the level start: " + ", ".join(surv[:6])) if surv else "nothing in the template class survived"
                self.llm_goal = None; self.llm_goal_reached_at = None; self.llm_excluded = set(); self.level_actions_n = 0; self.llm_last_ask_n = None; self.llm_asks_level = 0; self.llm_goal_accepted_n = None
            self.level_init_objs = objs; self.level_init_grid = grid
            self.levels_seen = latest.levels_completed
            self.tried = {}; self.plan = []; self.predicted_next = None; self.contacted = {}
            if not self.memory:
                self.model = EffectModel(); self.objs_cache = {sk: (objs, grid)}
            self.prev = None

        # learn from the last transition
        if self.prev is not None:
            p_objs, p_grid, p_key, p_ckey = self.prev
            clicked = None
            if isinstance(p_key, tuple) and p_key[0] == "click" and p_key[1] != "lattice":
                clicked = next((o for o in p_objs if (o.colour, o.h, o.w, o.y0, o.x0) == (p_key[1], p_key[2], p_key[3], p_key[4], p_key[5])), None)
            self.model.observe(p_objs, p_grid, p_ckey, objs, clicked=clicked)
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
        if self.sequences and self.seq_queue and not self.plan:
            legal = self.legal_actions(latest)
            click_action = next((a for a in legal if a.is_complex()), None)
            target = None
            while self.seq_queue and target is None:   # skip classes absent on this level
                cls = self.seq_queue.pop(0)
                target = next((o for o in objs if ident(o) == cls), None)
            if click_action is not None and target is not None:
                cy, cx = target.centre
                key = ("click",) + ident(target) + (target.y0, target.x0); ckey = ("click",) + ident(target)
                self.tried.setdefault(sk, set()).add(key)
                self.prev = (objs, grid, key, ckey); self.predicted_next = None; self.n_seq_steps += 1
                self.level_clicks.append(cls) if not self.level_clicks or self.level_clicks[-1] != cls else None
                click_action.set_data({"x": int(cx), "y": int(cy)})
                return click_action
        if self.proposer is not None:
            self._maybe_ask_proposer(objs, grid, mover_idents)
        if not self.plan:
            goal_test = None
            if self.goals:
                active = self.goal_memory.active(objs)
                if active:
                    mi = mover_idents
                    goal_test = lambda o, _a=active, _m=mi: any(p.holds(o, _m) for p in _a)
            if goal_test is None and self.llm_goal is not None and self.llm_goal_reached_at is None and not self.llm_goal.holds(objs, mover_idents):
                # E20c: a proposed goal is a planning target only until it is first reached; afterwards the agent
                # explores normally while the patience timer decides whether the goal was right (otherwise the
                # planner shuttles between goal-satisfying states and never finds the real transition: tu93).
                mi = mover_idents
                goal_test = lambda o, _p=self.llm_goal, _m=mi: _p.holds(o, _m)
            path, final = plan_to_information(self.model, objs, grid, keys_for, self.tried, self.objs_cache,
                                              self.max_depth, self.max_nodes, mover_idents or None,
                                              self.contacted if (mover_idents and self.contact) else None, goal_test,
                                              click_model=self.click_model, adj_cache=self.adj_cache)
            if path is not None:
                if final is None:
                    self.n_goal_plans += 1
                self._plan_is_goal = final is None
                self.plan = list(path) + ([final[:1] + (final[2], final[3])] if final else [])
                # normalise entries to (key, action, data)
                self.plan = [(e[0], e[-2], e[-1]) for e in self.plan]
                self.n_plans += 1
            if self.greedy and not self._plan_is_goal:
                cands = keys_for(objs)
                safe = [c for c in cands if not self.model.is_deadly(sk, c[0])] or cands
                g = self._greedy_step(objs, grid, sk, mover_idents, safe)
                if g is not None:  # a touch goal is active and one learned move brings the mover closer: take it
                    self.plan = [(g[0], g[2], g[3])]; self.n_greedy += 1
                    if self.llm_goal is not None:
                        self.n_greedy_goal += 1
        if self.plan:
            key, action, data = self.plan.pop(0)
            self.n_plan_steps += 1
        else:
            self.n_fallback += 1
            cands = keys_for(objs)
            safe = [c for c in cands if not self.model.is_deadly(sk, c[0])] or cands
            untried = [c for c in safe if c[0] not in self.tried.get(sk, set())]
            pool = untried or safe
            key, ckey, action, data = self.rng.choice(pool)
        ckey = key if not isinstance(key, tuple) else (("click",) + tuple(key[1:4]) if key[1] != "lattice" else ("click", "lattice"))
        self.tried.setdefault(sk, set()).add(key)
        # predict for accuracy accounting
        nk = self.model.next_key(sk, key)
        if nk is not None:
            self.predicted_next, self._pred_src = nk, "memo"
        else:
            if self.click_model and isinstance(key, tuple) and key[0] == "click" and key[1] != "lattice":
                clicked = next((o for o in objs if (o.colour, o.h, o.w, o.y0, o.x0) == (key[1], key[2], key[3], key[4], key[5])), None)
                pred, src = self.model.predict_click(objs, ckey, clicked) if clicked is not None else (None, "unknown")
            else:
                pred, src = self.model.predict(objs, grid, ckey)  # v7 path: clicks may move objects (displacement model)
            if pred is not None:
                self.predicted_next, self._pred_src = state_key(pred), src
        self.prev = (objs, grid, key, ckey)
        self.level_actions_n += 1
        if action.is_complex():
            action.set_data(data)
            if self.sequences and isinstance(key, tuple) and key[1] != "lattice":
                cls = ("click",) + tuple(key[1:4])
                cls = tuple(key[1:4])
                if not self.level_clicks or self.level_clicks[-1] != cls:
                    self.level_clicks.append(cls)
        return action

    def _greedy_step(self, objs, grid, sk, mover_idents, cands):
        """E20. With an active touch(c) goal and no plan, pick the candidate whose learned mover displacement most
        reduces the gap between the mover group and the nearest object of class c; None if no goal, no mover,
        no improving move, or the model predicts a block (so the curiosity fallback runs as before)."""
        goal = self.llm_goal
        if goal is None and self.goals:
            act = [p for p in self.goal_memory.active(objs) if p.kind == "touch"]
            goal = act[0] if act else None
        if goal is None or goal.kind != "touch" or not mover_idents:
            return None
        if goal is self.llm_goal and self.llm_goal_reached_at is not None:
            return None  # E20c: already reached once; stop walking toward it
        members = [o for o in objs if ident(o) in mover_idents]
        targets = [o for o in objs if ident(o) == goal.a]
        if not members or not targets:
            return None
        def gap(ms):
            best = None
            for m in ms:
                for t in targets:
                    dy = max(0, t.y0 - m.y1, m.y0 - t.y1); dx = max(0, t.x0 - m.x1, m.x0 - t.x1)
                    d = dy + dx
                    best = d if best is None or d < best else best
            return best
        now = gap(members)
        best = None
        for c in cands:
            key, ckey = c[0], c[1]
            if self.model.is_known_noop(ckey) or isinstance(key, tuple):
                continue  # clicks have no displacement semantics here
            grp = self.model.modal_group(ckey)
            if not grp or not (grp[0] & mover_idents):
                continue
            pred, src = self.model.predict(objs, grid, ckey)
            if pred is None or state_key(pred) == sk:
                continue  # unknown or predicted blocked
            moved = [o for o in pred if ident(o) in mover_idents]
            d = gap(moved)
            if d is not None and d < now and (best is None or d < best[0]):
                best = (d, c)
        return best[1] if best else None

    def _maybe_ask_proposer(self, objs, grid, mover_idents) -> None:
        """E19. Ask at a level start and every `llm_every` actions while this level has no goal from memory; drop a
        chosen goal that held for `llm_patience` actions without a level transition and ask again, excluding it."""
        from ..llm_goal import build_prompt, goal_menu, summarise_level
        if self.goals and self.goal_memory.active(objs):
            return  # an inferred goal exists: the proposer is not consulted
        if (self.llm_goal is not None and self.llm_unreached_cap and self.llm_goal_reached_at is None and self.llm_goal_accepted_n is not None
                and self.level_actions_n - self.llm_goal_accepted_n >= self.llm_unreached_cap and not self.llm_goal.holds(objs, mover_idents)):
            # E20d: never reached within the cap: drop it (bounded damage from plausible-but-far goals: tu93)
            self.llm_excluded.add(str(self.llm_goal)); self.llm_rejected += 1
            self.llm_log.append({"level": self.levels_seen, "n": self.level_actions_n, "rejected": str(self.llm_goal), "why": "unreached_cap"})
            self.llm_goal = None; self.llm_goal_reached_at = None; self.n_greedy_goal = 0
        if self.llm_goal is not None and self.greedy_cap and self.n_greedy_goal >= self.greedy_cap and not self.llm_goal.holds(objs, mover_idents):
            # E20b: walked toward it for `greedy_cap` steps without reaching it: not reachable by walking; ask again
            self.llm_excluded.add(str(self.llm_goal)); self.llm_rejected += 1
            self.llm_log.append({"level": self.levels_seen, "n": self.level_actions_n, "rejected": str(self.llm_goal), "why": "greedy_cap"})
            self.llm_goal = None; self.llm_goal_reached_at = None; self.n_greedy_goal = 0
        if self.llm_goal is not None:
            if self.llm_goal.holds(objs, mover_idents):
                if self.llm_goal_reached_at is None:
                    self.llm_goal_reached_at = self.level_actions_n
                elif self.level_actions_n - self.llm_goal_reached_at >= self.llm_patience:
                    self.llm_excluded.add(str(self.llm_goal)); self.llm_rejected += 1
                    self.llm_log.append({"level": self.levels_seen, "n": self.level_actions_n, "rejected": str(self.llm_goal)})
                    self.llm_goal = None; self.llm_goal_reached_at = None
            if self.llm_goal is not None:
                return
        n = self.level_actions_n
        just_rejected = bool(self.llm_log) and self.llm_log[-1].get("level") == self.levels_seen and "rejected" in self.llm_log[-1] and self.llm_log[-1]["n"] == n
        if self.llm_last_ask_n is None:
            if not mover_idents and n < 100:
                return  # wait until the agent knows what it controls (touch goals need a mover), at most 100 actions
        elif n - self.llm_last_ask_n < self.llm_every and not just_rejected:
            return
        self.llm_last_ask_n = n
        if self.llm_max_asks and self.llm_asks_level >= self.llm_max_asks:
            return  # E20d: ask budget for this level spent
        menu = goal_menu(objs, mover_idents, self.llm_excluded)
        if not menu:
            return
        prompt, options = build_prompt(summarise_level(objs, grid, self.model, mover_idents, self.levels_seen, self.transition_note, self.level_actions_n), menu)
        idx, raw = self.proposer.choose(prompt, options)
        self.llm_asks += 1; self.llm_asks_level += 1
        entry = {"level": self.levels_seen, "n": self.level_actions_n, "n_options": len(options), "chosen": None}
        if idx is not None and 0 <= idx < len(menu):
            self.llm_goal = menu[idx][0]; self.llm_goal_reached_at = None; self.llm_accepted += 1; self.n_greedy_goal = 0; self.llm_goal_accepted_n = self.level_actions_n
            entry["chosen"] = str(self.llm_goal); entry["desc"] = menu[idx][1]
            self.plan = []  # replan toward the new goal
        self.llm_log.append(entry)

    def stats(self) -> dict:
        return {"memory": self.memory, "contact": self.contact, "goals": self.goals, "click_model": self.click_model, "sequences": self.sequences, "seq_steps": self.n_seq_steps,
                "llm": (None if self.proposer is None else {"model": self.proposer.name, "asks": self.llm_asks, "accepted": self.llm_accepted, "rejected": self.llm_rejected,
                                                            "calls": getattr(self.proposer, "calls", 0), "cache_hits": getattr(self.proposer, "cache_hits", 0), "cost_usd": round(getattr(self.proposer, "cost_usd", 0.0), 5), "log": self.llm_log[-12:]}),
                "greedy_steps": self.n_greedy, "greedy_cap": self.greedy_cap, "learned_seq": [str(c) for c in (self.learned_seq or [])], "plans": self.n_plans, "goal_plans": self.n_goal_plans, "deaths": self.n_deaths,
                "surviving_goals": sorted(map(str, self.goal_memory.surviving)) if self.goal_memory.surviving else None, "plan_steps": self.n_plan_steps,
                "replans_on_error": self.n_replans_on_error, "fallback_steps": self.n_fallback,
                "pred_total": self.model.n_pred, "pred_acc": None if self.model.accuracy is None else round(self.model.accuracy, 3),
                "pred_by_source": {k: (v[0], round(v[1] / v[0], 3) if v[0] else None) for k, v in self.pred_by_source.items()},
                "movers": {str(k): [sorted(map(str, g[0])), list(g[1])] for k in self.model.moves if (g := self.model.modal_group(k))},
                "volatile_rows": [int(i) for i in np.where(self.volatile_rows)[0]], "terrain_colours": sorted(self.terrain_colours),
                "known_noops": [str(k) for k in self.model.effects if self.model.is_known_noop(k)],
                "click_classes_modelled": sum(1 for k in self.model.click_effects if self.model.modal_click(k) is not None),
                "key_reliability": {str(k): [len(v), round(sum(v) / len(v), 2)] for k, v in self.model.key_pred.items() if len(v)}}
