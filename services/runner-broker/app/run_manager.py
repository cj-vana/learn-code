"""Serializes runner-broker requests onto a single active run.

V1 supports exactly one active run at a time (docs/superpowers/specs/
2026-07-01-learn-code-design.md:295-299). A second request that arrives while
a run is in flight gets `BusyError` immediately rather than queueing, so
`POST /internal/v1/runs` never launches unbounded containers.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Protocol

from app.contracts import RunLimits, RunMode, RunnerRequest, RunnerResponse, RunStatus
from app.exercise_tests import ExerciseNotFoundError, resolve_test_plan


class BusyError(Exception):
    """Raised when a run is requested while another run is still active."""


class AsyncExecutor(Protocol):
    async def execute(self, job: dict, limits: RunLimits) -> dict: ...


class RunManager:
    def __init__(self, executor: AsyncExecutor, content_root: Path):
        self._executor = executor
        self._content_root = content_root
        self._lock = asyncio.Lock()

    async def run(self, request: RunnerRequest) -> RunnerResponse:
        if self._lock.locked():
            raise BusyError("runner-broker is already executing a run")
        async with self._lock:
            return await self._run_locked(request)

    async def _run_locked(self, request: RunnerRequest) -> RunnerResponse:
        try:
            job = self._build_job(request)
        except ExerciseNotFoundError as exc:
            return RunnerResponse(
                correlation_id=request.correlation_id,
                status=RunStatus.INTERNAL_ERROR,
                error_type="ExerciseNotFoundError",
                stderr=str(exc),
            )

        result = await self._executor.execute(job, request.limits)
        return RunnerResponse(correlation_id=request.correlation_id, **result)

    def _build_job(self, request: RunnerRequest) -> dict:
        if request.mode == RunMode.PLAYGROUND:
            return {
                "mode": "playground",
                "source": request.source,
                "function_name": None,
                "stdin": request.stdin,
                "tests": [],
            }

        plan = resolve_test_plan(
            exercise_id=request.exercise_id,
            test_profile=request.test_profile,
            content_root=self._content_root,
        )
        return {
            "mode": "exercise_tests",
            "source": request.source,
            "function_name": plan.function_name,
            "stdin": None,
            "tests": [
                {
                    "name": t.name,
                    "visibility": t.visibility,
                    "input": t.input,
                    "expected": t.expected,
                }
                for t in plan.tests
            ],
        }
