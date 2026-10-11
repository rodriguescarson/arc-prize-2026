"""Per-pixel volatility probe: which pixels change on (almost) every step regardless of action?

Runs an agent on each game, accumulating a 64x64 count of steps on which each pixel changed, plus the
set of distinct frames with/without the volatile pixels masked. Pixels whose change rate exceeds
`thresh` are declared volatile (HUD counters, timers, animations). Also reports how many distinct
states remain once volatile pixels are masked, i.e. whether the state space collapses.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
from arc_agi import Arcade, OperationMode
from arcengine import FrameData, GameAction, GameState

from .runner import DEFAULT_ENVS, ROOT, _to_frame_data
from .agents.explorer import ExplorerAgent


def probe(game_id: str, arc: Arcade, n_actions: int, thresh: float, seed: int = 0) -> dict:
    env = arc.make(game_id, seed=0)
    agent = ExplorerAgent(game_id=game_id, seed=seed)
    frames = [FrameData(levels_completed=0)]
    change = np.zeros((64, 64), dtype=np.int32)
    prev = None; steps_cmp = 0
    raw_frames: list[np.ndarray] = []
    anim_lengths = []
    for _ in range(n_actions):
        latest = frames[-1]
        if agent.is_done(frames, latest):
            break
        a = agent.choose_action(frames, latest)
        raw = env.step(a, data=a.action_data.model_dump())
        if raw is None:
            break
        fd = _to_frame_data(raw)
        frames.append(fd)
        if fd.frame:
            anim_lengths.append(len(fd.frame))
            g = np.asarray(fd.frame[-1], dtype=np.int8)
            if prev is not None and a is not GameAction.RESET:
                change += (g != prev); steps_cmp += 1
            prev = g
            raw_frames.append(g)
        if fd.state is GameState.WIN:
            break
    rate = change / max(1, steps_cmp)
    volatile = rate > thresh
    distinct_raw = len({f.tobytes() for f in raw_frames})
    masked = [np.where(volatile, -1, f) for f in raw_frames]
    distinct_masked = len({m.tobytes() for m in masked})
    # where are the volatile pixels? bbox
    ys, xs = np.where(volatile)
    bbox = [int(ys.min()), int(xs.min()), int(ys.max()) + 1, int(xs.max()) + 1] if len(ys) else None
    return {"game": game_id[:4], "steps": steps_cmp, "levels": frames[-1].levels_completed,
            "volatile_pixels": int(volatile.sum()), "volatile_bbox": bbox,
            "pixels_changing_gt_0": int((rate > 0).sum()), "mean_pixels_changed_per_step": round(float(change.sum() / max(1, steps_cmp)), 1),
            "distinct_raw": distinct_raw, "distinct_masked": distinct_masked,
            "collapse_ratio": round(distinct_masked / max(1, distinct_raw), 3),
            "anim_frames_mean": round(float(np.mean(anim_lengths)), 2) if anim_lengths else None,
            "anim_frames_max": int(max(anim_lengths)) if anim_lengths else None}


def main(argv=None):
    argv = argv or sys.argv[1:]
    n_actions = int(argv[0]) if argv else 1000
    thresh = float(argv[1]) if len(argv) > 1 else 0.5
    logging.getLogger().setLevel(logging.ERROR)
    arc = Arcade(environments_dir=str(DEFAULT_ENVS), recordings_dir=str(ROOT / "data" / "arc3_recordings"), operation_mode=OperationMode.OFFLINE)
    rows = []
    print(f"{'game':5s} {'steps':>5s} {'lv':>3s} {'volat':>5s} {'chg>0':>5s} {'px/step':>7s} {'raw':>5s} {'masked':>6s} {'ratio':>5s} {'anim':>5s} bbox")
    for e in sorted(arc.get_environments(), key=lambda e: e.game_id):
        r = probe(e.game_id, arc, n_actions, thresh)
        rows.append(r); arc.close_scorecard()
        print(f"{r['game']:5s} {r['steps']:5d} {r['levels']:3d} {r['volatile_pixels']:5d} {r['pixels_changing_gt_0']:5d} {r['mean_pixels_changed_per_step']:7.1f} "
              f"{r['distinct_raw']:5d} {r['distinct_masked']:6d} {r['collapse_ratio']:5.2f} {r['anim_frames_mean']!s:>5s} {r['volatile_bbox']}")
    out = ROOT / "experiments" / "arc3_E0_volatility" / f"volatility_a{n_actions}_t{thresh}.json"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(rows, indent=1)); print("->", out)


if __name__ == "__main__":
    main()
