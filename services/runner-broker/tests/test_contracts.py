import pytest
from pydantic import ValidationError

from app.contracts import (
    RunLimits,
    RunMode,
    RunnerRequest,
    RunnerResponse,
    RunStatus,
    TestProfile,
    TestSummaryEntry,
)


def test_run_mode_enum_values():
    assert {m.value for m in RunMode} == {"exercise_tests", "playground"}


def test_test_profile_enum_values():
    assert {p.value for p in TestProfile} == {"public", "validation", "playground"}


def test_run_status_enum_values():
    assert {s.value for s in RunStatus} == {
        "queued",
        "running",
        "passed",
        "failed_tests",
        "syntax_error",
        "runtime_error",
        "timeout",
        "memory_exceeded",
        "output_exceeded",
        "cancelled",
        "internal_error",
    }


def test_exercise_default_limits():
    limits = RunLimits.for_mode(RunMode.EXERCISE_TESTS)
    assert limits.timeout_seconds == 3
    assert limits.memory_mb == 256
    assert limits.cpu_count == 1
    assert limits.pids == 64
    assert limits.stdout_kb == 64
    assert limits.stderr_kb == 64


def test_playground_default_limits():
    limits = RunLimits.for_mode(RunMode.PLAYGROUND)
    assert limits.timeout_seconds == 5
    assert limits.memory_mb == 256
    assert limits.cpu_count == 1
    assert limits.pids == 64
    assert limits.stdout_kb == 128
    assert limits.stderr_kb == 128


def test_request_defaults_limits_by_mode_when_omitted():
    request = RunnerRequest(
        correlation_id="11111111-1111-1111-1111-111111111111",
        mode=RunMode.PLAYGROUND,
        language="python",
        source="print('hi')",
        exercise_id=None,
        test_profile=TestProfile.PLAYGROUND,
        stdin=None,
    )
    assert request.limits.timeout_seconds == 5
    assert request.limits.stdout_kb == 128


def test_request_rejects_non_python_language():
    with pytest.raises(ValidationError):
        RunnerRequest(
            correlation_id="11111111-1111-1111-1111-111111111111",
            mode=RunMode.PLAYGROUND,
            language="javascript",
            source="console.log('hi')",
            exercise_id=None,
            test_profile=TestProfile.PLAYGROUND,
            stdin=None,
        )


def test_request_parses_from_spec_shape_json():
    payload = {
        "correlation_id": "11111111-1111-1111-1111-111111111111",
        "mode": "exercise_tests",
        "language": "python",
        "source": "def f(x): return x",
        "exercise_id": "exercise.seed.example",
        "test_profile": "public",
        "stdin": None,
        "limits": {
            "timeout_seconds": 3,
            "memory_mb": 256,
            "cpu_count": 1,
            "pids": 64,
            "stdout_kb": 64,
            "stderr_kb": 64,
        },
    }
    request = RunnerRequest.model_validate(payload)
    assert request.mode == RunMode.EXERCISE_TESTS
    assert request.limits.memory_mb == 256


def test_response_matches_spec_shape():
    response = RunnerResponse(
        correlation_id="11111111-1111-1111-1111-111111111111",
        status=RunStatus.PASSED,
        passed=3,
        failed=1,
        stdout="",
        stderr="",
        duration_ms=123,
        timed_out=False,
        memory_exceeded=False,
        test_summary=[
            TestSummaryEntry(name="test_example_1", visibility="public", passed=True, message=None)
        ],
        error_type=None,
        educational_hint_id=None,
    )
    dumped = response.model_dump()
    assert dumped["status"] == "passed"
    assert dumped["test_summary"][0]["name"] == "test_example_1"
