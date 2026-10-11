"""Local ARC-AGI-3 scoring that mirrors `arc_agi.scorecard.EnvironmentScoreCalculator` (toolkit 0.9.9,
read 2026-10-12) on a 0-100 scale:

  per-level score  = min(115, 100 * (baseline_actions / actions_taken) ** 2)   if completed else 0
  per-game score   = sum_i w_i * s_i / sum_i w_i  with w_i = level index (1-based), over ALL levels
                     of the game (uncompleted levels contribute 0 with their full weight),
                     then capped at 100 * (sum of weights of completed levels / sum of all weights)
  total            = mean over games

The Kaggle Overview text says per-level credit is capped at 100 rather than 115; `level_cap`
switches between the two. Actions charged to a level include RESETs taken during that level.
Until matched against a real Kaggle score, treat local numbers as estimates.
"""
from __future__ import annotations


def level_score(human_actions: int, agent_actions: int | None, level_cap: float = 115.0) -> float:
    if agent_actions is None or agent_actions <= 0:
        return 0.0
    return min(100.0 * (human_actions / agent_actions) ** 2, level_cap)


def game_score(baseline_actions: list[int], agent_level_actions: list[int | None], level_cap: float = 115.0) -> float:
    """agent_level_actions[i] = actions spent completing level i, or None/absent if not completed."""
    L = len(baseline_actions)
    acts = (list(agent_level_actions) + [None] * L)[:L]
    weights = list(range(1, L + 1))
    total = sum(w * level_score(h, a, level_cap) for w, h, a in zip(weights, baseline_actions, acts))
    completed_w = sum(w for w, a in zip(weights, acts) if a is not None and a > 0)
    score = total / sum(weights)
    return min(score, 100.0 * completed_w / sum(weights))


def total_score(per_game: dict[str, float]) -> float:
    return sum(per_game.values()) / len(per_game) if per_game else 0.0
