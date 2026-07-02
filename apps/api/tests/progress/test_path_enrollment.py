from __future__ import annotations

from datetime import datetime, timezone

from learn_code_api.progress.db import ProgressRepository

NOW = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)


def make_repo(tmp_path) -> ProgressRepository:
    return ProgressRepository(tmp_path / "progress.sqlite3", now=NOW)


def test_no_active_path_by_default(tmp_path):
    repo = make_repo(tmp_path)
    assert repo.active_path_id() is None


def test_enroll_sets_active_path(tmp_path):
    repo = make_repo(tmp_path)
    repo.record_path_enrolled(path_id="path.skill.a", session_id="s", now=NOW)
    assert repo.active_path_id() == "path.skill.a"


def test_enrolling_again_supersedes(tmp_path):
    repo = make_repo(tmp_path)
    repo.record_path_enrolled(path_id="path.skill.a", session_id="s", now=NOW)
    repo.record_path_enrolled(path_id="path.career.b", session_id="s", now=NOW)
    assert repo.active_path_id() == "path.career.b"


def test_unenroll_clears_active_path(tmp_path):
    repo = make_repo(tmp_path)
    repo.record_path_enrolled(path_id="path.skill.a", session_id="s", now=NOW)
    repo.record_path_unenrolled(path_id="path.skill.a", session_id="s", now=NOW)
    assert repo.active_path_id() is None


def test_enrollment_survives_recompute(tmp_path):
    repo = make_repo(tmp_path)
    repo.record_path_enrolled(path_id="path.skill.a", session_id="s", now=NOW)
    repo.recompute_rollups()
    assert repo.active_path_id() == "path.skill.a"


def test_passed_exercise_ids_reads_summary(tmp_path):
    repo = make_repo(tmp_path)
    repo.record_exercise_submission(
        exercise_id="exercise.t.1",
        content_version=1,
        concepts=["python.lists"],
        status="passed",
        session_id="s",
        now=NOW,
    )
    repo.record_exercise_submission(
        exercise_id="exercise.t.2",
        content_version=1,
        concepts=["python.lists"],
        status="failed_tests",
        session_id="s",
        now=NOW,
    )
    assert repo.passed_exercise_ids() == {"exercise.t.1"}
