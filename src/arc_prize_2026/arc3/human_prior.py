"""H2: an exploration prior from human replays (no per-game knowledge is transferred, only habits).

Measures, per game and pooled by action-space signature:
  * first-k action distribution (which action ids humans try first),
  * for clicks: fraction landing on a non-terrain object vs background, and the size rank of the clicked object,
  * repeat rate: fraction of consecutive identical simple actions (humans hold a direction).
Outputs experiments/human_replays/prior.json for use by a prior-weighted explorer.
Usage: uv run python -m arc_prize_2026.arc3.human_prior data/human_replays [--max-sessions N]
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from .perception import segment


def terrain_colours(grid: np.ndarray, frac: float = 0.20) -> set[int]:
    counts = np.bincount(grid.ravel(), minlength=16)
    return {int(c) for c in np.where(counts >= frac * grid.size)[0]} or {int(counts.argmax())}


def main(argv=None):
    argv = argv or sys.argv[1:]
    root = Path(argv[0]); max_sessions = int(argv[argv.index("--max-sessions") + 1]) if "--max-sessions" in argv else None
    per_env = defaultdict(lambda: {"sessions": 0, "first5": Counter(), "clicks": 0, "clicks_on_object": 0, "click_obj_rank": Counter(),
                                   "simple": 0, "simple_repeat": 0, "avail": None})
    n = 0
    for f in sorted(root.glob("*.parquet")):
        df = pq.read_table(f).to_pandas()
        for _, row in df.iterrows():
            if max_sessions and n >= max_sessions:
                break
            n += 1
            e = per_env[row["env"]]; e["sessions"] += 1
            traj = json.loads(row["trajectory"])
            prev_grid = None; prev_simple = None; k = 0
            for ev in traj:
                d = ev.get("data") or {}
                fr = d.get("frame"); ai = d.get("action_input") or {}
                aid = str(ai.get("id", ""))
                if e["avail"] is None and d.get("available_actions"):
                    e["avail"] = sorted(int(x) for x in d["available_actions"])
                if aid.isdigit() and int(aid) != 0:
                    a = int(aid)
                    if k < 5:
                        e["first5"][a] += 1; k += 1
                    if a == 6 and prev_grid is not None:
                        x, y = (ai.get("data") or {}).get("x"), (ai.get("data") or {}).get("y")
                        if x is not None and y is not None:
                            e["clicks"] += 1
                            terr = terrain_colours(prev_grid)
                            objs = [o for o in segment(prev_grid, drop_background=False) if o.colour not in terr]
                            hit = [o for o in objs if o.y0 <= y < o.y1 and o.x0 <= x < o.x1]
                            if hit:
                                e["clicks_on_object"] += 1
                                ranks = sorted(objs, key=lambda o: -o.area)
                                e["click_obj_rank"][min(ranks.index(hit[0]), 5)] += 1
                    elif a in (1, 2, 3, 4, 5):
                        e["simple"] += 1
                        if prev_simple == a:
                            e["simple_repeat"] += 1
                        prev_simple = a
                if fr:
                    prev_grid = np.asarray(fr[-1], dtype=np.int16)
    out = {}
    print(f"{'env':5s} {'sess':>4s} {'avail':16s} {'first5 top':28s} {'clicks':>6s} {'on obj':>7s} {'rank0-2':>8s} {'repeat':>6s}")
    for env in sorted(per_env):
        e = per_env[env]
        on = e["clicks_on_object"] / e["clicks"] if e["clicks"] else float("nan")
        rep = e["simple_repeat"] / e["simple"] if e["simple"] else float("nan")
        r012 = sum(e["click_obj_rank"][i] for i in range(3)) / max(1, e["clicks_on_object"])
        print(f"{env:5s} {e['sessions']:4d} {str(e['avail']):16s} {str(e['first5'].most_common(3)):28s} {e['clicks']:6d} {on:7.2f} {r012:8.2f} {rep:6.2f}")
        out[env] = {"sessions": e["sessions"], "avail": e["avail"], "first5": dict(e["first5"]), "clicks": e["clicks"],
                    "click_on_object_frac": on, "click_rank_hist": dict(e["click_obj_rank"]), "simple_repeat_frac": rep}
    p = Path(__file__).resolve().parents[3] / "experiments" / "human_replays" / "prior.json"
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, indent=1, default=str)); print("->", p)


if __name__ == "__main__":
    main()
