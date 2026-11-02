"""How often M1's budget |W_k| is at least as long as the next human solution |W_{k+1}| (E21, testable pairs).

Descriptive, computed after the E21 outcome; not a filed prediction. Reads E21_level_transfer.json next to this file
(or the path given as the first argument); quoted in paper/paper_full.md section 4 and paper/writeup_v2.md.
Run from anywhere: python3 -I experiments/budget_check.py > experiments/budget_check.out
"""
import json
import os
import sys

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "E21_level_transfer.json")
d = json.load(open(path))
for label, keep in (("all testable pairs", lambda e: True), ("without tn36", lambda e: e != "tn36")):
    pairs = [p for s in d for p in s["pairs"] if p.get("reproducible") and keep(s["env"])]
    fit = [p for p in pairs if p["len_k1"] <= p["len_k"]]
    done = sum(1 for p in fit if p["m1"]["ok"])
    print(f"{label}: {len(pairs)} pairs, next human solution no longer than |W_k| in {len(fit)} ({len(fit) / len(pairs):.1%}); "
          f"W_k completes the next level in {done} of those")
