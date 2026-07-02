"""Resolves exercise content (function name + test cases) for `exercise_tests` runs.

The runner-broker reads exercise content YAML directly (content is data, not
API code), so this module has no dependency on apps/api. Given an
``exercise_id`` and a ``test_profile``, it picks which of the exercise's
public/validation test cases to send to the harness, along with the
function it should call.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from app.contracts import TestProfile


class ExerciseNotFoundError(Exception):
    def __init__(self, exercise_id: str):
        super().__init__(f"No exercise content found for id={exercise_id!r}")
        self.exercise_id = exercise_id


@dataclass(frozen=True)
class TestCase:
    name: str
    visibility: str  # "public" | "validation"
    input: Any
    expected: Any


@dataclass(frozen=True)
class ExerciseTestPlan:
    function_name: str
    tests: list[TestCase]


def _load_exercise_document(exercise_id: str, content_root: Path) -> dict:
    if content_root.exists():
        for path in sorted(content_root.rglob("*.yml")):
            document = yaml.safe_load(path.read_text())
            if isinstance(document, dict) and document.get("id") == exercise_id:
                return document
    raise ExerciseNotFoundError(exercise_id)


def resolve_test_plan(
    *, exercise_id: str, test_profile: TestProfile, content_root: Path
) -> ExerciseTestPlan:
    document = _load_exercise_document(exercise_id, content_root)
    function_name = document["function_name"]
    raw_tests = document.get("tests", {})

    public_cases = [
        TestCase(name=t["name"], visibility="public", input=t["input"], expected=t["expected"])
        for t in raw_tests.get("public", [])
    ]

    if test_profile == TestProfile.PUBLIC:
        tests = public_cases
    else:
        validation_cases = [
            TestCase(
                name=t["name"], visibility="validation", input=t["input"], expected=t["expected"]
            )
            for t in raw_tests.get("validation", [])
        ]
        tests = public_cases + validation_cases

    return ExerciseTestPlan(function_name=function_name, tests=tests)
