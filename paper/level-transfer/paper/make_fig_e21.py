"""Figure 6: the E21 result, read from the full-population JSON rather than typed in.

Panel A is the whole argument: replaying the plan that solved level k completes level k+1 in none of
the 1,186 testable pairs from the 23 games whose positive control works, while the level's OWN winning
sequence completes 99.7% of them from the same snapshot. The positive control is what makes the zero a
measurement instead of a broken harness. tn36 is excluded because its positive control fails on all 51
pairs (the filed run, with tn36, is 0 of 1,237 pairs, 24 games, control 95.6%; see the paper's caveats).

Panel B is the other memory: a mechanics model learned on level k, scored on level k+1, against the
exact mean over all non-identity permutations of its action labels, with the in-sample ceiling and the
0.8 bar filed in advance, which it did not clear.

    uv run python paper/make_fig_e21.py experiments/E21_level_transfer.json paper/figures
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

C1, C2, C3, ACC = "#1b3a4b", "#5c7f93", "#b9c9d1", "#c0392b"

# Games whose positive control (C2, the level's own winning sequence) fails on every pair. Their M1 result
# is uninformative, so panel A leaves them out (see paper_full.md section 4, caveats).
EXCLUDE_M1 = {"tn36"}


def main(src: Path, out: Path) -> None:
    res = json.loads(src.read_text())
    pairs = [p for r in res for p in r["pairs"]]
    rep_all = [(r["env"], p) for r in res for p in r["pairs"] if "m1" in p]
    rep = [p for env, p in rep_all if env not in EXCLUDE_M1]
    n_games = len({env for env, _ in rep_all if env not in EXCLUDE_M1})

    m1 = np.mean([p["m1"]["ok"] for p in rep])
    c1 = np.mean([np.mean(p["c1"]) for p in rep if p.get("c1")])
    c2 = np.mean([p["c2"]["ok"] for p in rep])
    c3 = np.mean([np.mean(p["c3"]) for p in rep if p.get("c3")])

    # P21b was filed on MOVEMENT games only, so the figure must use that subset: including the click
    # games gives 843 pairs at 0.716 against a 0.247 null, not the 431 pairs at 0.740 the bar was set for.
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
    from arc_prize_2026.arc3.human_sequences import CLICK_GAMES
    mv = [p for r in res for p in r["pairs"]
          if r["env"] not in CLICK_GAMES and "m3_transfer" in p and not np.isnan(p["m3_transfer"])]
    t = np.mean([p["m3_transfer"] for p in mv])
    ceil = np.mean([p["m3_ceiling"] for p in mv])
    null = np.nanmean([p["m3_null"] for p in mv])

    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.0))

    # A: plan transfer and its controls
    labels = ["replay $W_k$\n(the plan)", "$W_k$ shuffled\n(control)", "random actions\n(control)",
              "own $W_{k+1}$\n(positive control)"]
    vals = [m1 * 100, c1 * 100, c3 * 100, c2 * 100]
    bars = ax[0].bar(labels, vals, color=[ACC, C3, C3, C1], width=0.62)
    for b, v in zip(bars, vals):
        ax[0].text(b.get_x() + b.get_width() / 2, v + 2.5, f"{v:.1f}%", ha="center",
                   fontsize=10, fontweight="bold" if v < 1 else "normal")
    ax[0].set_ylim(0, 108)
    ax[0].set_ylabel("level $k{+}1$ completed (% of pairs)")
    ax[0].set_title(f"A. The plan does not transfer\n{len(rep):,} testable pairs, {n_games} games", fontsize=10.5)
    ax[0].tick_params(axis="x", labelsize=10)

    # B: mechanics transfer against its permuted null
    labels2 = ["permuted\nnull", "learned on $k$,\nscored on $k{+}1$", "in-sample\nceiling"]
    vals2 = [null, t, ceil]
    bars2 = ax[1].bar(labels2, vals2, color=[C3, C1, C2], width=0.58)
    for b, v in zip(bars2, vals2):
        # a label just under the 0.8 line would sit on it, so that one goes inside the bar
        inside = 0.72 < v < 0.8
        ax[1].text(b.get_x() + b.get_width() / 2, v - 0.025 if inside else v + 0.025, f"{v:.3f}",
                   ha="center", va="top" if inside else "baseline", fontsize=10,
                   color="white" if inside else "black")
    ax[1].axhline(0.8, color=ACC, ls="--", lw=1.3)
    # above the line on the left, over the short null bar, so it cannot collide with a value label
    ax[1].text(-0.36, 0.815, "filed bar 0.8 (not cleared)", color=ACC, fontsize=10,
               ha="left", va="bottom")
    ax[1].set_ylim(0, 1.08)
    ax[1].set_ylabel("action-effect prediction accuracy")
    n_mv_games = len({r["env"] for r in res for p in r["pairs"]
                      if r["env"] not in CLICK_GAMES and "m3_transfer" in p and not np.isnan(p["m3_transfer"])})
    ax[1].set_title(f"B. The mechanics partly do\n{len(mv):,} movement pairs, {n_mv_games} games", fontsize=10.5)
    ax[1].tick_params(axis="x", labelsize=10)

    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
        a.grid(axis="y", color=C3, alpha=0.35, lw=0.7)
        a.set_axisbelow(True)

    out.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out / "fig6_e21_transfer.png", dpi=170)
    plt.close(fig)
    print(f"M1 {m1:.3%}  C1 {c1:.3%}  C3 {c3:.3%}  C2 {c2:.1%}   "
          f"M3 {t:.3f} null {null:.3f} ceiling {ceil:.3f}  ({len(rep)} pairs, {n_games} games, "
          f"{len(mv)} movement pairs, {n_mv_games} games)")
    print(f"-> {out / 'fig6_e21_transfer.png'}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
