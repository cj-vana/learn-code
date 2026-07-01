from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from learn_code_api.content.loader import ContentLoadError, load_catalog
from tests.content.test_models import valid_exercise_data


def write_exercise(path: Path, **overrides: object) -> dict:
    data = valid_exercise_data()
    data.update(overrides)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return data


def test_default_loader_excludes_drafts(tmp_path: Path):
    write_exercise(tmp_path / "published.yml")
    write_exercise(
        tmp_path / "draft.yml",
        id="exercise.seed.draft-count-tags-001",
        slug="draft-count-tags-001",
        review_status="drafted",
    )

    default_catalog = load_catalog(tmp_path)
    draft_catalog = load_catalog(tmp_path, include_drafts=True)

    assert [exercise.id for exercise in default_catalog.exercises] == ["exercise.seed.count-tags-001"]
    assert {exercise.id for exercise in draft_catalog.exercises} == {
        "exercise.seed.count-tags-001",
        "exercise.seed.draft-count-tags-001",
    }


def test_loader_rejects_duplicate_ids(tmp_path: Path):
    write_exercise(tmp_path / "one.yml", slug="count-inventory-tags-a")
    write_exercise(tmp_path / "two.yml", slug="count-inventory-tags-b")

    with pytest.raises(ContentLoadError, match="duplicate id"):
        load_catalog(tmp_path)


def test_loader_rejects_duplicate_slugs(tmp_path: Path):
    write_exercise(tmp_path / "one.yml", id="exercise.seed.count-tags-a")
    write_exercise(tmp_path / "two.yml", id="exercise.seed.count-tags-b")

    with pytest.raises(ContentLoadError, match="duplicate slug"):
        load_catalog(tmp_path)
