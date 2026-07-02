from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from learn_code_api.progress.db import ProgressRepository
from learn_code_api.progress.events import EventType, ProgressEvent, fetch_events_ordered
from learn_code_api.progress.migrations import MIGRATIONS, apply_migrations
from learn_code_api.progress.rollups import MasteryLabel

NOW = datetime(2026, 7, 1, 12, 0, 0, tzinfo=UTC)


def make_repo(tmp_path: Path, *, now: datetime = NOW) -> ProgressRepository:
    return ProgressRepository(tmp_path / "progress.db", now=now)


def raw_connection(tmp_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(tmp_path / "progress.db")
    conn.row_factory = sqlite3.Row
    return conn


def test_apply_migrations_is_idempotent(tmp_path: Path):
    conn = sqlite3.connect(tmp_path / "raw.db")

    apply_migrations(conn, now=NOW)
    apply_migrations(conn, now=NOW)

    rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
    assert [row[0] for row in rows] == [migration.version for migration in MIGRATIONS]

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {
        "schema_migrations",
        "progress_events",
        "concept_mastery",
        "daily_activity",
        "review_queue",
        "exercise_summary",
    } <= tables


def test_append_event_preserves_content_version(tmp_path: Path):
    repo = make_repo(tmp_path)

    event = ProgressEvent(
        id="11111111-1111-1111-1111-111111111111",
        type=EventType.EXERCISE_SUBMITTED,
        created_at=NOW,
        content_id="exercise.seed.count-tags-001",
        content_version=3,
        language="python",
        session_id="session-1",
        payload={"status": "passed", "concepts": ["python.dictionaries"]},
    )
    repo.append_event(event)
    repo.close()

    conn = raw_connection(tmp_path)
    stored = fetch_events_ordered(conn)
    assert len(stored) == 1
    assert stored[0].content_version == 3
    assert stored[0].content_id == "exercise.seed.count-tags-001"


def test_append_event_supports_all_required_event_types(tmp_path: Path):
    repo = make_repo(tmp_path)

    for index, event_type in enumerate(EventType):
        payload = (
            {"status": "passed", "concepts": ["python.dictionaries"]}
            if event_type == EventType.EXERCISE_SUBMITTED
            else {}
        )
        repo.append_event(
            ProgressEvent(
                id=f"event-{index}",
                type=event_type,
                created_at=NOW,
                content_id="exercise.seed.count-tags-001",
                content_version=1,
                language="python",
                session_id="session-1",
                payload=payload,
            )
        )
    repo.close()

    conn = raw_connection(tmp_path)
    stored = fetch_events_ordered(conn)
    assert {event.type for event in stored} == set(EventType)


def test_record_exercise_submission_moves_mastery_from_new_to_learning(tmp_path: Path):
    repo = make_repo(tmp_path)

    # A single pass (+10) keeps mastery inside the "new" band (0-19); a second
    # passing submission crosses the "learning" floor (20) per the spec's
    # mastery scale.
    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW,
    )
    conn = raw_connection(tmp_path)
    first_row = conn.execute(
        "SELECT mastery, label FROM concept_mastery WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    conn.close()
    assert first_row["mastery"] == 10
    assert first_row["label"] == MasteryLabel.NEW.value

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW + timedelta(days=1),
    )
    repo.close()

    conn = raw_connection(tmp_path)
    second_row = conn.execute(
        "SELECT mastery, label FROM concept_mastery WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    assert second_row["mastery"] == 20
    assert second_row["label"] == MasteryLabel.LEARNING.value


def test_record_exercise_submission_schedules_first_review_in_one_day(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW,
    )
    repo.close()

    conn = raw_connection(tmp_path)
    row = conn.execute(
        "SELECT review_due_at, spacing_stage FROM review_queue WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    assert datetime.fromisoformat(row["review_due_at"]) == NOW + timedelta(days=1)
    assert row["spacing_stage"] == 1


def test_same_day_repeat_pass_does_not_double_advance_spacing_stage(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW,
    )
    # A second pass later the same calendar day must not count as a second
    # spaced review (spec: repeated success requires different days).
    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW + timedelta(hours=2),
    )
    repo.close()

    conn = raw_connection(tmp_path)
    row = conn.execute(
        "SELECT review_due_at, spacing_stage FROM review_queue WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    assert row["spacing_stage"] == 1
    assert datetime.fromisoformat(row["review_due_at"]) == NOW + timedelta(days=1)

    # A pass on the following day is a genuinely new spaced review.
    repo2 = ProgressRepository(tmp_path / "progress.db", now=NOW + timedelta(days=1))
    repo2.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW + timedelta(days=1),
    )
    repo2.close()

    conn2 = raw_connection(tmp_path)
    row2 = conn2.execute(
        "SELECT review_due_at, spacing_stage FROM review_queue WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    assert row2["spacing_stage"] == 2
    assert datetime.fromisoformat(row2["review_due_at"]) == NOW + timedelta(days=1 + 3)


def test_same_day_pass_after_earlier_failure_still_counts_as_first_review(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="failed_tests",
        session_id="session-1",
        now=NOW,
    )
    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW + timedelta(hours=1),
    )
    repo.close()

    conn = raw_connection(tmp_path)
    row = conn.execute(
        "SELECT review_due_at, spacing_stage FROM review_queue WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    assert row["spacing_stage"] == 1
    assert datetime.fromisoformat(row["review_due_at"]) == NOW + timedelta(hours=1, days=1)


def test_interview_ready_requires_three_spaced_successes_not_just_high_score(tmp_path: Path):
    repo = make_repo(tmp_path)

    # Five same-day passes with correct pattern prediction (+18 each) reach a
    # raw score of 90+, but the same-day guard keeps spacing_stage at 1 (a
    # single spaced review), so the label must stay capped below
    # interview_ready until reviews actually span different days.
    for hour in range(5):
        repo.record_exercise_submission(
            exercise_id="exercise.seed.count-tags-001",
            content_version=1,
            concepts=["python.dictionaries"],
            status="passed",
            session_id="session-1",
            now=NOW + timedelta(hours=hour),
            predicted_pattern="python.dictionaries",
        )
    repo.close()

    conn = raw_connection(tmp_path)
    row = conn.execute(
        "SELECT mastery, label FROM concept_mastery WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    assert row["mastery"] >= 90
    assert row["label"] == MasteryLabel.REVIEW_READY.value


def test_failed_submission_penalizes_and_resets_review(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW,
    )
    later = NOW + timedelta(days=1)
    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="failed_tests",
        session_id="session-1",
        now=later,
    )
    repo.close()

    conn = raw_connection(tmp_path)
    mastery_row = conn.execute(
        "SELECT mastery FROM concept_mastery WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    assert mastery_row["mastery"] == 6  # 10 (pass) - 4 (failed validation)

    review_row = conn.execute(
        "SELECT review_due_at, spacing_stage FROM review_queue WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    assert review_row["spacing_stage"] == 0
    assert datetime.fromisoformat(review_row["review_due_at"]) == later


def test_hints_and_low_confidence_cap_score_gain(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW,
        predicted_pattern="python.dictionaries",
        confidence=2,
    )
    repo.close()

    conn = raw_connection(tmp_path)
    row = conn.execute(
        "SELECT mastery FROM concept_mastery WHERE concept_id = ?",
        ("python.dictionaries",),
    ).fetchone()
    # 10 (pass) + 8 (correct pattern) = 18, capped at +6 because confidence < 3.
    assert row["mastery"] == 6


def test_exercise_summary_tracks_best_status_and_attempts(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="failed_tests",
        session_id="session-1",
        now=NOW,
    )
    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW + timedelta(hours=1),
    )
    repo.close()

    conn = raw_connection(tmp_path)
    row = conn.execute(
        "SELECT best_status, attempts FROM exercise_summary WHERE exercise_id = ?",
        ("exercise.seed.count-tags-001",),
    ).fetchone()
    assert row["best_status"] == "passed"
    assert row["attempts"] == 2


def test_daily_activity_tracks_time_and_completed_count(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW,
        time_minutes=12,
    )
    repo.close()

    conn = raw_connection(tmp_path)
    row = conn.execute(
        "SELECT time_minutes, completed_count FROM daily_activity WHERE day = ?",
        (NOW.date().isoformat(),),
    ).fetchone()
    assert row["time_minutes"] == 12
    assert row["completed_count"] == 1


def test_recompute_rollups_rebuilds_deterministically_from_events(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW,
    )
    repo.record_exercise_submission(
        exercise_id="exercise.seed.sum-delivery-minutes-001",
        content_version=1,
        concepts=["python.loops"],
        status="passed",
        session_id="session-1",
        now=NOW + timedelta(minutes=5),
    )

    before = raw_connection(tmp_path)
    before_rows = sorted(
        (dict(row) for row in before.execute("SELECT * FROM concept_mastery").fetchall()),
        key=lambda row: row["concept_id"],
    )
    before.close()

    repo.recompute_rollups()
    repo.close()

    after = raw_connection(tmp_path)
    after_rows = sorted(
        (dict(row) for row in after.execute("SELECT * FROM concept_mastery").fetchall()),
        key=lambda row: row["concept_id"],
    )
    assert before_rows == after_rows
    assert len(after_rows) == 2


def test_summary_shape_matches_contract(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW,
        time_minutes=10,
    )
    repo.record_exercise_submission(
        exercise_id="exercise.seed.sum-delivery-minutes-001",
        content_version=1,
        concepts=["python.loops"],
        status="failed_tests",
        session_id="session-1",
        now=NOW,
        time_minutes=5,
    )

    summary = repo.summary(now=NOW)
    repo.close()

    assert summary.streak_days == 1
    assert summary.total_time_minutes == 15
    concept_ids = {concept.id for concept in summary.concepts}
    assert concept_ids == {"python.dictionaries", "python.loops"}
    assert "exercise.seed.sum-delivery-minutes-001" in summary.recent_mistakes
    assert isinstance(summary.next_recommended_action, str)
    assert summary.next_recommended_action != ""


def test_summary_streak_breaks_on_missing_day(tmp_path: Path):
    repo = make_repo(tmp_path)

    repo.record_exercise_submission(
        exercise_id="exercise.seed.count-tags-001",
        content_version=1,
        concepts=["python.dictionaries"],
        status="passed",
        session_id="session-1",
        now=NOW - timedelta(days=5),
    )

    summary = repo.summary(now=NOW)
    repo.close()

    assert summary.streak_days == 0
