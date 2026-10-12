"""Human replay analysis (HF mirror magic-sword/arc_agi_3_public_demo_human_testing of the ARC Prize public
demo dataset; 340 sessions). Two uses:

1. Baselines and behaviour: per game, how many sessions, wins, per-level action counts, first-action habits.
2. Goal-template coverage (a test of our goal inference that needs no agent): for every human level
   transition, is at least one predicate from our template class TRUE at the pre-transition frame and FALSE
   at the level-start frame? If humans' solutions are explained by the templates, an agent that infers them
   has the right hypothesis class; where they are not, we have a measured limit of the method.

Usage: uv run python -m arc_prize_2026.arc3.human_replays data/human_replays [--max-sessions N]
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from .goals import candidate_predicates
from .perception import ident, segment, diff


def perceive(grid: np.ndarray, terrain_frac: float = 0.20):
    counts = np.bincount(grid.ravel(), minlength=16)
    terrain = {int(c) for c in np.where(counts >= terrain_frac * grid.size)[0]} or {int(counts.argmax())}
    return [o for o in segment(grid, drop_background=False) if o.colour not in terrain]


def analyse_session(row) -> dict:
    traj = json.loads(row["trajectory"])
    frames, actions, levels = [], [], []
    for ev in traj:
        d = ev.get("data") or {}
        fr = d.get("frame")
        if not fr:
            continue
        frames.append(np.asarray(fr[-1], dtype=np.int16))
        ai = d.get("action_input") or {}
        actions.append(int(ai.get("id", -1)) if str(ai.get("id", "")).lstrip("-").isdigit() else -1)
        levels.append(int(d.get("levels_completed", 0)))
    out = {"env": row["env"], "won": int(row["won"]), "n_frames": len(frames), "transitions": [], "first_actions": actions[1:6]}
    move_counts: Counter = Counter()
    for i in range(1, len(frames)):
        if actions[i] in (1, 2, 3, 4, 5):
            d = diff(perceive(frames[i - 1]), perceive(frames[i]))
            for o, p, delta in d["moved"]:
                move_counts[ident(o)] += 1
    mover = frozenset(c for c, n in move_counts.most_common(2)) if move_counts else frozenset()
    level_start = 0
    for i in range(1, len(frames)):
        if levels[i] > levels[i - 1]:
            init_objs = perceive(frames[level_start]); pre_objs = perceive(frames[i - 1])
            cands = candidate_predicates(init_objs, pre_objs, mover)
            out["transitions"].append({"level": levels[i], "actions": i - level_start, "n_candidates": len(cands),
                                       "kinds": sorted({p.kind for p in cands})})
            level_start = i
    return out


def main(argv=None):
    argv = argv or sys.argv[1:]
    root = Path(argv[0]); max_sessions = int(argv[argv.index("--max-sessions") + 1]) if "--max-sessions" in argv else None
    files = sorted(root.glob("*.parquet"))
    per_env = defaultdict(lambda: {"sessions": 0, "won": 0, "transitions": 0, "covered": 0, "kinds": Counter(), "first_actions": Counter()})
    n = 0
    for f in files:
        df = pq.read_table(f).to_pandas()
        for _, row in df.iterrows():
            if max_sessions and n >= max_sessions:
                break
            n += 1
            r = analyse_session(row)
            e = per_env[r["env"]]
            e["sessions"] += 1; e["won"] += r["won"]
            for a in r["first_actions"]:
                e["first_actions"][a] += 1
            for t in r["transitions"]:
                e["transitions"] += 1; e["covered"] += int(t["n_candidates"] > 0)
                for k in t["kinds"]:
                    e["kinds"][k] += 1
    print(f"{'env':5s} {'sess':>4s} {'won':>4s} {'trans':>5s} {'covered':>7s} {'cov%':>5s}  kinds(at covered transitions)   first actions")
    tot_t = tot_c = 0
    for env in sorted(per_env):
        e = per_env[env]; tot_t += e["transitions"]; tot_c += e["covered"]
        cov = 100 * e["covered"] / e["transitions"] if e["transitions"] else float("nan")
        print(f"{env:5s} {e['sessions']:4d} {e['won']:4d} {e['transitions']:5d} {e['covered']:7d} {cov:5.0f}  {dict(e['kinds'])}   {e['first_actions'].most_common(3)}")
    print(f"TOTAL transitions {tot_t} covered {tot_c} ({100 * tot_c / max(1, tot_t):.1f}%)")
    out = Path(__file__).resolve().parents[3] / "experiments" / "human_replays" / "template_coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({env: {k: (dict(v) if isinstance(v, Counter) else v) for k, v in e.items()} for env, e in per_env.items()}, indent=1))
    print("->", out)


if __name__ == "__main__":
    main()
