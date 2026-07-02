from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class EventType(StrEnum):
    """Required progress event types (spec: Progress storage contract)."""

    LESSON_COMPLETED = "LessonCompleted"
    HINT_VIEWED = "HintViewed"
    PATTERN_PREDICTED = "PatternPredicted"
    QUIZ_ANSWERED = "QuizAnswered"
    EXERCISE_SUBMITTED = "ExerciseSubmitted"
    PLAYGROUND_RUN_COMPLETED = "PlaygroundRunCompleted"
    REVIEW_COMPLETED = "ReviewCompleted"
    PLAN_ITEM_SKIPPED = "PlanItemSkipped"
    OLLAMA_REVIEW_REQUESTED = "OllamaReviewRequested"


class ProgressEvent(BaseModel):
    """Append-only progress event envelope (spec: Progress storage contract)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: EventType
    created_at: datetime
    content_id: str | None = None
    content_version: int | None = None
    language: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


def new_event_id() -> str:
    return str(uuid4())


def next_sequence(conn: sqlite3.Connection) -> int:
    """Next monotonic insertion sequence. API is the only writer, so a
    read-then-write within one connection is safe (no concurrent writers)."""
    row = conn.execute("SELECT COALESCE(MAX(sequence), 0) FROM progress_events").fetchone()
    return int(row[0]) + 1


def insert_event(conn: sqlite3.Connection, event: ProgressEvent, sequence: int) -> None:
    conn.execute(
        """
        INSERT INTO progress_events (
            id, type, created_at, content_id, content_version,
            language, session_id, payload_json, sequence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.id,
            event.type.value,
            event.created_at.isoformat(),
            event.content_id,
            event.content_version,
            event.language,
            event.session_id,
            json.dumps(event.payload, sort_keys=True),
            sequence,
        ),
    )


def fetch_events_ordered(conn: sqlite3.Connection) -> list[ProgressEvent]:
    """All events ordered by created_at then insertion sequence (spec rule)."""
    rows = conn.execute(
        """
        SELECT id, type, created_at, content_id, content_version,
               language, session_id, payload_json, sequence
        FROM progress_events
        ORDER BY created_at ASC, sequence ASC
        """
    ).fetchall()
    return [_row_to_event(row) for row in rows]


def _row_to_event(row: tuple[Any, ...]) -> ProgressEvent:
    (
        id_,
        type_,
        created_at,
        content_id,
        content_version,
        language,
        session_id,
        payload_json,
        _sequence,
    ) = row
    return ProgressEvent(
        id=id_,
        type=EventType(type_),
        created_at=datetime.fromisoformat(created_at),
        content_id=content_id,
        content_version=content_version,
        language=language,
        session_id=session_id,
        payload=json.loads(payload_json),
    )
