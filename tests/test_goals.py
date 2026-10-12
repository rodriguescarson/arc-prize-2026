import numpy as np
from arc_prize_2026.arc3.perception import segment
from arc_prize_2026.arc3.goals import candidate_predicates, GoalMemory, Predicate
g0 = np.zeros((64, 64), dtype=int); g0[10:12, 10:12] = 3; g0[30:32, 30:32] = 5; g0[40:42, 40:42] = 5
g1 = np.zeros((64, 64), dtype=int); g1[38:40, 40:42] = 3; g1[40:42, 40:42] = 5   # mover(3) now touches the remaining 5; the other 5 is gone
mover = frozenset({(3, 2, 2)})
c = candidate_predicates(segment(g0), segment(g1), mover)
kinds = {(p.kind, p.a) for p in c}
assert ("count", (5, 2, 2)) in kinds, c
assert ("touch", (5, 2, 2)) in kinds, c
gm = GoalMemory(); gm.update(c); gm.update({Predicate("touch", (5, 2, 2))})
assert gm.surviving == {Predicate("touch", (5, 2, 2))}
assert gm.active(segment(g0)) == [Predicate("touch", (5, 2, 2))]
print("goals ok")
