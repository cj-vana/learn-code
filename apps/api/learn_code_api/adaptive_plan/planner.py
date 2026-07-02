from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from learn_code_api.content.models import ContentCatalog, ExerciseContent
from learn_code_api.progress.rollups import MasteryLabel

# Fixed namespace so plan item ids are deterministic (uuid5) rather than random,
# per the "planner must be fully deterministic and inspectable" constraint.
_PLAN_ITEM_NAMESPACE = uuid.UUID("2f6e6b9e-8a9b-4d3e-9c1a-6d0a6a6b7a10")

PRACTICING_FLOOR = 50  # spec: "practicing" starts at mastery 50.
TINY_DRILL_MAX_MINUTES = 5
LOW_CONFIDENCE_THRESHOLD = 3
TARGET_DATE_WINDOW_DAYS = 30
DEFAULT_LIMIT = 5

TIER_BASE_PRIORITY = {
    1: 1.0,  # due reviews for weak/recently failed concepts
    2: 0.8,  # prerequisites blocking high-value patterns
    3: 0.6,  # weak patterns below 50 mastery
    4: 0.4,  # new high-yield patterns
    5: 0.2,  # mixed recognition quizzes (no quiz content in V1 catalog)
    6: 0.05,  # capstone / timed practice
}
DEPTH_PENALTY = 0.02
ATTEMPTS_PENALTY = 0.01
TINY_DRILL_BONUS = 0.03
MAX_TIE_BREAK_STEPS = 5


class PlanKind(StrEnum):
    LESSON = "lesson"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    REVIEW = "review"


class Rationale(BaseModel):
    """See spec: Adaptive planning > Required rationale fields."""

    model_config = ConfigDict(extra="forbid")

    reason: str
    because: list[str]
    alternatives: list[str]


class PlanItem(BaseModel):
    """See spec: Stable API contracts > Plan item."""

    model_config = ConfigDict(extra="forbid")

    id: str
    kind: PlanKind
    content_id: str
    title: str
    concepts: list[str]
    priority: float
    estimated_time_minutes: int
    rationale: Rationale


@dataclass(frozen=True)
class ConceptProgress:
    """The planner's view of one concept's progress state.

    This is a lighter, planner-focused shape than the API's ProgressSummary
    contract: it carries the extra signals (recent attempts, last status,
    last confidence) that the priority and tie-break rules need but the
    public summary does not expose.
    """

    concept_id: str
    mastery: int
    label: MasteryLabel
    attempted: bool
    review_due_at: datetime | None = None
    recent_attempts: int = 0
    last_status: str | None = None
    last_confidence: int | None = None


@dataclass(frozen=True)
class ProgressSnapshot:
    concepts: dict[str, ConceptProgress] = field(default_factory=dict)
    target_interview_date: date | None = None

    def concept(self, concept_id: str) -> ConceptProgress:
        return self.concepts.get(
            concept_id,
            ConceptProgress(
                concept_id=concept_id,
                mastery=0,
                label=MasteryLabel.NEW,
                attempted=False,
            ),
        )


@dataclass(frozen=True)
class _Candidate:
    exercise: ExerciseContent
    tier: int
    kind: PlanKind
    priority: float
    reason: str
    because: list[str]


def build_today_plan(
    catalog: ContentCatalog,
    progress: ProgressSnapshot,
    *,
    now: datetime,
    limit: int = DEFAULT_LIMIT,
) -> list[PlanItem]:
    """Build a deterministic, priority-ordered Today plan.

    See spec: Adaptive planning > Prioritization order and Tie-breaking.
    V1 content only ships exercises (see content/loader.py), so this only
    ever emits "exercise" and "review" plan items; lesson/quiz/capstone
    tiers are reserved for when that content exists.
    """
    prereq_depth = _concept_prereq_depth(catalog)
    blocking_concepts = _blocking_concepts(catalog)

    candidates: list[_Candidate] = []
    for exercise in sorted(catalog.exercises, key=lambda item: item.id):
        candidate = _classify_exercise(
            exercise, progress, now, prereq_depth, blocking_concepts
        )
        if candidate is not None:
            candidates.append(candidate)

    candidates.sort(key=lambda candidate: (-candidate.priority, candidate.exercise.id))

    items: list[PlanItem] = []
    for index, candidate in enumerate(candidates[:limit]):
        alternatives = [
            other.exercise.id
            for other in candidates[index + 1 : index + 1 + 2]
        ]
        items.append(_to_plan_item(candidate, alternatives))
    return items


def _concept_prereq_map(catalog: ContentCatalog) -> dict[str, set[str]]:
    prereqs: dict[str, set[str]] = {}
    for exercise in catalog.exercises:
        for concept_id in exercise.concepts:
            prereqs.setdefault(concept_id, set()).update(exercise.prerequisites)
    return prereqs


def _concept_prereq_depth(catalog: ContentCatalog) -> dict[str, int]:
    """Depth of each concept in the prerequisite graph (0 = no prerequisites)."""
    prereqs = _concept_prereq_map(catalog)
    depth_cache: dict[str, int] = {}

    def depth_of(concept_id: str, visiting: frozenset[str]) -> int:
        if concept_id in depth_cache:
            return depth_cache[concept_id]
        if concept_id in visiting:
            return 0  # cycle guard: treat as a root so depth stays deterministic.
        parents = prereqs.get(concept_id, set())
        if not parents:
            depth_cache[concept_id] = 0
            return 0
        result = 1 + max(
            depth_of(parent, visiting | {concept_id}) for parent in sorted(parents)
        )
        depth_cache[concept_id] = result
        return result

    all_concepts = set(prereqs) | {parent for parents in prereqs.values() for parent in parents}
    for concept_id in sorted(all_concepts):
        depth_of(concept_id, frozenset())
    return depth_cache


def _blocking_concepts(catalog: ContentCatalog) -> set[str]:
    """Concepts referenced as a prerequisite by at least one other exercise."""
    blocking: set[str] = set()
    for exercise in catalog.exercises:
        blocking.update(exercise.prerequisites)
    return blocking


def _classify_exercise(
    exercise: ExerciseContent,
    progress: ProgressSnapshot,
    now: datetime,
    prereq_depth: dict[str, int],
    blocking_concepts: set[str],
) -> _Candidate | None:
    concept_states = [progress.concept(concept_id) for concept_id in exercise.concepts]

    # Tier 1: due reviews for weak or recently failed concepts.
    due_weak = [
        state
        for state in concept_states
        if state.review_due_at is not None
        and state.review_due_at <= now
        and (state.mastery < PRACTICING_FLOOR or state.last_status not in (None, "passed"))
    ]
    if due_weak:
        primary = min(due_weak, key=lambda state: (state.mastery, state.concept_id))
        return _build_candidate(
            exercise,
            tier=1,
            kind=PlanKind.REVIEW,
            primary=primary,
            prereq_depth=prereq_depth,
            reason=f"Due review for {primary.concept_id} after recent difficulty",
            because=[
                f"{primary.concept_id} mastery is {primary.mastery}",
                f"last attempt status was {primary.last_status or 'unknown'}",
                f"review was due at {primary.review_due_at.isoformat()}",
            ],
        )

    # Tier 2: prerequisites blocking high-value interview patterns.
    blocking = [
        state
        for state in concept_states
        if state.concept_id in blocking_concepts and state.mastery < PRACTICING_FLOOR
    ]
    if blocking:
        primary = min(blocking, key=lambda state: (state.mastery, state.concept_id))
        return _build_candidate(
            exercise,
            tier=2,
            kind=PlanKind.EXERCISE,
            primary=primary,
            prereq_depth=prereq_depth,
            reason=f"{primary.concept_id} is a prerequisite blocking later patterns",
            because=[
                f"{primary.concept_id} mastery is {primary.mastery}",
                f"{primary.concept_id} gates at least one other exercise",
            ],
        )

    # Tier 3: weak patterns below 50 mastery.
    weak = [state for state in concept_states if state.attempted and state.mastery < PRACTICING_FLOOR]
    if weak:
        primary = min(weak, key=lambda state: (state.mastery, state.concept_id))
        return _build_candidate(
            exercise,
            tier=3,
            kind=PlanKind.EXERCISE,
            primary=primary,
            prereq_depth=prereq_depth,
            reason=f"{primary.concept_id} is still below practicing mastery",
            because=[f"{primary.concept_id} mastery is {primary.mastery}"],
        )

    # Tier 4: new high-yield patterns in the interview taxonomy.
    new = [state for state in concept_states if not state.attempted]
    if new:
        primary = min(new, key=lambda state: state.concept_id)
        because = [f"{primary.concept_id} has not been attempted yet"]
        if progress.target_interview_date is not None:
            days_out = (progress.target_interview_date - now.date()).days
            if 0 <= days_out <= TARGET_DATE_WINDOW_DAYS:
                because.append(f"target interview date is within {TARGET_DATE_WINDOW_DAYS} days")
        return _build_candidate(
            exercise,
            tier=4,
            kind=PlanKind.EXERCISE,
            primary=primary,
            prereq_depth=prereq_depth,
            reason=f"New high-yield pattern: {primary.concept_id}",
            because=because,
        )

    # Tier 6: capstone / timed practice, only once every concept is at least practicing.
    if concept_states and all(state.mastery >= PRACTICING_FLOOR for state in concept_states):
        primary = min(concept_states, key=lambda state: state.concept_id)
        return _build_candidate(
            exercise,
            tier=6,
            kind=PlanKind.EXERCISE,
            primary=primary,
            prereq_depth=prereq_depth,
            reason="Prerequisites are at least practicing; ready for timed practice",
            because=[f"all concepts for {exercise.id} are at or above practicing mastery"],
        )

    return None


def _build_candidate(
    exercise: ExerciseContent,
    *,
    tier: int,
    kind: PlanKind,
    primary: ConceptProgress,
    prereq_depth: dict[str, int],
    reason: str,
    because: list[str],
) -> _Candidate:
    depth = prereq_depth.get(primary.concept_id, 0)
    priority = TIER_BASE_PRIORITY[tier]
    priority -= min(depth, MAX_TIE_BREAK_STEPS) * DEPTH_PENALTY
    priority -= min(primary.recent_attempts, MAX_TIE_BREAK_STEPS) * ATTEMPTS_PENALTY

    is_tiny_drill = exercise.estimated_time_minutes <= TINY_DRILL_MAX_MINUTES
    low_confidence = (
        primary.last_confidence is not None and primary.last_confidence < LOW_CONFIDENCE_THRESHOLD
    )
    if low_confidence and is_tiny_drill:
        priority += TINY_DRILL_BONUS

    priority = round(min(max(priority, 0.0), 1.0), 4)

    return _Candidate(
        exercise=exercise,
        tier=tier,
        kind=kind,
        priority=priority,
        reason=reason,
        because=because,
    )


def _to_plan_item(candidate: _Candidate, alternatives: list[str]) -> PlanItem:
    exercise = candidate.exercise
    item_id = str(uuid.uuid5(_PLAN_ITEM_NAMESPACE, f"{candidate.kind.value}:{exercise.id}"))
    return PlanItem(
        id=item_id,
        kind=candidate.kind,
        content_id=exercise.id,
        title=exercise.title,
        concepts=list(exercise.concepts),
        priority=candidate.priority,
        estimated_time_minutes=exercise.estimated_time_minutes,
        rationale=Rationale(
            reason=candidate.reason,
            because=candidate.because,
            alternatives=alternatives,
        ),
    )
