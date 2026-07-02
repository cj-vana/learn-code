from __future__ import annotations

from datetime import UTC, datetime, timedelta

from learn_code_api.adaptive_plan.planner import (
    ConceptProgress,
    ProgressSnapshot,
    build_today_plan,
)
from learn_code_api.content.models import (
    ContentCatalog,
    ExerciseContent,
    LessonContent,
    QuizContent,
)
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


def _test_provenance() -> dict:
    return {
        "brief_id": "t.planner",
        "author": "generated",
        "generated_at": "2026-07-02T00:00:00Z",
        "inspiration_sources": [],
        "originality_notes": "Original planner fixture.",
    }


def make_lesson(**overrides: object) -> LessonContent:
    data = {
        "id": "lesson.t.1",
        "kind": "lesson",
        "version": 1,
        "language": "python",
        "title": "Lesson fixture",
        "slug": "lesson-fixture",
        "difficulty": "easy",
        "concepts": ["python.lists"],
        "prerequisites": [],
        "estimated_time_minutes": 10,
        "review_status": "published",
        "source_status": "original",
        "provenance": _test_provenance(),
        "body_markdown": "Body.",
        "checkpoints": [{"question": "q?", "answer": "a", "explanation": "e"}],
    }
    data.update(overrides)
    return LessonContent.model_validate(data)


def make_quiz(**overrides: object) -> QuizContent:
    data = {
        "id": "quiz.t.1",
        "kind": "quiz",
        "version": 1,
        "language": "python",
        "title": "Quiz fixture",
        "slug": "quiz-fixture",
        "difficulty": "easy",
        "concepts": ["python.lists", "python.strings"],
        "prerequisites": [],
        "estimated_time_minutes": 5,
        "review_status": "published",
        "source_status": "original",
        "provenance": _test_provenance(),
        "quiz_type": "mixed_review",
        "questions": [
            {
                "id": "quiz.t.1.q1",
                "prompt": "?",
                "choices": ["a", "b"],
                "correct_choice": "a",
                "explanation": "because",
                "concepts": ["python.lists"],
            }
        ],
    }
    data.update(overrides)
    return QuizContent.model_validate(data)


def _concept(
    concept_id: str,
    *,
    mastery: int,
    review_due_at: datetime | None = None,
    last_status: str | None = None,
) -> ConceptProgress:
    from learn_code_api.progress.rollups import mastery_label

    return ConceptProgress(
        concept_id=concept_id,
        mastery=mastery,
        label=mastery_label(mastery),
        attempted=True,
        review_due_at=review_due_at,
        last_status=last_status,
    )


def test_lesson_emitted_for_new_concept():
    catalog = ContentCatalog(
        exercises=[], lessons=[make_lesson(id="lesson.l1")], quizzes=[]
    )
    snapshot = ProgressSnapshot(concepts={})
    items = build_today_plan(catalog, snapshot, now=NOW)
    assert [item.kind.value for item in items] == ["lesson"]
    assert items[0].content_id == "lesson.l1"


def test_completed_lesson_never_reemits():
    catalog = ContentCatalog(
        exercises=[], lessons=[make_lesson(id="lesson.l1")], quizzes=[]
    )
    snapshot = ProgressSnapshot(
        concepts={}, completed_lesson_ids=frozenset({"lesson.l1"})
    )
    assert build_today_plan(catalog, snapshot, now=NOW) == []


def test_lesson_not_emitted_once_concepts_practicing():
    catalog = ContentCatalog(
        exercises=[], lessons=[make_lesson(id="lesson.l1")], quizzes=[]
    )
    snapshot = ProgressSnapshot(
        concepts={"python.lists": _concept("python.lists", mastery=60)}
    )
    assert build_today_plan(catalog, snapshot, now=NOW) == []


def test_quiz_emitted_when_concepts_ready():
    catalog = ContentCatalog(exercises=[], lessons=[], quizzes=[make_quiz(id="quiz.q1")])
    snapshot = ProgressSnapshot(
        concepts={
            "python.lists": _concept("python.lists", mastery=65),
            "python.strings": _concept("python.strings", mastery=70),
        }
    )
    items = build_today_plan(catalog, snapshot, now=NOW)
    assert [item.kind.value for item in items] == ["quiz"]
    assert items[0].content_id == "quiz.q1"


def test_completed_quiz_not_reemitted_when_not_due():
    catalog = ContentCatalog(exercises=[], lessons=[], quizzes=[make_quiz(id="quiz.q1")])
    snapshot = ProgressSnapshot(
        concepts={
            "python.lists": _concept("python.lists", mastery=65),
            "python.strings": _concept("python.strings", mastery=70),
        },
        completed_quiz_ids=frozenset({"quiz.q1"}),
    )
    assert build_today_plan(catalog, snapshot, now=NOW) == []


def test_due_review_quiz_outranks_and_reemits_even_if_completed():
    catalog = ContentCatalog(
        exercises=[],
        lessons=[],
        quizzes=[make_quiz(id="quiz.q1", concepts=["python.lists"])],
    )
    snapshot = ProgressSnapshot(
        concepts={
            "python.lists": _concept(
                "python.lists",
                mastery=30,
                review_due_at=NOW,
                last_status="failed_tests",
            )
        },
        completed_quiz_ids=frozenset({"quiz.q1"}),
    )
    items = build_today_plan(catalog, snapshot, now=NOW)
    assert len(items) == 1
    assert items[0].kind.value == "quiz"
    assert items[0].priority >= 0.9
