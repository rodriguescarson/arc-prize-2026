"""Hidden-set draws of the LLM harness: the numbers behind Table 2 and section 5b of the paper.

Reads hidden_draws.csv next to this file (or the path given as the first argument): every LLM-harness submission on
the hidden 55 games, rows 6 to 21 of submission/SUBMISSIONS.md as of 2 Nov 2026 (16 rows: 13 kept, 3 excluded, each
exclusion with a reason). Prints the per-variant table, the v2 (helper on) against v1 (helper off) comparison, the
five-draw no-helper pool and the 13-draw mean and SD, with the count of every draw taken.

Cross-check: when submission/SUBMISSIONS.md is found at the repository root, every CSV row is compared with the row of
that file that has the same number (submission id, kernel, version, time, status, score); any mismatch stops the run.
Rows added to that file after 2 Nov are not part of this table.

Stdlib only. Run from anywhere; from the repository root:

    python3 -I paper/level-transfer/experiments/hidden_draws.py | diff - paper/level-transfer/experiments/hidden_draws.out
    python3 -I paper/level-transfer/experiments/hidden_draws.py > paper/level-transfer/experiments/hidden_draws.out   # rewrite
"""
import csv
import os
import re
import sys
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, getcontext

getcontext().prec = 40
HERE = os.path.dirname(os.path.abspath(__file__))
CSV = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "hidden_draws.csv")
# <repo>/paper/level-transfer/experiments/ -> <repo>/submission/SUBMISSIONS.md
SUBMISSIONS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "submission", "SUBMISSIONS.md"))

# Copies of Franzen's unmodified notebook: mean 25.77, SD 3.93 (Kaggle discussion 745062, reference [19] of the paper;
# the thread is JavaScript-rendered and is not re-fetched here). The rule filed in HYPOTHESES.md line 211 used SD 3.9.
COPY_MEAN, COPY_SD, COPY_SD_FILED = Decimal("25.77"), Decimal("3.93"), Decimal("3.9")
Q2, Q1, Q3 = Decimal("0.01"), Decimal("0.1"), Decimal("0.001")


def r(x, q=Q2):
    return x.quantize(q, ROUND_HALF_UP)


def mean(v):
    return sum(v) / len(v)


def sd(v):
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)).sqrt()


def scores(rs):
    return [Decimal(x["score"]) for x in rs]


rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
assert [int(x["row"]) for x in rows] == list(range(6, 22)), "hidden_draws.csv must hold rows 6 to 21 of SUBMISSIONS.md"
kept = [x for x in rows if x["status"] == "kept"]
excluded = [x for x in rows if x["status"] == "excluded"]
assert len(kept) + len(excluded) == len(rows) and all(x["reason"] for x in excluded)
print(f"LLM-harness submissions on the hidden 55 in rows 6 to 21 of submission/SUBMISSIONS.md: {len(rows)} | kept {len(kept)} | excluded {len(excluded)}")
for x in excluded:
    print(f"  excluded row {x['row']} {x['submission_id']} {x['variant']} score {x['score']} ({x['submitted_ist']} IST): {x['reason']}")

# ---- the CSV is a copy of that file's rows
if os.path.exists(SUBMISSIONS):
    pat = re.compile(r"^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*carsonrodrigues/(\S+) v(\d+)\s*\|[^|]*\|[^|]*\|[^|]*\|\s*(\d{4}-\d\d-\d\d \d\d:\d\d)\s*\|\s*(\w+)\s*\|\s*\*\*([0-9.]+)\*\*")
    src = {}
    for line in open(SUBMISSIONS, encoding="utf-8"):
        m = pat.match(line)
        if m:
            src[int(m.group(1))] = m.groups()[1:]
    bad = []
    for x in rows:
        got = src.get(int(x["row"]))
        want = (x["submission_id"], x["kernel"], x["version"], x["submitted_ist"], "COMPLETE", x["score"])
        if got is None or got[:5] != want[:5] or Decimal(got[5]) != Decimal(want[5]):
            bad.append((x["row"], got, want))
    if bad:
        for b in bad:
            print("MISMATCH with submission/SUBMISSIONS.md, row", b[0], "file:", b[1], "csv:", b[2])
        sys.exit(1)
    print(f"cross-check: all {len(rows)} rows of hidden_draws.csv equal rows 6 to 21 of submission/SUBMISSIONS.md (id, kernel, version, time, COMPLETE, score)")
else:
    print("cross-check skipped: submission/SUBMISSIONS.md not found at the repository root")

# ---- one submission per day: the times are IST (UTC+5:30), so count days in both
ist = [datetime.strptime(x["submitted_ist"], "%Y-%m-%d %H:%M") for x in rows]
utc = [t - timedelta(hours=5, minutes=30) for t in ist]


def shared(days):
    seen = {}
    for x, d in zip(rows, days):
        seen.setdefault(d.date().isoformat(), []).append(x["submission_id"])
    return {d: ids for d, ids in seen.items() if len(ids) > 1}


print(f"days: {len(rows)} submissions; IST dates shared by more than one: {shared(ist) or 'none'}; UTC dates shared by more than one: {shared(utc) or 'none'}")

# ---- Table 2 and the draws not in it
print("\nvariant  helper  n  mean   SD     draws (kernel version), kept draws only")
order = ("v2", "v1", "v1f", "v8i", "v10")
assert {x["variant"] for x in kept} == set(order)
for var in order:
    rs = [x for x in kept if x["variant"] == var]
    v = scores(rs)
    s = f"{r(sd(v)):.2f}" if len(v) > 1 else "n/a"
    draws = ", ".join(f"{r(Decimal(x['score'])):.2f} (v{x['version']})" for x in rs)
    print(f"{var:7s}  {rs[0]['helper']:6s}  {len(v)}  {r(mean(v)):.2f}  {s:5s}  {draws}  [{rs[0]['submitted_ist'][:10]} to {rs[-1]['submitted_ist'][:10]}]")
assert len({x["helper"] for x in kept if x["variant"] == "v1"}) == 1

# ---- helper on (v2) against helper off (v1): two draws per arm
on = scores([x for x in kept if x["variant"] == "v2"])
off = scores([x for x in kept if x["variant"] == "v1"])
assert len(on) == len(off) == 2
gap = mean(off) - mean(on)
lo, hi = gap - Decimal("1.96") * COPY_SD, gap + Decimal("1.96") * COPY_SD
sd_mean2 = COPY_SD / Decimal(2).sqrt()
print(f"\nv1 (helper off) minus v2 (helper on), two draws each: {r(mean(off))} - {r(mean(on))} = {r(gap, Q3)} points (rounds to {r(gap, Q1)})")
print(f"copy SD {COPY_SD} (reference [19]); SD of a two-draw mean {r(sd_mean2)}; SD of a difference of two two-draw means {r(sd_mean2 * Decimal(2).sqrt())}; the gap is {r(gap / COPY_SD)} of it")
print(f"95% interval for off minus on at that SD: {r(lo, Q1)} to {r(hi, Q1)} ({r(lo, Q3)} to {r(hi, Q3)})")
for label, c in (("copy SD", COPY_SD), ("filed copy SD", COPY_SD_FILED)):
    d2 = c * Decimal(2).sqrt()
    print(f"SD of a difference of two single draws at the {label} {c}: {r(d2)}; twice that: {r(2 * d2)}")
print("rule filed before any pair ran (HYPOTHESES.md line 211, at the filed copy SD): an effect is claimed only above 11 points")

# ---- five no-helper draws (v1 + v1f) against the helper arm
pool = scores([x for x in kept if x["variant"] in ("v1", "v1f")])
assert len(pool) == 5
print(f"\nno-helper pool, v1 + v1f ({len(pool)} draws): mean {r(mean(pool)):.2f} SD {r(sd(pool)):.2f}; helper arm v2 ({len(on)} draws) mean {r(mean(on)):.2f}; pool minus helper arm {r(mean(pool) - mean(on), Q3)} (rounds to {r(mean(pool) - mean(on), Q1)})")

# ---- all kept draws (all on the Intel base)
allv = scores(kept)
variants = [v for v in order if any(x["variant"] == v for x in kept)]
print(f"all kept draws ({len(allv)} draws, {len(variants)} variants {', '.join(variants)}): mean {r(mean(allv)):.2f} SD {r(sd(allv)):.2f}")
se = COPY_SD / Decimal(len(allv)).sqrt()
print(f"copy mean {COPY_MEAN} SD {COPY_SD} (reference [19]): {len(allv)}-draw mean minus copy mean {r(mean(allv) - COPY_MEAN)}; standard error of a {len(allv)}-draw mean at the copy SD {r(se)}")
# the submission linked from the paper ("better of two draws, one SD above the 13-draw mean")
LINKED = "57477157"
lk = next(x for x in kept if x["submission_id"] == LINKED)
lk_pair = scores([x for x in kept if x["variant"] == lk["variant"]])
print(f"linked submission {LINKED} ({lk['variant']}, kernel version {lk['version']}): {r(Decimal(lk['score']))}, the better of its {len(lk_pair)} draws "
      f"{r(max(lk_pair))} and {r(min(lk_pair))}; {r(Decimal(lk['score']) - mean(allv))} above the {len(allv)}-draw mean = {r((Decimal(lk['score']) - mean(allv)) / sd(allv))} SD of the draws")
others = [x for x in kept if x["variant"] in ("v8i", "v10")]
print("draws not in Table 2:", "; ".join(f"{v}: " + ", ".join(f"{r(Decimal(x['score'])):.2f} (v{x['version']})" for x in others if x["variant"] == v) for v in ("v8i", "v10")))
