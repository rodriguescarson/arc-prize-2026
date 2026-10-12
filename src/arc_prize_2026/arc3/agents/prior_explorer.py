"""H2 ablation agent: the novelty explorer plus two habits measured from human replays (no game-specific
knowledge): (1) with probability p_repeat, repeat the previous simple action if it changed the frame
(humans hold a direction); (2) rank click targets by object size and try the largest objects first
(humans click on objects, mostly large ones). Everything else is identical to ExplorerAgent, so the
paired difference isolates the prior. Pre-registered in HYPOTHESES.md (H2)."""
from __future__ import annotations

import numpy as np
from arcengine import FrameData, GameAction, GameState

from .explorer import ExplorerAgent, click_targets, frame_hash


class PriorExplorerAgent(ExplorerAgent):
    def __init__(self, game_id: str, seed: int = 0, p_repeat: float = 0.6, top_objects: int = 3, **kwargs):
        super().__init__(game_id, seed, **kwargs)
        self.p_repeat, self.top_objects = p_repeat, top_objects
        self.last_simple: GameAction | None = None
        self.last_changed = False

    def _keys(self, latest: FrameData):
        out = []
        grid = np.asarray(latest.frame[-1], dtype=np.int8) if latest.frame else None
        for a in self.legal_actions(latest):
            if a.is_complex():
                if grid is None:
                    continue
                targets = click_targets(grid)  # largest components first, then a lattice
                for rank, (y, x) in enumerate(targets):
                    out.append((("click", y // 4, x // 4, min(rank, self.top_objects)), a, {"x": int(x), "y": int(y)}))
            else:
                out.append((a.value, a, {}))
        return out

    def choose_action(self, frames: list[FrameData], latest: FrameData) -> GameAction:
        if latest.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            self.last_simple = None
            return super().choose_action(frames, latest)
        # habit 1: hold a direction that just did something
        if self.last_simple is not None and self.last_changed and self.rng.random() < self.p_repeat:
            s = frame_hash(latest)
            self._record(latest)
            self.tried[s].add(self.last_simple.value)
            self.last_state, self.last_key = s, self.last_simple.value
            return self.last_simple
        before = frame_hash(latest)
        a = super().choose_action(frames, latest)
        self.last_simple = a if (not a.is_complex() and a is not GameAction.RESET) else None
        self._pending_before = before
        return a

    def _record(self, latest: FrameData) -> None:
        super()._record(latest)
        # did the last action change the frame? (called at the start of the next step)
        if getattr(self, "_pending_before", None) is not None:
            self.last_changed = frame_hash(latest) != self._pending_before
            self._pending_before = None
