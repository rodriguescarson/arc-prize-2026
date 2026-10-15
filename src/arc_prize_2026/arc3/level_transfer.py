"""E21: what carries over between levels, the plan or the mechanics? (pre-registered in HYPOTHESES.md)

Population: all 340 human sessions of the public 25 (HF mirror of the ARC Prize public demo data), same game
builds as the local environments. No agent is involved.

F   fidelity gate: replay each session's recorded actions in the local environment and compare every frame
    with the recorded one; a session is usable for in-environment tests up to its first mismatch.
M1  plan transfer: at the start of level k+1 (snapshot of the environment right after the human completed
    level k), execute W_k, the last attempt that completed level k (resets excluded, as the LLM harness's
    `solved_levels()` returns it; click coordinates verbatim). Success = level k+1 completed within |W_k|
    actions. Controls: C1 W_k shuffled (5x), C2 W_{k+1} itself (positive control), C3 uniform random actions
    from the available set, same length (5x).
M2  plan similarity on recorded data: 1 - Levenshtein(W_k, W_{k+1}) / max length over action-id tokens,
    against W_k shuffled (5x).
M3  mechanics transfer on recorded data, actions 1-5: each action's modal displacement learned on level k,
    scored on level k+1 steps where something moved (hit = prediction among the step's displacements).
    Ceiling: scored on level k itself. Null: exact mean over all non-identity permutations of the labels.

Usage: uv run python -m arc_prize_2026.arc3.level_transfer data/human_replays --pack   (once, ~3 min)
       uv run python -m arc_prize_2026.arc3.level_transfer data/human_replays [--max-sessions N] [--workers 6]
Each finished session is appended to E21_level_transfer.jsonl, so a run that is killed resumes where it
stopped when the same command is given again; --restart throws that away and starts from zero.
"""
from __future__ import annotations

import copy
import itertools
import json
import logging
import sys
import time
import zlib
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from .human_replays import perceive
from .human_sequences import CLICK_GAMES
from .perception import diff

ROOT = Path(__file__).resolve().parents[3]
N_SHUFFLE = 5
_ARC = None


def _arc():
    global _ARC
    if _ARC is None:
        logging.disable(logging.INFO)
        from arc_agi import Arcade, OperationMode
        from .runner import DEFAULT_ENVS
        _ARC = Arcade(environments_dir=str(DEFAULT_ENVS), recordings_dir=str(ROOT / "data" / "arc3_recordings"),
                      operation_mode=OperationMode.OFFLINE)
    return _ARC


#: the released replays write the action id in two forms, numeric ("6") and named ("ACTION6", "RESET");
#: the named form is 8% of all events and appears in 23 of the 340 sessions (checked 2026-10-15 over the
#: full population). Anything else is unknown and makes the rest of its session unusable.
NAMED = {"RESET": 0, **{f"ACTION{i}": i for i in range(1, 8)}}


def action_id(v) -> int:
    """Action id from either form, or -1 when it is neither."""
    s = str(v if v is not None else "").strip()
    if s.isdigit() and 0 <= int(s) <= 7:
        return int(s)
    return NAMED.get(s.upper(), -1)


def iter_events(traj):
    """Yield a session's recorded events one at a time.

    The released sessions run from 0.02 MB to 116 MB of trajectory JSON. `json.loads` on the largest one
    builds about 7.3 GB of Python objects, although the loop below keeps only a single 64x64 uint8 frame
    per event: three workers each holding one of those is what exhausted memory and wedged the run. Decoding
    the top-level array element by element holds the string plus one event instead.
    """
    if not isinstance(traj, str):
        yield from (traj or [])
        return
    dec = json.JSONDecoder()
    i, n = traj.find("["), len(traj)
    if i < 0:
        return
    i += 1
    while i < n:
        while i < n and traj[i] in ", \t\r\n":
            i += 1
        if i >= n or traj[i] == "]":
            return
        ev, i = dec.raw_decode(traj, i)
        yield ev


def parse(row) -> dict:
    """Recorded events -> parallel lists. Event i holds the action that produced frame i (event 0 = RESET)."""
    acts, frames, levels, states, avail = [], [], [], [], None
    for ev in iter_events(row["trajectory"]):
        d = ev.get("data") or {}
        fr = d.get("frame")
        if not fr:
            continue
        ai = d.get("action_input") or {}
        aid = action_id(ai.get("id"))
        dat = ai.get("data") or {}
        xy = (int(dat["x"]), int(dat["y"])) if aid == 6 and dat.get("x") is not None and dat.get("y") is not None else None
        acts.append((aid, xy))
        frames.append(np.asarray(fr[-1], dtype=np.uint8))
        levels.append(int(d.get("levels_completed", 0)))
        states.append(str(d.get("state", "")))
        if avail is None and d.get("available_actions"):
            aa = d["available_actions"]
            avail = [int(a) for a in (json.loads(aa) if isinstance(aa, str) else aa)]
    return {"acts": acts, "frames": frames, "levels": levels, "states": states, "avail": avail or [1, 2, 3, 4]}


PACKED = ROOT / "data" / "human_replays_packed"


def pack_path(guid: str) -> Path:
    return PACKED / f"{guid}.npz"


def pack(d: Path) -> int:
    """Convert the released parquet files into one compact file per session, once.

    The replays are stored as 7 parquet files of 50 sessions, one row group each, so reading any single
    session decompresses every session in its file: 6.2 GB for one `read_table`, 2.6 GB streaming a single
    row. That cost was paid once per session per run and is what exhausted a 16 GB machine. Each session's
    parsed arrays are a few MB, so they are written out once and read directly afterwards. The packed form
    is exactly what `parse()` returns, so nothing about the measurement changes.
    """
    PACKED.mkdir(parents=True, exist_ok=True)
    cols = ["env", "guid", "game_id", "trajectory", "won"]
    n = 0
    for f in sorted(d.glob("*.parquet")):
        for batch in pq.ParquetFile(f).iter_batches(batch_size=1, columns=cols):
            row = batch.to_pylist()[0]
            out = pack_path(row["guid"])
            if out.exists():
                continue
            s = parse(row)
            np.savez_compressed(
                out,
                frames=np.stack(s["frames"]) if s["frames"] else np.zeros((0, 0, 0), np.uint8),
                act_ids=np.array([a for a, _ in s["acts"]], np.int16),
                act_xy=np.array([xy if xy else (-1, -1) for _, xy in s["acts"]], np.int16),
                levels=np.array(s["levels"], np.int32),
                states=np.array(s["states"], dtype=object),
                avail=np.array(s["avail"], np.int16),
                env=row["env"], game_id=row["game_id"], guid=row["guid"],
            )
            n += 1
            del s, row, batch
    return n


def load_packed(guid: str) -> dict:
    z = np.load(pack_path(guid), allow_pickle=True)
    xy = z["act_xy"]
    acts = [(int(a), None if xy[i][0] < 0 else (int(xy[i][0]), int(xy[i][1]))) for i, a in enumerate(z["act_ids"])]
    return {"acts": acts, "frames": list(z["frames"]), "levels": [int(v) for v in z["levels"]],
            "states": [str(v) for v in z["states"]], "avail": [int(v) for v in z["avail"]]}


def winning_sequences(acts, levels) -> dict[int, tuple[int, int, list]]:
    """level k (1-based) -> (start index of the winning attempt, completing index, actions of that attempt).
    Mirrors `compute_solved_levels`: the attempt restarts at every RESET on that level."""
    out, cur, cur_start = {}, [], 1
    for i in range(1, len(acts)):
        aid = acts[i][0]
        if aid == 0:
            cur, cur_start = [], i + 1
            continue
        cur.append(acts[i])
        if levels[i] > levels[i - 1]:
            out.setdefault(levels[i], (cur_start, i, list(cur)))   # first completion only (a full reset can repeat a level)
            cur, cur_start = [], i + 1
    return out


def _step(env, a):
    from arcengine import GameAction
    aid, xy = a
    act = GameAction.from_id(aid) if hasattr(GameAction, "from_id") else list(GameAction)[aid]
    data = {"x": xy[0], "y": xy[1]} if xy is not None else {}
    return env.step(act, data=data)


def run_seq(env, seq, target_level: int) -> dict:
    """Execute seq on a copy of env; success when levels_completed reaches target_level."""
    e = copy.deepcopy(env)
    for n, a in enumerate(seq, 1):
        r = _step(e, a)
        if r is None:
            return {"ok": False, "n": n, "end": "none"}
        if r.levels_completed >= target_level:
            return {"ok": True, "n": n, "end": "level"}
        if str(r.state).endswith("GAME_OVER"):
            return {"ok": False, "n": n, "end": "game_over"}
    return {"ok": False, "n": len(seq), "end": "exhausted"}


def lev(a, b) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def sim(a, b) -> float:
    return 1.0 - lev(a, b) / max(len(a), len(b), 1)


def step_displacements(frames, acts, lo, hi) -> list[tuple[int, set]]:
    """(action, set of object displacements) for movement steps i in [lo, hi] where something moved."""
    out = []
    for i in range(max(lo, 1), hi + 1):
        aid = acts[i][0]
        if aid in (1, 2, 3, 4, 5):
            d = diff(perceive(frames[i - 1]), perceive(frames[i]))
            ds = {delta for _, _, delta in d["moved"]}
            if ds:
                out.append((aid, ds))
    return out


def modal_model(steps) -> dict[int, tuple]:
    c: dict[int, Counter] = defaultdict(Counter)
    for aid, ds in steps:
        for delta in ds:
            c[aid][delta] += 1
    return {a: cnt.most_common(1)[0][0] for a, cnt in c.items()}


def hit_rate(model, steps, relabel=None) -> tuple[float, int]:
    scored = [(a, ds) for a, ds in steps if (relabel or {}).get(a, a) in model]
    if not scored:
        return float("nan"), 0
    hits = sum(model[(relabel or {}).get(a, a)] in ds for a, ds in scored)
    return hits / len(scored), len(scored)


def analyse(row) -> dict:
    rng = np.random.default_rng(zlib.crc32(row["guid"].encode()))
    s = load_packed(row["guid"]) if row.get("trajectory") is None else parse(row)
    acts, frames, levels = s["acts"], s["frames"], s["levels"]
    game = row["env"]
    res = {"env": game, "guid": row["guid"], "n": len(acts), "max_level": max(levels) if levels else 0}
    # F: fidelity replay
    env = _arc().make(row["game_id"], seed=0)
    first_mismatch, snaps = None, {}
    for i, a in enumerate(acts):
        if a[0] < 0:                 # an id in neither form: the rest of this session cannot be replayed
            first_mismatch = i
            res["unknown_action_at"] = i
            break
        r = _step(env, a)
        if r is None or not np.array_equal(np.asarray(r.frame[-1], dtype=np.uint8), frames[i]):
            first_mismatch = i
            break
        if i > 0 and levels[i] > levels[i - 1] and levels[i] not in snaps:
            snaps[levels[i]] = copy.deepcopy(env)      # start of level levels[i] + 1
    res["first_mismatch"] = first_mismatch
    res["fidelity_full"] = first_mismatch is None
    wins = winning_sequences(acts, levels)
    pairs = []
    for k in sorted(wins):
        if k + 1 not in wins:
            continue
        sk, ik, wk = wins[k]
        sk1, ik1, wk1 = wins[k + 1]
        if not ik < ik1:
            continue
        p = {"k": k, "len_k": len(wk), "len_k1": len(wk1)}
        # F per pair: the human's own path through level k+1 reproduces
        p["reproducible"] = first_mismatch is None or first_mismatch > ik1
        # M2
        tk, tk1 = [a for a, _ in wk], [a for a, _ in wk1]
        shuf = [list(rng.permutation(tk)) for _ in range(N_SHUFFLE)]
        p["m2_sim"] = sim(tk, tk1)
        p["m2_shuffle"] = float(np.mean([sim(x, tk1) for x in shuf]))
        # M1 (only on reproducible pairs, from the snapshot at the start of level k+1)
        if p["reproducible"] and k in snaps:
            env0 = snaps.pop(k)        # freed as soon as this pair is done
            p["m1"] = run_seq(env0, wk, k + 1)
            p["c1"] = [run_seq(env0, [wk[j] for j in rng.permutation(len(wk))], k + 1)["ok"] for _ in range(N_SHUFFLE)]
            p["c2"] = run_seq(env0, wk1, k + 1)
            av = s["avail"]
            def rnd():
                out = []
                for _ in range(len(wk)):
                    aid = int(rng.choice(av))
                    out.append((aid, (int(rng.integers(0, 64)), int(rng.integers(0, 64))) if aid == 6 else None))
                return out
            p["c3"] = [run_seq(env0, rnd(), k + 1)["ok"] for _ in range(N_SHUFFLE)]
        # M3 (recorded data): level k = [start of level k .. its completion]; level k+1 likewise
        lk_lo = (wins[k - 1][1] + 1) if (k - 1) in wins else 1
        steps_k = step_displacements(frames, acts, lk_lo, ik)
        steps_k1 = step_displacements(frames, acts, ik + 1, ik1)
        model = modal_model(steps_k)
        if model and steps_k1:
            p["m3_transfer"], p["m3_n"] = hit_rate(model, steps_k1)
            p["m3_ceiling"], _ = hit_rate(model, steps_k)
            labels = sorted(model)
            nulls = []
            for perm in itertools.permutations(labels):
                if perm == tuple(labels):
                    continue
                nulls.append(hit_rate(model, steps_k1, relabel=dict(zip(labels, perm)))[0])
            p["m3_null"] = float(np.nanmean(nulls)) if nulls else float("nan")
            p["m3_n_actions"] = len(labels)
        pairs.append(p)
    res["pairs"] = pairs
    snaps.clear(); del frames, env
    return res


def summarise(results: list[dict]) -> str:
    lines = []
    allp = [(r["env"], p) for r in results for p in r["pairs"]]
    n_pairs = len(allp)
    rep = [(g, p) for g, p in allp if "m1" in p]
    lines.append(f"sessions {len(results)}; fully reproducible {sum(r['fidelity_full'] for r in results)}; "
                 f"consecutive completed level pairs {n_pairs}; reproducible pairs {len(rep)} "
                 f"({len(rep) / max(n_pairs, 1):.1%})")
    if rep:
        m1 = np.mean([p["m1"]["ok"] for _, p in rep]); c1 = np.mean([np.mean(p["c1"]) for _, p in rep])
        c2 = np.mean([p["c2"]["ok"] for _, p in rep]); c3 = np.mean([np.mean(p["c3"]) for _, p in rep])
        lines.append(f"M1 W_k completes k+1: {m1:.1%}   C1 shuffled {c1:.1%}   C2 own W_k+1 {c2:.1%}   C3 random {c3:.1%}")
        ends = Counter(p["m1"]["end"] for _, p in rep)
        lines.append(f"M1 endings: {dict(ends)}")
    lines.append("")
    lines.append("game  click pairs rep  M1    C1    C2    C3   | M2 sim  shuf  | M3 transfer ceiling null  n_steps")
    by = defaultdict(list)
    for g, p in allp:
        by[g].append(p)
    games_m1_zero = games_m2_exceeds = 0
    m3_rows = []
    for g in sorted({r["env"] for r in results}):
        ps = by.get(g, [])
        rp = [p for p in ps if "m1" in p]
        f = lambda xs: f"{np.mean(xs):.2f}" if len(xs) else "  — "
        m1 = [p["m1"]["ok"] for p in rp]
        if sum(m1) == 0:
            games_m1_zero += 1
        d2 = [p["m2_sim"] - p["m2_shuffle"] for p in ps]
        if d2 and np.mean(d2) > 0:
            games_m2_exceeds += 1
        m3 = [p for p in ps if "m3_transfer" in p and not np.isnan(p["m3_transfer"])]
        if m3:
            m3_rows.append((g, m3))
        lines.append(
            f"{g:5s} {'C' if g in CLICK_GAMES else 'M'}     {len(ps):4d} {len(rp):3d}  {f(m1)}  "
            f"{f([np.mean(p['c1']) for p in rp])}  {f([p['c2']['ok'] for p in rp])}  {f([np.mean(p['c3']) for p in rp])} | "
            f"{f([p['m2_sim'] for p in ps])}  {f([p['m2_shuffle'] for p in ps])} | "
            f"{f([p['m3_transfer'] for p in m3])}  {f([p['m3_ceiling'] for p in m3])}  "
            f"{f([p['m3_null'] for p in m3 if not np.isnan(p['m3_null'])])}  {sum(p['m3_n'] for p in m3)}"
        )
    lines.append("")
    lines.append(f"P21a: games with 0 successful W_k replays {games_m1_zero}/25 (prediction: >= 20; overall <= 10%)")
    lines.append(f"P21c: games where M2 similarity exceeds its shuffle control {games_m2_exceeds}/25 (prediction: < 13)")
    mv = [p for g, ps in m3_rows if g not in CLICK_GAMES for p in ps]
    if mv:
        t = np.mean([p["m3_transfer"] for p in mv]); c = np.mean([p["m3_ceiling"] for p in mv])
        nl = np.nanmean([p["m3_null"] for p in mv])
        lines.append(f"P21b: movement games, pair-mean M3 transfer {t:.3f} (ceiling {c:.3f}, permuted null {nl:.3f}, "
                     f"ratio {t / nl if nl else float('inf'):.1f}x; n pairs {len(mv)}) (prediction: >= 0.8 and >= 3x)")
    return "\n".join(lines)


def jsonable(o):
    return o.item() if isinstance(o, (np.integer, np.floating, np.bool_)) else o


def resume(shard: Path, wanted: set[str]) -> dict[str, dict]:
    """Sessions already finished, read back from the shard file.

    The full population takes ~25 min and the run has been killed four times (twice by the session
    closing, twice by system memory pressure), each time losing everything. One JSON line per finished
    session means a rerun costs only what was in flight. A line half-written when the process died is
    not valid JSON, so it is dropped rather than trusted.
    """
    done = {}
    if not shard.exists():
        return done
    for line in shard.read_text().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("guid") in wanted:
            done[r["guid"]] = r
    return done


def main(argv: list[str]) -> None:
    d = Path(argv[0]) if argv else ROOT / "data" / "human_replays"
    max_s = int(argv[argv.index("--max-sessions") + 1]) if "--max-sessions" in argv else None
    workers = int(argv[argv.index("--workers") + 1]) if "--workers" in argv else 4
    if "--pack" in argv:
        print(f"packed {pack(d)} new sessions into {PACKED}")
        return
    # the index carries no trajectory: the parent never holds a session, workers read the packed file
    rows = []
    for f in sorted(d.glob("*.parquet")):
        t = pq.read_table(f, columns=["env", "guid", "game_id", "won"])
        rows += [{**r, "trajectory": None} for r in t.to_pylist()]
        del t
    rows = rows[:max_s] if max_s else rows
    missing = [r for r in rows if not pack_path(r["guid"]).exists()]
    if missing:
        print(f"{len(missing)} sessions are not packed yet; run with --pack first", flush=True)
        return
    out = ROOT / "experiments" / "human_replays" / ("E21_level_transfer.json" if not max_s else f"E21_level_transfer_n{max_s}.json")
    shard = out.with_suffix(".jsonl")
    if "--restart" in argv and shard.exists():
        shard.unlink()
    done = resume(shard, {r["guid"] for r in rows})
    todo = [r for r in rows if r["guid"] not in done]
    results = list(done.values())
    print(f"{len(rows)} sessions: {len(done)} already in {shard.name}, {len(todo)} to run on {workers} workers", flush=True)
    t0 = time.time()
    if todo:
        # ProcessPoolExecutor, not multiprocessing.Pool: when the OS kills a worker, Pool waits for a result
        # that will never arrive (this run hung for 63 minutes that way), while this raises BrokenProcessPool.
        # One task per child returns each session's memory instead of keeping the high-water mark.
        with shard.open("a") as f, ProcessPoolExecutor(workers, max_tasks_per_child=1) as pool:
            for i, r in enumerate(pool.map(analyse, todo, chunksize=1), 1):
                f.write(json.dumps(r, default=jsonable) + "\n")
                f.flush()
                results.append(r)
                if i % 10 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)} done, {time.time() - t0:.0f} s", flush=True)
    out.write_text(json.dumps(results, default=jsonable, indent=1))
    print(summarise(results))
    print(f"-> {out}  ({len(results)} sessions, {time.time() - t0:.0f} s this run)")


if __name__ == "__main__":
    main(sys.argv[1:])
