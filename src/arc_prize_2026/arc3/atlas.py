"""E0 exploration atlas: per-game statistics of the reachable state space from a logged run.

For each game: steps, distinct raw frames, distinct abstract states (object configurations),
abstraction ratio, fraction of actions that changed nothing (no-op), per-action-type no-op rate,
mean branching (distinct abstract successors per abstract state), levels reached.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def atlas_from_results(path: Path) -> list[dict]:
    s = json.loads(Path(path).read_text())
    rows = []
    for r in s["games"]:
        log = r.get("log") or []
        if not log:
            continue
        frames, states = set(), set()
        noop = Counter(); tried = Counter()
        succ = defaultdict(set)
        prev_ak = None; prev_fk = None
        for e in log:
            if e["a"] == "RESET":
                prev_ak, prev_fk = e["ak"], e["fk"]; frames.add(e["fk"]); states.add(e["ak"]); continue
            kind = e["a"]
            tried[kind] += 1
            if prev_fk is not None and e["fk"] == prev_fk:
                noop[kind] += 1
            if prev_ak is not None:
                succ[prev_ak].add(e["ak"])
            frames.add(e["fk"]); states.add(e["ak"])
            prev_ak, prev_fk = e["ak"], e["fk"]
        n = sum(tried.values())
        rows.append({
            "game": r["game_id"][:4], "steps": n, "levels": r["levels_completed"], "total_levels": len(r["baseline_actions"]),
            "distinct_frames": len(frames), "distinct_abstract": len(states),
            "abstraction_ratio": round(len(states) / max(1, len(frames)), 3),
            "noop_frac": round(sum(noop.values()) / max(1, n), 3),
            "noop_by_action": {k: round(noop[k] / tried[k], 2) for k in sorted(tried)},
            "mean_branching": round(sum(len(v) for v in succ.values()) / max(1, len(succ)), 2),
            "actions_available": sorted(tried),
        })
    return rows


def main(argv=None):
    path = Path((argv or sys.argv[1:])[0])
    rows = atlas_from_results(path)
    out = path.parent / "atlas.json"
    out.write_text(json.dumps(rows, indent=1))
    print(f"{'game':6s} {'steps':>5s} {'lv':>5s} {'frames':>6s} {'abstr':>6s} {'ratio':>5s} {'noop':>5s} {'branch':>6s}  noop_by_action")
    for r in rows:
        print(f"{r['game']:6s} {r['steps']:5d} {r['levels']:>2d}/{r['total_levels']:<2d} {r['distinct_frames']:6d} {r['distinct_abstract']:6d} "
              f"{r['abstraction_ratio']:5.2f} {r['noop_frac']:5.2f} {r['mean_branching']:6.2f}  {r['noop_by_action']}")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
