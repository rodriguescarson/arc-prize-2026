"""E13 pre-check on human replays: are click-driven levels solved by a consistent ordered sequence of
clicked object CLASSES across the levels of one session?

For each session and each completed level: take the clicks within that level (action id 6 with x,y),
map each click to the class (colour, h, w) of the non-terrain object under it (or "bg"), compress
consecutive repeats, and keep the last K distinct-class steps before the transition. A session is
"sequence-consistent" if the last-K class sequence is identical for at least two of its levels; we also
report the longest common suffix across all its levels. Usage:
  uv run python -m arc_prize_2026.arc3.human_sequences data/human_replays [--k 4]
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from .perception import ident, segment

CLICK_GAMES = ["ar25", "bp35", "cn04", "ft09", "ka59", "lf52", "lp85", "r11l", "s5i5", "sb26", "sc25", "sk48", "vc33"]


def perceive(grid, frac=0.20):
    counts = np.bincount(grid.ravel(), minlength=16)
    terrain = {int(c) for c in np.where(counts >= frac * grid.size)[0]} or {int(counts.argmax())}
    return [o for o in segment(grid, drop_background=False) if o.colour not in terrain]


def class_under(objs, x, y):
    hit = [o for o in objs if o.y0 <= y < o.y1 and o.x0 <= x < o.x1]
    return ident(min(hit, key=lambda o: o.area)) if hit else "bg"


def session_sequences(row, k: int):
    traj = json.loads(row["trajectory"])
    seqs, cur, prev_grid, prev_level = [], [], None, 0
    for ev in traj:
        d = ev.get("data") or {}
        fr = d.get("frame"); ai = d.get("action_input") or {}
        lvl = int(d.get("levels_completed", 0))
        if str(ai.get("id")) == "6" and prev_grid is not None:
            data = ai.get("data") or {}
            if data.get("x") is not None and data.get("y") is not None:
                c = class_under(perceive(prev_grid), int(data["x"]), int(data["y"]))
                if not cur or cur[-1] != c:
                    cur.append(c)
        if lvl > prev_level:
            seqs.append(tuple(cur[-k:])); cur = []; prev_level = lvl
        if fr:
            prev_grid = np.asarray(fr[-1], dtype=np.int16)
    return seqs


def main(argv=None):
    argv = argv or sys.argv[1:]
    root = Path(argv[0]); k = int(argv[argv.index("--k") + 1]) if "--k" in argv else 4
    per = defaultdict(lambda: {"sessions": 0, "multi": 0, "consistent": 0, "examples": Counter()})
    for f in sorted(root.glob("*.parquet")):
        df = pq.read_table(f).to_pandas()
        for _, row in df.iterrows():
            if row["env"] not in CLICK_GAMES:
                continue
            e = per[row["env"]]; e["sessions"] += 1
            seqs = [s for s in session_sequences(row, k) if s]
            if len(seqs) >= 2:
                e["multi"] += 1
                c = Counter(seqs)
                top, n = c.most_common(1)[0]
                if n >= 2:
                    e["consistent"] += 1; e["examples"][top] += 1
    print(f"{'env':5s} {'sess':>4s} {'multi':>5s} {'consist':>7s}  most common repeated last-{k} class sequence")
    tot_m = tot_c = 0
    for env in CLICK_GAMES:
        e = per[env]; tot_m += e["multi"]; tot_c += e["consistent"]
        ex = e["examples"].most_common(1)[0] if e["examples"] else ("—", 0)
        print(f"{env:5s} {e['sessions']:4d} {e['multi']:5d} {e['consistent']:7d}  {ex[0]} ×{ex[1]}")
    print(f"TOTAL multi-level click sessions {tot_m}; with a repeated class sequence {tot_c} ({100 * tot_c / max(1, tot_m):.1f}%)")
    out = Path(__file__).resolve().parents[3] / "experiments" / "human_replays" / f"sequences_k{k}.json"
    out.write_text(json.dumps({env: {kk: (dict((str(a), b) for a, b in v.items()) if isinstance(v, Counter) else v) for kk, v in e.items()} for env, e in per.items()}, indent=1)); print("->", out)


if __name__ == "__main__":
    main()
