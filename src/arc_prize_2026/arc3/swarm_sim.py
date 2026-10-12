"""Simulate the Kaggle rerun's concurrency: every game played in its own thread at once (GIL-interleaved),
with the submission shim's per-game wall budget and action cap. Reports actions actually taken per game
and the resulting local score, to test whether the per-game wall budget starves games.
Usage: uv run python -m arc_prize_2026.arc3.swarm_sim --game-budget-s 600 --max-actions 1500 --games all
"""
from __future__ import annotations

import argparse
import json
import logging
import threading
import time
from pathlib import Path

import numpy as np
from arc_agi import Arcade, OperationMode
from arcengine import FrameData, GameAction, GameState

from ..arc3_score import game_score, total_score
from .agents.model_based import ModelBasedAgent
from .runner import DEFAULT_ENVS, ROOT, _to_frame_data, load_baselines


def play(arc, game_id, budget_s, max_actions, out, lock, cpu_s=float("inf")):
    env = arc.make(game_id, seed=0)
    agent = ModelBasedAgent(game_id=game_id, seed=0, memory=True, contact=True, goals=True)
    frames = [FrameData(levels_completed=0)]
    t0 = time.time(); c0 = time.thread_time(); n = 0; level_actions = []; acts_level = 0
    while n < max_actions and time.time() - t0 < budget_s and time.thread_time() - c0 < cpu_s:
        latest = frames[-1]
        if latest.state is GameState.WIN:
            break
        a = agent.choose_action(frames, latest)
        raw = env.step(a, data=a.action_data.model_dump()); n += 1; acts_level += 1
        if raw is None:
            break
        fd = _to_frame_data(raw)
        if fd.levels_completed > latest.levels_completed:
            level_actions.append(acts_level); acts_level = 0
        frames.append(fd)
    with lock:
        out[game_id] = {"actions": n, "levels": frames[-1].levels_completed, "level_actions": level_actions, "wall": round(time.time() - t0, 1), "cpu": round(time.thread_time() - c0, 1)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--game-budget-s", type=float, default=600)
    ap.add_argument("--max-actions", type=int, default=1500)
    ap.add_argument("--games", default="all")
    ap.add_argument("--game-cpu-s", type=float, default=float("inf"), help="per-game thread-CPU budget (s)")
    a = ap.parse_args(argv)
    logging.getLogger().setLevel(logging.ERROR)
    arc = Arcade(environments_dir=str(DEFAULT_ENVS), recordings_dir=str(ROOT / "data" / "arc3_recordings"), operation_mode=OperationMode.OFFLINE)
    envs = sorted(e.game_id for e in arc.get_environments())
    if a.games != "all":
        envs = [e for e in envs if e[:4] in a.games.split(",")]
    base = load_baselines(DEFAULT_ENVS)
    out, lock = {}, threading.Lock()
    threads = [threading.Thread(target=play, args=(arc, g, a.game_budget_s, a.max_actions, out, lock, a.game_cpu_s), daemon=True) for g in envs]
    t0 = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    scores = {g: game_score(base[g], r["level_actions"]) for g, r in out.items()}
    print(f"{'game':16s} {'actions':>7s} {'levels':>6s} {'wall':>7s} {'cpu':>7s} score")
    for g in envs:
        r = out[g]; print(f"{g:16s} {r['actions']:7d} {r['levels']:6d} {r['wall']:7.1f} {r['cpu']:7.1f} {scores[g]:.3f}")
    print(f"TOTAL {total_score(scores):.3f} | levels {sum(r['levels'] for r in out.values())} | mean actions {np.mean([r['actions'] for r in out.values()]):.0f} | wall {time.time()-t0:.0f}s | cpu sum {sum(r['cpu'] for r in out.values()):.0f}s | budget/game {a.game_budget_s}s, cpu/game {a.game_cpu_s}s, cap {a.max_actions}")
    Path(ROOT / "experiments" / "swarm_sim").mkdir(parents=True, exist_ok=True)
    (ROOT / "experiments" / "swarm_sim" / f"sim_b{int(a.game_budget_s)}_c{int(a.game_cpu_s) if a.game_cpu_s != float('inf') else 'inf'}_a{a.max_actions}.json").write_text(json.dumps({"config": vars(a), "games": out, "total": total_score(scores)}, indent=1))


if __name__ == "__main__":
    main()
