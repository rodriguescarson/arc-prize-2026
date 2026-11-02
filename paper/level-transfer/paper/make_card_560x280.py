"""Kaggle card image (560x280) for the paper-track writeup, Option B wording (0 of 1,186 pairs, 23 games).

Numbers come from experiments/E21_level_transfer.json (see paper/make_fig_e21.py and paper/paper_full.md section 4).
Run from anywhere: python3 paper/make_card_560x280.py  -> paper/figures/card_560x280.png
"""
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = pathlib.Path(__file__).resolve().parent / "figures" / "card_560x280.png"
DARK, MUTED, ACC, RULE = "#1b3a4b", "#5c7f93", "#c0392b", "#b9c9d1"
fig = plt.figure(figsize=(5.6, 2.8), dpi=100)
fig.patch.set_facecolor("white")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 560)
ax.set_ylim(280, 0)
ax.axis("off")


def t(y, s, size, color, weight="normal"):
    ax.text(280, y, s, ha="center", va="center", fontsize=size, color=color, fontweight=weight, family="DejaVu Sans")


t(26, "What should an agent carry", 14, DARK, "bold")
t(62, "from one level to the next?", 14, DARK, "bold")
ax.plot([45, 515], [96, 96], color=RULE, lw=1.2)
t(116, "Replaying the plan: does not transfer", 12, ACC, "bold")
t(144, "re-solves the next level in 0 of 1,186 pairs  ·  23 games", 11, DARK)
t(166, "control (the level's own winning sequence): 99.7%", 9, MUTED)
t(202, "The mechanics: partly transfer", 12, DARK, "bold")
t(230, "next-level movement predicted at 0.740 (null 0.301)", 11, DARK)
t(258, "340 human replay sessions  ·  3 predictions filed in advance, 1 met", 8, MUTED)
fig.savefig(OUT, dpi=100)
print("wrote", OUT)
