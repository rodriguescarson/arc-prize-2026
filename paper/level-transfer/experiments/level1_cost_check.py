"""Median level-1 cost (agent actions / human baseline actions) for the v4 contact-curiosity pair on the public 25.

Source results (tracked in this repository under the top-level experiments/):
  experiments/arc3_E2_v4_hud_contact1_a2000_s0/results.json   contact curiosity on
  experiments/arc3_E2_v4_hud_contact0_a2000_s0/results.json   contact curiosity off
Per game: level_actions[0] / baseline_actions[0]; games that never cleared level 1 are absent (empty level_actions).
Quoted in paper/paper_full.md section 6 (21.2 and 8.6 times; 21.95 against 8.59 on the games both sets share).

Run: python3 -I experiments/level1_cost_check.py > experiments/level1_cost_check.out
"""
import hashlib
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "experiments"
ON, OFF = "arc3_E2_v4_hud_contact1_a2000_s0", "arc3_E2_v4_hud_contact0_a2000_s0"


def load(name):
    path = ROOT / name / "results.json"
    raw = path.read_bytes()
    d = json.loads(raw)
    ratios = {
        g["game_id"][:4]: g["level_actions"][0] / g["baseline_actions"][0]
        for g in d["games"]
        if g["level_actions"]
    }
    return ratios, hashlib.sha256(raw).hexdigest()


on, sha_on = load(ON)
off, sha_off = load(OFF)
shared = sorted(set(on) & set(off))

print("sha256 contact on ", sha_on, ON)
print("sha256 contact off", sha_off, OFF)
print()
print("game   contact_on  contact_off   (agent level-1 actions / human baseline actions)")
for g in sorted(set(on) | set(off)):
    a = f"{on[g]:10.2f}" if g in on else "         -"
    b = f"{off[g]:11.2f}" if g in off else "          -"
    print(f"{g}   {a}  {b}{'   shared' if g in shared else ''}")
print()
print("contact ON ", len(on), "games, median", round(st.median(on.values()), 2))
print("contact OFF", len(off), "games, median", round(st.median(off.values()), 2))
print(
    "shared", len(shared), "games: ON", round(st.median(on[g] for g in shared), 2),
    "OFF", round(st.median(off[g] for g in shared), 2),
)
