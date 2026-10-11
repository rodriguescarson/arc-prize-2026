"""Novelty-seeking explorer (no learning across games, no LLM).

State = hash of the latest 64x64 frame. Memory per game:
  tried[state]      -> set of action keys already tried from this state
  noop[action_key]  -> count of times the action left the frame unchanged (anywhere)
  effect[(state, action_key)] -> hash of the frame it produced
Policy (in order): RESET if GAME_OVER / NOT_PLAYED; an untried action in this state (least globally
no-op first); else the action in this state whose recorded outcome is the least-visited frame;
small epsilon of uniform random. Click targets (ACTION6) are the centroids of connected components
of the current frame plus a coarse 8x8 lattice, so clicks land on objects, not uniformly.
"""
from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np
from arcengine import FrameData, GameAction, GameState

from .base import ACTION_BY_ID, BaseAgent


def frame_hash(fd: FrameData) -> int:
    if not fd.frame:
        return 0
    return hash(np.asarray(fd.frame[-1], dtype=np.int8).tobytes())


def click_targets(grid: np.ndarray, max_targets: int = 24) -> list[tuple[int, int]]:
    """Centroids of same-colour connected components (4-neighbourhood), largest-area first, plus a lattice."""
    h, w = grid.shape
    seen = np.zeros((h, w), dtype=bool)
    comps = []
    for y in range(h):
        for x in range(w):
            if seen[y, x]:
                continue
            c = grid[y, x]
            stack = [(y, x)]; seen[y, x] = True; cells = []
            while stack:
                cy, cx = stack.pop(); cells.append((cy, cx))
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx] and grid[ny, nx] == c:
                        seen[ny, nx] = True; stack.append((ny, nx))
            if 2 <= len(cells) <= h * w // 2:  # skip single pixels and the background
                ys, xs = zip(*cells)
                comps.append((len(cells), int(round(sum(ys) / len(ys))), int(round(sum(xs) / len(xs)))))
    comps.sort(reverse=True)
    targets = [(y, x) for _, y, x in comps[:max_targets]]
    lattice = [(y, x) for y in range(4, 64, 8) for x in range(4, 64, 8)]
    return targets + lattice


class ExplorerAgent(BaseAgent):
    def __init__(self, game_id: str, seed: int = 0, epsilon: float = 0.05, **kwargs):
        super().__init__(game_id, seed)
        self.epsilon = epsilon
        self.tried: dict[int, set] = defaultdict(set)
        self.noop: Counter = Counter()
        self.effect: dict[tuple[int, object], int] = {}
        self.visits: Counter = Counter()
        self.last_state: int | None = None
        self.last_key: object | None = None
        self.levels_seen = 0

    def _keys(self, latest: FrameData) -> list[tuple[object, GameAction, dict]]:
        out = []
        grid = np.asarray(latest.frame[-1], dtype=np.int8) if latest.frame else None
        for a in self.legal_actions(latest):
            if a.is_complex():
                if grid is None:
                    continue
                for (y, x) in click_targets(grid):
                    out.append((("click", y // 4, x // 4), a, {"x": int(x), "y": int(y)}))
            else:
                out.append((a.value, a, {}))
        return out

    def _record(self, latest: FrameData) -> None:
        s = frame_hash(latest)
        self.visits[s] += 1
        if self.last_state is not None and self.last_key is not None:
            self.effect[(self.last_state, self.last_key)] = s
            if s == self.last_state:
                self.noop[self.last_key] += 1
        if latest.levels_completed > self.levels_seen:
            self.levels_seen = latest.levels_completed
            self.tried.clear(); self.effect.clear()  # a new level is a new world; keep noop stats

    def choose_action(self, frames: list[FrameData], latest: FrameData) -> GameAction:
        self._record(latest)
        if latest.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            self.last_state, self.last_key = None, None
            return GameAction.RESET
        s = frame_hash(latest)
        options = self._keys(latest)
        if not options:
            return GameAction.RESET
        if self.rng.random() < self.epsilon:
            key, a, data = self.rng.choice(options)
        else:
            untried = [o for o in options if o[0] not in self.tried[s]]
            if untried:
                untried.sort(key=lambda o: (self.noop[o[0]], self.rng.random()))
                key, a, data = untried[0]
            else:
                options.sort(key=lambda o: (self.visits[self.effect.get((s, o[0]), -1)], self.rng.random()))
                key, a, data = options[0]
        self.tried[s].add(key)
        self.last_state, self.last_key = s, key
        if a.is_complex():
            a.set_data(data)
        return a
