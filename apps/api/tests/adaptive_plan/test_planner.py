from __future__ import annotations

from datetime import UTC, datetime, timedelta

from learn_code_api.adaptive_plan.planner import (
    ConceptProgress,
    ProgressSnapshot,
    build_today_plan,
)
from learn_code_api.content.models import ContentCatalog, ExerciseContent
from learn_code_api.progress.rollups import MasteryLabel
from tests.content.test_models import valid_exercise_data

NOW = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)


def make_exercise(**overrides: object) -> ExerciseContent:
    data = valid_exercise_data()
    data.update(overrides)
    return ExerciseContent.model_validate(data)


def test_due_weak_review_ranks_first():
    review_exercise = make_exercise(
        id="exercise.seed.two-pointers-001",
        slug="two-pointers-001",
        title="Two Pointers Review",
        concepts=["patterns.two_pointers"],
        prerequisites=[],
    )
    new_exercise = make_exercise(
        id="exercise.seed.new-pattern-001",
        slug="new-pattern-001",
        title="Brand New Pattern",
        concepts=["patterns.brand_new"],
        prerequisites=[],
    )
    catalog = ContentCatalog(exercises=[new_exercise, review_exercise])

    progress = ProgressSnapshot(
        concepts={
            "patterns.two_pointers": ConceptProgress(
                concept_id="patterns.two_pointers",
                mastery=42,
                label=MasteryLabel.LEARNING,
                attempted=True,
                review_due_at=NOW - timedelta(hours=1),
                last_status="failed_tests",
            ),
        }
    )

    plan = build_today_plan(catalog, progress, now=NOW)

    assert plan[0].content_id == review_exercise.id
    assert plan[0].kind == "review"


def test_prerequisite_ranks_before_new_pattern():
    prereq_exercise = make_exercise(
        id="exercise.seed.functions-basics-001",
        slug="functions-basics-001",
        title="Functions Basics",
        concepts=["python.functions"],
        prerequisites=[],
    )
    pattern_exercise = make_exercise(
        id="exercise.seed.sliding-window-001",
        slug="sliding-window-001",
        title="Sliding Window",
        concepts=["patterns.sliding_window"],
        prerequisites=["python.functions"],
    )
    catalog = ContentCatalog(exercises=[pattern_exercise, prereq_exercise])

    progress = ProgressSnapshot(concepts={})

    plan = build_today_plan(catalog, progress, now=NOW)

    ids = [item.content_id for item in plan]
    assert ids.index(prereq_exercise.id) < ids.index(pattern_exercise.id)


def test_weak_concepts_rank_before_new_concepts():
    weak_exercise = make_exercise(
        id="exercise.seed.dict-basics-001",
        slug="dict-basics-001",
        title="Dictionary Basics",
        concepts=["python.dictionaries"],
        prerequisites=[],
    )
    new_exercise = make_exercise(
        id="exercise.seed.set-basics-001",
        slug="set-basics-001",
        title="Set Basics",
        concepts=["python.sets"],
        prerequisites=[],
    )
    catalog = ContentCatalog(exercises=[new_exercise, weak_exercise])

    progress = ProgressSnapshot(
        concepts={
            "python.dictionaries": ConceptProgress(
                concept_id="python.dictionaries",
                mastery=30,
                label=MasteryLabel.LEARNING,
                attempted=True,
                review_due_at=NOW + timedelta(days=2),
                last_status="passed",
            ),
        }
    )

    plan = build_today_plan(catalog, progress, now=NOW)

    ids = [item.content_id for item in plan]
    assert ids.index(weak_exercise.id) < ids.index(new_exercise.id)


def test_low_confidence_prefers_tiny_drill_over_standard_drill():
    tiny_drill = make_exercise(
        id="exercise.seed.tuples-tiny-001",
        slug="tuples-tiny-001",
        title="Tuple Tiny Drill",
        concepts=["python.tuples"],
        prerequisites=[],
        estimated_time_minutes=4,
    )
    standard_drill = make_exercise(
        id="exercise.seed.tuples-standard-001",
        slug="tuples-standard-001",
        title="Tuple Standard Drill",
        concepts=["python.tuples"],
        prerequisites=[],
        estimated_time_minutes=20,
    )
    catalog = ContentCatalog(exercises=[standard_drill, tiny_drill])

    progress = ProgressSnapshot(
        concepts={
            "python.tuples": ConceptProgress(
                concept_id="python.tuples",
                mastery=25,
                label=MasteryLabel.LEARNING,
                attempted=True,
                review_due_at=NOW + timedelta(days=2),
                last_status="passed",
                last_confidence=2,
            ),
        }
    )

    plan = build_today_plan(catalog, progress, now=NOW)

    ids = [item.content_id for item in plan]
    assert ids.index(tiny_drill.id) < ids.index(standard_drill.id)


def test_rationale_includes_reason_because_and_alternatives():
    exercise_a = make_exercise(
        id="exercise.seed.rationale-a-001",
        slug="rationale-a-001",
        concepts=["python.strings"],
        prerequisites=[],
    )
    exercise_b = make_exercise(
        id="exercise.seed.rationale-b-001",
        slug="rationale-b-001",
        concepts=["python.tuples"],
        prerequisites=[],
    )
    catalog = ContentCatalog(exercises=[exercise_a, exercise_b])

    plan = build_today_plan(catalog, ProgressSnapshot(concepts={}), now=NOW)

    assert plan
    for item in plan:
        assert isinstance(item.rationale.reason, str) and item.rationale.reason
        assert isinstance(item.rationale.because, list) and item.rationale.because
        assert isinstance(item.rationale.alternatives, list)


def test_plan_ids_are_deterministic_across_calls():
    exercise = make_exercise(
        id="exercise.seed.deterministic-001",
        slug="deterministic-001",
        concepts=["python.strings"],
        prerequisites=[],
    )
    catalog = ContentCatalog(exercises=[exercise])
    progress = ProgressSnapshot(concepts={})

    plan_one = build_today_plan(catalog, progress, now=NOW)
    plan_two = build_today_plan(catalog, progress, now=NOW)

    assert [item.id for item in plan_one] == [item.id for item in plan_two]


def test_build_today_plan_respects_limit():
    exercises = [
        make_exercise(
            id=f"exercise.seed.limit-{index:03d}",
            slug=f"limit-{index:03d}",
            concepts=[f"python.concept_{index}"],
            prerequisites=[],
        )
        for index in range(8)
    ]
    catalog = ContentCatalog(exercises=exercises)

    plan = build_today_plan(catalog, ProgressSnapshot(concepts={}), now=NOW, limit=3)

    assert len(plan) == 3


def test_capstone_requires_all_concepts_at_least_practicing():
    exercise = make_exercise(
        id="exercise.seed.capstone-001",
        slug="capstone-001",
        concepts=["python.recursion"],
        prerequisites=[],
    )
    catalog = ContentCatalog(exercises=[exercise])

    progress = ProgressSnapshot(
        concepts={
            "python.recursion": ConceptProgress(
                concept_id="python.recursion",
                mastery=80,
                label=MasteryLabel.REVIEW_READY,
                attempted=True,
                review_due_at=NOW + timedelta(days=5),
                last_status="passed",
            ),
        }
    )

    plan = build_today_plan(catalog, progress, now=NOW)

    assert len(plan) == 1
    assert plan[0].content_id == exercise.id
    assert plan[0].kind == "exercise"
