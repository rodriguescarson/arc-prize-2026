"""Goal inference from level transitions.

When `levels_completed` increments, the state just before the transition is a positive example of the
level's goal; the level's initial state is a negative example. We enumerate predicates from a fixed
template class over object classes (ident = (colour, h, w)) and keep those that are TRUE at the
transition and FALSE at the level start. Across levels of one game, surviving predicates are those
that held at every transition seen (intersection). Later levels then plan toward any surviving predicate.

Templates:
  Gone(c)         : no object of class c remains                      (collect/clear everything of c)
  Count(c, k)     : exactly k objects of class c remain, k < initial  (partial clearing)
  Touch(c)        : the mover group's bbox touches an object of class c (reach c)
  Overlap(c, d)   : an object of class c overlaps an object of class d (bring c onto d)
  Appeared(c)     : class c absent at start, present at the end       (reveal/create c)
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .perception import Obj, ident


def _touch(a: Obj, b: Obj) -> bool:
    return a.y0 <= b.y1 and b.y0 <= a.y1 and a.x0 <= b.x1 and b.x0 <= a.x1


def _overlap(a: Obj, b: Obj) -> bool:
    return a.y0 < b.y1 and b.y0 < a.y1 and a.x0 < b.x1 and b.x0 < a.x1


@dataclass(frozen=True)
class Predicate:
    kind: str
    a: tuple
    b: tuple | int | None = None

    def holds(self, objs: list[Obj], mover_idents: frozenset) -> bool:
        if self.kind == "gone":
            return not any(ident(o) == self.a for o in objs)
        if self.kind == "count":
            return sum(ident(o) == self.a for o in objs) == self.b
        if self.kind == "appeared":
            return any(ident(o) == self.a for o in objs)
        if self.kind == "touch":
            members = [o for o in objs if ident(o) in mover_idents]
            targets = [o for o in objs if ident(o) == self.a]
            return any(_touch(m, t) for m in members for t in targets)
        if self.kind == "overlap":
            xs = [o for o in objs if ident(o) == self.a]; ys = [o for o in objs if ident(o) == self.b]
            return any(_overlap(x, y) for x in xs for y in ys)
        # ---- extended family (E18 analysis only; the agent uses the base family) ----
        if self.kind == "touch2":
            xs = [o for o in objs if ident(o) == self.a]; ys = [o for o in objs if ident(o) == self.b]
            return any(_touch(x, y) for x in xs for y in ys)
        if self.kind == "inside":
            xs = [o for o in objs if ident(o) == self.a]; ys = [o for o in objs if ident(o) == self.b]
            return any(y.y0 <= x.y0 and x.y1 <= y.y1 and y.x0 <= x.x0 and x.x1 <= y.x1 and (x.h, x.w) != (y.h, y.w)
                       for x in xs for y in ys)
        if self.kind == "aligned":
            xs = [o for o in objs if ident(o) == self.a]; ys = [o for o in objs if ident(o) == self.b]
            return any(x.centre[0] == y.centre[0] or x.centre[1] == y.centre[1] for x in xs for y in ys)
        if self.kind == "same_colour_all":
            cols = {o.colour for o in objs if (o.h, o.w) == self.a}
            return len(cols) == 1 and sum((o.h, o.w) == self.a for o in objs) >= 2
        if self.kind == "count_colour":
            return sum(o.colour == self.a for o in objs) == self.b
        if self.kind == "gone_colour":
            return not any(o.colour == self.a for o in objs)
        if self.kind == "appeared_colour":
            return any(o.colour == self.a for o in objs)
        return False

    def classes(self) -> set:
        return {self.a} | ({self.b} if isinstance(self.b, tuple) else set())

    def __str__(self) -> str:
        return f"{self.kind}({self.a}{', ' + str(self.b) if self.b is not None else ''})"


MAX_PREDICATE_AREA = 300  # objects this large are scenery, not goal participants


def is_bar(o: Obj) -> bool:
    """Thin, long objects are HUD bars / borders, never goal participants."""
    return (o.h <= 2 and o.w >= 20) or (o.w <= 2 and o.h >= 20)


def goal_participants(objs: list[Obj]) -> list[Obj]:
    return [o for o in objs if o.h * o.w < MAX_PREDICATE_AREA and not is_bar(o)]


def candidate_predicates(init_objs: list[Obj], final_objs: list[Obj], mover_idents: frozenset, family: str = "base") -> set[Predicate]:
    """family="base" is what the agent uses; "extended" adds the E18 analysis families."""
    init_objs = goal_participants(init_objs)
    final_objs = goal_participants(final_objs)
    ci, cf = Counter(ident(o) for o in init_objs), Counter(ident(o) for o in final_objs)
    classes = set(ci) | set(cf)
    cands: set[Predicate] = set()
    for c in classes:
        if c in mover_idents:
            continue
        if ci[c] > 0 and cf[c] == 0:
            cands.add(Predicate("gone", c))
        if ci[c] > cf[c] > 0:
            cands.add(Predicate("count", c, cf[c]))
        if ci[c] == 0 and cf[c] > 0:
            cands.add(Predicate("appeared", c))
    if mover_idents:
        for c in classes - set(mover_idents):
            p = Predicate("touch", c)
            if p.holds(final_objs, mover_idents) and not p.holds(init_objs, mover_idents):
                cands.add(p)
    non_mover = [c for c in classes if c not in mover_idents]
    for c in non_mover:
        for d in non_mover:
            if c >= d:
                continue
            p = Predicate("overlap", c, d)
            if p.holds(final_objs, mover_idents) and not p.holds(init_objs, mover_idents):
                cands.add(p)
    if family == "extended":
        for c in non_mover:
            for d in non_mover:
                if c == d:
                    continue
                for kind in (("touch2", "aligned") if c < d else ()) + ("inside",):
                    p = Predicate(kind, c, d)
                    if p.holds(final_objs, mover_idents) and not p.holds(init_objs, mover_idents):
                        cands.add(p)
        sizes = {(o.h, o.w) for o in init_objs + final_objs if ident(o) not in mover_idents}
        for sz in sizes:
            p = Predicate("same_colour_all", sz)
            if p.holds(final_objs, mover_idents) and not p.holds(init_objs, mover_idents):
                cands.add(p)
        mover_colours = {c[0] for c in mover_idents}
        coli = Counter(o.colour for o in init_objs if o.colour not in mover_colours)
        colf = Counter(o.colour for o in final_objs if o.colour not in mover_colours)
        for col in set(coli) | set(colf):
            if coli[col] > 0 and colf[col] == 0:
                cands.add(Predicate("gone_colour", col))
            if coli[col] > colf[col] > 0:
                cands.add(Predicate("count_colour", col, colf[col]))
            if coli[col] == 0 and colf[col] > 0:
                cands.add(Predicate("appeared_colour", col))
    return cands


class GoalMemory:
    def __init__(self) -> None:
        self.surviving: set[Predicate] | None = None
        self.transitions = 0

    def update(self, cands: set[Predicate]) -> None:
        self.transitions += 1
        self.surviving = set(cands) if self.surviving is None else (self.surviving & cands)

    def active(self, objs: list[Obj]) -> list[Predicate]:
        """Surviving predicates whose classes exist (or, for gone/count, existed) in the current level."""
        if not self.surviving:
            return []
        present = {ident(o) for o in objs}
        out = []
        for p in self.surviving:
            if p.kind in ("gone", "count", "touch") and p.a not in present:
                continue
            if p.kind == "overlap" and not (p.a in present and p.b in present):
                continue
            out.append(p)
        order = {"touch": 0, "overlap": 1, "count": 2, "gone": 3, "appeared": 4}
        return sorted(out, key=lambda p: order[p.kind])
