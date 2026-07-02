"""Builds the adaptive Today plan from progress rollups.

Bridges the Task 3 wiring gap: ``build_today_plan`` consumes a
``planner.ProgressSnapshot`` while progress state lives in the rollup tables.
This maps the repository's read-only snapshot rows onto that dataclass.
"""

from __future__ import annotations

from datetime import datetime

from learn_code_api.adaptive_plan.planner import (
    ConceptProgress,
    PlanItem,
    ProgressSnapshot,
    build_today_plan,
)
from learn_code_api.content.models import ContentCatalog
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.progress.rollups import MasteryLabel


def build_snapshot(repo: ProgressRepository) -> ProgressSnapshot:
    rows = repo.concept_snapshot()
    concepts = {
        concept_id: ConceptProgress(
            concept_id=row.concept_id,
            mastery=row.mastery,
            label=MasteryLabel(row.label),
            attempted=True,
            review_due_at=row.review_due_at,
            recent_attempts=row.recent_attempts,
            last_status=row.last_status,
            last_confidence=row.last_confidence,
        )
        for concept_id, row in rows.items()
    }
    # V1 has no target-date UI, so interview date pacing stays unset.
    return ProgressSnapshot(concepts=concepts, target_interview_date=None)


def today_plan(
    catalog: ContentCatalog, repo: ProgressRepository, *, now: datetime
) -> list[PlanItem]:
    snapshot = build_snapshot(repo)
    return build_today_plan(catalog, snapshot, now=now)
