from __future__ import annotations

import json
from pathlib import Path

from learn_code_api.content.loader import load_catalog
from learn_code_api.content.schema_export import export_content_schema
from learn_code_api.content.validator import validate_content_tree

ROOT = Path(__file__).resolve().parents[4]
CONTENT_ROOT = ROOT / "content/python/seed"
SCHEMA_PATH = ROOT / "schemas/content.schema.json"


def test_seed_content_is_valid():
    report = validate_content_tree(CONTENT_ROOT)

    assert report.ok, [issue.model_dump() for issue in report.issues]
    assert report.catalog is not None
    assert len(report.catalog.exercises) >= 2


def test_seed_sample_solutions_pass():
    catalog = load_catalog(CONTENT_ROOT)

    report = validate_content_tree(CONTENT_ROOT, run_solutions=True)

    assert report.ok, [issue.model_dump() for issue in report.issues]
    assert len(catalog.exercises) >= 2


def test_content_schema_export_writes_exercise_schema(tmp_path: Path):
    output_path = tmp_path / "content.schema.json"

    export_content_schema(output_path)

    schema = json.loads(output_path.read_text(encoding="utf-8"))
    assert schema["title"] == "ExerciseContent"
    assert schema["properties"]["language"]["const"] == "python"


def test_checked_in_content_schema_is_current():
    expected = export_content_schema()
    actual = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert actual == expected
