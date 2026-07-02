from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from learn_code_api.progress import events as events_mod
from learn_code_api.progress import migrations as migrations_mod
from learn_code_api.progress import rollups as rollups_mod
from learn_code_api.progress.events import EventType, ProgressEvent
from learn_code_api.progress.rollups import ProgressSummary


class ProgressRepository:
    """SQLite-backed store for progress events and derived rollups.

    The API process is the only SQLite writer (spec rule). Migrations run
    automatically on construction.
    """

    def __init__(self, db_path: str | Path, *, now: datetime):
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute("PRAGMA foreign_keys = ON")
        migrations_mod.apply_migrations(self._conn, now=now)

    def close(self) -> None:
        self._conn.close()

    def append_event(self, event: ProgressEvent) -> ProgressEvent:
        """Store an event and fold it into the rollups it affects.

        `recompute_rollups` replays events ordered by `created_at ASC,
        sequence ASC` (spec rule), but this incremental fold applies each
        newly-appended event in insertion order. If the new event's
        `created_at` is earlier than the max `created_at` already stored,
        incremental folding would apply events out of chronological order
        and silently diverge from a full replay -- so fall back to a full
        `recompute_rollups()` in that case instead of the incremental fold.
        """
        max_created_at_before = events_mod.max_created_at(self._conn)
        out_of_order = max_created_at_before is not None and event.created_at < max_created_at_before

        sequence = events_mod.next_sequence(self._conn)
        events_mod.insert_event(self._conn, event, sequence)
        self._conn.commit()

        if out_of_order:
            rollups_mod.recompute_rollups(self._conn)
        elif event.type == EventType.EXERCISE_SUBMITTED:
            rollups_mod.apply_exercise_submission(self._conn, event)
            self._conn.commit()
        elif event.type == EventType.QUIZ_ANSWERED:
            rollups_mod.apply_quiz_answered(self._conn, event)
            self._conn.commit()
        elif event.type == EventType.PATTERN_PREDICTED:
            rollups_mod.apply_pattern_predicted(self._conn, event)
            self._conn.commit()
        elif event.type == EventType.LESSON_COMPLETED:
            rollups_mod.apply_lesson_completed(self._conn, event)
            self._conn.commit()
        elif event.type == EventType.PATH_ENROLLED:
            rollups_mod.apply_path_enrolled(self._conn, event)
            self._conn.commit()
        elif event.type == EventType.PATH_UNENROLLED:
            rollups_mod.apply_path_unenrolled(self._conn, event)
            self._conn.commit()

        return event

    def record_exercise_submission(
        self,
        *,
        exercise_id: str,
        content_version: int,
        concepts: list[str],
        status: str,
        session_id: str,
        now: datetime,
        hints_used: int = 0,
        confidence: int | None = None,
        predicted_pattern: str | None = None,
        time_minutes: int = 0,
        language: str = "python",
    ) -> ProgressEvent:
        """Convenience wrapper that builds and appends an ExerciseSubmitted event."""
        event = ProgressEvent(
            id=events_mod.new_event_id(),
            type=EventType.EXERCISE_SUBMITTED,
            created_at=now,
            content_id=exercise_id,
            content_version=content_version,
            language=language,
            session_id=session_id,
            payload={
                "status": status,
                "concepts": concepts,
                "hints_used": hints_used,
                "confidence": confidence,
                "predicted_pattern": predicted_pattern,
                "time_minutes": time_minutes,
            },
        )
        return self.append_event(event)

    def record_lesson_completed(
        self,
        *,
        lesson_id: str,
        content_version: int,
        session_id: str,
        now: datetime,
        language: str = "python",
    ) -> ProgressEvent:
        """Convenience wrapper that builds and appends a LessonCompleted event."""
        event = ProgressEvent(
            id=events_mod.new_event_id(),
            type=EventType.LESSON_COMPLETED,
            created_at=now,
            content_id=lesson_id,
            content_version=content_version,
            language=language,
            session_id=session_id,
            payload={},
        )
        return self.append_event(event)

    def record_path_enrolled(
        self, *, path_id: str, session_id: str, now: datetime, language: str = "python"
    ) -> ProgressEvent:
        event = ProgressEvent(
            id=events_mod.new_event_id(),
            type=EventType.PATH_ENROLLED,
            created_at=now,
            content_id=path_id,
            language=language,
            session_id=session_id,
            payload={},
        )
        return self.append_event(event)

    def record_path_unenrolled(
        self, *, path_id: str, session_id: str, now: datetime, language: str = "python"
    ) -> ProgressEvent:
        event = ProgressEvent(
            id=events_mod.new_event_id(),
            type=EventType.PATH_UNENROLLED,
            created_at=now,
            content_id=path_id,
            language=language,
            session_id=session_id,
            payload={},
        )
        return self.append_event(event)

    def active_path_id(self) -> str | None:
        """Read-only: the currently enrolled path id, if any."""
        return rollups_mod.read_active_path_id(self._conn)

    def passed_exercise_ids(self) -> set[str]:
        """Read-only: exercise ids whose best status is a validation pass."""
        return rollups_mod.read_passed_exercise_ids(self._conn)

    def completed_lesson_ids(self) -> set[str]:
        """Read-only: ids of lessons the learner has completed."""
        return rollups_mod.read_completed_lesson_ids(self._conn)

    def quiz_question_coverage(self) -> dict[str, set[str]]:
        """Read-only: per-quiz set of question ids answered at least once."""
        return rollups_mod.read_quiz_question_coverage(self._conn)

    def recompute_rollups(self) -> None:
        """Rebuild all rollup tables from the stored event log."""
        rollups_mod.recompute_rollups(self._conn)

    def summary(self, *, now: datetime) -> ProgressSummary:
        return rollups_mod.build_summary(self._conn, now=now)

    def concept_mastery_map(self) -> dict[str, int]:
        """Read-only: current mastery score per concept."""
        return rollups_mod.read_concept_mastery(self._conn)

    def review_due_map(self) -> dict[str, datetime]:
        """Read-only: current review due timestamp per concept."""
        return rollups_mod.read_review_due(self._conn)

    def concept_snapshot(self) -> dict[str, rollups_mod.ConceptSnapshotRow]:
        """Read-only per-concept planner state built from rollups + events."""
        return rollups_mod.read_concept_snapshot(self._conn)
