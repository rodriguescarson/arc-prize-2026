from arc_prize_2026.arc3_score import level_score, game_score, total_score
assert level_score(10, 10) == 100.0
assert level_score(10, 20) == 25.0
assert level_score(10, 5) == 115.0           # toolkit cap
assert level_score(10, 5, level_cap=100) == 100.0
assert level_score(10, None) == 0.0
# two levels, weights 1 and 2
assert abs(game_score([10, 10], [10, None]) - min((1*100 + 2*0)/3, 100*1/3)) < 1e-9
assert abs(game_score([10, 10], [20, 10]) - (1*25 + 2*100)/3) < 1e-9
assert abs(game_score([10, 10], [5, 5]) - 100.0) < 1e-9     # 115s capped by completion fraction
assert total_score({"a": 100.0, "b": 0.0}) == 50.0
print("arc3_score ok")
