import pytest
from pydantic import ValidationError

from learn_code_api.content.models import ExerciseContent


def valid_exercise_data() -> dict:
    return {
        "id": "exercise.seed.count-tags-001",
        "kind": "exercise",
        "version": 1,
        "language": "python",
        "title": "Count Inventory Tags",
        "slug": "count-inventory-tags-001",
        "difficulty": "easy",
        "concepts": ["python.dictionaries", "patterns.hash_map_counting"],
        "prerequisites": ["python.functions"],
        "estimated_time_minutes": 12,
        "review_status": "published",
        "source_status": "original",
        "provenance": {
            "brief_id": "seed.hash-map-counting",
            "author": "mixed",
            "generated_at": "2026-07-01T00:00:00Z",
            "inspiration_sources": [],
            "originality_notes": "Original inventory-tag prompt, examples, tests, and explanation.",
        },
        "prompt_markdown": "Return counts for each tag.",
        "starter_code": "def count_tags(tags):\n    return {}\n",
        "function_name": "count_tags",
        "input_mode": "function",
        "solution_sketch": "Use a dictionary and increment counts.",
        "sample_solution": "def count_tags(tags):\n    counts = {}\n    for tag in tags:\n        counts[tag] = counts.get(tag, 0) + 1\n    return counts\n",
        "hints": [
            {"level": 1, "text": "Track one count per tag."},
            {"level": 2, "text": "A dictionary can map tag to count."},
            {"level": 3, "text": "Use counts.get(tag, 0) + 1."},
        ],
        "tests": {
            "public": [
                {"name": "empty", "input": [], "expected": {}},
                {"name": "one", "input": ["red"], "expected": {"red": 1}},
                {"name": "repeat", "input": ["red", "red", "blue"], "expected": {"red": 2, "blue": 1}},
            ],
            "validation": [
                {"name": "mixed", "input": ["a", "b", "a"], "expected": {"a": 2, "b": 1}},
                {"name": "case", "input": ["A", "a"], "expected": {"A": 1, "a": 1}},
                {"name": "long", "input": ["x", "x", "x"], "expected": {"x": 3}},
            ],
        },
        "explanation_markdown": "A dictionary stores one counter per tag.",
        "common_mistakes": ["Returning None", "Using list.count inside a loop"],
    }


def test_exercise_model_accepts_valid_content():
    exercise = ExerciseContent.model_validate(valid_exercise_data())
    assert exercise.id == "exercise.seed.count-tags-001"
    assert exercise.language == "python"
    assert len(exercise.tests.public) == 3


def test_exercise_model_rejects_non_python_language():
    data = valid_exercise_data()
    data["language"] = "javascript"
    with pytest.raises(ValidationError):
        ExerciseContent.model_validate(data)


def test_exercise_model_rejects_missing_provenance():
    data = valid_exercise_data()
    data.pop("provenance")
    with pytest.raises(ValidationError):
        ExerciseContent.model_validate(data)
