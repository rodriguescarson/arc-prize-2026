"""E21 helpers: the winning sequence must be exactly what the LLM harness's `solved_levels()` shows the model,
and the similarity / mechanics scores must behave on hand-made cases. Run: uv run python tests/test_level_transfer.py"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS

from arc_prize_2026.arc3.level_transfer import (
    BUDGET_S, PACKED, action_id, hit_rate, iter_events, lev, load_packed, modal_model, pack_path,
    parse, resume, run_seq, sim, winning_sequences,
)

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


def test_resume_reads_back_finished_sessions(tmp=None):
    """The run has been killed four times; a rerun must cost only what was in flight."""
    import json, tempfile
    d = Path(tempfile.mkdtemp())
    shard = d / "E21_level_transfer.jsonl"
    assert resume(shard, {"a"}) == {}                       # nothing written yet
    with shard.open("w") as f:
        f.write(json.dumps({"guid": "a", "n": 1}) + "\n")
        f.write(json.dumps({"guid": "b", "n": 2}) + "\n")
        f.write(json.dumps({"guid": "c", "n": 3})[:12])      # killed mid-write: not valid JSON
    done = resume(shard, {"a", "b", "c"})
    assert set(done) == {"a", "b"} and done["b"]["n"] == 2   # the torn line is dropped, not trusted
    assert set(resume(shard, {"b"})) == {"b"}                # a smaller --max-sessions run ignores the rest


def test_iter_events_streams_without_materialising():
    """One 116 MB session peaked at 7.3 GB under json.loads; the events must come out one at a time."""
    import json
    evs = [{"data": {"frame": [[[i]]], "levels_completed": 0}} for i in range(5)]
    blob = json.dumps(evs)
    assert list(iter_events(blob)) == evs
    assert list(iter_events(json.dumps(evs, indent=2))) == evs      # whitespace between elements
    assert list(iter_events("[]")) == [] and list(iter_events("")) == []
    assert list(iter_events(evs)) == evs                            # already decoded
    assert list(iter_events(None)) == []
    import types
    assert isinstance(iter_events(blob), types.GeneratorType)       # not a list built up front


def test_packed_store_matches_the_raw_parse():
    """The packed store is a 106x cheaper path to the same data, so it must be the same data.

    Reading one session from the released parquet costs 6.2 GB, because each file holds 50 sessions in a
    single row group; the packed form costs 0.06 GB. That is only safe if it is byte-identical to parsing
    the file, so this compares the two on the largest session and on one carrying the named action ids.
    """
    import numpy as np, pyarrow.parquet as pq
    raw = Path.home() / "Projects/arc_prize_2026/data/human_replays"
    if not PACKED.exists() or not raw.exists():
        print("skip: replay data not present")
        return
    checked = 0
    for f in sorted(raw.glob("*.parquet")):
        for b in pq.ParquetFile(f).iter_batches(batch_size=1, columns=["env", "guid", "game_id", "trajectory", "won"]):
            r = b.to_pylist()[0]
            big = len(r["trajectory"]) > 1e8
            if not (big or (r["env"] == "m0r0" and checked < 2)) or not pack_path(r["guid"]).exists():
                continue
            a, c = parse(r), load_packed(r["guid"])
            assert a["acts"] == c["acts"], r["guid"]
            assert a["levels"] == c["levels"] and a["states"] == c["states"] and a["avail"] == c["avail"]
            assert len(a["frames"]) == len(c["frames"])
            assert all(np.array_equal(x, y) for x, y in zip(a["frames"], c["frames"])), ("frames", r["guid"])
            checked += 1
            if checked >= 3:
                return
    assert checked, "no session compared"


def test_run_seq_budget_is_unevaluable_not_failure():
    """A random control can drive lf52 into steps costing 40 s each; that must not read as a clean failure."""
    import time
    from types import SimpleNamespace as NS

    class SlowEnv:
        """Each step costs a tenth of a second, as the pathological states do, only smaller."""
        def __init__(self): self.n = 0
        def action(self, *a, **k):
            time.sleep(0.1); self.n += 1
            return NS(levels_completed=0, state="NOT_FINISHED", frame=[[[0]]])

    import arc_prize_2026.arc3.level_transfer as M
    real_step, M._step = M._step, lambda e, a: e.action()
    try:
        r = M.run_seq(SlowEnv(), [(1, None)] * 100, 1, budget_s=0.3)
        assert r["end"] == "budget" and r["ok"] is False, r
        assert 1 <= r["n"] < 100 and r["of"] == 100, r      # says how far it got, and of how many
        fast = M.run_seq(SlowEnv(), [(1, None)] * 2, 1, budget_s=60)
        assert fast["end"] == "exhausted", fast             # a short run is unaffected
    finally:
        M._step = real_step
    assert BUDGET_S >= 60, "the budget must stay far above the ~0.3 s a normal control replay takes"


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
