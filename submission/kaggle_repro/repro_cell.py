# Reproduce the public-25 numbers of the writeup inside Kaggle's runtime (CPU, offline).
import os, sys, time, json, logging, types
import numpy as np
MAX_ACTIONS = int(os.getenv("ARC3_REPRO_MAX_ACTIONS", "2000"))
TIME_BUDGET_S = float(os.getenv("ARC3_REPRO_TIME_BUDGET_S", "900"))
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

baselines = {}
for root, _, files in os.walk(ENVS):
    if "metadata.json" in files:
        d = json.load(open(os.path.join(root, "metadata.json"))); baselines[d["game_id"]] = d["baseline_actions"]
arc = Arcade(environments_dir=ENVS, operation_mode=OperationMode.OFFLINE)
games = sorted(e.game_id for e in arc.get_environments())
print(f"{len(games)} games, {MAX_ACTIONS} actions each, agent = {my_agent.MyAgent.__name__} (memory {my_agent._MEMORY}, contact {my_agent._CONTACT}, goals {my_agent._GOALS})")
results = {}; t_all = time.time()
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
    results[gid] = {"levels": frames[-1].levels_completed, "level_actions": level_actions, "actions": n, "resets": resets,
                    "score": sc, "seconds": round(time.time() - t0, 1), "human": baselines[gid]}
    print(f"{gid:16s} levels {frames[-1].levels_completed:2d}/{len(baselines[gid])}  level_actions {level_actions}  human {baselines[gid][:len(level_actions)]}  score {sc:7.3f}  {results[gid]['seconds']:7.1f}s", flush=True)
    arc.close_scorecard()
total = sum(r["score"] for r in results.values()) / len(results)
levels = sum(r["levels"] for r in results.values()); games_l1 = sum(r["levels"] >= 1 for r in results.values())
print(f"\nTOTAL {total:.4f} | levels {levels}/{sum(len(b) for b in baselines.values())} | games with level 1: {games_l1} | wall {time.time() - t_all:.0f}s")
json.dump({"max_actions": MAX_ACTIONS, "total_score": total, "levels": levels, "games": results}, open("/kaggle/working/results_public25.json" if os.path.isdir("/kaggle/working") else "results_public25.json", "w"), indent=1)
