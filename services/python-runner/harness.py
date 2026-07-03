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

import base64
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path

RESULT_SENTINEL = "<<<LEARN_CODE_RESULT>>>"

# The appendix that runs inside the untrusted submission process. It receives
# only the test *inputs* (base64-encoded JSON, decoded with json.loads at
# runtime so booleans/None survive as real Python objects), never the expected
# answers: it reports each call's actual return value and lets the trusted
# parent process decide pass/fail. Keeping expected values out of this process
# means submitted code cannot read the answer key off disk.
_EXERCISE_APPENDIX = """
import base64 as _lc_base64
import json as _lc_json
import contextlib as _lc_contextlib
import io as _lc_io

_lc_cases = _lc_json.loads(_lc_base64.b64decode(__LC_CASES_B64__).decode("utf-8"))
_lc_function_name = __LC_FUNCTION_NAME__
_lc_results = []
_lc_stdout_parts = []

_lc_target = globals().get(_lc_function_name)
if not callable(_lc_target):
    for _lc_case in _lc_cases:
        _lc_results.append({
            "name": _lc_case["name"],
            "visibility": _lc_case["visibility"],
            "outcome": "missing_function",
        })
else:
    for _lc_case in _lc_cases:
        _lc_buf = _lc_io.StringIO()
        try:
            with _lc_contextlib.redirect_stdout(_lc_buf):
                _lc_actual = _lc_target(_lc_case["input"])
            try:
                _lc_json.dumps(_lc_actual)
                _lc_entry = {
                    "name": _lc_case["name"],
                    "visibility": _lc_case["visibility"],
                    "outcome": "value",
                    "actual": _lc_actual,
                }
            except (TypeError, ValueError):
                _lc_entry = {
                    "name": _lc_case["name"],
                    "visibility": _lc_case["visibility"],
                    "outcome": "unrepresentable",
                    "actual_repr": repr(_lc_actual)[:200],
                }
            _lc_results.append(_lc_entry)
        except Exception as _lc_exc:
            _lc_results.append({
                "name": _lc_case["name"],
                "visibility": _lc_case["visibility"],
                "outcome": "error",
                "error_type": type(_lc_exc).__name__,
                "error_message": "{}".format(_lc_exc),
            })
        finally:
            _lc_stdout_parts.append(_lc_buf.getvalue())

print("__SENTINEL__" + _lc_json.dumps({
    "results": _lc_results,
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
    # Only name/visibility/input reach the untrusted process; expected answers
    # stay in the parent. base64 keeps the payload out of the source grammar so
    # booleans/None never render as the invalid Python tokens true/false/null.
    cases = [
        {"name": t["name"], "visibility": t["visibility"], "input": t["input"]}
        for t in (job.get("tests") or [])
    ]
    cases_b64 = base64.b64encode(json.dumps(cases).encode("utf-8")).decode("ascii")
    function_name_json = json.dumps(job.get("function_name"))
    appendix = _EXERCISE_APPENDIX.replace("__LC_CASES_B64__", repr(cases_b64)).replace(
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
        result = _exercise_tests_result(proc, job, duration_ms)

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


def _exercise_tests_result(proc: subprocess.CompletedProcess, job: dict, duration_ms: int) -> dict:
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

    # Grade in the parent: expected values only ever live here, so the child
    # process (the submission) can never read them off disk to fake a pass.
    cases = job.get("tests") or []
    test_summary, had_crash, crash_type = _grade_cases(cases, payload.get("results"))
    passed_count = sum(1 for entry in test_summary if entry["passed"])
    failed_count = len(test_summary) - passed_count

    if had_crash:
        status = "runtime_error"
        error_type = crash_type
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


def _grade_cases(cases: list, raw_results) -> tuple[list, bool, str | None]:
    """Compare each recorded actual output against the (parent-held) expected.

    Grading is driven by the parent-held ``cases`` list, never by the length or
    contents of the child-reported ``raw_results``. The child process is the
    untrusted submission: it can print extra, reordered, or truncated result
    sentinels (e.g. via an ``atexit`` handler that omits hidden validation
    cases). Results are matched back to cases by name and any case the child
    failed to report is counted as a failure, so a submission can never make a
    case silently vanish from the score.

    Validation-visibility messages are sanitized here so hidden inputs/expected
    values are never returned to the frontend.
    """
    results_by_name: dict = {}
    if isinstance(raw_results, list):
        for res in raw_results:
            if isinstance(res, dict):
                res_name = res.get("name")
                # Keep the first report for a name so a later forged duplicate
                # cannot override the genuine appendix result.
                if res_name is not None and res_name not in results_by_name:
                    results_by_name[res_name] = res

    test_summary: list[dict] = []
    had_crash = False
    crash_type: str | None = None

    for case in cases:
        name = case["name"]
        visibility = case["visibility"]
        res = results_by_name.get(name)

        if res is None:
            # The child never reported a result for this case (missing or forged
            # output). Treat it as a crash so it can never count as a pass.
            had_crash = True
            crash_type = crash_type or "MissingResult"
            message = (
                "No result was reported for this test."
                if visibility == "public"
                else "Validation test did not pass."
            )
            test_summary.append(
                {"name": name, "visibility": visibility, "passed": False, "message": message}
            )
            continue

        outcome = res.get("outcome")

        if outcome == "missing_function":
            had_crash = True
            crash_type = "NameError"
            passed = False
            message = (
                "Submitted code does not define the required function."
                if visibility == "public"
                else "Validation test raised an error."
            )
        elif outcome == "error":
            had_crash = True
            crash_type = res.get("error_type") or "RuntimeError"
            passed = False
            if visibility == "public":
                message = "{}: {}".format(res.get("error_type"), res.get("error_message"))
            else:
                message = "Validation test raised an error."
        elif outcome == "unrepresentable":
            passed = False
            if visibility == "public":
                message = "expected {!r}, got {}".format(case["expected"], res.get("actual_repr"))
            else:
                message = "Validation test did not pass."
        else:  # "value"
            actual = res.get("actual")
            passed = actual == case["expected"]
            if passed:
                message = None
            elif visibility == "public":
                message = "expected {!r}, got {!r}".format(case["expected"], actual)
            else:
                message = "Validation test did not pass."

        test_summary.append(
            {"name": name, "visibility": visibility, "passed": passed, "message": message}
        )

    return test_summary, had_crash, crash_type


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
        # The job file holds every validation test's expected answer. Remove it
        # before running the submission so submitted code sharing this workspace
        # cannot open it and read the answer key.
        job_path.unlink(missing_ok=True)
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
