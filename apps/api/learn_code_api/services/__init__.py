"""Wiring layer between thin routers and the Task 2-4 domain modules."""

from __future__ import annotations

from learn_code_api.content.models import ContentCatalog, ExerciseContent
from learn_code_api.errors import ContentNotFoundError


def find_exercise(catalog: ContentCatalog, exercise_id: str) -> ExerciseContent:
    for exercise in catalog.exercises:
        if exercise.id == exercise_id:
            return exercise
    raise ContentNotFoundError(
        f"no published exercise with id {exercise_id!r}",
        details={"exercise_id": exercise_id},
    )
