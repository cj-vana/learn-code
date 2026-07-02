from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from learn_code_api.content.loader import ContentLoadError, load_catalog
from learn_code_api.content.validator import validate_content_tree


def _provenance() -> dict:
    return {
        "brief_id": "t.1",
        "author": "generated",
        "generated_at": "2026-07-02T00:00:00Z",
        "inspiration_sources": [],
        "originality_notes": "Original teaching content.",
    }


def _lesson(**over) -> dict:
    data = {
        "id": "lesson.t.1",
        "kind": "lesson",
        "version": 1,
        "language": "python",
        "title": "Intro to Loops",
        "slug": "intro-loops",
        "difficulty": "easy",
        "concepts": ["python.loops"],
        "prerequisites": ["python.functions"],
        "estimated_time_minutes": 8,
        "review_status": "published",
        "source_status": "original",
        "provenance": _provenance(),
        "body_markdown": "Loops repeat work until a condition ends them.",
        "checkpoints": [{"question": "What repeats?", "answer": "The body", "explanation": "Each pass runs the body."}],
    }
    data.update(over)
    return data


def _quiz(**over) -> dict:
    data = {
        "id": "quiz.t.1",
        "kind": "quiz",
        "version": 1,
        "language": "python",
        "title": "Loop check",
        "slug": "loop-check",
        "difficulty": "easy",
        "concepts": ["python.loops"],
        "prerequisites": [],
        "estimated_time_minutes": 4,
        "review_status": "published",
        "source_status": "original",
        "provenance": _provenance(),
        "quiz_type": "syntax",
        "questions": [
            {
                "id": "q1",
                "prompt": "Which keyword starts a counted loop?",
                "choices": ["for", "when"],
                "correct_choice": "for",
                "explanation": "`for` iterates over a sequence.",
                "concepts": ["python.loops"],
            }
        ],
    }
    data.update(over)
    return data


def _write(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_loads_lessons_and_quizzes(tmp_path: Path):
    _write(tmp_path / "lesson.yml", _lesson())
    _write(tmp_path / "quiz.yml", _quiz())

    catalog = load_catalog(tmp_path)

    assert len(catalog.lessons) == 1
    assert len(catalog.quizzes) == 1
    assert catalog.lessons[0].checkpoints[0].answer == "The body"
    assert catalog.quizzes[0].questions[0].correct_choice == "for"


def test_library_validator_accepts_lesson_and_quiz(tmp_path: Path):
    _write(tmp_path / "lesson.yml", _lesson())
    _write(tmp_path / "quiz.yml", _quiz())

    report = validate_content_tree(tmp_path, profile="library", run_solutions=False)

    assert report.ok, [issue.message for issue in report.issues]


def test_validator_rejects_quiz_correct_choice_not_in_choices(tmp_path: Path):
    _write(
        tmp_path / "quiz.yml",
        _quiz(
            questions=[
                {
                    "id": "q1",
                    "prompt": "Pick one",
                    "choices": ["a", "b"],
                    "correct_choice": "c",
                    "explanation": "e",
                    "concepts": [],
                }
            ]
        ),
    )

    report = validate_content_tree(tmp_path, profile="library", run_solutions=False)

    assert not report.ok
    assert any("correct_choice is not one of choices" in i.message for i in report.issues)


def test_validator_rejects_lesson_unknown_concept(tmp_path: Path):
    _write(tmp_path / "lesson.yml", _lesson(concepts=["python.nope"]))

    report = validate_content_tree(tmp_path, profile="library", run_solutions=False)

    assert not report.ok
    assert any("unknown lesson concept: python.nope" in i.message for i in report.issues)


def test_dedup_across_content_kinds(tmp_path: Path):
    _write(tmp_path / "lesson.yml", _lesson(id="dup.shared.1"))
    _write(tmp_path / "quiz.yml", _quiz(id="dup.shared.1"))

    with pytest.raises(ContentLoadError):
        load_catalog(tmp_path)
