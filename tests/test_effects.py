import numpy as np
from arc_prize_2026.arc3.perception import segment, state_key, ident
from arc_prize_2026.arc3.effects import EffectModel, DEATH

def grid_with(player_at, wall_cols=None):
    g = np.zeros((64, 64), dtype=np.int16); g[:, :] = 4      # terrain colour 4
    y, x = player_at; g[y:y+2, x:x+2] = 9; g[y, x+2] = 7       # rigid group: 2x2 colour-9 body + 1 px colour-7 marker
    if wall_cols:
        g[:, wall_cols[0]:wall_cols[1]] = 5
    return g

def objs(g): return [o for o in segment(g, drop_background=False) if o.colour != 4]

m = EffectModel()
# three observed moves to the right by 1
for x in (10, 11, 12):
    m.observe(objs(grid_with((10, x))), grid_with((10, x)), 4, objs(grid_with((10, x + 1))))
idents, delta = m.modal_group(4)
assert delta == (0, 1) and (9, 2, 2) in idents and (7, 1, 1) in idents, (idents, delta)
# prediction moves the whole group
pred, src = m.predict(objs(grid_with((10, 20))), grid_with((10, 20)), 4)
assert src == "model" and {(o.colour, o.x0) for o in pred} == {(9, 21), (7, 23)}, pred
# a wall ahead: after one blocked observation, the model predicts no move into colour 5
gw = grid_with((10, 20), wall_cols=(23, 25))
m.observe(objs(gw), gw, 4, objs(gw))          # pressed right, nothing moved
assert m.blocked[4][5] > 0
gw2 = grid_with((10, 19), wall_cols=(23, 25))   # unseen state, wall still 2 cells ahead of the marker's path
pred, src = m.predict(objs(gw2), gw2, 4)
assert src == "model" and pred is not None, (pred, src)
# only the swept cells matter: body sweeps x=21, marker sweeps x=22 -> no wall touched, so it moves
assert {(o.colour, o.x0) for o in pred if o.colour in (9, 7)} == {(9, 20), (7, 22)}, pred
gw3 = grid_with((10, 20), wall_cols=(23, 25))   # marker at x=22 would sweep into x=23 (wall)
sk3 = state_key(objs(gw3))
assert (sk3, 4) in m.transitions  # memoised as blocked from the observation above
assert m.next_key(sk3, 4) == sk3
# death memo
sk = state_key(objs(gw)); m.record_death(sk, 2)
assert m.is_deadly(sk, 2) and m.next_key(sk, 2) == DEATH
print("effects ok")
