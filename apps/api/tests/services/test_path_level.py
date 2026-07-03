from __future__ import annotations

from pathlib import Path

from learn_code_api.content.loader import load_catalog
from learn_code_api.services.paths import path_level

CONTENT_ROOT = Path(__file__).resolve().parents[4] / "content" / "python"


def test_levels_bucket_by_assumed_concepts():
    catalog = load_catalog(CONTENT_ROOT)
    by_id = {p.id: p for p in catalog.paths}
    assert path_level(by_id["path.skill.python_foundations"]) == "beginner"
    assert path_level(by_id["path.career.python_interview_prep"]) == "beginner"
    assert path_level(by_id["path.career.python_developer_mastery"]) == "beginner"
    assert path_level(by_id["path.skill.ml_from_scratch"]) == "advanced"
    levels = {path_level(p) for p in catalog.paths}
    assert levels == {"beginner", "intermediate", "advanced"}


def test_flagship_career_paths_assume_nothing():
    """A brand-new learner must qualify for the two flagship career paths."""
    catalog = load_catalog(CONTENT_ROOT)
    by_id = {p.id: p for p in catalog.paths}
    assert by_id["path.career.python_interview_prep"].assumed_concepts == []
    assert by_id["path.career.python_developer_mastery"].assumed_concepts == []
