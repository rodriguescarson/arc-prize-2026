import numpy as np
from arc_prize_2026.arc3.perception import segment, state_key, diff
g = np.zeros((64, 64), dtype=int); g[10:13, 10:12] = 3; g[40, 40] = 5
objs = segment(g)
assert len(objs) == 2, objs
assert {o.colour for o in objs} == {3, 5}
g2 = g.copy(); g2[10:13, 10:12] = 0; g2[10:13, 14:16] = 3
d = diff(segment(g), segment(g2))
assert len(d["moved"]) == 1 and d["moved"][0][2] == (0, 4), d
assert state_key(segment(g)) != state_key(segment(g2)) and state_key(segment(g)) == state_key(segment(g.copy()))
g3 = g.copy(); g3[10:13, 10:12] = 7
d = diff(segment(g), segment(g3)); assert len(d["recoloured"]) == 1
print("perception ok")
