"""Solvers take a Task and return, per test input, a ranked list of candidate output grids.

Signature: solve(task) -> list[list[Grid]]  (outer: test inputs; inner: candidates, best first).
The runner takes the first two distinct candidates as attempt_1 / attempt_2.
"""
