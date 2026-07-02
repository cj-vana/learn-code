"""Shared fake Docker adapter for executor/run_manager tests.

Real Docker is never required to exercise the executor's behavior: the fake
adapter records exactly what container options the executor asked for, and
lets each test script how the "container" behaves (writes a result.json,
times out, gets OOM-killed, or crashes) without touching a Docker daemon.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.executor import ContainerRunOutcome


@dataclass
class RecordedRun:
    image: str
    command: list[str]
    volumes: dict
    options: dict
    timeout_seconds: float


class FakeDockerAdapter:
    def __init__(self):
        self.calls: list[RecordedRun] = []
        self.next_outcome: ContainerRunOutcome | None = None
        self.result_to_write: dict | None = None

    def run(
        self,
        *,
        image: str,
        command: list[str],
        volumes: dict,
        options: dict,
        timeout_seconds: float,
    ) -> ContainerRunOutcome:
        self.calls.append(
            RecordedRun(
                image=image,
                command=list(command),
                volumes=volumes,
                options=dict(options),
                timeout_seconds=timeout_seconds,
            )
        )
        host_workspace = next(iter(volumes.keys()))
        if self.result_to_write is not None:
            (Path(host_workspace) / "result.json").write_text(json.dumps(self.result_to_write))
        if self.next_outcome is not None:
            return self.next_outcome
        return ContainerRunOutcome(exit_code=0, timed_out=False, oom_killed=False)
