"""Build the Paper-Track reproduction notebook: runs the submitted agent on the 25 public games inside Kaggle's
runtime (CPU, no internet) with the toolkit-exact scorer and prints the public-25 table the writeup reports.
Usage: uv run python -m arc_prize_2026.arc3.kaggle.build_repro --max-actions 2000 --out-dir submission/kaggle_repro
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from .build_notebook import INSTALL_CELL, MODULES, ROOT, SHIM, SRC, strip_relative_imports

REPRO_CELL = r'''# Reproduce the public-25 numbers of the writeup inside Kaggle's runtime (CPU, offline).
import os, sys, time, json, logging, types
import numpy as np
MAX_ACTIONS = int(os.getenv("ARC3_REPRO_MAX_ACTIONS", "{max_actions}"))
TIME_BUDGET_S = float(os.getenv("ARC3_REPRO_TIME_BUDGET_S", "{time_budget_s}"))
ENVS = os.getenv("ARC3_ENVS", "/kaggle/input/competitions/arc-prize-2026-arc-agi-3/environment_files")
sys.path.insert(0, os.getenv("ARC3_AGENT_DIR", "/kaggle/working"))
fw = types.ModuleType("agents"); fa = types.ModuleType("agents.agent")
class _A:
    MAX_ACTIONS = 80
    def __init__(self, card_id="", game_id="x", agent_name="", ROOT_URL="", record=False, arc_env=None, tags=None): self.game_id = game_id
    @property
    def name(self): return self.game_id
fa.Agent = _A; fw.agent = fa; sys.modules["agents"] = fw; sys.modules["agents.agent"] = fa
import my_agent
from arc_agi import Arcade, OperationMode
from arcengine import FrameData, GameAction, GameState
logging.getLogger().setLevel(logging.ERROR)

# ---- toolkit-exact scorer (mirrors arc_agi.scorecard.EnvironmentScoreCalculator, 0-100 scale) ----
def level_score(h, a, cap=115.0):
    return 0.0 if a is None or a <= 0 else min(100.0 * (h / a) ** 2, cap)
def game_score(baseline, level_actions, cap=115.0):
    L = len(baseline); acts = (list(level_actions) + [None] * L)[:L]; w = list(range(1, L + 1))
    total = sum(wi * level_score(h, a, cap) for wi, h, a in zip(w, baseline, acts))
    done_w = sum(wi for wi, a in zip(w, acts) if a is not None and a > 0)
    return min(total / sum(w), 100.0 * done_w / sum(w))

baselines = {{}}
for root, _, files in os.walk(ENVS):
    if "metadata.json" in files:
        d = json.load(open(os.path.join(root, "metadata.json"))); baselines[d["game_id"]] = d["baseline_actions"]
arc = Arcade(environments_dir=ENVS, operation_mode=OperationMode.OFFLINE)
games = sorted(e.game_id for e in arc.get_environments())
print(f"{{len(games)}} games, {{MAX_ACTIONS}} actions each, agent = {{my_agent.MyAgent.__name__}} (memory {{my_agent._MEMORY}}, contact {{my_agent._CONTACT}}, goals {{my_agent._GOALS}})")
results = {{}}; t_all = time.time()
for gid in games:
    env = arc.make(gid, seed=0); ag = my_agent.MyAgent(game_id=gid)
    frames = [FrameData(levels_completed=0)]; level_actions = []; n = 0; acts_level = 0; resets = 0; t0 = time.time()
    while n < MAX_ACTIONS and time.time() - t0 < TIME_BUDGET_S:
        latest = frames[-1]
        if latest.state is GameState.WIN:
            break
        a = ag.impl.choose_action(frames, latest)
        raw = env.step(a, data=a.action_data.model_dump()); n += 1; acts_level += 1; resets += int(a is GameAction.RESET)
        if raw is None:
            break
        fd = FrameData(game_id=raw.game_id, frame=[np.asarray(x).tolist() for x in raw.frame], state=raw.state,
                       levels_completed=raw.levels_completed, win_levels=raw.win_levels, available_actions=raw.available_actions)
        if fd.levels_completed > latest.levels_completed:
            level_actions.append(acts_level)
            for _ in range(fd.levels_completed - latest.levels_completed - 1): level_actions.append(1)
            acts_level = 0
        frames.append(fd)
    sc = game_score(baselines[gid], level_actions)
    results[gid] = {{"levels": frames[-1].levels_completed, "level_actions": level_actions, "actions": n, "resets": resets,
                    "score": sc, "seconds": round(time.time() - t0, 1), "human": baselines[gid]}}
    print(f"{{gid:16s}} levels {{frames[-1].levels_completed:2d}}/{{len(baselines[gid])}}  level_actions {{level_actions}}  human {{baselines[gid][:len(level_actions)]}}  score {{sc:7.3f}}  {{results[gid]['seconds']:7.1f}}s", flush=True)
    arc.close_scorecard()
total = sum(r["score"] for r in results.values()) / len(results)
levels = sum(r["levels"] for r in results.values()); games_l1 = sum(r["levels"] >= 1 for r in results.values())
print(f"\nTOTAL {{total:.4f}} | levels {{levels}}/{{sum(len(b) for b in baselines.values())}} | games with level 1: {{games_l1}} | wall {{time.time() - t_all:.0f}}s")
json.dump({{"max_actions": MAX_ACTIONS, "total_score": total, "levels": levels, "games": results}}, open("/kaggle/working/results_public25.json" if os.path.isdir("/kaggle/working") else "results_public25.json", "w"), indent=1)
'''


def build(max_actions: int, time_budget_s: int, username: str, out_dir: Path, memory: bool = True, contact: bool = True, goals: bool = True) -> dict:
    parts = ['"""Auto-generated by arc_prize_2026.arc3.kaggle.build_repro — the agent bundle of the submitted kernel."""',
             "from __future__ import annotations", "import random", "from collections import Counter, defaultdict, deque",
             "from dataclasses import dataclass, field", "from typing import Any", "import numpy as np",
             "from arcengine import FrameData, GameAction, GameState", ""]
    for m in MODULES:
        src = (SRC / m).read_text().replace("from __future__ import annotations\n", "")
        src = strip_relative_imports(src)
        src = "\n".join(l for l in src.splitlines() if not re.match(r"^(import (random|numpy as np)|from (collections|dataclasses|typing|arcengine) import )", l))
        parts.append(f"\n# ---- {m} ----\n" + src)
    agent_src = "\n".join(parts) + SHIM.format(budget_s=30600, max_actions=max_actions, memory=int(memory), contact=int(contact),
                                              game_budget_s=30600, game_cpu_s=100000, goals=int(goals))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "my_agent.py").write_text(agent_src)
    repro = REPRO_CELL.format(max_actions=max_actions, time_budget_s=time_budget_s)
    nb = {"cells": [
        {"cell_type": "markdown", "metadata": {}, "source": "# Learning what actions do — reproduction of the public-25 numbers\n\nThis notebook runs the submitted agent (same `my_agent.py` as the competition kernel) on the 25 public ARC-AGI-3 games offline on CPU and scores them with the toolkit-exact formula. No internet, no GPU, no training. Expect ~1 h."},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": INSTALL_CELL},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": "%%writefile /kaggle/working/my_agent.py\n" + agent_src},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": repro},
    ], "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    (out_dir / "reproduce.ipynb").write_text(json.dumps(nb, indent=1))
    (out_dir / "repro_cell.py").write_text(repro)  # for the local smoke test
    slug = "arc3-paper-reproduce-public25"
    meta = {"id": f"{username}/{slug}", "title": slug, "code_file": "reproduce.ipynb", "language": "python", "kernel_type": "notebook",
            "is_private": True, "enable_gpu": False, "enable_tpu": False, "enable_internet": False, "keywords": [], "dataset_sources": [],
            "kernel_sources": [], "competition_sources": ["arc-prize-2026-arc-agi-3"], "model_sources": []}
    (out_dir / "kernel-metadata.json").write_text(json.dumps(meta, indent=1))
    sha = hashlib.sha256(agent_src.encode()).hexdigest()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    info = {"my_agent_sha256": sha, "git_commit": commit, "max_actions": max_actions, "time_budget_s": time_budget_s, "kernel_id": meta["id"]}
    (out_dir / "BUILD.json").write_text(json.dumps(info, indent=1))
    return info


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-actions", type=int, default=2000)
    ap.add_argument("--time-budget-s", type=int, default=900)
    ap.add_argument("--username", default="carsonrodrigues")
    ap.add_argument("--out-dir", default=str(ROOT / "submission" / "kaggle_repro"))
    a = ap.parse_args(argv)
    print(json.dumps(build(a.max_actions, a.time_budget_s, a.username, Path(a.out_dir)), indent=1))


if __name__ == "__main__":
    main()
