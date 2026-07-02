from pathlib import Path

from fastapi.testclient import TestClient

from app.contracts import RunnerRequest
from app.main import create_app
from app.run_manager import BusyError, RunManager

FIXTURE_CONTENT_ROOT = Path(__file__).parent / "fixtures" / "content" / "python"


class StubExecutor:
    def __init__(self, result: dict | None = None, raise_busy: bool = False):
        self.result = result or {
            "status": "passed",
            "passed": 1,
            "failed": 0,
            "stdout": "",
            "stderr": "",
            "duration_ms": 1,
            "timed_out": False,
            "memory_exceeded": False,
            "test_summary": [],
            "error_type": None,
        }
        self.raise_busy = raise_busy
        self.calls: list[dict] = []

    async def execute(self, job: dict, limits) -> dict:
        self.calls.append(job)
        return self.result


def build_client(executor=None) -> TestClient:
    executor = executor or StubExecutor()
    manager = RunManager(executor=executor, content_root=FIXTURE_CONTENT_ROOT)
    app = create_app(manager)
    return TestClient(app)


VALID_PAYLOAD = {
    "correlation_id": "11111111-1111-1111-1111-111111111111",
    "mode": "playground",
    "language": "python",
    "source": "print('hi')",
    "exercise_id": None,
    "test_profile": "playground",
    "stdin": None,
}


def test_runs_endpoint_returns_runner_response():
    client = build_client()
    resp = client.post("/internal/v1/runs", json=VALID_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["correlation_id"] == VALID_PAYLOAD["correlation_id"]
    assert body["status"] == "passed"


def test_runs_endpoint_rejects_non_python_language():
    client = build_client()
    payload = dict(VALID_PAYLOAD, language="javascript")
    resp = client.post("/internal/v1/runs", json=payload)
    assert resp.status_code == 422


def test_runs_endpoint_returns_409_when_busy():
    class BusyRunManager:
        async def run(self, request: RunnerRequest):
            raise BusyError("busy")

    app = create_app(BusyRunManager())
    client = TestClient(app)
    resp = client.post("/internal/v1/runs", json=VALID_PAYLOAD)
    assert resp.status_code == 409
