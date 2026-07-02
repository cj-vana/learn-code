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
