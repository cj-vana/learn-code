from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from learn_code_api.content.models import (
    ContentCatalog,
    ExerciseContent,
    LessonContent,
    PathContent,
    QuizContent,
    ReviewStatus,
)


class ContentLoadError(ValueError):
    """Raised when content files cannot be loaded into a valid catalog."""


def load_catalog(content_root: Path, include_drafts: bool = False) -> ContentCatalog:
    """Load exercise, lesson, and quiz content from a recursive YAML tree."""
    root = Path(content_root)
    if not root.exists():
        raise ContentLoadError(f"content root does not exist: {root}")
    if not root.is_dir():
        raise ContentLoadError(f"content root is not a directory: {root}")

    exercises: list[ExerciseContent] = []
    lessons: list[LessonContent] = []
    quizzes: list[QuizContent] = []
    paths: list[PathContent] = []
    for path in _yaml_files(root):
        raw = _load_raw_content(path)
        review_status = _load_review_status(path, raw)
        if not include_drafts and review_status != ReviewStatus.PUBLISHED:
            continue
        kind = raw.get("kind")
        if kind == "exercise":
            exercises.append(_load_exercise(path, raw))
        elif kind == "lesson":
            lessons.append(_load_lesson(path, raw))
        elif kind == "quiz":
            quizzes.append(_load_quiz(path, raw))
        elif kind == "path":
            paths.append(_load_path(path, raw))
        else:
            raise ContentLoadError(f"unsupported content kind in {path}: {kind!r}")

    _reject_duplicates([*exercises, *lessons, *quizzes, *paths])
    return ContentCatalog(
        exercises=exercises, lessons=lessons, quizzes=quizzes, paths=paths
    )


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


def _load_review_status(path: Path, raw: dict[str, Any]) -> ReviewStatus:
    if "review_status" not in raw:
        raise ContentLoadError(f"missing review_status in {path}")

    try:
        return ReviewStatus(raw["review_status"])
    except ValueError as exc:
        raise ContentLoadError(f"invalid review_status in {path}: {raw['review_status']!r}") from exc


def _load_exercise(path: Path, raw: dict[str, Any]) -> ExerciseContent:
    try:
        return ExerciseContent.model_validate(raw)
    except ValidationError as exc:
        raise ContentLoadError(f"invalid content in {path}: {exc}") from exc


def _load_lesson(path: Path, raw: dict[str, Any]) -> LessonContent:
    try:
        return LessonContent.model_validate(raw)
    except ValidationError as exc:
        raise ContentLoadError(f"invalid content in {path}: {exc}") from exc


def _load_quiz(path: Path, raw: dict[str, Any]) -> QuizContent:
    try:
        return QuizContent.model_validate(raw)
    except ValidationError as exc:
        raise ContentLoadError(f"invalid content in {path}: {exc}") from exc


def _load_path(path: Path, raw: dict[str, Any]) -> PathContent:
    try:
        return PathContent.model_validate(raw)
    except ValidationError as exc:
        raise ContentLoadError(f"invalid content in {path}: {exc}") from exc


def _reject_duplicates(items: list[Any]) -> None:
    _reject_duplicate_field(items, "id")
    _reject_duplicate_field(items, "slug")


def _reject_duplicate_field(items: list[Any], field_name: str) -> None:
    seen: dict[Any, Any] = {}
    for item in items:
        value = getattr(item, field_name)
        if value in seen:
            raise ContentLoadError(f"duplicate {field_name}: {value}")
        seen[value] = item
