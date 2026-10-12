"""Assemble the paper's results table from results.json files (one command once runs finish).
Usage: uv run python -m arc_prize_2026.arc3.assemble_results name=path ... > paper/results_table.md
Columns: score (0-100), levels, games with level 1, games with level >=2, median actions/human on level 1,
faster-than-human levels, wall seconds. Also prints the per-level ratio list for games with >=2 levels.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from ..arc3_score import game_score, total_score


def summarise(name: str, path: Path) -> tuple[str, dict]:
    s = json.loads(Path(path).read_text())
    g = s["games"]
    # recompute with the toolkit-exact scorer so files written before the scorer rewrite are comparable
    s["total_score"] = total_score({r["game_id"]: game_score(r["baseline_actions"], r.get("level_actions", [])) for r in g})
    l1 = [r for r in g if r["levels_completed"] >= 1]
    l2 = [r for r in g if r["levels_completed"] >= 2]
    ratios_l1 = [r["level_actions"][0] / r["baseline_actions"][0] for r in l1]
    faster = sum(1 for r in g for a, h in zip(r["level_actions"], r["baseline_actions"]) if a <= h)
    curves = {r["game_id"][:4]: [round(a / h, 1) for a, h in zip(r["level_actions"], r["baseline_actions"])] for r in l2}
    row = (f"| {name} | {s['total_score']:.3f} | {s['levels_completed']}/{s['total_levels']} | {len(l1)} | {len(l2)} | "
           f"{statistics.median(ratios_l1):.1f}× | {faster} | {s['wall_s']:.0f} |") if l1 else f"| {name} | {s['total_score']:.3f} | {s['levels_completed']}/{s['total_levels']} | 0 | 0 | — | 0 | {s['wall_s']:.0f} |"
    return row, curves


def main(argv=None):
    argv = argv or sys.argv[1:]
    print("| agent | score (0–100) | levels | games ≥1 level | games ≥2 levels | median L1 actions/human | levels ≤ human | wall s |")
    print("|---|---|---|---|---|---|---|---|")
    curves_all = {}
    for kv in argv:
        name, path = kv.split("=", 1)
        row, curves = summarise(name, Path(path)); print(row); curves_all[name] = curves
    print()
    for name, curves in curves_all.items():
        if curves:
            print(f"{name}: per-level actions/human — " + "; ".join(f"{g} {v}" for g, v in curves.items()))


if __name__ == "__main__":
    main()
