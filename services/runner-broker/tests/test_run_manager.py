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


class GatedExecutor:
    """Blocks the first execute() on an event so the run stays 'in flight'
    until the test releases it; later calls return immediately.

    Stands in for the production executor, whose real work happens in an
    uncancellable worker thread (main.py's `_ThreadedExecutor` via
    `asyncio.to_thread`)."""

    def __init__(self):
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.calls = 0
        self.result = {
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

    async def execute(self, job: dict, limits) -> dict:
        self.calls += 1
        if self.calls == 1:
            self.started.set()
            await self.release.wait()
        return self.result


@pytest.mark.asyncio
async def test_cancelled_request_keeps_run_slot_until_executor_finishes():
    """A client disconnect cancels the request coroutine, but the executor's
    work (a worker thread in prod) cannot be cancelled and keeps running. The
    single-active-run slot must stay taken until that work actually finishes,
    so a cancel+retry burst can't launch a second concurrent container."""
    executor = GatedExecutor()
    manager = RunManager(executor=executor, content_root=FIXTURE_CONTENT_ROOT)

    first = asyncio.create_task(manager.run(make_playground_request()))
    await asyncio.wait_for(executor.started.wait(), timeout=1.0)  # run is now in flight

    first.cancel()  # client disconnected mid-run
    with pytest.raises(asyncio.CancelledError):
        await first

    # The in-flight run has not finished, so a retry must be rejected as busy
    # rather than starting a second concurrent run.
    with pytest.raises(BusyError):
        await manager.run(
            make_playground_request(correlation_id="33333333-3333-3333-3333-333333333333")
        )

    # Once the in-flight run actually completes, the slot frees up again.
    executor.release.set()
    for _ in range(100):
        if not manager._lock.locked():
            break
        await asyncio.sleep(0)
    assert not manager._lock.locked()

    await manager.run(
        make_playground_request(correlation_id="44444444-4444-4444-4444-444444444444")
    )
    # The busy retry never reached the executor: only the cancelled run and the
    # final run invoked execute().
    assert executor.calls == 2
