"""uv run arc3 --agent random --max-actions 500 [--games ls20,vc33]"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

from .runner import ROOT, run, print_summary
from ..registry import log_run

AGENTS = {"random": ("arc_prize_2026.arc3.agents.random_agent", "RandomAgent"),
          "explorer": ("arc_prize_2026.arc3.agents.explorer", "ExplorerAgent"),
          "model_based": ("arc_prize_2026.arc3.agents.model_based", "ModelBasedAgent"),
          "prior_explorer": ("arc_prize_2026.arc3.agents.prior_explorer", "PriorExplorerAgent")}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="arc3")
    ap.add_argument("--agent", required=True, choices=sorted(AGENTS))
    ap.add_argument("--games", default=None, help="comma-separated 4-char ids")
    ap.add_argument("--max-actions", type=int, default=500)
    ap.add_argument("--time-budget", type=float, default=300.0, help="seconds per game")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--kwargs", default="{}")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--hypothesis", default="")
    ap.add_argument("--keep-logs", action="store_true")
    ap.add_argument("--no-log", action="store_true")
    a = ap.parse_args(argv)
    mod, cls = AGENTS[a.agent]
    agent_cls = getattr(importlib.import_module(mod), cls)
    kwargs = json.loads(a.kwargs)
    run_id = a.run_id or f"arc3_{a.agent}_a{a.max_actions}_s{a.seed}"
    out = ROOT / "experiments" / run_id / "results.json"
    s = run(agent_cls, games=a.games.split(",") if a.games else None, max_actions=a.max_actions,
            time_budget_s=a.time_budget, seed=a.seed, out_path=out, agent_kwargs=kwargs, keep_logs=a.keep_logs)
    print_summary(s)
    if not a.no_log and not a.games:
        log_run(run_id=run_id, hypothesis=a.hypothesis, method=f"arc3/{a.agent}", config={**kwargs, "max_actions": a.max_actions, "seed": a.seed},
                dataset_split="ARC-AGI-3/public-25", n_tasks=s["n_games"], score=s["total_score"], tasks_solved=s["games_won"],
                runtime_s=s["wall_s"], outcome="baseline" if a.agent == "random" else "measured",
                interpretation=f"levels {s['levels_completed']}/{s['total_levels']}")
    print(f"results -> {out}")


if __name__ == "__main__":
    main()
