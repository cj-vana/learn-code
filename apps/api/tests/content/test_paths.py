from __future__ import annotations

import pytest
from pydantic import ValidationError

from learn_code_api.content.loader import ContentLoadError, load_catalog
from learn_code_api.content.models import PathContent


def _provenance() -> dict:
    return {
        "brief_id": "brief.paths.test",
        "author": "agent",
        "generated_at": "2026-07-02T00:00:00Z",
        "inspiration_sources": [],
        "originality_notes": "Original curated sequence over original content.",
    }


def _path(**over) -> dict:
    data = {
        "id": "path.skill.test",
        "kind": "path",
        "path_type": "skill",
        "version": 1,
        "language": "python",
        "title": "Test Path",
        "slug": "test-path",
        "description": "A tiny path for tests.",
        "outcomes": ["Recognize the two pointers pattern"],
        "estimated_hours": 2,
        "review_status": "published",
        "source_status": "original",
        "provenance": _provenance(),
        "units": [
            {
                "id": "unit.one",
                "title": "Unit One",
                "description": "Start here.",
                "items": ["lesson.library.two_pointers.a01", "exercise.library.two_pointers.a01"],
            }
        ],
    }
    data.update(over)
    return data


def test_valid_path_model_validates():
    path = PathContent.model_validate(_path())
    assert path.path_type == "skill"
    assert path.units[0].items[0] == "lesson.library.two_pointers.a01"


def test_duplicate_items_across_units_rejected():
    units = [
        {"id": "unit.one", "title": "One", "description": "d", "items": ["lesson.library.two_pointers.a01"]},
        {"id": "unit.two", "title": "Two", "description": "d", "items": ["lesson.library.two_pointers.a01"]},
    ]
    with pytest.raises(ValidationError):
        PathContent.model_validate(_path(units=units))


def test_empty_unit_rejected():
    units = [{"id": "unit.one", "title": "One", "description": "d", "items": []}]
    with pytest.raises(ValidationError):
        PathContent.model_validate(_path(units=units))


def test_loader_dispatches_path_kind(tmp_path):
    import yaml

    (tmp_path / "path.yml").write_text(yaml.safe_dump(_path()), encoding="utf-8")
    catalog = load_catalog(tmp_path)
    assert [p.id for p in catalog.paths] == ["path.skill.test"]


def test_loader_rejects_duplicate_path_ids(tmp_path):
    import yaml

    (tmp_path / "a.yml").write_text(yaml.safe_dump(_path()), encoding="utf-8")
    (tmp_path / "b.yml").write_text(
        yaml.safe_dump(_path(slug="other-slug")), encoding="utf-8"
    )
    with pytest.raises(ContentLoadError):
        load_catalog(tmp_path)


def test_validator_errors_on_unknown_path_item(tmp_path):
    import yaml

    from learn_code_api.content.validator import validate_content_tree

    src = _path(
        units=[
            {
                "id": "unit.one",
                "title": "One",
                "description": "d",
                "items": ["lesson.library.does_not_exist.a01"],
            }
        ]
    )
    (tmp_path / "path.yml").write_text(yaml.safe_dump(src), encoding="utf-8")
    report = validate_content_tree(tmp_path, profile="none", run_solutions=False)
    assert not report.ok
    assert any("unknown path item" in issue.message for issue in report.issues)


def test_validator_accepts_path_with_real_items(tmp_path):
    import yaml

    from learn_code_api.content.validator import validate_content_tree

    lesson = {
        "id": "lesson.t.1",
        "kind": "lesson",
        "version": 1,
        "language": "python",
        "title": "Intro",
        "slug": "intro",
        "difficulty": "easy",
        "concepts": ["python.loops"],
        "prerequisites": [],
        "estimated_time_minutes": 8,
        "review_status": "published",
        "source_status": "original",
        "provenance": _provenance(),
        "body_markdown": "Body.",
        "checkpoints": [{"question": "q?", "answer": "a", "explanation": "e"}],
    }
    path_data = _path(
        units=[{"id": "unit.one", "title": "One", "description": "d", "items": ["lesson.t.1"]}]
    )
    (tmp_path / "lesson.yml").write_text(yaml.safe_dump(lesson), encoding="utf-8")
    (tmp_path / "path.yml").write_text(yaml.safe_dump(path_data), encoding="utf-8")
    report = validate_content_tree(tmp_path, profile="none", run_solutions=False)
    assert report.ok, [issue.message for issue in report.issues]
