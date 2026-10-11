from __future__ import annotations

from arcengine import FrameData, GameAction, GameState

from .base import BaseAgent


class RandomAgent(BaseAgent):
    """Uniform random over the legal action space; RESET after GAME_OVER. The floor."""

    def choose_action(self, frames: list[FrameData], latest_frame: FrameData) -> GameAction:
        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
            return GameAction.RESET
        return self.random_action(latest_frame)
