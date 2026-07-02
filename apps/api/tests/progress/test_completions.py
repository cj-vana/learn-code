from __future__ import annotations

from datetime import datetime, timezone

from learn_code_api.progress.db import ProgressRepository
from learn_code_api.progress.events import EventType, ProgressEvent, new_event_id

NOW = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)


def make_repo(tmp_path) -> ProgressRepository:
    return ProgressRepository(tmp_path / "progress.sqlite3", now=NOW)


def quiz_event(question_id: str, *, correct: bool = True) -> ProgressEvent:
    return ProgressEvent(
        id=new_event_id(),
        type=EventType.QUIZ_ANSWERED,
        created_at=NOW,
        content_id="quiz.sample.q1",
        content_version=1,
        language="python",
        session_id="s",
        payload={"question_id": question_id, "correct": correct, "concepts": ["python.lists"]},
    )


def test_lesson_completion_recorded_and_readable(tmp_path):
    repo = make_repo(tmp_path)
    repo.record_lesson_completed(
        lesson_id="lesson.sample.l1", content_version=1, session_id="s", now=NOW
    )
    assert repo.completed_lesson_ids() == {"lesson.sample.l1"}


def test_lesson_completion_grants_no_mastery(tmp_path):
    repo = make_repo(tmp_path)
    repo.record_lesson_completed(
        lesson_id="lesson.sample.l1", content_version=1, session_id="s", now=NOW
    )
    assert repo.concept_mastery_map() == {}


def test_quiz_answer_log_tracks_question_coverage(tmp_path):
    repo = make_repo(tmp_path)
    repo.append_event(quiz_event("q1"))
    repo.append_event(quiz_event("q2", correct=False))
    assert repo.quiz_question_coverage() == {"quiz.sample.q1": {"q1", "q2"}}


def test_completions_survive_recompute(tmp_path):
    repo = make_repo(tmp_path)
    repo.record_lesson_completed(
        lesson_id="lesson.sample.l1", content_version=1, session_id="s", now=NOW
    )
    repo.append_event(quiz_event("q1"))
    repo.recompute_rollups()
    assert repo.completed_lesson_ids() == {"lesson.sample.l1"}
    assert repo.quiz_question_coverage() == {"quiz.sample.q1": {"q1"}}
