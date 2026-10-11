# Failure table — ModelBasedAgent seed=0 max_actions=2000 total=0.110 levels=8/183

| game | levels | score | actions/level (human) | resets | distinct frames | model acc | plan steps / fallback | stall |
|---|---|---|---|---|---|---|---|---|
| ar25 | 0/8 | 0.000 | — | 23 | 375 | 0.41 | 1977 / 0 | no_progress |
| bp35 | 0/9 | 0.000 | — | 41 | 3562 | 0.428 | 1109 / 850 | no_progress |
| cd82 | 0/6 | 0.000 | — | 20 | 869 | 0.289 | 1980 / 0 | model_blind |
| cn04 | 0/6 | 0.000 | — | 27 | 496 | 0.176 | 1973 / 0 | model_blind |
| dc22 | 0/6 | 0.000 | — | 16 | 636 | 0.141 | 1984 / 0 | model_blind |
| ft09 | 1/6 | 0.096 | 303 (43) | 44 | 490 | 1.0 | 1739 / 217 | no_progress |
| g50t | 0/7 | 0.000 | — | 16 | 2651 | 0.218 | 1984 / 0 | model_blind |
| ka59 | 0/7 | 0.000 | — | 20 | 1031 | 0.125 | 1980 / 0 | model_blind |
| lf52 | 1/10 | 0.112 | 129 (32) | 5 | 5619 | 0.731 | 1995 / 0 | no_progress |
| lp85 | 1/8 | 2.478 | 18 (17) | 26 | 1010 | 0.277 | 1974 / 0 | model_blind |
| ls20 | 1/7 | 0.002 | 951 (22) | 22 | 1508 | 0.852 | 1453 / 525 | no_progress |
| m0r0 | 0/6 | 0.000 | — | 14 | 578 | 0.559 | 1986 / 0 | no_progress |
| r11l | 0/6 | 0.000 | — | 33 | 997 | 0.375 | 1967 / 0 | no_progress |
| re86 | 0/8 | 0.000 | — | 20 | 1685 | 0.017 | 1980 / 0 | model_blind |
| s5i5 | 0/8 | 0.000 | — | 40 | 1496 | 0.773 | 1960 / 0 | no_progress |
| sb26 | 0/8 | 0.000 | — | 4 | 1085 | 0.683 | 1996 / 0 | no_progress |
| sc25 | 0/6 | 0.000 | — | 31 | 1428 | 0.135 | 1833 / 136 | model_blind |
| sk48 | 0/8 | 0.000 | — | 7 | 773 | 0.258 | 1993 / 0 | model_blind |
| sp80 | 0/6 | 0.000 | — | 65 | 1104 | 0.969 | 748 / 1187 | no_progress |
| su15 | 1/9 | 0.006 | 434 (22) | 38 | 4942 | 0.992 | 1940 / 22 | no_progress |
| tn36 | 0/7 | 0.000 | — | 33 | 1841 | 1.0 | 1967 / 0 | no_progress |
| tr87 | 0/6 | 0.000 | — | 16 | 1787 | 0.155 | 1984 / 0 | model_blind |
| tu93 | 1/9 | 0.003 | 500 (19) | 299 | 2350 | 0.847 | 1701 / 0 | game_over_loop |
| vc33 | 2/7 | 0.046 | 67 (7), 570 (18) | 30 | 1749 | 0.796 | 1970 / 0 | no_progress |
| wa30 | 0/9 | 0.000 | — | 10 | 1090 | 0.129 | 1990 / 0 | model_blind |

Stall counts: game_over_loop=1, model_blind=11, no_progress=13