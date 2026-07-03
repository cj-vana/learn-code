"""Contract tests for the FastAPI surface (Task 5).

The runner-broker and Ollama clients are injected through the app factory so
these tests never touch a live broker or a running Ollama. Content is the real
published seed catalog and progress is a temporary SQLite database per test.
"""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from learn_code_api.content.loader import load_catalog
from learn_code_api.dependencies import AppDependencies
from learn_code_api.main import create_app
from learn_code_api.ollama.client import (
    UNAVAILABLE_REVIEW,
    HttpOllamaClient,
    OllamaReview,
    OllamaSettings,
    ReviewContext,
)
from learn_code_api.runner_broker.client import (
    HttpRunnerBrokerClient,
    RunMode,
    RunnerRequest,
    RunnerResponse,
    RunnerUnavailableError,
    RunStatus,
    TestProfile,
    TestSummaryEntry,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_ROOT = REPO_ROOT / "content" / "python"
CATALOG = load_catalog(CONTENT_ROOT)

NOW = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)

COUNT_TAGS_ID = "exercise.seed.count-tags-001"
COUNT_TAGS_CONCEPTS = ["python.dictionaries", "patterns.hash_map_counting"]

LESSON_ID = CATALOG.lessons[0].id
QUIZ = CATALOG.quizzes[0]
QUIZ_ID = QUIZ.id
QUESTION = QUIZ.questions[0]


def passed_response(status: RunStatus = RunStatus.PASSED) -> RunnerResponse:
    return RunnerResponse(
        correlation_id="pending",
        status=status,
        passed=3,
        failed=0,
        stdout="ok",
        stderr="",
        duration_ms=7,
        test_summary=[TestSummaryEntry(name="mixed", visibility="validation", passed=True)],
    )


class FakeRunner:
    """Records requests and returns a canned response echoing the correlation id."""

    def __init__(self, response: RunnerResponse | None = None):
        self.response = response or passed_response()
        self.requests: list[RunnerRequest] = []

    def run(self, request: RunnerRequest) -> RunnerResponse:
        self.requests.append(request)
        return self.response.model_copy(update={"correlation_id": request.correlation_id})


class UnavailableRunner:
    def __init__(self) -> None:
        self.requests: list[RunnerRequest] = []

    def run(self, request: RunnerRequest) -> RunnerResponse:
        self.requests.append(request)
        raise RunnerUnavailableError("runner-broker connection refused")


class FakeOllama:
    def __init__(self, review: OllamaReview):
        self.review_value = review
        self.contexts: list[ReviewContext] = []

    def review(self, context: ReviewContext) -> OllamaReview:
        self.contexts.append(context)
        return self.review_value


def make_client(
    tmp_path: Path,
    *,
    runner=None,
    ollama=None,
    now: datetime = NOW,
    session_id: str = "test-session",
) -> tuple[TestClient, FakeRunner, FakeOllama]:
    runner = runner if runner is not None else FakeRunner()
    ollama = ollama if ollama is not None else FakeOllama(UNAVAILABLE_REVIEW)
    deps = AppDependencies(
        catalog=CATALOG,
        runner_client=runner,
        ollama_client=ollama,
        db_path=tmp_path / "progress.sqlite3",
        session_id=session_id,
        clock=lambda: now,
    )
    return TestClient(create_app(deps)), runner, ollama


def test_health(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_content_list_omits_solution(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get("/api/v1/content")
    assert resp.status_code == 200
    items = resp.json()
    ids = {item["id"] for item in items}
    assert COUNT_TAGS_ID in ids
    for item in items:
        assert "sample_solution" not in item
        assert "solution_sketch" not in item


def test_content_detail_hides_validation_and_solution(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get(f"/api/v1/content/{COUNT_TAGS_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == COUNT_TAGS_ID
    assert body["prompt_markdown"]
    assert body["starter_code"]
    assert body["public_tests"]
    assert "sample_solution" not in body
    assert "solution_sketch" not in body
    assert "validation" not in body
    assert "explanation_markdown" not in body


def test_content_detail_not_found(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get("/api/v1/content/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "content_not_found"


def test_today_plan(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get("/api/v1/plan")
    assert resp.status_code == 200
    items = resp.json()
    assert items
    first = items[0]
    assert set(first) == {
        "id",
        "kind",
        "content_id",
        "title",
        "concepts",
        "priority",
        "estimated_time_minutes",
        "rationale",
    }
    assert set(first["rationale"]) == {"reason", "because", "alternatives"}


def test_progress_summary_empty(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get("/api/v1/progress")
    assert resp.status_code == 200
    body = resp.json()
    assert body["streak_days"] == 0
    assert body["concepts"] == []
    assert body["next_recommended_action"] == "Start a new exercise"


def test_public_run_uses_public_profile(tmp_path):
    client, runner, _ = make_client(tmp_path)
    resp = client.post(
        "/api/v1/exercises/run",
        json={
            "exercise_id": COUNT_TAGS_ID,
            "language": "python",
            "source": "def count_tags(t): ...",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "passed"
    assert body["passed"] == 3
    assert len(runner.requests) == 1
    sent = runner.requests[0]
    assert sent.mode == RunMode.EXERCISE_TESTS
    assert sent.test_profile == TestProfile.PUBLIC
    assert sent.exercise_id == COUNT_TAGS_ID


def test_submit_records_progress(tmp_path):
    client, runner, _ = make_client(tmp_path)
    resp = client.post(
        "/api/v1/exercises/submit",
        json={
            "exercise_id": COUNT_TAGS_ID,
            "content_version": 1,
            "language": "python",
            "source": "def count_tags(tags): ...",
            "predicted_pattern": "patterns.hash_map_counting",
            "confidence": 4,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["submission_id"]
    assert body["run"]["status"] == "passed"
    assert set(body["run"]) == {
        "status",
        "passed",
        "failed",
        "stdout",
        "stderr",
        "duration_ms",
        "test_summary",
    }
    delta = body["progress_delta"]
    assert set(delta["concepts_changed"]) == set(COUNT_TAGS_CONCEPTS)
    assert delta["mastery_after"] > delta["mastery_before"]
    assert delta["review_due_at"]
    assert body["next_actions"]

    # The submit was recorded via the validation profile.
    assert runner.requests[0].test_profile == TestProfile.VALIDATION

    # Progress now reflects the recorded concepts.
    progress = client.get("/api/v1/progress").json()
    recorded = {c["id"]: c["mastery"] for c in progress["concepts"]}
    for concept in COUNT_TAGS_CONCEPTS:
        assert recorded.get(concept, 0) > 0


def test_submit_hints_used_reduces_mastery_gain(tmp_path):
    # Revealing hints before passing costs mastery (spec: -2 per hint, capped
    # at -6). This guards the end-to-end wiring: the score input is inert unless
    # the request carries hints_used all the way to record_exercise_submission.
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    body = {
        "exercise_id": COUNT_TAGS_ID,
        "content_version": 1,
        "language": "python",
        "source": "def count_tags(tags): ...",
        "predicted_pattern": "patterns.hash_map_counting",
        "confidence": 4,
    }
    unhinted_client, _, _ = make_client(tmp_path / "a")
    unhinted = unhinted_client.post(
        "/api/v1/exercises/submit", json={**body, "hints_used": 0}
    ).json()

    hinted_client, _, _ = make_client(tmp_path / "b")
    hinted = hinted_client.post(
        "/api/v1/exercises/submit", json={**body, "hints_used": 3}
    ).json()

    unhinted_after = unhinted["progress_delta"]["mastery_after"]
    hinted_after = hinted["progress_delta"]["mastery_after"]
    assert hinted_after < unhinted_after
    # 3 hints -> min(3*2, 6) == 6 penalty applied to the same passing solution.
    assert unhinted_after - hinted_after == 6


def test_submit_runner_unavailable_does_not_record(tmp_path):
    client, _, _ = make_client(tmp_path, runner=UnavailableRunner())
    resp = client.post(
        "/api/v1/exercises/submit",
        json={
            "exercise_id": COUNT_TAGS_ID,
            "content_version": 1,
            "language": "python",
            "source": "def count_tags(tags): ...",
            "predicted_pattern": None,
            "confidence": None,
        },
    )
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "runner_unavailable"

    progress = client.get("/api/v1/progress").json()
    assert progress["concepts"] == []


def test_playground_run(tmp_path):
    client, runner, _ = make_client(tmp_path)
    resp = client.post(
        "/api/v1/runs",
        json={"language": "python", "source": "print('hi')", "stdin": None},
    )
    assert resp.status_code == 200
    assert runner.requests[0].mode == RunMode.PLAYGROUND
    assert runner.requests[0].test_profile == TestProfile.PLAYGROUND


def test_quiz_answer_grades_correct_choice(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post(
        "/api/v1/quizzes/answer",
        json={
            "quiz_id": QUIZ.id,
            "question_id": QUESTION.id,
            "choice": QUESTION.correct_choice,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["correct"] is True
    assert body["explanation"] == QUESTION.explanation
    assert body["question_id"] == QUESTION.id
    assert body["concepts_changed"]
    assert body["next_review_due_at"]

    progress = client.get("/api/v1/progress").json()
    recorded = {c["id"]: c["mastery"] for c in progress["concepts"]}
    graded_concepts = QUESTION.concepts or QUIZ.concepts
    assert recorded.get(graded_concepts[0], 0) > 0


def test_quiz_answer_grades_wrong_choice(tmp_path):
    client, _, _ = make_client(tmp_path)
    wrong = next(c for c in QUESTION.choices if c != QUESTION.correct_choice)
    resp = client.post(
        "/api/v1/quizzes/answer",
        json={"quiz_id": QUIZ.id, "question_id": QUESTION.id, "choice": wrong},
    )
    assert resp.status_code == 200
    assert resp.json()["correct"] is False


def test_quiz_answer_unknown_question_is_404(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post(
        "/api/v1/quizzes/answer",
        json={"quiz_id": QUIZ.id, "question_id": "nope", "choice": "x"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "content_not_found"


def test_review_unavailable_returns_exact_payload(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post(
        "/api/v1/reviews",
        json={"exercise_id": COUNT_TAGS_ID, "source": "def count_tags(tags): ..."},
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "status": "unavailable",
        "summary": "Ollama is not reachable. Tests still decide pass/fail.",
        "correctness_notes": [],
        "readability_notes": [],
        "python_simplifications": [],
        "big_o_notes": None,
        "next_improvement": None,
        "encouragement": None,
        "solution_disclosed": False,
    }


def test_review_available_returns_model_output(tmp_path):
    review = OllamaReview(
        status="available",
        summary="Clean single-pass counter.",
        correctness_notes=["Handles the empty list."],
        readability_notes=[],
        python_simplifications=["Consider collections.Counter."],
        big_o_notes="O(n) time.",
        next_improvement="Add a docstring.",
        encouragement="Nice work.",
        solution_disclosed=False,
    )
    client, _, ollama = make_client(tmp_path, ollama=FakeOllama(review))
    resp = client.post(
        "/api/v1/reviews",
        json={"exercise_id": COUNT_TAGS_ID, "source": "def count_tags(tags): ..."},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "available"
    assert resp.json()["summary"] == "Clean single-pass counter."
    assert ollama.contexts[0].learner_code == "def count_tags(tags): ..."


def test_validation_error_uses_envelope(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post("/api/v1/exercises/submit", json={"exercise_id": COUNT_TAGS_ID})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_runner_client_maps_connection_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = HttpRunnerBrokerClient(
        base_url="http://runner-broker:8080", transport=httpx.MockTransport(handler)
    )
    request = RunnerRequest(
        correlation_id="c1",
        mode=RunMode.PLAYGROUND,
        language="python",
        source="print('hi')",
        test_profile=TestProfile.PLAYGROUND,
    )
    with pytest.raises(RunnerUnavailableError):
        client.run(request)


def test_ollama_client_unreachable_returns_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client = HttpOllamaClient(
        settings=OllamaSettings(
            enabled="auto",
            host="http://host.docker.internal:11434",
            model="granite-code:8b",
            timeout_seconds=1,
        ),
        transport=httpx.MockTransport(handler),
    )
    context = ReviewContext(
        exercise_prompt="Count tags.",
        concepts=COUNT_TAGS_CONCEPTS,
        expected_pattern="patterns.hash_map_counting",
        learner_code="def count_tags(tags): ...",
        test_result_summary="3/3 public tests passed",
        learner_level="beginner",
        allow_solution_disclosure=False,
    )
    review = client.review(context)
    assert review == UNAVAILABLE_REVIEW


def test_ollama_available_parses_compliant_model_reply():
    # The model is told to reply WITHOUT a `status` field; the client must still
    # surface the review as `available` rather than falling into the error path.
    compliant = {
        "summary": "Clean single-pass counter.",
        "correctness_notes": ["Handles the empty list."],
        "readability_notes": [],
        "python_simplifications": ["Consider collections.Counter."],
        "big_o_notes": "O(n) time.",
        "next_improvement": "Add a docstring.",
        "encouragement": "Nice work.",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": json.dumps(compliant)}})

    client = HttpOllamaClient(
        settings=OllamaSettings(
            enabled="auto",
            host="http://host.docker.internal:11434",
            model="granite-code:8b",
            timeout_seconds=1,
        ),
        transport=httpx.MockTransport(handler),
    )
    context = ReviewContext(
        exercise_prompt="Count tags.",
        concepts=COUNT_TAGS_CONCEPTS,
        expected_pattern="patterns.hash_map_counting",
        learner_code="def count_tags(tags): ...",
        test_result_summary="3/3 public tests passed",
        learner_level="beginner",
        allow_solution_disclosure=False,
    )
    review = client.review(context)
    assert review.status == "available"
    assert review.summary == "Clean single-pass counter."
    assert review.correctness_notes == ["Handles the empty list."]
    assert review.big_o_notes == "O(n) time."


def test_runner_client_maps_nonjson_body_to_unavailable():
    # A 200 with an empty/non-JSON body must surface as runner_unavailable, not
    # a bare 500: response.json() raises a ValueError we must translate.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"", headers={"content-type": "text/plain"})

    client = HttpRunnerBrokerClient(
        base_url="http://runner-broker:8080", transport=httpx.MockTransport(handler)
    )
    request = RunnerRequest(
        correlation_id="c1",
        mode=RunMode.PLAYGROUND,
        language="python",
        source="print('hi')",
        test_profile=TestProfile.PLAYGROUND,
    )
    with pytest.raises(RunnerUnavailableError):
        client.run(request)


def test_runner_client_maps_unknown_status_to_unavailable():
    # The broker contract has statuses (e.g. "cancelled") the API enum omits; a
    # 200 carrying one must not leak an unhandled ValidationError / bare 500.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"correlation_id": "c1", "status": "cancelled"})

    client = HttpRunnerBrokerClient(
        base_url="http://runner-broker:8080", transport=httpx.MockTransport(handler)
    )
    request = RunnerRequest(
        correlation_id="c1",
        mode=RunMode.PLAYGROUND,
        language="python",
        source="print('hi')",
        test_profile=TestProfile.PLAYGROUND,
    )
    with pytest.raises(RunnerUnavailableError):
        client.run(request)


def test_unexpected_error_uses_internal_error_envelope(tmp_path):
    class BoomOllama:
        def review(self, context: ReviewContext) -> OllamaReview:
            raise RuntimeError("unexpected boom")

    deps = AppDependencies(
        catalog=CATALOG,
        runner_client=FakeRunner(),
        ollama_client=BoomOllama(),
        db_path=tmp_path / "progress.sqlite3",
        session_id="test-session",
        clock=lambda: NOW,
    )
    client = TestClient(create_app(deps), raise_server_exceptions=False)
    resp = client.post(
        "/api/v1/reviews",
        json={"exercise_id": COUNT_TAGS_ID, "source": "def count_tags(tags): ..."},
    )
    assert resp.status_code == 500
    body = resp.json()
    assert body["error"]["code"] == "internal_error"
    assert set(body["error"]) == {"code", "message", "details"}


def test_importing_main_has_no_import_time_catalog_load(monkeypatch):
    # Importing the module must not touch the filesystem: it previously loaded
    # the catalog from a cwd-relative default, aborting collection unless run
    # from the repo root.
    monkeypatch.setenv("LEARN_CODE_CONTENT_ROOT", str(tmp_nonexistent := Path("/nonexistent/content")))
    assert not tmp_nonexistent.exists()
    main_module = importlib.import_module("learn_code_api.main")
    importlib.reload(main_module)  # must not raise despite the invalid content root
    assert callable(main_module.create_app)


def test_content_list_includes_all_kinds_and_filters(tmp_path):
    client, _, _ = make_client(tmp_path)
    items = client.get("/api/v1/content").json()
    kinds = {item["kind"] for item in items}
    assert kinds == {"exercise", "lesson", "quiz"}

    lessons = client.get("/api/v1/content", params={"kind": "lesson"}).json()
    assert lessons and all(item["kind"] == "lesson" for item in lessons)


def test_lesson_detail_returns_body_and_checkpoints(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get(f"/api/v1/content/{LESSON_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "lesson"
    assert body["body_markdown"]
    assert body["checkpoints"][0]["question"]
    assert body["checkpoints"][0]["answer"]


def test_quiz_detail_never_leaks_answers(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get(f"/api/v1/content/{QUIZ_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["kind"] == "quiz"
    assert body["questions"]
    for question in body["questions"]:
        assert question["choices"]
        assert "correct_choice" not in question
        assert "explanation" not in question


def test_complete_lesson_records_completion(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post(f"/api/v1/lessons/{LESSON_ID}/complete")
    assert resp.status_code == 200
    body = resp.json()
    assert body["lesson_id"] == LESSON_ID
    assert body["completed_at"]


def test_complete_lesson_unknown_id_is_404(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post("/api/v1/lessons/lesson.nope/complete")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "content_not_found"


def test_paths_list_shows_seed_paths(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get("/api/v1/paths")
    assert resp.status_code == 200
    items = resp.json()
    ids = {item["id"] for item in items}
    assert "path.career.python_interview_prep" in ids
    assert "path.career.python_developer_mastery" in ids
    assert "path.career.algorithms_specialist" in ids
    assert "path.career.python_data_automation" in ids
    assert "path.career.ai_engineer_python" in ids
    assert len(items) == 21
    for item in items:
        assert item["enrolled"] is False
        assert item["percent_complete"] == 0
        assert item["path_type"] in {"career", "skill"}
        assert item["units"] > 0
        assert item["items"] > 0


def test_path_detail_tracks_completion_and_next_item(tmp_path):
    client, _, _ = make_client(tmp_path)
    detail = client.get("/api/v1/paths/path.skill.python_foundations").json()
    first_unit = detail["units"][0]
    first_item = first_unit["items"][0]
    assert first_item["status"] == "todo"
    assert detail["next_item_id"] == first_item["id"]
    assert first_item["kind"] == "lesson"

    done = client.post(f"/api/v1/lessons/{first_item['id']}/complete")
    assert done.status_code == 200

    detail = client.get("/api/v1/paths/path.skill.python_foundations").json()
    assert detail["units"][0]["items"][0]["status"] == "complete"
    assert detail["next_item_id"] == first_unit["items"][1]["id"]
    assert detail["percent_complete"] > 0


def test_path_units_gate_on_mastery_and_carry_milestones(tmp_path):
    client, _, _ = make_client(tmp_path)
    detail = client.get("/api/v1/paths/path.career.python_interview_prep").json()
    units = detail["units"]
    assert units[0]["status"] == "available"
    assert all(unit["status"] == "locked" for unit in units[1:])
    assert any(unit["milestone"] for unit in units)

    # Completing one item makes the first unit in_progress; the rest stay locked.
    first_lesson = next(i for i in units[0]["items"] if i["kind"] == "lesson")
    assert client.post(f"/api/v1/lessons/{first_lesson['id']}/complete").status_code == 200
    detail = client.get("/api/v1/paths/path.career.python_interview_prep").json()
    assert detail["units"][0]["status"] == "in_progress"
    assert detail["units"][1]["status"] == "locked"


def test_path_enroll_unenroll_roundtrip(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post("/api/v1/paths/path.skill.python_foundations/enroll")
    assert resp.status_code == 200
    assert resp.json() == {"path_id": "path.skill.python_foundations", "enrolled": True}

    listing = client.get("/api/v1/paths").json()
    enrolled = {item["id"]: item["enrolled"] for item in listing}
    assert enrolled["path.skill.python_foundations"] is True
    assert enrolled["path.career.python_interview_prep"] is False

    resp = client.post("/api/v1/paths/path.skill.python_foundations/unenroll")
    assert resp.json() == {"path_id": "path.skill.python_foundations", "enrolled": False}
    listing = client.get("/api/v1/paths").json()
    assert all(item["enrolled"] is False for item in listing)


def test_path_unknown_id_is_404(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.get("/api/v1/paths/path.skill.nope")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "content_not_found"


def _master_concepts(client, exercise_id: str, times: int = 5) -> None:
    for _ in range(times):
        client.post(
            "/api/v1/exercises/submit",
            json={
                "exercise_id": exercise_id,
                "content_version": 1,
                "language": "python",
                "source": "def f(): ...",
            },
        )


def test_timed_session_empty_when_nothing_practicing(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post("/api/v1/sessions/timed", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["session_id"]
    assert body["minutes_per_problem"] == 15
    assert body["exercises"] == []


def test_timed_session_selects_practicing_exercises(tmp_path):
    client, _, _ = make_client(tmp_path)
    _master_concepts(client, COUNT_TAGS_ID)

    resp = client.post("/api/v1/sessions/timed", json={"count": 2, "minutes_per_problem": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["minutes_per_problem"] == 10
    assert len(body["exercises"]) == 2

    progress = client.get("/api/v1/progress").json()
    practicing = {c["id"] for c in progress["concepts"] if c["mastery"] >= 50}
    for item in body["exercises"]:
        assert set(item["concepts"]) <= practicing


def test_timed_session_concept_filter(tmp_path):
    client, _, _ = make_client(tmp_path)
    _master_concepts(client, COUNT_TAGS_ID)

    resp = client.post(
        "/api/v1/sessions/timed",
        json={"count": 10, "concept_filter": "patterns.hash_map_counting"},
    )
    for item in resp.json()["exercises"]:
        assert "patterns.hash_map_counting" in item["concepts"]


def test_submit_records_timed_session_id(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post(
        "/api/v1/exercises/submit",
        json={
            "exercise_id": COUNT_TAGS_ID,
            "content_version": 1,
            "language": "python",
            "source": "def f(): ...",
            "timed_session_id": "timed-123",
        },
    )
    assert resp.status_code == 200
