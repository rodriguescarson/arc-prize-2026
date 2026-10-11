"""Local ARC-AGI-3 scoring mirroring the Kaggle competition formula (as published on the
competition Overview/Data pages, read 2026-10-12):

  per-level score  = min(human_actions / agent_actions, 1.0) ** 2        (0 if level not completed)
  per-game score   = level-index-weighted average of per-level scores, weights 1..L (1-indexed)
  total            = mean over games, capped at 100%

`baseline_actions` (the human baseline per level) comes from each game's metadata.json.
UNVERIFIED detail: whether the weighted average uses weights i/sum(i) exactly as here. Treat local
numbers as estimates until matched against a real Kaggle score.
"""
from __future__ import annotations


def level_score(human_actions: int, agent_actions: int | None) -> float:
    if agent_actions is None or agent_actions <= 0:
        return 0.0
    return min(human_actions / agent_actions, 1.0) ** 2


def game_score(baseline_actions: list[int], agent_level_actions: list[int | None]) -> float:
    """agent_level_actions[i] = actions the agent spent to complete level i, or None if not completed."""
    L = len(baseline_actions)
    weights = list(range(1, L + 1))
    num = sum(w * level_score(h, a) for w, h, a in zip(weights, baseline_actions,
                                                       (agent_level_actions + [None] * L)[:L]))
    return num / sum(weights)


def total_score(per_game: dict[str, float]) -> float:
    if not per_game:
        return 0.0
    return min(sum(per_game.values()) / len(per_game), 1.0)
