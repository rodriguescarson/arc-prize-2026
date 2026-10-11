"""Per-game failure table for a results.json produced by the arc3 runner.

Stall categories (first match wins) for games that did not finish:
  game_over_loop   : resets > 10% of actions (keeps dying)
  stuck            : distinct frames < 10% of actions (same few states revisited)
  model_blind      : generative prediction accuracy < 0.3 (dynamics not captured)
  no_progress      : none of the above; explored widely but never hit a level transition
Also reports actions per completed level vs human baseline and whether the first level was reached.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def classify(r: dict) -> str:
    acts = max(1, r.get("actions", 0))
    st = r.get("agent_stats") or {}
    if r.get("final_state") == "WIN":
        return "won"
    if r.get("resets", 0) > 0.10 * acts:
        return "game_over_loop"
    if r.get("distinct_frames", 0) < 0.10 * acts:
        return "stuck"
    acc = st.get("pred_acc")
    if acc is not None and acc < 0.3:
        return "model_blind"
    return "no_progress"


def table(path: Path) -> str:
    s = json.loads(Path(path).read_text())
    lines = [f"# Failure table — {s['agent']} seed={s['seed']} max_actions={s['max_actions']} total={s['total_score']:.3f} levels={s['levels_completed']}/{s['total_levels']}", "",
             "| game | levels | score | actions/level (human) | resets | distinct frames | model acc | plan steps / fallback | stall |", "|---|---|---|---|---|---|---|---|---|"]
    counts: dict[str, int] = {}
    for r in s["games"]:
        st = r.get("agent_stats") or {}
        cat = classify(r); counts[cat] = counts.get(cat, 0) + 1
        per_level = ", ".join(f"{a} ({h})" for a, h in zip(r.get("level_actions", []), r.get("baseline_actions", []))) or "—"
        lines.append(f"| {r['game_id'][:4]} | {r['levels_completed']}/{len(r.get('baseline_actions') or [])} | {r['score']:.3f} | {per_level} | {r.get('resets', 0)} | "
                     f"{r.get('distinct_frames', 0)} | {st.get('pred_acc')} | {st.get('plan_steps', '—')} / {st.get('fallback_steps', '—')} | {cat} |")
    lines += ["", "Stall counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))]
    return "\n".join(lines)


def main(argv=None):
    path = Path((argv or sys.argv[1:])[0])
    out = table(path)
    (path.parent / "failure_table.md").write_text(out)
    print(out)


if __name__ == "__main__":
    main()
