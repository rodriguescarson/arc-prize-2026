"""Build the Kaggle ARC-AGI-3 submission notebook from our agent sources.

Concatenates perception.py, effects.py, planner.py, agents/base.py, agents/model_based.py into one
self-contained `my_agent.py` (numpy + stdlib only), wraps ModelBasedAgent in a framework `Agent`
subclass named MyAgent, and writes a 4-cell notebook with the same rerun plumbing as Kaggle's official
Stochastic Goose sample (gateway at http://gateway:8001, KAGGLE_IS_COMPETITION_RERUN switch).

Usage: uv run python -m arc_prize_2026.arc3.kaggle.build_notebook --memory 1 --max-actions 1500 --budget-h 8.5 --game-cpu-s 700
Outputs: submission/kaggle/my_agent.py, submission/kaggle/submission.ipynb, submission/kaggle/kernel-metadata.json,
         submission/kaggle/BUILD.json (sha256 of my_agent.py, git commit, flags).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src" / "arc_prize_2026" / "arc3"
OUT = ROOT / "submission" / "kaggle"  # overridden by --out-dir
MODULES = ["perception.py", "effects.py", "goals.py", "planner.py", "agents/base.py", "agents/model_based.py"]

SHIM = '''

# ======================================================================================
# Kaggle framework adapter (ARC-AGI-3-Agents contract)
# ======================================================================================
import os as _os, time as _time
from agents.agent import Agent as _FrameworkAgent

_START = _time.time()
_BUDGET_S = float(_os.getenv("ARC3_BUDGET_S", "{budget_s}"))
_MAX_ACTIONS = int(_os.getenv("ARC3_MAX_ACTIONS", "{max_actions}"))
_MEMORY = _os.getenv("ARC3_MEMORY", "{memory}") == "1"
_CONTACT = _os.getenv("ARC3_CONTACT", "{contact}") == "1"
_GOALS = _os.getenv("ARC3_GOALS", "{goals}") == "1"
_GAME_BUDGET_S = float(_os.getenv("ARC3_GAME_BUDGET_S", "{game_budget_s}"))
# Per-game CPU budget (seconds of *this thread's* CPU time). The rerun plays all 110 games as concurrent threads
# under one GIL, so wall time is shared and meaningless per game; thread CPU time is each game's fair-share meter.
_GAME_CPU_S = float(_os.getenv("ARC3_GAME_CPU_S", "{game_cpu_s}"))


class MyAgent(_FrameworkAgent):
    """ModelBasedAgent behind the framework's Agent interface. One instance per game."""

    MAX_ACTIONS = _MAX_ACTIONS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.impl = ModelBasedAgent(game_id=self.game_id, seed=0, memory=_MEMORY, contact=_CONTACT, goals=_GOALS)
        self._n = 0
        self._t0 = _time.time()
        self._c0 = None  # thread CPU clock, captured lazily inside the game's own thread (init runs in the main thread)

    @property
    def name(self) -> str:
        return f"{{super().name}}.modelbased.mem{{int(_MEMORY)}}.contact{{int(_CONTACT)}}.goals{{int(_GOALS)}}"

    def is_done(self, frames, latest_frame) -> bool:
        if latest_frame.state is GameState.WIN:
            return True
        if _time.time() - _START > _BUDGET_S or _time.time() - self._t0 > _GAME_BUDGET_S:
            return True
        if self._c0 is None:
            self._c0 = _time.thread_time()
        if _time.thread_time() - self._c0 > _GAME_CPU_S:
            return True
        return self._n >= _MAX_ACTIONS

    def choose_action(self, frames, latest_frame) -> GameAction:
        self._n += 1
        if self._c0 is None:
            self._c0 = _time.thread_time()
        # The framework keeps every frame of every game in RAM and only reads frames[-1]; the recorder has
        # already streamed each frame to disk by the time we see it. 110 games x 3,000 frames x ~40 KB would
        # be ~13 GB, so keep only the last two frames (the agent itself reads latest_frame only).
        if len(frames) > 2:
            del frames[:-2]
        try:
            return self.impl.choose_action(frames, latest_frame)
        except Exception as e:  # never crash the swarm thread
            if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER):
                return GameAction.RESET
            acts = [a for a in GameAction if a is not GameAction.RESET and a.value in (latest_frame.available_actions or [1, 2, 3, 4])]
            a = acts[self._n % len(acts)] if acts else GameAction.ACTION1
            if a.is_complex():
                a.set_data({{"x": 32, "y": 32}})
            return a
'''

RERUN_CELL = r'''import os

if os.getenv('KAGGLE_IS_COMPETITION_RERUN'):
    # Wait for the gateway to be ready
    !curl --fail --retry 999 --retry-all-errors --retry-delay 5 --retry-max-time 600 http://gateway:8001/api/games

    !cp -r /kaggle/input/competitions/arc-prize-2026-arc-agi-3/ARC-AGI-3-Agents /kaggle/working/ARC-AGI-3-Agents
    !cp /kaggle/working/my_agent.py /kaggle/working/ARC-AGI-3-Agents/agents/templates/my_agent.py

    with open('/kaggle/working/ARC-AGI-3-Agents/agents/__init__.py', 'w') as f:
        f.write("""from typing import Type, cast
from dotenv import load_dotenv
from .agent import Agent, Playback
from .swarm import Swarm
from .templates.random_agent import Random
from .templates.my_agent import MyAgent

load_dotenv()

AVAILABLE_AGENTS: dict[str, Type[Agent]] = {
    "random": Random,
    "myagent": MyAgent,
}
""")

    with open('/kaggle/working/ARC-AGI-3-Agents/.env', 'w') as f:
        f.write("""SCHEME=http
HOST=gateway
PORT=8001
ARC_API_KEY=test-key-123
ARC_BASE_URL=http://gateway:8001/
OPERATION_MODE=online
ENVIRONMENTS_DIR=
RECORDINGS_DIR=/kaggle/working/server_recording
""")

    !cd /kaggle/working/ARC-AGI-3-Agents && MPLBACKEND=agg python main.py --agent myagent
'''

DUMMY_CELL = r'''import os
if not os.getenv('KAGGLE_IS_COMPETITION_RERUN'):
    # Self-test in Kaggle's own environment: play two public games offline with the agent (no gateway needed)
    import sys, time, logging, types
    sys.path.insert(0, '/kaggle/working')
    fw = types.ModuleType('agents'); fa = types.ModuleType('agents.agent')
    class _A:
        MAX_ACTIONS = 80
        def __init__(self, card_id='', game_id='x', agent_name='', ROOT_URL='', record=False, arc_env=None, tags=None): self.game_id = game_id
        @property
        def name(self): return self.game_id
    fa.Agent = _A; fw.agent = fa; sys.modules['agents'] = fw; sys.modules['agents.agent'] = fa
    import my_agent
    import arc_agi
    from arc_agi import Arcade, OperationMode
    from arcengine import FrameData, GameState
    logging.getLogger().setLevel(logging.ERROR)
    arc = Arcade(environments_dir='/kaggle/input/competitions/arc-prize-2026-arc-agi-3/environment_files', operation_mode=OperationMode.OFFLINE)
    for gid in ['vc33', 'ls20']:
        env = arc.make(gid); ag = my_agent.MyAgent(game_id=gid); frames = [FrameData(levels_completed=0)]; t0 = time.time()
        for _ in range(150):
            a = ag.choose_action(frames, frames[-1]); raw = env.step(a, data=a.action_data.model_dump())
            if raw is None: break
            frames.append(FrameData(game_id=raw.game_id, frame=[x.tolist() for x in raw.frame], state=raw.state, levels_completed=raw.levels_completed, win_levels=raw.win_levels, available_actions=raw.available_actions))
            if frames[-1].state is GameState.WIN: break
        print(f'SELFTEST {gid}: actions {len(frames)-1} levels {frames[-1].levels_completed} secs {time.time()-t0:.1f} stats {ag.impl.stats().get("pred_acc")}')
        arc.close_scorecard()
    # produce a dummy submission file so "Save & Run All" succeeds
    import pandas as pd
    submission = pd.DataFrame(data=[['1_0', '1', True, 1]], columns=['row_id', 'game_id', 'end_of_game', 'score'])
    submission.to_parquet('/kaggle/working/submission.parquet', index=False)
    submission.head()
'''

INSTALL_CELL = "!pip install --no-index --find-links /kaggle/input/competitions/arc-prize-2026-arc-agi-3/arc_agi_3_wheels arc-agi python-dotenv\n"


def strip_relative_imports(src: str) -> str:
    """Drop package-relative imports (every module is concatenated into one file) but keep their aliases:
    `from .perception import moved as _moved` becomes `_moved = moved`. Dropping the alias silently left
    `_moved` undefined in every kernel bundle up to v7 (found 2026-10-12 15:20 by calling the bundled agent
    outside the shim's exception handler)."""
    out = []
    for line in src.splitlines():
        m = re.match(r"^\s*from \.\.?[\w.]* import (.*)$", line)
        if m:
            for item in m.group(1).strip("() ").split(","):
                parts = item.strip().split()
                if len(parts) == 3 and parts[1] == "as":
                    out.append(f"{parts[2]} = {parts[0]}")
            continue
        if re.match(r"^\s*from \.\.?[\w.]*\s+import\s*\(", line):
            continue
        out.append(line)
    return "\n".join(out)


def build(memory: bool, max_actions: int, budget_h: float, username: str, contact: bool = True, game_budget_s: int = 30600, out_dir: Path | None = None, game_cpu_s: int = 700, goals: bool = True) -> dict:
    global OUT
    if out_dir is not None:
        OUT = Path(out_dir)
    parts = ['"""Auto-generated by arc_prize_2026.arc3.kaggle.build_notebook — do not edit; edit the sources in src/."""',
             "from __future__ import annotations", "import random", "from collections import Counter, defaultdict, deque",
             "from dataclasses import dataclass, field", "from typing import Any", "import numpy as np",
             "from arcengine import FrameData, GameAction, GameState", ""]
    for m in MODULES:
        src = (SRC / m).read_text()
        src = src.replace("from __future__ import annotations\n", "")
        src = strip_relative_imports(src)
        # drop module-level duplicate imports we already provide
        src = "\n".join(l for l in src.splitlines() if not re.match(r"^(import (random|numpy as np)|from (collections|dataclasses|typing|arcengine) import )", l))
        parts.append(f"\n# ---- {m} ----\n" + src)
    agent_src = "\n".join(parts) + SHIM.format(budget_s=int(budget_h * 3600), max_actions=max_actions, memory=int(memory),
                                              contact=int(contact), game_budget_s=game_budget_s, game_cpu_s=game_cpu_s, goals=int(goals))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "my_agent.py").write_text(agent_src)
    nb = {"cells": [
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": INSTALL_CELL},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": "%%writefile /kaggle/working/my_agent.py\n" + agent_src},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": RERUN_CELL},
        {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": DUMMY_CELL},
    ], "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                    "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
    (OUT / "submission.ipynb").write_text(json.dumps(nb, indent=1))
    slug = f"arc3-model-based-explorer-mem{int(memory)}-c{int(contact)}" + ("" if goals else "-g0")
    meta = {"id": f"{username}/{slug}", "title": slug,
            "code_file": "submission.ipynb", "language": "python", "kernel_type": "notebook", "is_private": True,
            "enable_gpu": False, "enable_tpu": False, "enable_internet": False, "keywords": [],
            "dataset_sources": [], "kernel_sources": [], "competition_sources": ["arc-prize-2026-arc-agi-3"], "model_sources": []}
    (OUT / "kernel-metadata.json").write_text(json.dumps(meta, indent=1))
    sha = hashlib.sha256(agent_src.encode()).hexdigest()
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        commit = "unknown"
    info = {"my_agent_sha256": sha, "git_commit": commit, "memory": memory, "contact": contact, "max_actions": max_actions,
            "budget_h": budget_h, "game_budget_s": game_budget_s, "game_cpu_s": game_cpu_s, "goals": goals, "kernel_id": meta["id"]}
    (OUT / "BUILD.json").write_text(json.dumps(info, indent=1))
    return info


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--memory", type=int, default=1)
    ap.add_argument("--max-actions", type=int, default=1500)
    ap.add_argument("--budget-h", type=float, default=8.5)
    ap.add_argument("--username", default="carsonrodrigues")
    ap.add_argument("--contact", type=int, default=1)
    ap.add_argument("--goals", type=int, default=1)
    ap.add_argument("--game-budget-s", type=int, default=30600)
    ap.add_argument("--game-cpu-s", type=int, default=700, help="per-game thread-CPU budget (s); 110 games share one 8.5 h GIL")
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args(argv)
    print(json.dumps(build(bool(a.memory), a.max_actions, a.budget_h, a.username, bool(a.contact), a.game_budget_s, Path(a.out_dir) if a.out_dir else None, a.game_cpu_s, bool(a.goals)), indent=1))


if __name__ == "__main__":
    main()
