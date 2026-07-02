from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from learn_code_api.progress.events import EventType, ProgressEvent, fetch_events_ordered


class MasteryLabel(StrEnum):
    """Mastery scale labels (spec: Adaptive planning > Mastery scale)."""

    NEW = "new"
    LEARNING = "learning"
    PRACTICING = "practicing"
    REVIEW_READY = "review_ready"
    INTERVIEW_READY = "interview_ready"


_LABEL_FLOORS: tuple[tuple[int, MasteryLabel], ...] = (
    (90, MasteryLabel.INTERVIEW_READY),
    (75, MasteryLabel.REVIEW_READY),
    (50, MasteryLabel.PRACTICING),
    (20, MasteryLabel.LEARNING),
    (0, MasteryLabel.NEW),
)

MIN_MASTERY = 0
MAX_MASTERY = 100

# Score inputs (spec: Adaptive planning > Mastery scale > Score inputs).
CORRECT_PATTERN_PREDICTION = 8
CORRECT_SOLUTION_PASS = 10
CORRECT_QUIZ_ANSWER = 4
HINT_PENALTY_PER_HINT = 2
HINT_PENALTY_CAP = 6
FAILED_VALIDATION_PENALTY = 4
LOW_CONFIDENCE_THRESHOLD = 3
LOW_CONFIDENCE_GAIN_CAP = 6

# Review cadence (spec: Adaptive planning > Review cadence).
REVIEW_INTERVALS_DAYS = (1, 3, 7)
REVIEWS_REQUIRED_FOR_INTERVIEW_READY = len(REVIEW_INTERVALS_DAYS)

PASSING_STATUSES = {"passed"}
FAILED_TESTS_STATUS = "failed_tests"

RECENT_MISTAKES_LIMIT = 5

# Best-status ranking for exercise_summary (lower rank wins).
_STATUS_RANK = {
    "passed": 0,
    "failed_tests": 1,
    "runtime_error": 2,
    "syntax_error": 2,
    "timeout": 2,
    "memory_exceeded": 2,
    "output_exceeded": 2,
    "internal_error": 3,
}


def mastery_label(score: int) -> MasteryLabel:
    for floor, label in _LABEL_FLOORS:
        if score >= floor:
            return label
    return MasteryLabel.NEW


def clamp_mastery(score: int) -> int:
    return max(MIN_MASTERY, min(MAX_MASTERY, score))


def effective_mastery_label(score: int, spacing_stage: int) -> MasteryLabel:
    """Repeated success across spaced reviews is required for interview_ready
    (spec: "Repeated success on different days is required for interview_ready").
    """
    label = mastery_label(score)
    if label == MasteryLabel.INTERVIEW_READY and spacing_stage < REVIEWS_REQUIRED_FOR_INTERVIEW_READY:
        return MasteryLabel.REVIEW_READY
    return label


def exercise_submission_score_delta(
    *,
    status: str,
    hints_used: int,
    confidence: int | None,
    pattern_predicted_correct: bool,
) -> int:
    """Score delta for one ExerciseSubmitted event.

    See spec: Adaptive planning > Mastery scale > Score inputs.
    """
    if status in PASSING_STATUSES:
        gain = CORRECT_SOLUTION_PASS
        if pattern_predicted_correct:
            gain += CORRECT_PATTERN_PREDICTION
        hint_penalty = min(hints_used * HINT_PENALTY_PER_HINT, HINT_PENALTY_CAP)
        gain -= hint_penalty
        if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD:
            gain = min(gain, LOW_CONFIDENCE_GAIN_CAP)
        return gain
    if status == FAILED_TESTS_STATUS:
        return -FAILED_VALIDATION_PENALTY
    # Runtime/syntax/timeout/etc: no penalty, but review is rescheduled earlier below.
    return 0


def next_review(
    *,
    passed: bool,
    previous_stage: int,
    now: datetime,
    repeats_same_day_success: bool,
    previous_due_at: datetime | None,
) -> tuple[int, datetime]:
    """Next spacing stage and due date after a review outcome.

    See spec: Adaptive planning > Review cadence. "Repeated success on
    different days is required for interview_ready", so a second pass on the
    same calendar day as an already-recorded success does not advance the
    spacing stage again -- only a pass on a later day counts as the next
    spaced review.
    """
    if passed:
        if repeats_same_day_success and previous_due_at is not None:
            return previous_stage, previous_due_at
        stage = min(previous_stage + 1, len(REVIEW_INTERVALS_DAYS))
        interval_days = REVIEW_INTERVALS_DAYS[stage - 1]
        return stage, now + timedelta(days=interval_days)
    # Failed attempt or low confidence: due later same day / next session, and
    # spacing progress resets (spec: "Review due later the same day or next session").
    return 0, now


def best_status(current: str | None, candidate: str) -> str:
    if current is None:
        return candidate
    current_rank = _STATUS_RANK.get(current, 99)
    candidate_rank = _STATUS_RANK.get(candidate, 99)
    return candidate if candidate_rank < current_rank else current


def apply_exercise_submission(conn: sqlite3.Connection, event: ProgressEvent) -> None:
    """Fold one ExerciseSubmitted event into the rollup tables.

    Uses the event's own created_at as the time reference so replay via
    recompute_rollups is deterministic regardless of wall-clock time.
    """
    payload = event.payload
    status = payload["status"]
    concepts: list[str] = payload.get("concepts", [])
    hints_used: int = payload.get("hints_used", 0)
    confidence: int | None = payload.get("confidence")
    predicted_pattern: str | None = payload.get("predicted_pattern")
    time_minutes: int = payload.get("time_minutes", 0)
    now = event.created_at
    passed = status in PASSING_STATUSES
    pattern_predicted_correct = predicted_pattern is not None and predicted_pattern in concepts

    delta = exercise_submission_score_delta(
        status=status,
        hints_used=hints_used,
        confidence=confidence,
        pattern_predicted_correct=pattern_predicted_correct,
    )

    for concept_id in concepts:
        _apply_concept_outcome(conn, concept_id=concept_id, delta=delta, passed=passed, now=now)

    if event.content_id is not None:
        _update_exercise_summary(conn, exercise_id=event.content_id, status=status, now=now)

    _update_daily_activity(conn, now=now, passed=passed, time_minutes=time_minutes)


def _apply_concept_outcome(
    conn: sqlite3.Connection, *, concept_id: str, delta: int, passed: bool, now: datetime
) -> None:
    mastery_row = conn.execute(
        "SELECT mastery, updated_at FROM concept_mastery WHERE concept_id = ?", (concept_id,)
    ).fetchone()
    current_score = mastery_row[0] if mastery_row is not None else 0
    previous_updated_at = datetime.fromisoformat(mastery_row[1]) if mastery_row is not None else None
    new_score = clamp_mastery(current_score + delta)

    queue_row = conn.execute(
        "SELECT spacing_stage, review_due_at FROM review_queue WHERE concept_id = ?", (concept_id,)
    ).fetchone()
    previous_stage = queue_row[0] if queue_row is not None else 0
    previous_due_at = datetime.fromisoformat(queue_row[1]) if queue_row is not None else None

    # A same-day repeat only replays a prior *success*; a same-day pass right
    # after a failure (previous_stage reset to 0) still counts as the first
    # spaced review, not a duplicate of it.
    repeats_same_day_success = (
        previous_updated_at is not None
        and previous_updated_at.date() == now.date()
        and previous_stage > 0
    )
    new_stage, due_at = next_review(
        passed=passed,
        previous_stage=previous_stage,
        now=now,
        repeats_same_day_success=repeats_same_day_success,
        previous_due_at=previous_due_at,
    )

    label = effective_mastery_label(new_score, new_stage)

    conn.execute(
        """
        INSERT INTO concept_mastery (concept_id, mastery, label, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(concept_id) DO UPDATE SET
            mastery = excluded.mastery,
            label = excluded.label,
            updated_at = excluded.updated_at
        """,
        (concept_id, new_score, label.value, now.isoformat()),
    )
    conn.execute(
        """
        INSERT INTO review_queue (concept_id, review_due_at, spacing_stage)
        VALUES (?, ?, ?)
        ON CONFLICT(concept_id) DO UPDATE SET
            review_due_at = excluded.review_due_at,
            spacing_stage = excluded.spacing_stage
        """,
        (concept_id, due_at.isoformat(), new_stage),
    )


def _update_exercise_summary(
    conn: sqlite3.Connection, *, exercise_id: str, status: str, now: datetime
) -> None:
    row = conn.execute(
        "SELECT best_status, attempts FROM exercise_summary WHERE exercise_id = ?",
        (exercise_id,),
    ).fetchone()
    current_best = row[0] if row is not None else None
    attempts = (row[1] if row is not None else 0) + 1
    updated_best = best_status(current_best, status)

    conn.execute(
        """
        INSERT INTO exercise_summary (exercise_id, best_status, attempts, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(exercise_id) DO UPDATE SET
            best_status = excluded.best_status,
            attempts = excluded.attempts,
            updated_at = excluded.updated_at
        """,
        (exercise_id, updated_best, attempts, now.isoformat()),
    )


def _update_daily_activity(
    conn: sqlite3.Connection, *, now: datetime, passed: bool, time_minutes: int
) -> None:
    day = now.date().isoformat()
    row = conn.execute(
        "SELECT time_minutes, completed_count FROM daily_activity WHERE day = ?", (day,)
    ).fetchone()
    current_time = row[0] if row is not None else 0
    current_completed = row[1] if row is not None else 0

    conn.execute(
        """
        INSERT INTO daily_activity (day, time_minutes, completed_count)
        VALUES (?, ?, ?)
        ON CONFLICT(day) DO UPDATE SET
            time_minutes = excluded.time_minutes,
            completed_count = excluded.completed_count
        """,
        (
            day,
            current_time + time_minutes,
            current_completed + (1 if passed else 0),
        ),
    )


def recompute_rollups(conn: sqlite3.Connection) -> None:
    """Rebuild all rollup tables from the event log (spec rule: "Rollups can
    be recomputed from events")."""
    conn.execute("DELETE FROM concept_mastery")
    conn.execute("DELETE FROM review_queue")
    conn.execute("DELETE FROM exercise_summary")
    conn.execute("DELETE FROM daily_activity")

    for event in fetch_events_ordered(conn):
        if event.type == EventType.EXERCISE_SUBMITTED:
            apply_exercise_submission(conn, event)
        # Other required event types (LessonCompleted, HintViewed, PatternPredicted,
        # QuizAnswered, PlaygroundRunCompleted, ReviewCompleted, PlanItemSkipped,
        # OllamaReviewRequested) are stored for audit today; V1 content only ships
        # exercises, so there is no rollup behavior to implement for them yet.

    conn.commit()


class ConceptSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    mastery: int
    label: MasteryLabel
    review_due_at: datetime | None = None


class ProgressSummary(BaseModel):
    """See spec: Stable API contracts > Progress summary."""

    model_config = ConfigDict(extra="forbid")

    streak_days: int
    total_time_minutes: int
    concepts: list[ConceptSummary]
    recent_mistakes: list[str]
    next_recommended_action: str


def build_summary(conn: sqlite3.Connection, *, now: datetime) -> ProgressSummary:
    concept_rows = conn.execute(
        """
        SELECT concept_mastery.concept_id, concept_mastery.mastery, concept_mastery.label,
               review_queue.review_due_at
        FROM concept_mastery
        LEFT JOIN review_queue ON review_queue.concept_id = concept_mastery.concept_id
        ORDER BY concept_mastery.concept_id ASC
        """
    ).fetchall()
    concepts = [
        ConceptSummary(
            id=row[0],
            mastery=row[1],
            label=MasteryLabel(row[2]),
            review_due_at=datetime.fromisoformat(row[3]) if row[3] is not None else None,
        )
        for row in concept_rows
    ]

    total_time_minutes = conn.execute(
        "SELECT COALESCE(SUM(time_minutes), 0) FROM daily_activity"
    ).fetchone()[0]

    streak_days = _compute_streak_days(conn, now=now)

    recent_mistakes = [
        row[0]
        for row in conn.execute(
            """
            SELECT exercise_id FROM exercise_summary
            WHERE best_status != 'passed'
            ORDER BY updated_at DESC, exercise_id ASC
            LIMIT ?
            """,
            (RECENT_MISTAKES_LIMIT,),
        ).fetchall()
    ]

    next_recommended_action = _recommend_next_action(conn, now=now)

    return ProgressSummary(
        streak_days=streak_days,
        total_time_minutes=total_time_minutes,
        concepts=concepts,
        recent_mistakes=recent_mistakes,
        next_recommended_action=next_recommended_action,
    )


def _compute_streak_days(conn: sqlite3.Connection, *, now: datetime) -> int:
    active_days = {
        row[0]
        for row in conn.execute(
            "SELECT day FROM daily_activity WHERE completed_count > 0"
        ).fetchall()
    }
    streak = 0
    cursor_day = now.date()
    while cursor_day.isoformat() in active_days:
        streak += 1
        cursor_day -= timedelta(days=1)
    return streak


def _recommend_next_action(conn: sqlite3.Connection, *, now: datetime) -> str:
    due_row = conn.execute(
        """
        SELECT concept_id FROM review_queue
        WHERE review_due_at <= ?
        ORDER BY review_due_at ASC, concept_id ASC
        LIMIT 1
        """,
        (now.isoformat(),),
    ).fetchone()
    if due_row is not None:
        return f"Review {due_row[0]}"

    weak_row = conn.execute(
        """
        SELECT concept_id FROM concept_mastery
        WHERE mastery < 50
        ORDER BY mastery ASC, concept_id ASC
        LIMIT 1
        """
    ).fetchone()
    if weak_row is not None:
        return f"Practice {weak_row[0]}"

    return "Start a new exercise"
