"""The generated single-file agent must run in the offline harness with a stubbed framework Agent."""
import sys, types, importlib.util, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
# stub the ARC-AGI-3-Agents framework base class the bundle imports
agents = types.ModuleType("agents"); agent_mod = types.ModuleType("agents.agent")
class Agent:
    MAX_ACTIONS = 80
    def __init__(self, card_id="", game_id="x", agent_name="", ROOT_URL="", record=False, arc_env=None, tags=None):
        self.game_id = game_id
    @property
    def name(self): return f"{self.game_id}.stub"
agent_mod.Agent = Agent; agents.agent = agent_mod
sys.modules["agents"] = agents; sys.modules["agents.agent"] = agent_mod
spec = importlib.util.spec_from_file_location("my_agent", ROOT / "submission/kaggle/my_agent.py")
m = importlib.util.module_from_spec(spec); sys.modules["my_agent"] = m; spec.loader.exec_module(m)
from arc_prize_2026.arc3.runner import run
class Wrapped(m.MyAgent):
    def __init__(self, game_id, seed=0, **kw):
        super().__init__(game_id=game_id)
s = run(Wrapped, games=["vc33", "ls20"], max_actions=200, seed=0)
assert s["n_games"] == 2 and all(g["actions"] > 0 for g in s["games"]), s
print("kaggle bundle ok:", {g["game_id"][:4]: (g["levels_completed"], g["actions"]) for g in s["games"]})
