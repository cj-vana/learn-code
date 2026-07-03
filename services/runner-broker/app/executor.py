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
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.contracts import RunLimits

HARNESS_COMMAND = ["python3", "/app/harness.py", "/workspace/job.json", "/workspace/result.json"]
CONTAINER_WORKSPACE_PATH = "/workspace"
# Fixed non-root identity baked into the python-runner image (its Dockerfile
# creates uid/gid 1000); the workspace is chowned to it before each run.
RUNNER_UID = 1000
RUNNER_GID = 1000


def build_container_options(limits: RunLimits) -> dict[str, Any]:
    """The container hardening options required by the brief, with
    mem_limit/nano_cpus/pids_limit driven by the run's limits (256m/1 CPU/64 by
    default). `nano_cpus` enforces the spec's "CPU quota: 1 CPU" (design spec,
    "Runner default limits"); docker-py expresses a CPU quota in units of 1e-9
    CPUs, so cpu_count=1 => 1_000_000_000."""
    return {
        "network_disabled": True,
        "mem_limit": f"{limits.memory_mb}m",
        "nano_cpus": limits.cpu_count * 1_000_000_000,
        "pids_limit": limits.pids,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "read_only": True,
        "user": f"{RUNNER_UID}:{RUNNER_GID}",
        # `auto_remove` (not `remove`) is the kwarg docker-py's containers.create()
        # accepts; `remove` is a run()-only convenience and makes create() raise
        # TypeError. It maps to the daemon's HostConfig AutoRemove.
        "auto_remove": True,
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

    def ensure_image(self, image: str) -> None:
        """Best-effort image freshness at startup. Registry-hosted tags (the
        checkout-free install) are pulled so the sandbox tracks the tag even
        though it never runs as a service Watchtower could update; local tags
        and offline hosts fall back to whatever the daemon already has. Never
        raises — a truly missing image surfaces as a clear per-run error."""
        try:
            client = self._client_or_connect()
            if "/" in image:
                try:
                    client.images.pull(image)
                    return
                except Exception:
                    pass
            client.images.get(image)
        except Exception:
            logging.getLogger(__name__).warning(
                "runner image %s is not available yet; runs will fail until it is pulled or built",
                image,
            )

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
                    # With auto_remove=True the daemon deletes the
                    # container on exit, so reload()/inspect usually 404s here
                    # and can never report OOMKilled. Fall through to the exit
                    # code below.
                    pass
                # Exit code 137 == 128 + SIGKILL. In the non-timeout path the
                # only thing that SIGKILLs the container is the daemon reaping
                # it for exceeding mem_limit, so treat 137 as an OOM kill even
                # when inspect could not confirm it.
                if not oom_killed and exit_code == 137:
                    oom_killed = True
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
        # mkdtemp yields 0700 owned by the broker's user, but the runner
        # container runs as RUNNER_UID and must write result.json into the
        # bind-mounted workspace; Linux hosts enforce ownership. Hand the dir
        # to the runner uid (the root broker still bypasses 0700 to read the
        # result). Outside the container the broker isn't root, so fall back
        # to a world-writable dir — dev/test only, and Docker Desktop masks
        # host ownership there regardless.
        try:
            os.chown(workspace, RUNNER_UID, RUNNER_GID)
            os.chmod(workspace, 0o700)
        except PermissionError:
            os.chmod(workspace, 0o777)
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
