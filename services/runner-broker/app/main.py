"""FastAPI app exposing runner-broker's sole internal endpoint.

`runner-broker` is an internal-only service: no host port, reachable only by
the API's `runner_broker` module (docs/superpowers/specs/
2026-07-01-learn-code-design.md:232-246). This is the only service allowed to
talk to Docker.
"""

from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException

from app.contracts import RunLimits, RunnerRequest, RunnerResponse
from app.executor import DockerPyAdapter, Executor
from app.run_manager import BusyError, RunManager
from app.settings import settings


class _ThreadedExecutor:
    """Adapts the synchronous, blocking `Executor` to `RunManager`'s async
    interface by running each call in a worker thread, so one in-flight
    Docker run doesn't block the event loop."""

    def __init__(self, executor: Executor):
        self._executor = executor

    async def execute(self, job: dict, limits: RunLimits) -> dict:
        return await asyncio.to_thread(self._executor.execute, job, limits)


def create_app(run_manager: RunManager) -> FastAPI:
    app = FastAPI(title="learn-code-runner-broker")

    @app.post("/internal/v1/runs", response_model=RunnerResponse)
    async def create_run(request: RunnerRequest) -> RunnerResponse:
        try:
            return await run_manager.run(request)
        except BusyError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    return app


def _build_default_run_manager() -> RunManager:
    executor = Executor(
        adapter=DockerPyAdapter(),
        image=settings.python_runner_image,
        workspace_root=settings.workspace_root,
        timeout_buffer_seconds=settings.docker_timeout_buffer_seconds,
    )
    return RunManager(executor=_ThreadedExecutor(executor), content_root=settings.content_root)


app = create_app(_build_default_run_manager())
