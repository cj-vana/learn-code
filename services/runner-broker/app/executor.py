"""Runs one job in an ephemeral python-runner container.

`Executor` is the only place that knows how to turn a job + limits into a
container run. It talks to Docker only through the `DockerAdapter` seam, so
tests can swap in a fake adapter and never need a real Docker daemon.

Container security options mirror the brief verbatim (see
.superpowers/sdd/task-4-brief.md Step 5) and the spec's "Runner default
limits" (docs/superpowers/specs/2026-07-01-learn-code-design.md:267-299).
"""

from __future__ import annotations

import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.contracts import RunLimits

HARNESS_COMMAND = ["python3", "/app/harness.py", "/workspace/job.json", "/workspace/result.json"]
CONTAINER_WORKSPACE_PATH = "/workspace"


def build_container_options(limits: RunLimits) -> dict[str, Any]:
    """The exact container hardening options required by the brief, with
    mem_limit/pids_limit driven by the run's limits (256m/64 by default)."""
    return {
        "network_disabled": True,
        "mem_limit": f"{limits.memory_mb}m",
        "pids_limit": limits.pids,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "read_only": True,
        "user": "1000:1000",
        "remove": True,
    }


@dataclass
class ContainerRunOutcome:
    exit_code: int | None
    timed_out: bool
    oom_killed: bool


class DockerAdapter(Protocol):
    def run(
        self,
        *,
        image: str,
        command: list[str],
        volumes: dict[str, dict[str, str]],
        options: dict,
        timeout_seconds: float,
    ) -> ContainerRunOutcome: ...


class DockerPyAdapter:
    """Talks to a real Docker daemon via docker-py.

    This is the only place in the codebase that is allowed to import `docker`
    and reach the socket mounted into the runner-broker container. It is not
    exercised in this task's test suite (no Docker daemon required to verify
    the executor's behavior); the `FakeDockerAdapter` test seam covers the
    contract this class must satisfy.
    """

    def __init__(self) -> None:
        self._client = None  # connected lazily so importing this module never touches Docker

    def _client_or_connect(self):
        if self._client is None:
            import docker  # local import: keep `docker` optional for adapter-less usage

            self._client = docker.from_env()
        return self._client

    def run(
        self,
        *,
        image: str,
        command: list[str],
        volumes: dict[str, dict[str, str]],
        options: dict,
        timeout_seconds: float,
    ) -> ContainerRunOutcome:
        client = self._client_or_connect()
        container = client.containers.create(
            image=image,
            command=command,
            volumes=volumes,
            working_dir=CONTAINER_WORKSPACE_PATH,
            **options,
        )
        timed_out = False
        exit_code: int | None = None
        try:
            container.start()
            try:
                wait_result = container.wait(timeout=timeout_seconds)
                exit_code = wait_result.get("StatusCode")
            except Exception:
                timed_out = True
                try:
                    container.kill()
                except Exception:
                    pass
            oom_killed = False
            if not timed_out:
                try:
                    container.reload()
                    oom_killed = bool(container.attrs.get("State", {}).get("OOMKilled"))
                except Exception:
                    pass
        finally:
            try:
                container.remove(force=True)
            except Exception:
                pass
        return ContainerRunOutcome(exit_code=exit_code, timed_out=timed_out, oom_killed=oom_killed)


def _blank_result(**overrides) -> dict:
    result = {
        "status": "internal_error",
        "passed": 0,
        "failed": 0,
        "stdout": "",
        "stderr": "",
        "duration_ms": 0,
        "timed_out": False,
        "memory_exceeded": False,
        "test_summary": [],
        "error_type": None,
    }
    result.update(overrides)
    return result


class Executor:
    def __init__(
        self,
        adapter: DockerAdapter,
        image: str,
        workspace_root: Path | None = None,
        timeout_buffer_seconds: float = 2.0,
    ):
        self._adapter = adapter
        self._image = image
        self._workspace_root = str(workspace_root) if workspace_root is not None else None
        self._timeout_buffer_seconds = timeout_buffer_seconds

    def execute(self, job: dict, limits: RunLimits) -> dict:
        workspace = Path(tempfile.mkdtemp(prefix="learn-code-run-", dir=self._workspace_root))
        try:
            return self._run_in_workspace(workspace, job, limits)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def _run_in_workspace(self, workspace: Path, job: dict, limits: RunLimits) -> dict:
        job_payload = dict(job)
        job_payload["limits"] = {
            "timeout_seconds": limits.timeout_seconds,
            "stdout_kb": limits.stdout_kb,
            "stderr_kb": limits.stderr_kb,
        }
        (workspace / "job.json").write_text(json.dumps(job_payload))

        options = build_container_options(limits)
        outcome = self._adapter.run(
            image=self._image,
            command=HARNESS_COMMAND,
            volumes={str(workspace): {"bind": CONTAINER_WORKSPACE_PATH, "mode": "rw"}},
            options=options,
            timeout_seconds=limits.timeout_seconds + self._timeout_buffer_seconds,
        )

        if outcome.oom_killed:
            return _blank_result(
                status="memory_exceeded", memory_exceeded=True, error_type="MemoryExceeded"
            )
        if outcome.timed_out:
            return _blank_result(status="timeout", timed_out=True, error_type="Timeout")

        result_path = workspace / "result.json"
        if not result_path.exists():
            return _blank_result(
                status="internal_error",
                error_type="MissingResult",
                stderr=f"container exited (code={outcome.exit_code}) without writing a result",
            )
        return json.loads(result_path.read_text())
