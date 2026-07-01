from __future__ import annotations

from pathlib import Path

import yaml

from learn_code_api.content.sample_solution_runner import run_sample_solution
from learn_code_api.content.validator import validate_content_tree
from tests.content.test_loader import write_exercise
from tests.content.test_models import valid_exercise_data


def test_validator_rejects_missing_prerequisite(tmp_path: Path):
    write_exercise(tmp_path / "exercise.yml", prerequisites=["python.nonexistent"])

    report = validate_content_tree(tmp_path, run_solutions=False)

    assert not report.ok
    assert any("missing prerequisite" in issue.message for issue in report.issues)


def test_validator_rejects_insufficient_tests(tmp_path: Path):
    data = valid_exercise_data()
    data["tests"]["validation"] = [{"name": "only", "input": ["x"], "expected": {"x": 1}}]
    (tmp_path / "exercise.yml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    report = validate_content_tree(tmp_path, run_solutions=False)

    assert not report.ok
    assert any("at least 3 validation tests" in issue.message for issue in report.issues)


def test_validator_rejects_platform_name_in_originality_metadata(tmp_path: Path):
    data = valid_exercise_data()
    data["provenance"]["originality_notes"] = "Inspired by LeetCode problem statements."
    (tmp_path / "exercise.yml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    report = validate_content_tree(tmp_path, run_solutions=False)

    assert not report.ok
    assert any("suspicious platform name" in issue.message for issue in report.issues)


def test_sample_solution_runner_executes_function_mode_solution():
    exercise = valid_exercise_data()

    result = run_sample_solution(exercise)

    assert result.ok
    assert result.failures == []


def test_validator_rejects_failing_sample_solution(tmp_path: Path):
    write_exercise(
        tmp_path / "exercise.yml",
        sample_solution="def count_tags(tags):\n    return {}\n",
    )

    report = validate_content_tree(tmp_path)

    assert not report.ok
    assert any("sample solution failed" in issue.message for issue in report.issues)
