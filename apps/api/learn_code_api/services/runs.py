"""Runner-broker backed executions that do not record progress.

Covers the public example run for an exercise and the free playground run. Both
delegate execution to the runner-broker over HTTP; the API never runs code
itself.
"""

from __future__ import annotations

from uuid import uuid4

from learn_code_api.contracts import PlaygroundRunRequest, PublicRunRequest, RunResult
from learn_code_api.content.models import ContentCatalog
from learn_code_api.runner_broker.client import (
    RunMode,
    RunnerClient,
    RunnerRequest,
    RunnerResponse,
    TestProfile,
)
from learn_code_api.services import find_exercise


def to_run_result(response: RunnerResponse) -> RunResult:
    return RunResult(
        status=response.status,
        passed=response.passed,
        failed=response.failed,
        stdout=response.stdout,
        stderr=response.stderr,
        duration_ms=response.duration_ms,
        test_summary=response.test_summary,
    )


def public_run(
    catalog: ContentCatalog, runner: RunnerClient, request: PublicRunRequest
) -> RunResult:
    exercise = find_exercise(catalog, request.exercise_id)
    runner_request = RunnerRequest(
        correlation_id=str(uuid4()),
        mode=RunMode.EXERCISE_TESTS,
        language="python",
        source=request.source,
        exercise_id=exercise.id,
        test_profile=TestProfile.PUBLIC,
    )
    return to_run_result(runner.run(runner_request))


def playground_run(runner: RunnerClient, request: PlaygroundRunRequest) -> RunResult:
    runner_request = RunnerRequest(
        correlation_id=str(uuid4()),
        mode=RunMode.PLAYGROUND,
        language="python",
        source=request.source,
        exercise_id=None,
        test_profile=TestProfile.PLAYGROUND,
        stdin=request.stdin,
    )
    return to_run_result(runner.run(runner_request))
