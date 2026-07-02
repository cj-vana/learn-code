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
        ],
    )
    assert result.exit_code == 0
    assert "mastery: 40 -> 55" in result.stdout
    assert "Try count-tags again tomorrow" in result.stdout
    body = submit_route.calls.last.request.content
    assert b'"content_version":4' in body.replace(b" ", b"")
    assert b"patterns.hash_map_counting" in body


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


@respx.mock
def test_quiz_posts_answer(runner, api_base):
    route = respx.post(f"{api_base}/quizzes/answer").mock(
        return_value=httpx.Response(
            200,
            json={
                "question_id": "q1",
                "correct": True,
                "explanation": "Yes.",
                "concepts_changed": ["python.loops"],
                "next_review_due_at": "2026-07-05T00:00:00Z",
            },
        )
    )
    result = runner.invoke(
        app, ["quiz", "--question-id", "q1", "--concept", "python.loops", "--correct"]
    )
    assert result.exit_code == 0
    assert "q1: correct" in result.stdout
    body = route.calls.last.request.content.replace(b" ", b"")
    assert b'"concepts":["python.loops"]' in body
    assert b'"correct":true' in body


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
