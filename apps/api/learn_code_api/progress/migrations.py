from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Migration:
    version: int
    description: str
    sql: str


# Table shapes are taken verbatim from the plan (spec: Progress storage contract).
MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        description="create core progress tables",
        sql="""
        CREATE TABLE IF NOT EXISTS progress_events (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            content_id TEXT,
            content_version INTEGER,
            language TEXT NOT NULL,
            session_id TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            sequence INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS concept_mastery (
            concept_id TEXT PRIMARY KEY,
            mastery INTEGER NOT NULL,
            label TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS daily_activity (
            day TEXT PRIMARY KEY,
            time_minutes INTEGER NOT NULL DEFAULT 0,
            completed_count INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS review_queue (
            concept_id TEXT PRIMARY KEY,
            review_due_at TEXT NOT NULL,
            spacing_stage INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS exercise_summary (
            exercise_id TEXT PRIMARY KEY,
            best_status TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );
        """,
    ),
    Migration(
        version=2,
        description="add lesson completion and quiz answer coverage rollups",
        sql="""
        CREATE TABLE IF NOT EXISTS lesson_completions (
            lesson_id TEXT PRIMARY KEY,
            completed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS quiz_answer_log (
            quiz_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            correct INTEGER NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (quiz_id, question_id)
        );
        """,
    ),
    Migration(
        version=3,
        description="add single-row active path enrollment rollup",
        sql="""
        CREATE TABLE IF NOT EXISTS active_path (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            path_id TEXT NOT NULL,
            enrolled_at TEXT NOT NULL
        );
        """,
    ),
)


def ensure_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    conn.commit()


def applied_versions(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def apply_migrations(conn: sqlite3.Connection, *, now: datetime) -> None:
    """Apply any pending migrations, in version order.

    Idempotent: already-applied versions are skipped, and each migration's DDL
    uses CREATE TABLE IF NOT EXISTS so re-running is always safe.
    """
    ensure_schema_migrations_table(conn)
    applied = applied_versions(conn)
    for migration in sorted(MIGRATIONS, key=lambda item: item.version):
        if migration.version in applied:
            continue
        conn.executescript(migration.sql)
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            (migration.version, now.isoformat()),
        )
        conn.commit()
