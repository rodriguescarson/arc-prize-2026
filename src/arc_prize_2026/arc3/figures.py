"""Paper figures from results.json files. Usage:
  uv run python -m arc_prize_2026.arc3.figures --ladder random=experiments/arc3_random_a2000_s0/results.json \
      explorer=... model_based=... --atlas experiments/arc3_E0_explorer_a2000_s0_logged/atlas.json --out paper/figures
Produces: fig1_atlas.png (distinct frames + no-op fraction per game), fig2_levels_ladder.png (levels per game
per agent), fig3_pred_acc.png (model prediction accuracy per game), fig4_learning_curve.png (actions/human
per level for games with >= 2 levels), plus tables as CSV. Colours: two hues + one accent, no orange+blue.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

C1, C2, C3, ACC = "#1b3a4b", "#5c7f93", "#b9c9d1", "#c0392b"


def load(path): return json.loads(Path(path).read_text())


def fig_atlas(atlas_path: Path, out: Path):
    rows = load(atlas_path)
    games = [r["game"] for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    ax[0].bar(games, [r["distinct_frames"] for r in rows], color=C1)
    ax[0].set_ylabel("distinct frames in 2000 actions"); ax[0].tick_params(axis="x", rotation=90)
    ax[1].bar(games, [r["noop_frac"] for r in rows], color=C2)
    ax[1].set_ylabel("fraction of actions that changed nothing"); ax[1].tick_params(axis="x", rotation=90)
    fig.suptitle("Exploration atlas of the 25 public ARC-AGI-3 games (novelty explorer, seed 0)")
    fig.tight_layout(); fig.savefig(out / "fig1_atlas.png", dpi=160); plt.close(fig)


def fig_ladder(runs: dict[str, dict], out: Path):
    names = list(runs)
    games = [g["game_id"][:4] for g in runs[names[0]]["games"]]
    fig, ax = plt.subplots(figsize=(11, 4))
    w = 0.8 / len(names)
    palette = [C3, C2, C1, ACC][: len(names)]
    for i, n in enumerate(names):
        lv = {g["game_id"][:4]: g["levels_completed"] for g in runs[n]["games"]}
        ax.bar([x + i * w for x in range(len(games))], [lv.get(g, 0) for g in games], width=w, label=f"{n} ({runs[n]['levels_completed']} levels, score {runs[n]['total_score']:.3f})", color=palette[i])
    ax.set_xticks([x + 0.4 for x in range(len(games))]); ax.set_xticklabels(games, rotation=90)
    ax.set_ylabel("levels completed (2000 actions)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out / "fig2_levels_ladder.png", dpi=160); plt.close(fig)
    with (out / "table_ladder.csv").open("w", newline="") as f:
        wtr = csv.writer(f); wtr.writerow(["game"] + [f"{n}_levels" for n in names] + [f"{n}_score" for n in names])
        for g in games:
            wtr.writerow([g] + [next(x["levels_completed"] for x in runs[n]["games"] if x["game_id"][:4] == g) for n in names]
                         + [round(next(x["score"] for x in runs[n]["games"] if x["game_id"][:4] == g), 3) for n in names])


def fig_pred_acc(run: dict, out: Path):
    games, memo, model = [], [], []
    for g in run["games"]:
        st = g.get("agent_stats") or {}; src = st.get("pred_by_source") or {}
        games.append(g["game_id"][:4]); memo.append(src.get("memo", [0, None])[1] or 0); model.append(src.get("model", [0, None])[1] or 0)
    fig, ax = plt.subplots(figsize=(11, 3.8))
    xs = range(len(games))
    ax.bar([x - 0.2 for x in xs], memo, width=0.4, label="memoised transitions (state determinism)", color=C1)
    ax.bar([x + 0.2 for x in xs], model, width=0.4, label="generative movement model", color=ACC)
    ax.set_xticks(list(xs)); ax.set_xticklabels(games, rotation=90); ax.set_ylim(0, 1.05); ax.set_ylabel("next-state prediction accuracy"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out / "fig3_pred_acc.png", dpi=160); plt.close(fig)


def fig_learning(run: dict, out: Path):
    fig, ax = plt.subplots(figsize=(6, 4))
    any_ = False
    palette = [C1, ACC, C2, "#6b4c8a", "#2e7d5b", "#8c6d1f"]
    i = 0
    for g in run["games"]:
        la, base = g.get("level_actions", []), g.get("baseline_actions", [])
        if len(la) >= 2:
            any_ = True
            ax.plot(range(1, len(la) + 1), [a / h for a, h in zip(la, base)], marker="o", label=g["game_id"][:4], color=palette[i % len(palette)])
            i += 1
    ax.axhline(1.0, color=C3, ls="--", lw=1)
    ax.set_yscale("log"); ax.set_xlabel("level"); ax.set_ylabel("agent actions / human baseline (log)")
    if any_: ax.legend(fontsize=8)
    ax.set_title("Within-game learning curves (games with ≥2 levels)")
    fig.tight_layout(); fig.savefig(out / "fig4_learning_curve.png", dpi=160); plt.close(fig)


def fig_budget(run4000: dict, out: Path, measured_cpu: dict[int, float] | None = None, kaggle_speed: float = 4.5,
               n_hidden: int = 110, budget_s: float = 30600.0):
    """E17: levels completed as a function of the per-game action cap (cumulative level-action counts of one
    4,000-action run) with the rerun CPU fraction from the 25-thread simulations' measured thread-CPU sums
    (seconds per 25 games), extrapolated as 110 games x mean x Kaggle slowdown."""
    budgets = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000]
    levels = []
    for b in budgets:
        n = 0
        for g in run4000["games"]:
            c = 0
            for x in g["level_actions"]:
                if x is None:
                    break
                c += x
                n += int(c <= b)
        levels.append(n)
    measured_cpu = measured_cpu or {1500: 451.0, 3000: 886.0}  # experiments/swarm_sim_c155_v6.out, swarm_sim_c155_a3000.out
    xs = sorted(measured_cpu); ys = [100 * measured_cpu[b] / 25 * n_hidden * kaggle_speed / budget_s for b in xs]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(budgets, levels, marker="o", color=C1, label="levels completed (public 25, one run)")
    ax.set_xlabel("actions per game (cap)"); ax.set_ylabel("levels completed", color=C1)
    ax.set_ylim(0, max(levels) + 3)
    ax2 = ax.twinx()
    ax2.plot(xs, ys, marker="s", ls="--", color=ACC, label="rerun CPU, measured thread-CPU x 110 games x 4.5")
    ax2.axhline(60, color=C3, ls=":", lw=1); ax2.set_ylabel("% of the 8.5 h rerun budget", color=ACC)
    ax2.set_ylim(0, 100)
    ax.axvline(3000, color=C2, lw=1, ls="-.")
    ax.set_title("E17: coverage vs action cap; cap set to 3,000 (57% of budget)")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower right", fontsize=8)
    fig.tight_layout(); fig.savefig(out / "fig5_budget.png", dpi=160); plt.close(fig)

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ladder", nargs="+", required=True, help="name=path/to/results.json ...")
    ap.add_argument("--atlas", default=None)
    ap.add_argument("--main", default=None, help="name (from --ladder) of the run for fig3/fig4; default last")
    ap.add_argument("--out", default="paper/figures")
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    runs = {kv.split("=", 1)[0]: load(kv.split("=", 1)[1]) for kv in a.ladder}
    if a.atlas:
        fig_atlas(Path(a.atlas), out)
    fig_ladder(runs, out)
    main_run = runs[a.main] if a.main else runs[list(runs)[-1]]
    fig_pred_acc(main_run, out); fig_learning(main_run, out)
    print("figures ->", sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
