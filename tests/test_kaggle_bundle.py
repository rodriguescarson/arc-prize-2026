"""The kernel bundle must behave exactly like the repo agent. Two checks the old test lacked:
1. call the bundled agent's `impl.choose_action` directly (outside the shim's exception handler), so any NameError
   or missing alias in the concatenated file surfaces instead of being swallowed as a fallback action;
2. the bundle's action sequence on three public games must be identical to the repo agent's.
"""
import sys, types, logging
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arc_prize_2026.arc3.kaggle.build_notebook import build  # noqa: E402

out = Path("/tmp/arc3_bundle_test"); build(True, 1500, 8.5, "test", True, 30600, out, 700, True)
sys.path.insert(0, str(out))
fw = types.ModuleType("agents"); fa = types.ModuleType("agents.agent")
class _A:
    MAX_ACTIONS = 80
    def __init__(self, card_id="", game_id="x", agent_name="", ROOT_URL="", record=False, arc_env=None, tags=None): self.game_id = game_id
    @property
    def name(self): return self.game_id
fa.Agent = _A; fw.agent = fa; sys.modules["agents"] = fw; sys.modules["agents.agent"] = fa
import my_agent  # noqa: E402
from arc_agi import Arcade, OperationMode  # noqa: E402
from arcengine import FrameData, GameState  # noqa: E402
from arc_prize_2026.arc3.agents.model_based import ModelBasedAgent  # noqa: E402
logging.getLogger().setLevel(logging.ERROR)
ENVS = ROOT / "data" / "kaggle" / "arc-prize-2026-arc-agi-3" / "environment_files"
arc = Arcade(environments_dir=str(ENVS), operation_mode=OperationMode.OFFLINE)

def play(agent_fn, gid, n_actions):
    env = arc.make(gid, seed=0); frames = [FrameData(levels_completed=0)]; seq = []
    for _ in range(n_actions):
        a = agent_fn(frames, frames[-1])  # no try/except: exceptions must surface
        raw = env.step(a, data=a.action_data.model_dump())
        seq.append((a.name, a.action_data.model_dump() if a.is_complex() else None))
        if raw is None: break
        frames.append(FrameData(game_id=raw.game_id, frame=[np.asarray(x).tolist() for x in raw.frame], state=raw.state,
                                levels_completed=raw.levels_completed, win_levels=raw.win_levels, available_actions=raw.available_actions))
        if frames[-1].state is GameState.WIN: break
    arc.close_scorecard()
    return seq, frames[-1].levels_completed

report = {}
for gid, n in [("ls20", 400), ("vc33", 400), ("tu93", 300), ("sp80", 300)]:
    bundle = my_agent.MyAgent(game_id=gid)
    b_seq, b_lv = play(bundle.impl.choose_action, gid, n)
    repo = ModelBasedAgent(game_id=gid, seed=0, memory=True, contact=True, goals=True)
    r_seq, r_lv = play(repo.choose_action, gid, n)
    assert b_seq == r_seq, f"{gid}: bundle diverges from the repo agent at step {next(i for i, (x, y) in enumerate(zip(b_seq, r_seq)) if x != y)}"
    # 3. through the shim (framework entry point, which trims the frames list in place): same sequence again,
    #    and the list the framework keeps must stay short.
    shim = my_agent.MyAgent(game_id=gid); kept = []
    def via_shim(frames, latest, _s=shim, _k=kept):
        a = _s.choose_action(frames, latest); _k.append(len(frames)); return a
    s_seq, s_lv = play(via_shim, gid, n)
    assert s_seq == r_seq, f"{gid}: shim path diverges from the repo agent"
    assert max(kept) <= 2, f"{gid}: frames list grew to {max(kept)}"
    report[gid] = (b_lv, len(b_seq))
print("kaggle bundle ok (direct + shim paths bit-identical to the repo agent; frames list bounded):", report)
