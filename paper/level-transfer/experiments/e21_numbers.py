"""Regenerate every E21 number quoted in section 4 of the paper from the committed result file.

Reads only E21_level_transfer.json next to this file (the full-population run, 340 sessions), or the path given as the
first argument. No network, no environment replay, no other file of this repository. Needs numpy (the repository's
locked environment has it). Run from anywhere; from the repository root:

    uv run python paper/level-transfer/experiments/e21_numbers.py | diff - paper/level-transfer/experiments/e21_numbers.out
    uv run python paper/level-transfer/experiments/e21_numbers.py > paper/level-transfer/experiments/e21_numbers.out   # rewrite

`python3 -I` works too wherever numpy is installed system-wide; -I hides a user-site install, so on a machine where
numpy lives there use `python3` without -I. Verified identical output with numpy 2.0.2 (Python 3.9) and numpy 2.5.4
(Python 3.12).

The first 40 lines of the output are the 30 Oct 2026 analysis, unchanged. The block after "Added 2 Nov 2026" prints counts
the text quotes that the 30 Oct run did not print (the 6,185 random-control runs, the click/movement split of the
23 games, the games without an M3 value, transitions per movement game).

New analyses, all on the committed pair records:
  * session-clustered bootstrap (2,000 resamples, seed 0) for the M2 and M3 headline means, because pairs
    from one session are not independent and the 1,186 M1 pairs rest on 144 distinct transitions;
  * M3 with each movement game left out in turn, and a game-weighted (macro) mean, because three games hold
    48 percent of the M3 pairs;
  * M2 counted three ways (filed rule, games where a shuffle can differ, session-clustered).
"""
import hashlib
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "E21_level_transfer.json")
# Same list as CLICK_GAMES at line 23 of src/arc_prize_2026/arc3/human_sequences.py in this repository (13 games);
# a movement game is one of the other 12.
CLICK_GAMES = {"ar25", "bp35", "cn04", "ft09", "ka59", "lf52", "lp85", "r11l", "s5i5", "sb26", "sc25", "sk48", "vc33"}
rng = np.random.default_rng(0)
B = 2000


def cp_upper_zero(n, alpha=0.05):
    """Clopper-Pearson one-sided-to-two-sided upper bound at 95 percent for 0 successes in n trials."""
    return 1 - (alpha / 2) ** (1 / n)


raw = open(SRC, "rb").read()
res = json.loads(raw)
print("sha256", hashlib.sha256(raw).hexdigest())
print("sessions", len(res), "fully reproducible", sum(r["fidelity_full"] for r in res))

allp = [(r["env"], r["guid"], p) for r in res for p in r["pairs"]]
rep = [(g, s, p) for g, s, p in allp if p.get("reproducible") and "m1" in p]
print("pairs", len(allp), "testable", len(rep), f"({100 * len(rep) / len(allp):.1f}%)")
print("M1 endings", {e: sum(p["m1"]["end"] == e for _, _, p in rep) for e in sorted({p["m1"]["end"] for _, _, p in rep})})
print("M1 successes (all)", sum(p["m1"]["ok"] for _, _, p in rep))
c2_all = sum(p["c2"]["ok"] for _, _, p in rep)
print(f"C2 all {c2_all}/{len(rep)} = {100 * c2_all / len(rep):.2f}%")
print("C2 failures by game", {g: sum(not p["c2"]["ok"] for gg, _, p in rep if gg == g) for g in sorted({g for g, _, _ in rep}) if any(not p["c2"]["ok"] for gg, _, p in rep if gg == g)})
r23 = [(g, s, p) for g, s, p in rep if g != "tn36"]
c2 = sum(p["c2"]["ok"] for _, _, p in r23)
print(f"without tn36: pairs {len(r23)}, games {len({g for g, _, _ in r23})}, M1 successes {sum(p['m1']['ok'] for _, _, p in r23)}, C2 {c2}/{len(r23)} = {100 * c2 / len(r23):.2f}%")
trans = {(g, p["k"]) for g, _, p in r23}
trans_all = {(g, p["k"]) for g, _, p in rep}
print("distinct (game, k) transitions: without tn36", len(trans), "with tn36", len(trans_all))
print(f"Clopper-Pearson 95% upper bound, pairs as units (n={len(r23)}): {100 * cp_upper_zero(len(r23)):.2f}%")
print(f"Clopper-Pearson 95% upper bound, transitions as units (n={len(trans)}): {100 * cp_upper_zero(len(trans)):.2f}%")
sess = {s for _, s, _ in r23}
print("sessions contributing a testable pair (without tn36)", len(sess))
c1 = [x for _, _, p in r23 for x in p.get("c1", [])]
c3 = [x for _, _, p in r23 for x in p.get("c3", [])]
print("C1 runs", len(c1), "completions", sum(c1), "| C3 runs scored", len(c3), "completions", sum(c3))
# budget-excluded controls: runs that returned null/None or are missing
n_c3_missing = sum(5 - len(p.get("c3", [])) for _, _, p in rep)
print("C3 runs absent (excluded as unevaluable) among testable pairs", n_c3_missing)
len_ge = sum(p["len_k"] >= p["len_k1"] for _, _, p in rep)
print("budget |W_k| >= next human solution length:", len_ge, "of", len(rep), "; |W_k| > 60:", sum(p["len_k"] > 60 for _, _, p in rep))
# Budget restriction: M1 gives the replay |W_k| actions. Where that is shorter than the next human solution the
# replay cannot finish the level even if the plan transferred perfectly, so those pairs cannot refute transfer.
print("budget shorter than next human solution:", len(rep) - len_ge, "of", len(rep))
long_ok = [(g, s, p) for g, s, p in r23 if p["len_k"] >= p["len_k1"]]
tl = {(g, p["k"]) for g, _, p in long_ok}
print(f"budget-sufficient pairs without tn36: {len(long_ok)}, games {len({g for g, _, _ in long_ok})}, distinct transitions {len(tl)}, "
      f"M1 successes {sum(p['m1']['ok'] for _, _, p in long_ok)}")
print(f"  Clopper-Pearson 95% upper bound, pairs (n={len(long_ok)}): {100 * cp_upper_zero(len(long_ok)):.2f}%; "
      f"transitions (n={len(tl)}): {100 * cp_upper_zero(len(tl)):.2f}%")
print("  endings", {e: sum(p["m1"]["end"] == e for _, _, p in long_ok) for e in sorted({p["m1"]["end"] for _, _, p in long_ok})})

# ---- M2 over all pairs with a similarity
m2 = [(g, s, p["m2_sim"], p["m2_shuffle"]) for g, s, p in allp if "m2_sim" in p]
print("\nM2 pairs", len(m2), f"pooled sim {np.mean([a for *_, a, b in m2]):.4f} shuffle {np.mean([b for *_, a, b in m2]):.4f}")
games = sorted({g for g, *_ in m2})
d = {g: np.mean([a - b for gg, _, a, b in m2 if gg == g]) for g in games}
print("games above shuffle (filed rule, >0):", sum(v > 0 for v in d.values()), "of", len(games))
tol = 1e-9
print("games above by more than 1e-9:", sum(v > tol for v in d.values()), "; tied (|d|<=1e-9):", [g for g, v in d.items() if abs(v) <= tol], "; below:", [g for g, v in d.items() if v < -tol])
# session-clustered bootstrap of the pooled difference
bys = {}
for g, s, a, b in m2:
    bys.setdefault(s, []).append(a - b)
keys = list(bys)
sums = np.array([sum(bys[k]) for k in keys]); cnts = np.array([len(bys[k]) for k in keys])
bs = []
for _ in range(B):
    ix = rng.integers(0, len(keys), len(keys))
    bs.append(sums[ix].sum() / cnts[ix].sum())
print("pooled M2 difference", f"{np.mean([a - b for *_, a, b in m2]):.4f}", "session-cluster 95% CI", np.round(np.percentile(bs, [2.5, 97.5]), 4))
# per-game session-clustered CI: how many games have a CI excluding 0
ex = 0
dirs = []
for g in games:
    bg = {}
    for gg, s, a, b in m2:
        if gg == g:
            bg.setdefault(s, []).append(a - b)
    kk = list(bg)
    ss = np.array([sum(bg[k]) for k in kk]); cc = np.array([len(bg[k]) for k in kk])
    vals = [ss[i].sum() / cc[i].sum() for i in (rng.integers(0, len(kk), len(kk)) for _ in range(500))]
    lo, hi = np.percentile(vals, [2.5, 97.5])
    ex += (lo > 0 or hi < 0)
    dirs.append((g, 'above' if lo > 0 else 'below' if hi < 0 else 'spans 0'))
print("per-game direction:", {k: [g for g, v in dirs if v == k] for k in ("above", "below")})
print("games whose session-clustered 95% CI for (similarity - shuffle) excludes 0:", ex, "of", len(games))

# ---- M3 on movement games
mv = [(g, s, p) for g, s, p in allp if g not in CLICK_GAMES and "m3_transfer" in p and not math.isnan(p["m3_transfer"])]
t = np.array([p["m3_transfer"] for *_, p in mv]); ce = np.array([p["m3_ceiling"] for *_, p in mv])
nu = np.array([p["m3_null"] if p.get("m3_null") is not None else np.nan for *_, p in mv], dtype=float)
print("\nM3 movement pairs", len(mv), "games", len({g for g, *_ in mv}), f"transfer {t.mean():.3f} ceiling {ce.mean():.3f}")
ok = ~np.isnan(nu)
print("pairs with a null", ok.sum(), f"null {nu[ok].mean():.3f} transfer on those {t[ok].mean():.3f} ratio {t[ok].mean() / nu[ok].mean():.2f}")
print("distinct (game,k) transitions behind the M3 pairs", len({(g, p['k']) for g, _, p in mv}))
gm = {}
for g, s, p in mv:
    gm.setdefault(g, []).append(p["m3_transfer"])
print("per game (pairs, mean):", {g: (len(v), round(float(np.mean(v)), 2)) for g, v in sorted(gm.items())})
print(f"game-weighted (macro) mean over {len(gm)} games: {np.mean([np.mean(v) for v in gm.values()]):.3f}")
top3 = sorted(gm, key=lambda g: -len(gm[g]))[:3]
print("largest three games", top3, f"hold {100 * sum(len(gm[g]) for g in top3) / len(mv):.0f}% of pairs")
rest = [x for g, v in gm.items() if g not in top3 for x in v]
print(f"M3 without those three: {np.mean(rest):.3f} over {len(rest)} pairs")
print("leave-one-game-out M3 (pair mean):", {g: round(float(np.mean([x for h, v in gm.items() if h != g for x in v])), 3) for g in sorted(gm)})
# bootstrap by session (and, separately, by game)
bys = {}
for g, s, p in mv:
    bys.setdefault(s, []).append(p["m3_transfer"])
keys = list(bys); sums = np.array([sum(bys[k]) for k in keys]); cnts = np.array([len(bys[k]) for k in keys])
bs = [sums[ix].sum() / cnts[ix].sum() for ix in (rng.integers(0, len(keys), len(keys)) for _ in range(B))]
print("M3 pair mean, session-cluster 95% CI", np.round(np.percentile(bs, [2.5, 97.5]), 3), f"({len(keys)} sessions)")
gk = list(gm)
bg = [np.mean([np.mean(gm[gk[i]]) for i in ix]) for ix in (rng.integers(0, len(gk), len(gk)) for _ in range(B))]
print("M3 game-weighted mean, game-cluster 95% CI", np.round(np.percentile(bg, [2.5, 97.5]), 3), f"({len(gk)} games)")
print("M3 per-pair share below 0.8:", f"{100 * (t < 0.8).mean():.0f}%")

# ---- hand-checked cases (a failed assert stops the run)
assert abs(cp_upper_zero(144) - 0.02531) < 5e-5   # 1 - 0.025**(1/144), checked by hand: ln(0.025)=-3.689, /144=-0.02562, exp=0.97471
assert abs(cp_upper_zero(1186) - 0.003105) < 5e-5
assert len(r23) == 1186 and sum(p["m1"]["ok"] for _, _, p in r23) == 0
print("\nhand-checked asserts passed")

# ---- Added 2 Nov 2026: counts the text quotes that the lines above do not print. Nothing above this line was changed, so
# ---- the first 40 lines of the output are byte-identical to the 30 Oct e21_numbers.out. Uses no random numbers.
print("\nAdded 2 Nov 2026: counts quoted in the text")
all_games = {g for g, _, _ in allp}
click = set(CLICK_GAMES)
assert click <= all_games
print("games in the release", len(all_games), "| click-driven (CLICK_GAMES)", len(click), "| movement (the other)", len(all_games - click))
print("games with no testable pair:", sorted(all_games - {g for g, _, _ in rep}))
games23 = {g for g, _, _ in r23}
m1_click = sum(p["m1"]["ok"] for g, _, p in r23 if g in click)
m1_move = sum(p["m1"]["ok"] for g, _, p in r23 if g not in click)
print("the", len(games23), "games with a working positive control: click-driven", len(games23 & click), "| movement", len(games23 - click),
      "| M1 successes in click-driven", m1_click, "| in movement", m1_move)
print(f"mean pairs per distinct transition (without tn36): {len(r23) / len(trans):.1f}")
# C3 random control: five runs per testable pair; a run absent from "c3" is one the replay run log marks unevaluable because
# the environment exceeded the 60-second budget (E21_level_transfer.out: "C3 188/6185")
assert all(len(p.get("c3", [])) <= 5 for _, _, p in rep)
c3_expected = 5 * len(rep)
c3_absent = {g: sum(5 - len(p.get("c3", [])) for gg, _, p in rep if gg == g) for g in sorted({g for g, _, _ in rep})}
c3_absent = {g: n for g, n in c3_absent.items() if n}
print(f"C3 random-control runs expected (5 per testable pair) {c3_expected} | absent {sum(c3_absent.values())} "
      f"= {100 * sum(c3_absent.values()) / c3_expected:.1f}% | absent by game {c3_absent}")
# M3 coverage: a game has an M3 value when at least one of its pairs has one
m3_games = {g for g, _, p in allp if "m3_transfer" in p and not math.isnan(p["m3_transfer"])}
silent = sorted(all_games - m3_games)
no_pair = sorted(all_games - {g for g, _, _ in rep})
print("games with no M3 value in any pair:", len(silent), silent, "| without the game that has no testable pair:", len(set(silent) - set(no_pair)))
print("movement games with an M3 value:", len(m3_games - click), "of", len(all_games - click), "| movement games without:", sorted((all_games - click) - m3_games))
trans_by_game = {g: len({p["k"] for gg, _, p in mv if gg == g}) for g in sorted(gm)}
print("M3 per game (pairs, distinct transitions):", {g: (len(gm[g]), trans_by_game[g]) for g in sorted(gm)})
# 0 of n for M1 in each group of the 23 games, for the sentence "replay fails alike in the click-driven and movement-driven games"
assert m1_click == 0 and m1_move == 0
print("added block asserts passed")
