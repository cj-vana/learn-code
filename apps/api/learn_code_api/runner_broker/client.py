"""HTTP client and DTOs for the runner-broker service.

The API never executes learner code and never touches the Docker socket
(docs/superpowers/specs/2026-07-01-learn-code-design.md); it reaches the
runner only through the broker's single internal endpoint. These DTOs mirror
the broker request/response contract (spec lines 301-352) but are defined here
independently -- the API must not import the runner-broker package.

A connection failure to the broker is surfaced as ``RunnerUnavailableError`` so
the API can translate it into the ``runner_unavailable`` error envelope.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Protocol

import httpx
from pydantic import BaseModel, Field

RUNS_PATH = "/internal/v1/runs"


class RunMode(str, Enum):
    EXERCISE_TESTS = "exercise_tests"
    PLAYGROUND = "playground"


class TestProfile(str, Enum):
    __test__ = False  # mirrors the spec's "test_profile"; not a pytest class

    PUBLIC = "public"
    VALIDATION = "validation"
    PLAYGROUND = "playground"


class RunStatus(str, Enum):
    PASSED = "passed"
    FAILED_TESTS = "failed_tests"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"
    OUTPUT_EXCEEDED = "output_exceeded"
    INTERNAL_ERROR = "internal_error"


class RunLimits(BaseModel):
    timeout_seconds: int
    memory_mb: int
    cpu_count: int
    pids: int
    stdout_kb: int
    stderr_kb: int


class RunnerRequest(BaseModel):
    correlation_id: str
    mode: RunMode
    language: Literal["python"]
    source: str
    exercise_id: str | None = None
    test_profile: TestProfile
    stdin: str | None = None
    # Sent as null so the broker fills mode-appropriate defaults (spec line 314).
    limits: RunLimits | None = None


class TestSummaryEntry(BaseModel):
    __test__ = False  # mirrors the spec's "test_summary"; not a pytest class

    name: str
    visibility: Literal["public", "validation"]
    passed: bool
    message: str | None = None


class RunnerResponse(BaseModel):
    correlation_id: str
    status: RunStatus
    passed: int = 0
    failed: int = 0
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    timed_out: bool = False
    memory_exceeded: bool = False
    test_summary: list[TestSummaryEntry] = Field(default_factory=list)
    error_type: str | None = None
    educational_hint_id: str | None = None


class RunnerUnavailableError(RuntimeError):
    """The runner-broker could not be reached or returned an unusable response."""


class RunnerClient(Protocol):
    def run(self, request: RunnerRequest) -> RunnerResponse: ...


class HttpRunnerBrokerClient:
    """Synchronous httpx client for ``POST {base_url}/internal/v1/runs``.

    ``transport`` is injectable so tests can drive the connection-failure path
    without a live broker.
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self._base_url = base_url
        self._timeout = timeout_seconds
        self._transport = transport

    def run(self, request: RunnerRequest) -> RunnerResponse:
        try:
            with httpx.Client(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = client.post(RUNS_PATH, json=request.model_dump(mode="json"))
                response.raise_for_status()
                payload: Any = response.json()
        except httpx.HTTPStatusError as exc:
            raise RunnerUnavailableError(
                f"runner-broker returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise RunnerUnavailableError(f"runner-broker is unreachable: {exc}") from exc

        return RunnerResponse.model_validate(payload)
