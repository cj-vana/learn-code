from __future__ import annotations

import multiprocessing as mp
import traceback
from dataclasses import dataclass, field
from typing import Any

from learn_code_api.content.models import ExerciseContent


@dataclass(frozen=True)
class SampleSolutionResult:
    ok: bool
    failures: list[str] = field(default_factory=list)


def run_sample_solution(exercise: ExerciseContent | dict[str, Any], timeout_seconds: float = 2.0) -> SampleSolutionResult:
    """Run trusted seed sample-solution code against function-mode tests in a short-lived process."""
    if isinstance(exercise, dict):
        exercise = ExerciseContent.model_validate(exercise)

    if exercise.input_mode != "function":
        return SampleSolutionResult(False, [f"unsupported input mode: {exercise.input_mode}"])

    queue: mp.Queue[dict[str, Any]] = mp.Queue()
    process = mp.Process(target=_run_in_child, args=(exercise.model_dump(mode="python"), queue))
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join(1)
        return SampleSolutionResult(False, [f"sample solution timed out after {timeout_seconds:g}s"])

    if process.exitcode != 0 and queue.empty():
        return SampleSolutionResult(False, [f"sample solution process exited with {process.exitcode}"])

    payload = queue.get() if not queue.empty() else {"ok": False, "failures": ["no result returned"]}
    return SampleSolutionResult(ok=bool(payload["ok"]), failures=list(payload["failures"]))


def _run_in_child(exercise_data: dict[str, Any], queue: mp.Queue[dict[str, Any]]) -> None:
    failures: list[str] = []
    try:
        namespace: dict[str, Any] = {}
        exec(exercise_data["sample_solution"], namespace)
        function = namespace.get(exercise_data["function_name"])
        if not callable(function):
            failures.append(f"missing callable function: {exercise_data['function_name']}")
        else:
            test_groups = exercise_data["tests"]
            for group_name in ("public", "validation"):
                for case in test_groups[group_name]:
                    actual = function(case["input"])
                    expected = case["expected"]
                    if actual != expected:
                        failures.append(
                            f"{group_name}.{case['name']}: expected {expected!r}, got {actual!r}"
                        )
    except Exception as exc:  # pragma: no cover - exercised through child-process result
        failures.append(f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}")

    queue.put({"ok": not failures, "failures": failures})
