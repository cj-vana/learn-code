from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from learn_code_api.content.models import ContentCatalog, ExerciseContent, ReviewStatus


class ContentLoadError(ValueError):
    """Raised when content files cannot be loaded into a valid catalog."""


def load_catalog(content_root: Path, include_drafts: bool = False) -> ContentCatalog:
    """Load exercise content from a recursive YAML tree."""
    root = Path(content_root)
    if not root.exists():
        raise ContentLoadError(f"content root does not exist: {root}")
    if not root.is_dir():
        raise ContentLoadError(f"content root is not a directory: {root}")

    exercises: list[ExerciseContent] = []
    for path in _yaml_files(root):
        raw = _load_raw_content(path)
        if not include_drafts and raw.get("review_status") != ReviewStatus.PUBLISHED.value:
            continue
        exercises.append(_load_exercise(path, raw))

    _reject_duplicates(exercises)
    return ContentCatalog(exercises=exercises)


def _yaml_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )


def _load_raw_content(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ContentLoadError(f"invalid yaml in {path}: {exc}") from exc
    except OSError as exc:
        raise ContentLoadError(f"could not read {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ContentLoadError(f"content file must contain a mapping: {path}")
    return raw


def _load_exercise(path: Path, raw: dict[str, Any]) -> ExerciseContent:
    if raw.get("kind") != "exercise":
        raise ContentLoadError(f"unsupported content kind in {path}: {raw.get('kind')!r}")

    try:
        return ExerciseContent.model_validate(raw)
    except ValidationError as exc:
        raise ContentLoadError(f"invalid content in {path}: {exc}") from exc


def _reject_duplicates(exercises: list[ExerciseContent]) -> None:
    _reject_duplicate_field(exercises, "id")
    _reject_duplicate_field(exercises, "slug")


def _reject_duplicate_field(exercises: list[ExerciseContent], field_name: str) -> None:
    seen: dict[Any, ExerciseContent] = {}
    for exercise in exercises:
        value = getattr(exercise, field_name)
        if value in seen:
            raise ContentLoadError(f"duplicate {field_name}: {value}")
        seen[value] = exercise
