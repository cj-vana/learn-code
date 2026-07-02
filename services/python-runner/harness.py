#!/usr/bin/env python3
"""Executes one runner job inside the ephemeral python-runner container.

Contract (CLI): ``python3 harness.py <job.json> <result.json>``

``job.json`` (written by runner-broker before the container starts):

    {
      "mode": "exercise_tests" | "playground",
      "source": "<submitted code>",
      "function_name": "<name>|null",     # required for exercise_tests
      "stdin": "<string>|null",           # used for playground only
      "tests": [                          # used for exercise_tests only
        {"name": str, "visibility": "public"|"validation", "input": any, "expected": any}
      ],
      "limits": {"timeout_seconds": int, "stdout_kb": int, "stderr_kb": int}
    }

``result.json`` (written by this script before it exits) is the body of the
runner-broker's internal response shape, minus ``correlation_id`` and
``educational_hint_id`` (the broker fills those in). See
docs/superpowers/specs/2026-07-01-learn-code-design.md lines 218-352.

This script has no third-party dependencies so the python-runner image can
stay minimal (stdlib only).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import traceback
from pathlib import Path

RESULT_SENTINEL = "<<<LEARN_CODE_RESULT>>>"

_EXERCISE_APPENDIX = """
import json as _lc_json
import contextlib as _lc_contextlib
import io as _lc_io

_lc_tests = __LC_TESTS_JSON__
_lc_function_name = __LC_FUNCTION_NAME__
_lc_results = []
_lc_had_crash = False
_lc_crash_type = None
_lc_stdout_parts = []

_lc_target = globals().get(_lc_function_name)
if not callable(_lc_target):
    _lc_had_crash = True
    _lc_crash_type = "NameError"
    for _lc_case in _lc_tests:
        _lc_results.append({
            "name": _lc_case["name"],
            "visibility": _lc_case["visibility"],
            "passed": False,
            "message": (
                "Submitted code does not define the required function."
                if _lc_case["visibility"] == "public"
                else "Validation test raised an error."
            ),
        })
else:
    for _lc_case in _lc_tests:
        _lc_buf = _lc_io.StringIO()
        try:
            with _lc_contextlib.redirect_stdout(_lc_buf):
                _lc_actual = _lc_target(_lc_case["input"])
            _lc_passed = _lc_actual == _lc_case["expected"]
            if _lc_passed:
                _lc_message = None
            elif _lc_case["visibility"] == "public":
                _lc_message = "expected {!r}, got {!r}".format(_lc_case["expected"], _lc_actual)
            else:
                _lc_message = "Validation test did not pass."
            _lc_results.append({
                "name": _lc_case["name"],
                "visibility": _lc_case["visibility"],
                "passed": _lc_passed,
                "message": _lc_message,
            })
        except Exception as _lc_exc:
            _lc_had_crash = True
            _lc_crash_type = type(_lc_exc).__name__
            if _lc_case["visibility"] == "public":
                _lc_message = "{}: {}".format(type(_lc_exc).__name__, _lc_exc)
            else:
                _lc_message = "Validation test raised an error."
            _lc_results.append({
                "name": _lc_case["name"],
                "visibility": _lc_case["visibility"],
                "passed": False,
                "message": _lc_message,
            })
        finally:
            _lc_stdout_parts.append(_lc_buf.getvalue())

print("__SENTINEL__" + _lc_json.dumps({
    "results": _lc_results,
    "had_crash": _lc_had_crash,
    "crash_type": _lc_crash_type,
    "program_stdout": "".join(_lc_stdout_parts),
}))
""".replace("__SENTINEL__", RESULT_SENTINEL)


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


def _truncate(text: str, cap_kb: int) -> tuple[str, bool]:
    cap_bytes = cap_kb * 1024
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= cap_bytes:
        return text, False
    truncated = encoded[:cap_bytes].decode("utf-8", errors="ignore")
    return truncated, True


def _build_script(job: dict) -> str:
    source = job["source"]
    if job["mode"] == "playground":
        return source
    tests_json = json.dumps(job.get("tests") or [])
    function_name_json = json.dumps(job.get("function_name"))
    appendix = _EXERCISE_APPENDIX.replace("__LC_TESTS_JSON__", tests_json).replace(
        "__LC_FUNCTION_NAME__", function_name_json
    )
    return source + "\n" + appendix


def _last_exception_type(stderr: str) -> str | None:
    for line in reversed(stderr.strip().splitlines()):
        line = line.strip()
        if not line or line.startswith("Traceback") or line.startswith("  "):
            continue
        if ":" in line:
            return line.split(":", 1)[0].strip()
        return line
    return None


def run_job(job: dict, workdir: Path) -> dict:
    mode = job["mode"]
    limits = job.get("limits") or {}
    timeout_seconds = limits.get("timeout_seconds", 3)
    stdout_kb = limits.get("stdout_kb", 64)
    stderr_kb = limits.get("stderr_kb", 64)

    syntax_check_source = job["source"]
    try:
        compile(syntax_check_source, "<submission>", "exec")
    except SyntaxError as exc:
        return _blank_result(status="syntax_error", error_type="SyntaxError", stderr=str(exc))

    script = _build_script(job)
    script_path = workdir / "_submission.py"
    script_path.write_text(script)

    started = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            input=job.get("stdin") or "",
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=workdir,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        stdout, _ = _truncate(exc.stdout or "", stdout_kb)
        stderr, _ = _truncate(exc.stderr or "", stderr_kb)
        return _blank_result(
            status="timeout",
            timed_out=True,
            error_type="Timeout",
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
        )

    duration_ms = int((time.monotonic() - started) * 1000)

    if mode == "playground":
        result = _playground_result(proc, duration_ms)
    else:
        result = _exercise_tests_result(proc, duration_ms)

    result = _apply_output_caps(result, stdout_kb, stderr_kb)
    return result


def _playground_result(proc: subprocess.CompletedProcess, duration_ms: int) -> dict:
    if proc.returncode == 0:
        return _blank_result(
            status="passed", stdout=proc.stdout, stderr=proc.stderr, duration_ms=duration_ms
        )
    error_type = _last_exception_type(proc.stderr) or "RuntimeError"
    return _blank_result(
        status="runtime_error",
        error_type=error_type,
        stdout=proc.stdout,
        stderr=proc.stderr,
        duration_ms=duration_ms,
    )


def _exercise_tests_result(proc: subprocess.CompletedProcess, duration_ms: int) -> dict:
    stdout = proc.stdout or ""
    marker = stdout.rfind(RESULT_SENTINEL)
    if marker == -1:
        error_type = _last_exception_type(proc.stderr) or "RuntimeError"
        return _blank_result(
            status="runtime_error",
            error_type=error_type,
            stdout=stdout,
            stderr=proc.stderr,
            duration_ms=duration_ms,
        )

    payload_text = stdout[marker + len(RESULT_SENTINEL) :].strip()
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return _blank_result(
            status="internal_error",
            error_type="HarnessDecodeError",
            stdout=stdout,
            stderr=proc.stderr,
            duration_ms=duration_ms,
        )

    test_summary = payload["results"]
    passed_count = sum(1 for entry in test_summary if entry["passed"])
    failed_count = len(test_summary) - passed_count

    if payload["had_crash"]:
        status = "runtime_error"
        error_type = payload["crash_type"]
    elif failed_count == 0:
        status = "passed"
        error_type = None
    else:
        status = "failed_tests"
        error_type = None

    return _blank_result(
        status=status,
        passed=passed_count,
        failed=failed_count,
        stdout=payload.get("program_stdout", ""),
        stderr=proc.stderr,
        duration_ms=duration_ms,
        test_summary=test_summary,
        error_type=error_type,
    )


def _apply_output_caps(result: dict, stdout_kb: int, stderr_kb: int) -> dict:
    stdout, stdout_truncated = _truncate(result["stdout"], stdout_kb)
    stderr, stderr_truncated = _truncate(result["stderr"], stderr_kb)
    result["stdout"] = stdout
    result["stderr"] = stderr
    if (stdout_truncated or stderr_truncated) and result["status"] in (
        "passed",
        "failed_tests",
        "runtime_error",
    ):
        result["status"] = "output_exceeded"
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: harness.py <job.json> <result.json>", file=sys.stderr)
        return 2

    job_path = Path(argv[1])
    result_path = Path(argv[2])
    workdir = result_path.parent

    try:
        job = json.loads(job_path.read_text())
        result = run_job(job, workdir)
    except Exception:  # last-resort guard so a result.json is always written
        result = _blank_result(
            status="internal_error",
            error_type="HarnessInternalError",
            stderr=traceback.format_exc(),
        )

    result_path.write_text(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
