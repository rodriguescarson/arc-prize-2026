"""pass@2 scoring matching the ARC Prize Kaggle metric.

Per test input: 1 if either attempt equals the ground truth exactly, else 0.
Per task: mean over its test inputs.
Overall: mean over tasks (so a 2-test task is worth the same as a 1-test task).

The Kaggle 2025 competition averaged per-task scores this way; we keep `per_task_mean=True`
as the default and also report the per-test-output rate for transparency.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .data import Grid, Task


def grids_equal(a: Grid | None, b: Grid | None) -> bool:
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    return all(len(ra) == len(rb) and ra == rb for ra, rb in zip(a, b))


@dataclass
class TaskResult:
    task_id: str
    n_test: int
    per_test_correct: list[bool]
    attempt_hits: list[int]  # which attempt (1 or 2) matched, 0 if none

    @property
    def score(self) -> float:
        return sum(self.per_test_correct) / self.n_test if self.n_test else 0.0

    @property
    def solved(self) -> bool:
        return all(self.per_test_correct)


@dataclass
class ScoreReport:
    n_tasks: int
    n_test_outputs: int
    task_results: list[TaskResult] = field(default_factory=list)

    @property
    def score(self) -> float:
        """Competition-style score: mean over tasks of per-task pass@2 fraction."""
        return sum(r.score for r in self.task_results) / self.n_tasks if self.n_tasks else 0.0

    @property
    def tasks_fully_solved(self) -> int:
        return sum(r.solved for r in self.task_results)

    @property
    def test_output_rate(self) -> float:
        hits = sum(sum(r.per_test_correct) for r in self.task_results)
        return hits / self.n_test_outputs if self.n_test_outputs else 0.0

    def summary(self) -> dict:
        return {
            "score": round(self.score, 6),
            "tasks": self.n_tasks,
            "tasks_fully_solved": self.tasks_fully_solved,
            "test_outputs": self.n_test_outputs,
            "test_output_rate": round(self.test_output_rate, 6),
            "attempt1_hits": sum(r.attempt_hits.count(1) for r in self.task_results),
            "attempt2_hits": sum(r.attempt_hits.count(2) for r in self.task_results),
        }


def score_submission(tasks: list[Task], submission: dict) -> ScoreReport:
    """submission: {task_id: [{"attempt_1": Grid, "attempt_2": Grid}, ...]} (Kaggle layout)."""
    report = ScoreReport(n_tasks=len(tasks), n_test_outputs=sum(len(t.test) for t in tasks))
    for t in tasks:
        if not t.has_solutions():
            raise ValueError(f"{t.task_id}: cannot score without test outputs")
        attempts = submission.get(t.task_id, [])
        correct, hits = [], []
        for i, truth in enumerate(t.test_outputs):
            a = attempts[i] if i < len(attempts) else {}
            if grids_equal(a.get("attempt_1"), truth):
                correct.append(True); hits.append(1)
            elif grids_equal(a.get("attempt_2"), truth):
                correct.append(True); hits.append(2)
            else:
                correct.append(False); hits.append(0)
        report.task_results.append(TaskResult(t.task_id, len(t.test), correct, hits))
    return report
