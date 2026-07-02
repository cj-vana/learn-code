"""Runner-broker request/response contracts.

Shapes and enum values mirror docs/superpowers/specs/2026-07-01-learn-code-design.md
lines 218-352 ("Runner design") verbatim. Treat this module as binding.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class RunMode(str, Enum):
    EXERCISE_TESTS = "exercise_tests"
    PLAYGROUND = "playground"


class TestProfile(str, Enum):
    __test__ = False  # not a pytest test class; name mirrors the spec's "test_profile"

    PUBLIC = "public"
    VALIDATION = "validation"
    PLAYGROUND = "playground"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED_TESTS = "failed_tests"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"
    OUTPUT_EXCEEDED = "output_exceeded"
    CANCELLED = "cancelled"
    INTERNAL_ERROR = "internal_error"


# Exercise runs per "Runner default limits".
_EXERCISE_LIMITS = {
    "timeout_seconds": 3,
    "memory_mb": 256,
    "cpu_count": 1,
    "pids": 64,
    "stdout_kb": 64,
    "stderr_kb": 64,
}

# Playground runs per "Runner default limits" (same user/capability/workspace/fs
# constraints as exercise runs; timeout and output caps differ).
_PLAYGROUND_LIMITS = {
    "timeout_seconds": 5,
    "memory_mb": 256,
    "cpu_count": 1,
    "pids": 64,
    "stdout_kb": 128,
    "stderr_kb": 128,
}


class RunLimits(BaseModel):
    timeout_seconds: int
    memory_mb: int
    cpu_count: int
    pids: int
    stdout_kb: int
    stderr_kb: int

    @classmethod
    def for_mode(cls, mode: RunMode) -> "RunLimits":
        defaults = _EXERCISE_LIMITS if mode == RunMode.EXERCISE_TESTS else _PLAYGROUND_LIMITS
        return cls(**defaults)


class RunnerRequest(BaseModel):
    correlation_id: str
    mode: RunMode
    language: Literal["python"]
    source: str
    exercise_id: str | None = None
    test_profile: TestProfile
    stdin: str | None = None
    limits: RunLimits | None = None

    def model_post_init(self, __context: object) -> None:
        """Fill in mode-appropriate default limits when the caller omits them."""
        if self.limits is None:
            object.__setattr__(self, "limits", RunLimits.for_mode(self.mode))


class TestSummaryEntry(BaseModel):
    __test__ = False  # not a pytest test class; name mirrors the spec's "test_summary"

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
