"""Contract tests for the FastAPI surface (Task 5).

The runner-broker and Ollama clients are injected through the app factory so
these tests never touch a live broker or a running Ollama. Content is the real
published seed catalog and progress is a temporary SQLite database per test.
"""

from __future__ import annotations

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


def test_quiz_answer_records_mastery(tmp_path):
    client, _, _ = make_client(tmp_path)
    resp = client.post(
        "/api/v1/quizzes/answer",
        json={"question_id": "q-recursion-1", "correct": True, "concepts": ["python.recursion"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["question_id"] == "q-recursion-1"
    assert body["correct"] is True
    assert body["concepts_changed"] == ["python.recursion"]
    assert body["next_review_due_at"]

    progress = client.get("/api/v1/progress").json()
    recorded = {c["id"]: c["mastery"] for c in progress["concepts"]}
    assert recorded.get("python.recursion", 0) > 0


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
