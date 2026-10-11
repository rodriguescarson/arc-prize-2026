from __future__ import annotations

import random
from typing import Any

from arcengine import FrameData, GameAction, GameState

ACTION_BY_ID = {a.value: a for a in GameAction}


class BaseAgent:
    """Minimal stand-in for agents.agent.Agent with the same two abstract methods."""

    MAX_ACTIONS: int = 2000

    def __init__(self, game_id: str, seed: int = 0, **kwargs: Any) -> None:
        self.game_id = game_id
        self.rng = random.Random(seed)

    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction:
        raise NotImplementedError

    # helpers shared by agents -------------------------------------------------------------
    @staticmethod
    def legal_actions(latest_frame: FrameData) -> list[GameAction]:
        ids = latest_frame.available_actions or [1, 2, 3, 4, 5, 6, 7]
        return [ACTION_BY_ID[i] for i in ids if i in ACTION_BY_ID and i != 0]

    def random_action(self, latest_frame: FrameData) -> GameAction:
        a = self.rng.choice(self.legal_actions(latest_frame))
        if a.is_complex():
            a.set_data({"x": self.rng.randint(0, 63), "y": self.rng.randint(0, 63)})
        return a
