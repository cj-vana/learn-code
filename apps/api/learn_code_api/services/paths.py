"""Derived path progress: completion is computed from existing rollups, never
stored (spec: Part 2 > Progress and enrollment). An item is complete when its
kind's completion rule holds — lesson completed, every quiz question answered,
or exercise validation passed."""

from __future__ import annotations

from learn_code_api.content.concepts import concept_label
from learn_code_api.content.models import ContentCatalog, PathContent
from learn_code_api.contracts import (
    PathDetail,
    PathItemStatus,
    PathSummary,
    PathUnitDetail,
)
from learn_code_api.progress.db import ProgressRepository


def completed_content_ids(catalog: ContentCatalog, repo: ProgressRepository) -> set[str]:
    """Content ids (all kinds) the learner has completed."""
    coverage = repo.quiz_question_coverage()
    completed_quizzes = {
        quiz.id
        for quiz in catalog.quizzes
        if {question.id for question in quiz.questions} <= coverage.get(quiz.id, set())
    }
    return repo.completed_lesson_ids() | completed_quizzes | repo.passed_exercise_ids()


def _percent(done: int, total: int) -> int:
    return round(100 * done / total) if total else 0


# A unit unlocks once the previous unit is at least this complete. Derived at
# read time like all path progress; the gate is guidance, not enforcement.
MASTERY_THRESHOLD_PERCENT = 70


def path_summary(
    path_content: PathContent, *, completed: set[str], active_path_id: str | None
) -> PathSummary:
    item_ids = [item for unit in path_content.units for item in unit.items]
    done = sum(1 for item in item_ids if item in completed)
    return PathSummary(
        id=path_content.id,
        path_type=path_content.path_type,
        title=path_content.title,
        slug=path_content.slug,
        description=path_content.description,
        outcomes=list(path_content.outcomes),
        assumed_concepts=[concept_label(c) for c in path_content.assumed_concepts],
        estimated_hours=path_content.estimated_hours,
        units=len(path_content.units),
        items=len(item_ids),
        enrolled=path_content.id == active_path_id,
        percent_complete=_percent(done, len(item_ids)),
    )


def path_detail(
    path_content: PathContent,
    catalog: ContentCatalog,
    *,
    completed: set[str],
    active_path_id: str | None,
) -> PathDetail:
    items_by_id = {
        item.id: item
        for pool in (catalog.exercises, catalog.lessons, catalog.quizzes)
        for item in pool
    }

    units: list[PathUnitDetail] = []
    next_item_id: str | None = None
    total = 0
    total_done = 0
    previous_percent = 100  # the first unit is always available
    for unit in path_content.units:
        item_statuses: list[PathItemStatus] = []
        unit_done = 0
        for item_id in unit.items:
            item = items_by_id[item_id]  # validator guarantees existence
            is_complete = item_id in completed
            if is_complete:
                unit_done += 1
            elif next_item_id is None:
                next_item_id = item_id
            item_statuses.append(
                PathItemStatus(
                    id=item.id,
                    kind=item.kind,
                    title=item.title,
                    estimated_time_minutes=item.estimated_time_minutes,
                    status="complete" if is_complete else "todo",
                )
            )
        total += len(unit.items)
        total_done += unit_done
        unit_percent = _percent(unit_done, len(unit.items))
        if unit_percent == 100:
            unit_status = "complete"
        elif previous_percent < MASTERY_THRESHOLD_PERCENT:
            unit_status = "locked"
        elif unit_done:
            unit_status = "in_progress"
        else:
            unit_status = "available"
        units.append(
            PathUnitDetail(
                id=unit.id,
                title=unit.title,
                description=unit.description,
                items=item_statuses,
                percent_complete=unit_percent,
                status=unit_status,
                milestone=unit.milestone,
            )
        )
        previous_percent = unit_percent

    return PathDetail(
        id=path_content.id,
        path_type=path_content.path_type,
        title=path_content.title,
        slug=path_content.slug,
        description=path_content.description,
        outcomes=list(path_content.outcomes),
        assumed_concepts=[concept_label(c) for c in path_content.assumed_concepts],
        estimated_hours=path_content.estimated_hours,
        enrolled=path_content.id == active_path_id,
        percent_complete=_percent(total_done, total),
        units=units,
        next_item_id=next_item_id,
    )
