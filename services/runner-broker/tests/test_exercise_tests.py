from pathlib import Path

import pytest

from app.contracts import TestProfile
from app.exercise_tests import ExerciseNotFoundError, resolve_test_plan

FIXTURE_CONTENT_ROOT = Path(__file__).parent / "fixtures" / "content" / "python"


def test_resolve_public_profile_returns_only_public_tests():
    plan = resolve_test_plan(
        exercise_id="exercise.seed.add-two-001",
        test_profile=TestProfile.PUBLIC,
        content_root=FIXTURE_CONTENT_ROOT,
    )
    assert plan.function_name == "add_two"
    assert [t.name for t in plan.tests] == ["basic", "zero"]
    assert all(t.visibility == "public" for t in plan.tests)


def test_resolve_validation_profile_returns_public_and_validation_tests():
    plan = resolve_test_plan(
        exercise_id="exercise.seed.add-two-001",
        test_profile=TestProfile.VALIDATION,
        content_root=FIXTURE_CONTENT_ROOT,
    )
    names_by_visibility = {(t.name, t.visibility) for t in plan.tests}
    assert names_by_visibility == {
        ("basic", "public"),
        ("zero", "public"),
        ("negative", "validation"),
    }


def test_resolve_missing_exercise_raises():
    with pytest.raises(ExerciseNotFoundError):
        resolve_test_plan(
            exercise_id="exercise.seed.does-not-exist",
            test_profile=TestProfile.PUBLIC,
            content_root=FIXTURE_CONTENT_ROOT,
        )
