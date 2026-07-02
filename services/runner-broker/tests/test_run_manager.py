import asyncio
from pathlib import Path

import pytest

from app.contracts import RunMode, RunnerRequest, RunStatus, TestProfile
from app.run_manager import BusyError, RunManager

FIXTURE_CONTENT_ROOT = Path(__file__).parent / "fixtures" / "content" / "python"


class StubExecutor:
    """Records the job/limits it was given and returns a canned result."""

    def __init__(self, result: dict | None = None, delay: float = 0.0):
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
        self.delay = delay
        self.calls: list[dict] = []

    async def execute(self, job: dict, limits) -> dict:
        self.calls.append({"job": job, "limits": limits})
        if self.delay:
            await asyncio.sleep(self.delay)
        return self.result


def make_playground_request(correlation_id="11111111-1111-1111-1111-111111111111") -> RunnerRequest:
    return RunnerRequest(
        correlation_id=correlation_id,
        mode=RunMode.PLAYGROUND,
        language="python",
        source="print('hi')",
        exercise_id=None,
        test_profile=TestProfile.PLAYGROUND,
        stdin=None,
    )


def make_exercise_request(test_profile=TestProfile.PUBLIC) -> RunnerRequest:
    return RunnerRequest(
        correlation_id="22222222-2222-2222-2222-222222222222",
        mode=RunMode.EXERCISE_TESTS,
        language="python",
        source="def add_two(x):\n    return x[0] + x[1]\n",
        exercise_id="exercise.seed.add-two-001",
        test_profile=test_profile,
        stdin=None,
    )


@pytest.mark.asyncio
async def test_playground_run_returns_response_from_executor():
    executor = StubExecutor()
    manager = RunManager(executor=executor, content_root=FIXTURE_CONTENT_ROOT)

    response = await manager.run(make_playground_request())

    assert response.correlation_id == "11111111-1111-1111-1111-111111111111"
    assert response.status == RunStatus.PASSED
    assert len(executor.calls) == 1
    assert executor.calls[0]["job"]["mode"] == "playground"
    assert executor.calls[0]["job"]["source"] == "print('hi')"
    assert executor.calls[0]["job"]["stdin"] is None


@pytest.mark.asyncio
async def test_exercise_run_builds_job_from_resolved_test_plan():
    executor = StubExecutor()
    manager = RunManager(executor=executor, content_root=FIXTURE_CONTENT_ROOT)

    await manager.run(make_exercise_request(test_profile=TestProfile.VALIDATION))

    job = executor.calls[0]["job"]
    assert job["mode"] == "exercise_tests"
    assert job["function_name"] == "add_two"
    names = {t["name"] for t in job["tests"]}
    assert names == {"basic", "zero", "negative"}


@pytest.mark.asyncio
async def test_unknown_exercise_id_returns_internal_error_response():
    executor = StubExecutor()
    manager = RunManager(executor=executor, content_root=FIXTURE_CONTENT_ROOT)
    request = make_exercise_request()
    request = request.model_copy(update={"exercise_id": "exercise.seed.does-not-exist"})

    response = await manager.run(request)

    assert response.status == RunStatus.INTERNAL_ERROR
    assert executor.calls == []


@pytest.mark.asyncio
async def test_second_concurrent_request_gets_busy():
    executor = StubExecutor(delay=0.2)
    manager = RunManager(executor=executor, content_root=FIXTURE_CONTENT_ROOT)

    first = asyncio.create_task(manager.run(make_playground_request()))
    await asyncio.sleep(0.02)  # let the first request acquire the lock

    with pytest.raises(BusyError):
        await manager.run(make_playground_request(correlation_id="33333333-3333-3333-3333-333333333333"))

    await first  # let the first run finish cleanly


@pytest.mark.asyncio
async def test_lock_released_after_run_completes():
    executor = StubExecutor()
    manager = RunManager(executor=executor, content_root=FIXTURE_CONTENT_ROOT)

    await manager.run(make_playground_request())
    # A second run after the first completed should not raise BusyError.
    await manager.run(make_playground_request(correlation_id="44444444-4444-4444-4444-444444444444"))

    assert len(executor.calls) == 2
