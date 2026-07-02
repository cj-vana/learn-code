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
        """Store an event and fold it into the rollups it affects."""
        sequence = events_mod.next_sequence(self._conn)
        events_mod.insert_event(self._conn, event, sequence)
        self._conn.commit()

        if event.type == EventType.EXERCISE_SUBMITTED:
            rollups_mod.apply_exercise_submission(self._conn, event)
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

    def recompute_rollups(self) -> None:
        """Rebuild all rollup tables from the stored event log."""
        rollups_mod.recompute_rollups(self._conn)

    def summary(self, *, now: datetime) -> ProgressSummary:
        return rollups_mod.build_summary(self._conn, now=now)
