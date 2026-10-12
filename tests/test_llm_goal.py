"""E19 tests: (1) the stub-'explore' control reproduces the plain agent's action sequence exactly; (2) a stub
that always picks option 1 makes the agent plan toward that goal without crashing and logs it; (3) the menu
only offers goals that are currently false; (4) the prompt is compact."""
import sys, logging
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from arc_agi import Arcade, OperationMode
from arcengine import FrameData, GameState
from arc_prize_2026.arc3.agents.model_based import ModelBasedAgent
from arc_prize_2026.arc3.llm_goal import build_prompt, goal_menu, summarise_level
from arc_prize_2026.arc3.perception import ident
logging.getLogger().setLevel(logging.ERROR)
ENVS = ROOT / "data" / "kaggle" / "arc-prize-2026-arc-agi-3" / "environment_files"
arc = Arcade(environments_dir=str(ENVS), operation_mode=OperationMode.OFFLINE)

def play(agent, gid, n):
    env = arc.make(gid, seed=0); frames = [FrameData(levels_completed=0)]; seq = []
    for _ in range(n):
        a = agent.choose_action(frames, frames[-1]); raw = env.step(a, data=a.action_data.model_dump())
        seq.append((a.name, a.action_data.model_dump() if a.is_complex() else None))
        if raw is None: break
        frames.append(FrameData(game_id=raw.game_id, frame=[np.asarray(x).tolist() for x in raw.frame], state=raw.state,
                                levels_completed=raw.levels_completed, win_levels=raw.win_levels, available_actions=raw.available_actions))
        if frames[-1].state is GameState.WIN: break
    arc.close_scorecard()
    return seq, frames[-1]

for gid in ["ls20", "tu93"]:
    plain = ModelBasedAgent(game_id=gid, seed=0); p_seq, _ = play(plain, gid, 350)
    ctrl = ModelBasedAgent(game_id=gid, seed=0, llm_goals="stub"); c_seq, _ = play(ctrl, gid, 350)
    assert p_seq == c_seq, f"{gid}: stub-explore control diverges from the plain agent"
    assert ctrl.llm_asks >= 1 and ctrl.llm_accepted == 0, ctrl.stats()["llm"]
    pick = ModelBasedAgent(game_id=gid, seed=0, llm_goals="stub:1"); k_seq, last = play(pick, gid, 350)
    st = pick.stats()["llm"]
    assert st["accepted"] >= 1 and st["log"][0]["chosen"] is not None, st
    # the menu never offers a goal that already holds, and the prompt stays small
    grid = np.asarray(last.frame[-1], dtype=np.int16); objs = pick.perceive(grid)
    mi = frozenset().union(*[g[0] for k in pick.model.moves if (g := pick.model.modal_group(k))]) if pick.model.moves else frozenset()
    menu = goal_menu(objs, mi)
    assert all(not pr.holds(objs, mi) for pr, _ in menu), "menu offers an already-true goal"
    prompt, options = build_prompt(summarise_level(objs, grid, pick.model, mi, 0, None, 10), menu)
    assert len(prompt.split()) < 900 and options[-1].startswith("explore"), len(prompt.split())
    print(f"{gid}: control identical over {len(p_seq)} actions; stub:1 accepted {st['accepted']} goal(s), e.g. {st['log'][0].get('chosen')}; prompt {len(prompt.split())} words, {len(options)} options")
print("llm_goal ok")
