from arc_prize_2026.arc3_score import level_score, game_score, total_score
assert level_score(10, 10) == 1.0
assert level_score(10, 20) == 0.25
assert level_score(10, 5) == 1.0
assert level_score(10, None) == 0.0
assert abs(game_score([10, 10], [10, None]) - (1*1.0 + 2*0.0)/3) < 1e-9
assert abs(game_score([10, 10], [20, 10]) - (1*0.25 + 2*1.0)/3) < 1e-9
assert total_score({"a": 1.0, "b": 0.0}) == 0.5
print("arc3_score ok")
