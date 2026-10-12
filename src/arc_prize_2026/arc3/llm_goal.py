"""E19: a decision model as goal proposer over the symbolic state.

The agent keeps perception, the effect model, the planner and memory; this module only answers one question at
a level start (and every `llm_every` actions while no transition has been seen): *which currently-false goal
predicate from the template menu should the planner aim for?* The proposer sees a ~600-token summary of the
level (object classes, the mover and its learned displacements, what the last transition changed) and a
numbered menu; it returns one index, or "explore" (= no goal, identical to the plain agent).

Proposers: `StubProposer` (tests and the control: always "explore" reproduces the plain agent exactly),
`ChatProposer` (OpenRouter chat/completions, temperature 0), `JevProposer` (OpenRouter Decisions API, a
"choice" question with per-option probabilities). Every remote answer is cached on disk under
`experiments/llm_cache/` keyed by the request, so re-runs are free and deterministic. The Kaggle rerun has no
internet: this is a development experiment; a positive result is ported to an offline model.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from collections import Counter
from pathlib import Path

import numpy as np

from .goals import Predicate, goal_participants
from .perception import Obj, ident

ROOT = Path(__file__).resolve().parents[3]
CACHE_DIR = ROOT / "experiments" / "llm_cache"
COLOUR_NAMES = ["black", "blue", "red", "green", "yellow", "grey", "magenta", "orange", "cyan", "brown",
                "white", "light-grey", "dark-red", "dark-green", "dark-blue", "pink"]  # ARC-AGI-3 palette, approximate
EXPLORE = "explore: no goal, keep exploring untried actions"


def _cname(c: int) -> str:
    return COLOUR_NAMES[c] if 0 <= c < len(COLOUR_NAMES) else f"colour{c}"


def _class_desc(cls: tuple, objs: list[Obj]) -> str:
    col, h, w = cls
    xs = [o for o in objs if ident(o) == cls]
    pos = ", ".join(f"({o.y0},{o.x0})" for o in xs[:3]) + (", …" if len(xs) > 3 else "")
    return f"{len(xs)}× {_cname(col)} {h}x{w} at {pos}"


def goal_menu(objs: list[Obj], mover_idents: frozenset, excluded: set[str] | None = None, max_options: int = 20) -> list[tuple[Predicate, str]]:
    """Concrete goal predicates that are FALSE now (so the planner has something to reach), with descriptions."""
    excluded = excluded or set()
    parts = goal_participants(objs)
    classes = Counter(ident(o) for o in parts)
    non_mover = [c for c in classes if c not in mover_idents]
    cands: list[tuple[int, Predicate, str]] = []  # (priority, predicate, description)
    if mover_idents:
        for c in non_mover:
            p = Predicate("touch", c)
            if not p.holds(objs, mover_idents):
                cands.append((0, p, f"move the player ({', '.join(_cname(m[0]) for m in sorted(mover_idents))}) onto/against {_class_desc(c, parts)}"))
    for c in non_mover:
        if classes[c] <= 6:
            cands.append((2, Predicate("gone", c), f"make every {_class_desc(c, parts)} disappear"))
    small = [c for c in non_mover if classes[c] <= 4]
    for i, c in enumerate(small):
        for d in small[i + 1:]:
            p = Predicate("overlap", c, d)
            if not p.holds(objs, mover_idents):
                cands.append((1, p, f"bring a {_cname(c[0])} {c[1]}x{c[2]} onto a {_cname(d[0])} {d[1]}x{d[2]}"))
            q = Predicate("aligned", c, d)
            if not q.holds(objs, mover_idents):
                cands.append((3, q, f"line up a {_cname(c[0])} {c[1]}x{c[2]} with a {_cname(d[0])} {d[1]}x{d[2]} (same row or column)"))
    cands.sort(key=lambda t: t[0])
    out = []
    for _, p, desc in cands:
        if str(p) in excluded:
            continue
        out.append((p, desc))
        if len(out) >= max_options:
            break
    return out


def summarise_level(objs: list[Obj], grid: np.ndarray, model, mover_idents: frozenset, level: int,
                    transition_note: str | None, actions_so_far: int) -> str:
    parts = goal_participants(objs)
    classes = Counter(ident(o) for o in parts)
    lines = [f"ARC-AGI-3 game, level {level + 1}, {actions_so_far} actions taken on this level, 64x64 grid.",
             f"Background colour: {_cname(int(np.bincount(grid.ravel(), minlength=16).argmax()))}.",
             "Objects (same-colour connected components; class = colour and size):"]
    for c, n in sorted(classes.items(), key=lambda kv: (-kv[1], kv[0]))[:20]:
        tag = " [THE PLAYER / what the actions move]" if c in mover_idents else ""
        lines.append(f"  - {_class_desc(c, parts)}{tag}")
    if model is not None and getattr(model, "moves", None):
        eff = []
        for key in sorted(model.moves, key=str):
            g = model.modal_group(key)
            if g:
                idents, (dy, dx) = g
                eff.append(f"action {key}: moves {', '.join(_cname(i[0]) + ' ' + str(i[1]) + 'x' + str(i[2]) for i in sorted(idents))} by (dy={dy}, dx={dx})")
        if eff:
            lines.append("Learned action effects: " + "; ".join(eff[:8]))
    else:
        lines.append("Learned action effects: none yet.")
    if transition_note:
        lines.append("What completed the previous level: " + transition_note)
    return "\n".join(lines)


def build_prompt(summary: str, menu: list[tuple[Predicate, str]]) -> tuple[str, list[str]]:
    options = [desc for _, desc in menu] + [EXPLORE]
    lines = [summary, "", "Which single goal is most likely what this level asks the player to achieve?",
             "Answer with the option number only."]
    for i, o in enumerate(options, 1):
        lines.append(f"{i}. {o}")
    return "\n".join(lines), options


class StubProposer:
    """Deterministic proposer for tests and the control: `answer` = option index (1-based) or 'explore'."""
    name = "stub"

    def __init__(self, answer="explore"):
        self.answer = answer; self.calls = 0

    def choose(self, prompt: str, options: list[str]) -> tuple[int | None, dict]:
        self.calls += 1
        if self.answer == "explore":
            return None, {"stub": "explore"}
        i = int(self.answer)
        return (i - 1 if 1 <= i <= len(options) - 1 else None), {"stub": i}


def _cache_path(payload: dict) -> Path:
    key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return CACHE_DIR / f"{key}.json"


def _api_key() -> str:
    for p in (Path.home() / "Projects" / ".env",):
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("OPENROUTER_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("OPENROUTER_KEY", "")


class ChatProposer:
    """OpenRouter chat/completions proposer: asks for the option number at temperature 0; cached."""

    def __init__(self, model: str, max_tokens: int = 16, timeout: float = 90.0):
        import requests  # local import: not needed on Kaggle
        self._requests = requests
        self.model = model; self.max_tokens = max_tokens; self.timeout = timeout
        self.name = model; self.calls = 0; self.cache_hits = 0; self.cost_usd = 0.0; self.failures = 0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def choose(self, prompt: str, options: list[str]) -> tuple[int | None, dict]:
        body = {"model": self.model, "temperature": 0, "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}]}
        cp = _cache_path({"kind": "chat", **body})
        if cp.exists():
            data = json.loads(cp.read_text()); self.cache_hits += 1
        else:
            data = None
            for attempt in range(4):
                try:
                    r = self._requests.post("https://openrouter.ai/api/v1/chat/completions", json=body, timeout=self.timeout,
                                            headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"})
                    data = r.json()
                    if "choices" in data and data["choices"]:
                        break
                except Exception as e:  # noqa: BLE001
                    data = {"error": str(e)}
                time.sleep(3 * (attempt + 1))
            self.calls += 1
            if data is None or "choices" not in data or not data["choices"]:
                self.failures += 1
                return None, {"error": (data or {}).get("error")}
            cp.write_text(json.dumps(data))
        text = (data["choices"][0]["message"].get("content") or "").strip()
        usage = data.get("usage") or {}
        self.cost_usd += float(usage.get("cost", 0) or 0)
        digits = "".join(ch for ch in text.split("\n")[0] if ch.isdigit() or ch == " ").split()
        idx = int(digits[0]) - 1 if digits else None
        if idx is None or not (0 <= idx < len(options) - 1):
            return None, {"text": text}
        return idx, {"text": text, "usage": usage}


class JevProposer:
    """OpenRouter Decisions API ('choice' question): per-option probabilities, pick the arg-max; cached."""

    def __init__(self, model: str = "typesafe/jev-1.13", timeout: float = 90.0, min_prob: float = 0.0):
        import requests
        self._requests = requests
        self.model = model; self.timeout = timeout; self.min_prob = min_prob
        self.name = model; self.calls = 0; self.cache_hits = 0; self.cost_usd = 0.0; self.failures = 0
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def choose(self, prompt: str, options: list[str]) -> tuple[int | None, dict]:
        body = {"model": self.model, "input": prompt, "question": {"type": "choice", "options": options}}
        cp = _cache_path({"kind": "decision", **body})
        if cp.exists():
            data = json.loads(cp.read_text()); self.cache_hits += 1
        else:
            data = None
            for attempt in range(4):
                try:
                    r = self._requests.post("https://openrouter.ai/api/alpha/decisions", json=body, timeout=self.timeout,
                                            headers={"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"})
                    data = r.json()
                    if "error" not in data:
                        break
                except Exception as e:  # noqa: BLE001
                    data = {"error": str(e)}
                time.sleep(3 * (attempt + 1))
            self.calls += 1
            if data is None or "error" in data:
                self.failures += 1
                return None, {"error": (data or {}).get("error")}
            cp.write_text(json.dumps(data))
        probs = _extract_probs(data, options)
        if not probs:
            return None, {"raw": str(data)[:300]}
        best = max(range(len(options)), key=lambda i: probs[i])
        if probs[best] < self.min_prob or best == len(options) - 1:
            return None, {"probs": probs}
        return best, {"probs": probs}


def _extract_probs(data: dict, options: list[str]) -> list[float] | None:
    """Tolerant reader for the Decisions API response (schema read 2026-10-12; see RESEARCH_LOG)."""
    def walk(x):
        if isinstance(x, dict):
            for k in ("probabilities", "probs", "distribution", "options", "choices", "result", "decision", "output"):
                if k in x:
                    r = walk(x[k])
                    if r: return r
            if all(o in x for o in options):
                return [float(x[o]) for o in options]
        if isinstance(x, list) and x and all(isinstance(e, dict) for e in x):
            by = {}
            for e in x:
                lab = e.get("option") or e.get("label") or e.get("text") or e.get("name")
                pr = e.get("probability", e.get("prob", e.get("p", e.get("score"))))
                if lab is not None and pr is not None:
                    by[lab] = float(pr)
            if all(o in by for o in options):
                return [by[o] for o in options]
        if isinstance(x, list) and len(x) == len(options) and all(isinstance(e, (int, float)) for e in x):
            return [float(e) for e in x]
        return None
    return walk(data)


def make_proposer(spec: str | None):
    """'stub' / 'stub:3' / 'jev' / 'jev:typesafe/jev-1.13' / any OpenRouter chat model id."""
    if not spec:
        return None
    if spec == "stub" or spec.startswith("stub:"):
        return StubProposer("explore" if spec == "stub" else spec.split(":", 1)[1])
    if spec == "jev" or spec.startswith("jev:"):
        return JevProposer("typesafe/jev-1.13" if spec == "jev" else spec.split(":", 1)[1])
    return ChatProposer(spec)
