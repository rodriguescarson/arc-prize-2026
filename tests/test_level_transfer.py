"""E21 helpers: the winning sequence must be exactly what the LLM harness's `solved_levels()` shows the model,
and the similarity / mechanics scores must behave on hand-made cases. Run: uv run python tests/test_level_transfer.py"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS

from arc_prize_2026.arc3.level_transfer import action_id, hit_rate, lev, modal_model, parse, sim, winning_sequences

SIBLING = Path.home() / "Projects/arc-agi-3/harness/ARC3-Inference/inference/utils/level_memory.py"

# event 0 = RESET; level 1 solved on the second attempt (RESET at i=3), level 2 solved first try
ACTS = [(0, None), (1, None), (2, None), (0, None), (3, None), (4, None), (1, None), (6, (5, 7)), (2, None)]
LEVELS = [0, 0, 0, 0, 0, 0, 1, 1, 2]


def test_winning_sequences():
    w = winning_sequences(ACTS, LEVELS)
    assert w[1] == (4, 6, [(3, None), (4, None), (1, None)])
    assert w[2] == (7, 8, [(6, (5, 7)), (2, None)])


def test_matches_sibling_solved_levels():
    if not SIBLING.exists():
        print("skip: sibling repo not present")
        return
    spec = importlib.util.spec_from_file_location("level_memory", SIBLING)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    names = {0: "RESET", 1: "ACTION1", 2: "ACTION2", 3: "ACTION3", 4: "ACTION4", 6: "ACTION6"}
    hist = [NS(action="" if i == 0 else names[a], frame=NS(level=lv + 1), result={}) for i, ((a, _), lv) in enumerate(zip(ACTS, LEVELS))]
    theirs = {d["level"]: [s for s in d["winning_actions"]] for d in mod.compute_solved_levels(hist)}
    ours = {k: [names[a] for a, _ in v[2]] for k, v in winning_sequences(ACTS, LEVELS).items()}
    assert theirs == ours, (theirs, ours)


def test_action_id_both_forms():
    """The released replays write ids numerically AND by name (8% of events, 23 of 340 sessions)."""
    assert action_id("6") == 6 and action_id(6) == 6
    assert action_id("ACTION6") == 6 and action_id("action6") == 6
    assert action_id("RESET") == 0 and action_id("0") == 0
    assert action_id("") == -1 and action_id(None) == -1 and action_id("ACTION9") == -1
    assert action_id("8") == -1 and action_id("-1") == -1


def test_parse_reads_named_ids():
    import json
    ev = lambda i: {"data": {"frame": [[[1]]], "levels_completed": 0, "action_input": {"id": i, "data": {}}}}
    row = {"trajectory": json.dumps([ev("RESET"), ev("ACTION3"), ev("4"), ev("nonsense")])}
    assert [a for a, _ in parse(row)["acts"]] == [0, 3, 4, -1]


def test_similarity():
    assert lev([1, 2, 3], [1, 2, 3]) == 0 and sim([1, 2, 3], [1, 2, 3]) == 1.0
    assert lev([1, 2, 3], [3, 2, 1]) == 2
    assert sim([], []) == 1.0 and sim([1], []) == 0.0


def test_mechanics_model():
    steps = [(1, {(-1, 0)}), (1, {(-1, 0)}), (2, {(1, 0)}), (3, {(0, -1), (2, 2)})]
    m = modal_model(steps)
    assert m[1] == (-1, 0) and m[2] == (1, 0)
    assert hit_rate(m, steps)[0] == 1.0
    swapped = hit_rate(m, steps, relabel={1: 2, 2: 1})[0]
    assert swapped < 0.5


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
