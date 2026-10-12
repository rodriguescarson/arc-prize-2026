"""Offline runner: plays an agent on every local game and scores with the Kaggle formula.

Per-level action accounting: every step() (including RESET) is charged to the level that was in
progress when it was taken. Level i is "completed" when levels_completed rises from i to i+1.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np
from arc_agi import Arcade, OperationMode
from arcengine import FrameData, GameAction, GameState

from ..arc3_score import game_score, total_score
from .perception import segment, state_key, frame_key

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ENVS = ROOT / "data" / "kaggle" / "arc-prize-2026-arc-agi-3" / "environment_files"


def _to_frame_data(raw) -> FrameData:
    return FrameData(
        game_id=raw.game_id, frame=[np.asarray(a).tolist() for a in raw.frame], state=raw.state,
        levels_completed=raw.levels_completed, win_levels=raw.win_levels, guid=raw.guid,
        full_reset=raw.full_reset, available_actions=raw.available_actions,
    )


def load_baselines(envs_dir: Path) -> dict[str, list[int]]:
    out = {}
    for md in Path(envs_dir).glob("*/*/metadata.json"):
        d = json.loads(md.read_text())
        out[d["game_id"]] = d["baseline_actions"]
    return out


def play_game(arc: Arcade, game_id: str, agent, max_actions: int, time_budget_s: float, log: list | None = None) -> dict:
    env = arc.make(game_id, seed=0)
    if env is None:
        return {"game_id": game_id, "error": "make failed"}
    t0 = time.time()
    frames: list[FrameData] = [FrameData(levels_completed=0)]
    level_actions: list[int | None] = []
    actions_this_level = 0
    n_actions = 0
    n_resets = 0
    frame_hashes: set[int] = set()
    agent_errors: list[str] = []
    while n_actions < max_actions and (time.time() - t0) < time_budget_s:
        latest = frames[-1]
        if agent.is_done(frames, latest):
            break
        try:
            action = agent.choose_action(frames, latest)
        except Exception as e:  # noqa: BLE001 - record and fall back, never abort the run
            agent_errors.append(f"{type(e).__name__}: {e}")
            action = GameAction.RESET if latest.state in (GameState.NOT_PLAYED, GameState.GAME_OVER) else GameAction.ACTION1
            if action.is_complex():
                action.set_data({"x": 32, "y": 32})
        data = action.action_data.model_dump() if hasattr(action, "action_data") else {}
        raw = env.step(action, data=data)
        n_actions += 1
        actions_this_level += 1
        if action is GameAction.RESET:
            n_resets += 1
        if raw is None:
            break
        fd = _to_frame_data(raw)
        for g in fd.frame:
            frame_hashes.add(hash(np.asarray(g, dtype=np.int8).tobytes()))
        prev_levels = latest.levels_completed
        frames.append(fd)
        if log is not None:
            g = fd.frame[-1] if fd.frame else None
            akey = state_key(segment(np.asarray(g))) if g is not None else 0
            cd = data if action.is_complex() else {}
            log.append({"a": action.name, "x": cd.get("x"), "y": cd.get("y"), "state": fd.state.value,
                        "lv": fd.levels_completed, "fk": frame_key(g) if g is not None else 0, "ak": akey})
        if fd.levels_completed > prev_levels:
            # may jump by more than one in principle; charge all actions to the first completed level
            level_actions.append(actions_this_level)
            for _ in range(fd.levels_completed - prev_levels - 1):
                level_actions.append(1)
            actions_this_level = 0
        if fd.state is GameState.WIN:
            break
    win_levels = frames[-1].win_levels
    stats = agent.stats() if hasattr(agent, "stats") else None
    return {"agent_stats": stats, "agent_errors": len(agent_errors), "agent_error_sample": agent_errors[:3],
        "game_id": game_id, "levels_completed": frames[-1].levels_completed, "win_levels": win_levels,
        "level_actions": level_actions, "actions": n_actions, "resets": n_resets,
        "distinct_frames": len(frame_hashes), "final_state": frames[-1].state.value,
        "seconds": round(time.time() - t0, 2),
    }


def run(agent_cls, envs_dir: Path = DEFAULT_ENVS, games: list[str] | None = None, max_actions: int = 2000,
        time_budget_s: float = 300.0, seed: int = 0, out_path: Path | None = None, agent_kwargs: dict | None = None,
        keep_logs: bool = False) -> dict:
    logging.getLogger().setLevel(logging.ERROR)
    for name in ("arc_agi", "arcengine"):
        logging.getLogger(name).setLevel(logging.ERROR)
    arc = Arcade(environments_dir=str(envs_dir), recordings_dir=str(ROOT / "data" / "arc3_recordings"),
                 operation_mode=OperationMode.OFFLINE)
    baselines = load_baselines(envs_dir)
    envs = sorted(arc.get_environments(), key=lambda e: e.game_id)
    if games:
        envs = [e for e in envs if e.game_id.split("-")[0] in games]
    results, per_game_scores = [], {}
    t_all = time.time()
    for e in envs:
        agent = agent_cls(game_id=e.game_id, seed=seed, **(agent_kwargs or {}))
        log = [] if keep_logs else None
        r = play_game(arc, e.game_id, agent, max_actions, time_budget_s, log)
        base = baselines.get(e.game_id)
        r["baseline_actions"] = base
        r["score"] = game_score(base, r.get("level_actions", [])) if base and "error" not in r else 0.0
        if log is not None:
            r["log"] = log
        per_game_scores[e.game_id] = r["score"]
        results.append(r)
        arc.close_scorecard()
    summary = {
        "agent": agent_cls.__name__, "agent_kwargs": agent_kwargs or {}, "seed": seed, "max_actions": max_actions,
        "time_budget_s": time_budget_s, "n_games": len(results), "total_score": round(total_score(per_game_scores), 6),
        "levels_completed": sum(r.get("levels_completed", 0) for r in results),
        "total_levels": sum(len(b) for g, b in baselines.items() if any(r["game_id"] == g for r in results)),
        "games_won": sum(1 for r in results if r.get("final_state") == "WIN"),
        "wall_s": round(time.time() - t_all, 1), "games": results,
    }
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(summary, indent=1))
    return summary


def print_summary(s: dict) -> None:
    print(f"{s['agent']} seed={s['seed']} max_actions={s['max_actions']}: score={s['total_score']:.4f} "
          f"levels={s['levels_completed']}/{s['total_levels']} won={s['games_won']}/{s['n_games']} wall={s['wall_s']}s")
    print(f"{'game':16s} {'lv/tot':>7s} {'score':>7s} {'acts':>6s} {'rst':>4s} {'frames':>6s} level_actions")
    for r in s["games"]:
        tot = len(r.get("baseline_actions") or [])
        print(f"{r['game_id']:16s} {r.get('levels_completed',0):>3d}/{tot:<3d} {r.get('score',0):7.3f} {r.get('actions',0):6d} "
              f"{r.get('resets',0):4d} {r.get('distinct_frames',0):6d} {r.get('level_actions')}")
