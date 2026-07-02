"""Timed-practice exercise selection (spec: Part 3).

Eligibility mirrors the planner's tier-6 gate: an exercise qualifies once every
concept it touches is at least `practicing` mastery (>= 50). Selection is
deterministic (sorted by id) so the same progress state yields the same set.
"""

from __future__ import annotations

from learn_code_api.adaptive_plan.planner import PRACTICING_FLOOR
from learn_code_api.content.models import ContentCatalog
from learn_code_api.contracts import TimedSessionExercise
from learn_code_api.progress.db import ProgressRepository


def select_timed_exercises(
    catalog: ContentCatalog,
    repo: ProgressRepository,
    *,
    concept_filter: str | None,
    count: int,
) -> list[TimedSessionExercise]:
    mastery = repo.concept_mastery_map()
    selected: list[TimedSessionExercise] = []
    for exercise in sorted(catalog.exercises, key=lambda item: item.id):
        if concept_filter is not None and concept_filter not in exercise.concepts:
            continue
        if not all(mastery.get(concept, 0) >= PRACTICING_FLOOR for concept in exercise.concepts):
            continue
        selected.append(
            TimedSessionExercise(
                id=exercise.id,
                title=exercise.title,
                concepts=list(exercise.concepts),
                estimated_time_minutes=exercise.estimated_time_minutes,
            )
        )
        if len(selected) == count:
            break
    return selected
