from __future__ import annotations

import httpx
import respx

from learn_code_cli.main import app


def _write(tmp_path, name, text="def solve():\n    return 1\n"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


@respx.mock
def test_next_lists_plan(runner, api_base):
    respx.get(f"{api_base}/plan").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "p1",
                    "kind": "exercise",
                    "content_id": "exercise.seed.count-tags-001",
                    "title": "Count inventory tags",
                    "concepts": ["python.dictionaries"],
                    "priority": 0.91,
                    "estimated_time_minutes": 12,
                    "rationale": {
                        "reason": "Weakest concept",
                        "because": ["low mastery"],
                        "alternatives": [],
                    },
                }
            ],
        )
    )
    result = runner.invoke(app, ["next"])
    assert result.exit_code == 0
    assert "Count inventory tags" in result.stdout
    assert "python.dictionaries" in result.stdout
    assert "Weakest concept" in result.stdout


@respx.mock
def test_run_posts_source_and_shows_summary(runner, api_base, tmp_path):
    route = respx.post(f"{api_base}/exercises/run").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "passed",
                "passed": 3,
                "failed": 0,
                "stdout": "",
                "stderr": "",
                "duration_ms": 8,
                "test_summary": [],
            },
        )
    )
    solution = _write(tmp_path, "sol.py")
    result = runner.invoke(app, ["run", "exercise.seed.count-tags-001", str(solution)])
    assert result.exit_code == 0
    assert "passed: 3 passed, 0 failed" in result.stdout
    sent = route.calls.last.request
    body = httpx.Request("POST", "x", content=sent.content).content
    assert b"exercise.seed.count-tags-001" in body
    assert b"def solve" in body


@respx.mock
def test_submit_fetches_version_then_submits(runner, api_base, tmp_path):
    respx.get(f"{api_base}/content/exercise.seed.count-tags-001").mock(
        return_value=httpx.Response(200, json={"version": 4})
    )
    submit_route = respx.post(f"{api_base}/exercises/submit").mock(
        return_value=httpx.Response(
            200,
            json={
                "submission_id": "s1",
                "run": {
                    "status": "passed",
                    "passed": 5,
                    "failed": 0,
                    "stdout": "",
                    "stderr": "",
                    "duration_ms": 10,
                    "test_summary": [],
                },
                "progress_delta": {
                    "concepts_changed": ["python.dictionaries"],
                    "mastery_before": 40,
                    "mastery_after": 55,
                    "review_due_at": "2026-07-05T00:00:00Z",
                },
                "next_actions": ["Try count-tags again tomorrow"],
            },
        )
    )
    solution = _write(tmp_path, "sol.py")
    result = runner.invoke(
        app,
        [
            "submit",
            "exercise.seed.count-tags-001",
            str(solution),
            "--predicted-pattern",
            "patterns.hash_map_counting",
            "--confidence",
            "4",
            "--hints-used",
            "2",
        ],
    )
    assert result.exit_code == 0
    assert "mastery: 40 -> 55" in result.stdout
    assert "Try count-tags again tomorrow" in result.stdout
    body = submit_route.calls.last.request.content
    assert b'"content_version":4' in body.replace(b" ", b"")
    assert b"patterns.hash_map_counting" in body
    # Hints revealed before submitting must reach the API (they cost mastery).
    assert b'"hints_used":2' in body.replace(b" ", b"")


def test_run_rejects_non_utf8_file(runner, tmp_path):
    # A binary/non-UTF-8 solution file must fail with a friendly message, not a
    # raw UnicodeDecodeError traceback.
    bad = tmp_path / "bad.py"
    bad.write_bytes(b"\xff\xfe\x00 def solve(): pass")
    result = runner.invoke(app, ["run", "exercise.seed.count-tags-001", str(bad)])
    assert result.exit_code == 1
    assert "Can't read" in result.stdout


@respx.mock
def test_playground_runs_file_with_stdin(runner, api_base, tmp_path):
    route = respx.post(f"{api_base}/runs").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "passed",
                "passed": 0,
                "failed": 0,
                "stdout": "hi",
                "stderr": "",
                "duration_ms": 3,
                "test_summary": [],
            },
        )
    )
    scratch = _write(tmp_path, "scratch.py", "print(input())\n")
    result = runner.invoke(app, ["playground", str(scratch), "--stdin", "hi"])
    assert result.exit_code == 0
    body = route.calls.last.request.content.replace(b" ", b"")
    assert b'"stdin":"hi"' in body


QUIZ_DETAIL = {
    "id": "quiz.t.1",
    "kind": "quiz",
    "title": "Loop check",
    "quiz_type": "mixed_review",
    "concepts": ["python.loops"],
    "questions": [
        {
            "id": "q1",
            "prompt": "What repeats the body?",
            "choices": ["a loop", "a dict"],
            "concepts": ["python.loops"],
        }
    ],
}

LESSON_DETAIL = {
    "id": "lesson.t.1",
    "kind": "lesson",
    "title": "Intro to Loops",
    "difficulty": "easy",
    "estimated_time_minutes": 8,
    "concepts": ["python.loops"],
    "body_markdown": "Loops repeat work until a condition ends them.",
    "checkpoints": [
        {"question": "What repeats?", "answer": "The body", "explanation": "Each pass runs the body."}
    ],
}


@respx.mock
def test_quiz_grades_answers_via_api(runner, api_base):
    respx.get(f"{api_base}/content/quiz.t.1").mock(
        return_value=httpx.Response(200, json=QUIZ_DETAIL)
    )
    route = respx.post(f"{api_base}/quizzes/answer").mock(
        return_value=httpx.Response(
            200,
            json={
                "question_id": "q1",
                "correct": True,
                "explanation": "Loops repeat the body.",
                "concepts_changed": ["python.loops"],
                "next_review_due_at": "2026-07-05T00:00:00Z",
            },
        )
    )
    result = runner.invoke(app, ["quiz", "quiz.t.1"], input="1\n")
    assert result.exit_code == 0
    assert "Loops repeat the body." in result.stdout
    assert "Score: 1/1" in result.stdout
    body = route.calls.last.request.content.replace(b" ", b"")
    assert b'"quiz_id":"quiz.t.1"' in body
    assert b'"question_id":"q1"' in body
    assert b'"choice":"aloop"' in body


@respx.mock
def test_quiz_rejects_non_quiz_content(runner, api_base):
    respx.get(f"{api_base}/content/lesson.t.1").mock(
        return_value=httpx.Response(200, json=LESSON_DETAIL)
    )
    result = runner.invoke(app, ["quiz", "lesson.t.1"])
    assert result.exit_code == 1
    assert "not a quiz" in result.stdout


@respx.mock
def test_lesson_prints_body_and_checkpoints(runner, api_base):
    respx.get(f"{api_base}/content/lesson.t.1").mock(
        return_value=httpx.Response(200, json=LESSON_DETAIL)
    )
    result = runner.invoke(app, ["lesson", "lesson.t.1"])
    assert result.exit_code == 0
    assert "Loops repeat work until a condition ends them." in result.stdout
    assert "What repeats?" in result.stdout


@respx.mock
def test_progress_renders_summary(runner, api_base):
    respx.get(f"{api_base}/progress").mock(
        return_value=httpx.Response(
            200,
            json={
                "streak_days": 3,
                "total_time_minutes": 120,
                "concepts": [
                    {
                        "id": "python.loops",
                        "mastery": 42,
                        "label": "learning",
                        "review_due_at": None,
                    }
                ],
                "recent_mistakes": ["off-by-one"],
                "next_recommended_action": "Start a new exercise",
            },
        )
    )
    result = runner.invoke(app, ["progress"])
    assert result.exit_code == 0
    assert "streak: 3 days" in result.stdout
    assert "python.loops: 42 (learning)" in result.stdout
    assert "Start a new exercise" in result.stdout


@respx.mock
def test_review_shows_ollama_summary(runner, api_base, tmp_path):
    respx.post(f"{api_base}/reviews").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "available",
                "summary": "Clean single-pass counter.",
                "correctness_notes": ["Handles empty list."],
                "readability_notes": [],
                "python_simplifications": ["Use collections.Counter."],
                "big_o_notes": "O(n) time.",
                "next_improvement": "Add a docstring.",
                "encouragement": "Nice work.",
                "solution_disclosed": False,
            },
        )
    )
    solution = _write(tmp_path, "sol.py")
    result = runner.invoke(app, ["review", "exercise.seed.count-tags-001", str(solution)])
    assert result.exit_code == 0
    assert "Clean single-pass counter." in result.stdout
    assert "collections.Counter" in result.stdout


@respx.mock
def test_review_unavailable_is_rendered(runner, api_base, tmp_path):
    respx.post(f"{api_base}/reviews").mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "unavailable",
                "summary": "Ollama is not reachable. Tests still decide pass/fail.",
                "correctness_notes": [],
                "readability_notes": [],
                "python_simplifications": [],
                "big_o_notes": None,
                "next_improvement": None,
                "encouragement": None,
                "solution_disclosed": False,
            },
        )
    )
    solution = _write(tmp_path, "sol.py")
    result = runner.invoke(app, ["review", "exercise.seed.count-tags-001", str(solution)])
    assert result.exit_code == 0
    assert "unavailable" in result.stdout
    assert "Tests still decide pass/fail." in result.stdout


@respx.mock
def test_content_not_found_is_friendly(runner, api_base, tmp_path):
    respx.get(f"{api_base}/content/missing").mock(
        return_value=httpx.Response(
            404,
            json={"error": {"code": "content_not_found", "message": "unknown", "details": {}}},
        )
    )
    solution = _write(tmp_path, "sol.py")
    result = runner.invoke(app, ["submit", "missing", str(solution)])
    assert result.exit_code == 1
    assert "No such exercise." in result.stdout


@respx.mock
def test_runner_unavailable_is_friendly(runner, api_base, tmp_path):
    respx.post(f"{api_base}/exercises/run").mock(
        return_value=httpx.Response(
            503,
            json={
                "error": {
                    "code": "runner_unavailable",
                    "message": "runner-broker connection refused",
                    "details": {},
                }
            },
        )
    )
    solution = _write(tmp_path, "sol.py")
    result = runner.invoke(app, ["run", "exercise.seed.count-tags-001", str(solution)])
    assert result.exit_code == 1
    assert "runner isn't available" in result.stdout


def test_missing_solution_file_is_friendly(runner, tmp_path):
    result = runner.invoke(app, ["run", "ex", str(tmp_path / "nope.py")])
    assert result.exit_code == 1
    assert "Can't read" in result.stdout


PATH_SUMMARY = {
    "id": "path.skill.python_foundations",
    "path_type": "skill",
    "title": "Python Foundations",
    "slug": "python-foundations",
    "description": "The ground floor.",
    "outcomes": ["Use variables and conditionals"],
    "estimated_hours": 9,
    "units": 2,
    "items": 56,
    "enrolled": True,
    "percent_complete": 25,
}

PATH_DETAIL = {
    **{k: v for k, v in PATH_SUMMARY.items() if k not in {"units", "items"}},
    "units": [
        {
            "id": "unit.python_refresh",
            "title": "Python Refresh",
            "description": "Start here.",
            "percent_complete": 50,
            "items": [
                {
                    "id": "lesson.library.python_refresh.a01",
                    "kind": "lesson",
                    "title": "Variables, gently",
                    "estimated_time_minutes": 8,
                    "status": "complete",
                },
                {
                    "id": "quiz.library.python_refresh.a01",
                    "kind": "quiz",
                    "title": "Refresh check",
                    "estimated_time_minutes": 5,
                    "status": "todo",
                },
            ],
        }
    ],
    "next_item_id": "quiz.library.python_refresh.a01",
}


@respx.mock
def test_paths_lists_progress(runner, api_base):
    respx.get(f"{api_base}/paths").mock(
        return_value=httpx.Response(200, json=[PATH_SUMMARY])
    )
    result = runner.invoke(app, ["paths"])
    assert result.exit_code == 0
    assert "Python Foundations" in result.stdout
    assert "25%" in result.stdout
    assert "enrolled" in result.stdout


@respx.mock
def test_path_shows_syllabus(runner, api_base):
    respx.get(f"{api_base}/paths/path.skill.python_foundations").mock(
        return_value=httpx.Response(200, json=PATH_DETAIL)
    )
    result = runner.invoke(app, ["path", "path.skill.python_foundations"])
    assert result.exit_code == 0
    assert "Python Refresh" in result.stdout
    assert "Variables, gently" in result.stdout
    assert "next: quiz.library.python_refresh.a01" in result.stdout


@respx.mock
def test_enroll_and_unenroll(runner, api_base):
    respx.post(f"{api_base}/paths/path.skill.python_foundations/enroll").mock(
        return_value=httpx.Response(
            200, json={"path_id": "path.skill.python_foundations", "enrolled": True}
        )
    )
    respx.post(f"{api_base}/paths/path.skill.python_foundations/unenroll").mock(
        return_value=httpx.Response(
            200, json={"path_id": "path.skill.python_foundations", "enrolled": False}
        )
    )
    result = runner.invoke(app, ["enroll", "path.skill.python_foundations"])
    assert result.exit_code == 0
    assert "Enrolled" in result.stdout

    result = runner.invoke(app, ["unenroll", "path.skill.python_foundations"])
    assert result.exit_code == 0
    assert "Unenrolled" in result.stdout
