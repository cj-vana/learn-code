from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learn_code_api.content.models import ExerciseContent

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SCHEMA_PATH = ROOT / "schemas/content.schema.json"


def export_content_schema(output_path: Path | None = DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    """Export the ExerciseContent JSON schema and return the schema object."""
    schema = ExerciseContent.model_json_schema()
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return schema


if __name__ == "__main__":
    export_content_schema()
