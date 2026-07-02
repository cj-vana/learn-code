import json
import subprocess
import sys
from pathlib import Path

import harness

HARNESS_PATH = Path(harness.__file__)


def _default_limits(**overrides):
    limits = {
        "timeout_seconds": 3,
        "stdout_kb": 64,
        "stderr_kb": 64,
    }
    limits.update(overrides)
    return limits


def run_job(job: dict, tmp_path: Path) -> dict:
    """Run the harness as a real subprocess against a trusted fixture workspace.

    This exercises the actual CLI contract (job.json in, result.json out) so at
    least one path per scenario proves the standalone script works end to end,
    without requiring Docker.
    """
    job_path = tmp_path / "job.json"
    result_path = tmp_path / "result.json"
    job_path.write_text(json.dumps(job))
    subprocess.run(
        [sys.executable, str(HARNESS_PATH), str(job_path), str(result_path)],
        check=True,
        cwd=tmp_path,
        timeout=30,
    )
    return json.loads(result_path.read_text())


def test_exercise_tests_all_pass(tmp_path):
    job = {
        "mode": "exercise_tests",
        "source": "def add(x):\n    return x[0] + x[1]\n",
        "function_name": "add",
        "stdin": None,
        "tests": [
            {"name": "basic", "visibility": "public", "input": [1, 2], "expected": 3},
            {"name": "hidden_basic", "visibility": "validation", "input": [4, 5], "expected": 9},
        ],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "passed"
    assert result["passed"] == 2
    assert result["failed"] == 0
    assert result["error_type"] is None
    names = {entry["name"] for entry in result["test_summary"]}
    assert names == {"basic", "hidden_basic"}
    assert all(entry["passed"] for entry in result["test_summary"])


def test_exercise_tests_failed_public_test_shows_detail(tmp_path):
    job = {
        "mode": "exercise_tests",
        "source": "def add(x):\n    return x[0] + x[1] + 1\n",
        "function_name": "add",
        "stdin": None,
        "tests": [
            {"name": "basic", "visibility": "public", "input": [1, 2], "expected": 3},
        ],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "failed_tests"
    assert result["passed"] == 0
    assert result["failed"] == 1
    entry = result["test_summary"][0]
    assert entry["visibility"] == "public"
    assert entry["passed"] is False
    assert "3" in entry["message"]
    assert "4" in entry["message"]


def test_exercise_tests_failed_validation_test_is_sanitized(tmp_path):
    job = {
        "mode": "exercise_tests",
        "source": "def add(x):\n    return x[0] + x[1] + 1\n",
        "function_name": "add",
        "stdin": None,
        "tests": [
            {"name": "hidden", "visibility": "validation", "input": [4, 5], "expected": 9},
        ],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "failed_tests"
    entry = result["test_summary"][0]
    assert entry["visibility"] == "validation"
    assert entry["passed"] is False
    assert entry["message"]
    # Sanitized: no leaked expected/actual values or raw input from the hidden case.
    assert "9" not in entry["message"]
    assert "10" not in entry["message"]
    assert "4" not in entry["message"]
    assert "5" not in entry["message"]


def test_syntax_error(tmp_path):
    job = {
        "mode": "exercise_tests",
        "source": "def add(x)\n    return x\n",
        "function_name": "add",
        "stdin": None,
        "tests": [
            {"name": "basic", "visibility": "public", "input": [1, 2], "expected": 3},
        ],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "syntax_error"
    assert result["error_type"] == "SyntaxError"
    assert result["test_summary"] == []


def test_runtime_error_in_playground(tmp_path):
    job = {
        "mode": "playground",
        "source": "raise ValueError('boom')\n",
        "function_name": None,
        "stdin": None,
        "tests": [],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "runtime_error"
    assert result["error_type"] == "ValueError"
    assert "boom" in result["stderr"]


def test_runtime_error_when_exercise_function_crashes(tmp_path):
    job = {
        "mode": "exercise_tests",
        "source": "def add(x):\n    raise RuntimeError('kaboom')\n",
        "function_name": "add",
        "stdin": None,
        "tests": [
            {"name": "basic", "visibility": "public", "input": [1, 2], "expected": 3},
        ],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "runtime_error"
    assert result["error_type"] == "RuntimeError"
    entry = result["test_summary"][0]
    assert entry["passed"] is False
    assert "kaboom" in entry["message"]


def test_playground_stdin_is_piped_in(tmp_path):
    job = {
        "mode": "playground",
        "source": "name = input()\nprint(f'hi {name}')\n",
        "function_name": None,
        "stdin": "world\n",
        "tests": [],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "passed"
    assert result["stdout"].strip() == "hi world"


def test_stdout_truncation(tmp_path):
    job = {
        "mode": "playground",
        "source": "print('x' * 5000)\n",
        "function_name": None,
        "stdin": None,
        "tests": [],
        "limits": _default_limits(stdout_kb=1),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "output_exceeded"
    assert len(result["stdout"].encode("utf-8")) <= 1024


def test_submission_cannot_read_answer_key_from_job_json(tmp_path):
    # A submission that tries to read the validation answers straight out of
    # job.json must not be able to pass without solving the exercise.
    job = {
        "mode": "exercise_tests",
        "source": (
            "import json\n"
            "def add(x):\n"
            "    for t in json.load(open('job.json'))['tests']:\n"
            "        if t['input'] == x:\n"
            "            return t['expected']\n"
            "    return None\n"
        ),
        "function_name": "add",
        "stdin": None,
        "tests": [
            {"name": "basic", "visibility": "public", "input": [1, 2], "expected": 3},
            {"name": "hidden", "visibility": "validation", "input": [40, 50], "expected": 999},
        ],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] != "passed"


def test_submission_cannot_forge_results_via_late_sentinel(tmp_path):
    # The untrusted child reports its results on stdout. A submission that only
    # solves the public case can register an atexit handler that prints a second,
    # forged result sentinel omitting the hidden validation case entirely. The
    # parent reads the LAST sentinel, so grading must still account for every job
    # case: the omitted hidden case must count as a failure, never silently vanish.
    job = {
        "mode": "exercise_tests",
        "source": (
            "import atexit, json\n"
            "def add(x):\n"
            "    return x[0] + x[1]\n"
            "def _cheat():\n"
            "    print('<<<LEARN_CODE_RESULT>>>' + json.dumps({\n"
            "        'results': [\n"
            "            {'name': 'basic', 'visibility': 'public',\n"
            "             'outcome': 'value', 'actual': 3}\n"
            "        ],\n"
            "        'program_stdout': '',\n"
            "    }))\n"
            "atexit.register(_cheat)\n"
        ),
        "function_name": "add",
        "stdin": None,
        "tests": [
            {"name": "basic", "visibility": "public", "input": [1, 2], "expected": 3},
            {"name": "hidden", "visibility": "validation", "input": [40, 50], "expected": 999},
        ],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] != "passed"
    # The dropped hidden case must still appear and must be marked as not passed.
    summary = {entry["name"]: entry for entry in result["test_summary"]}
    assert "hidden" in summary
    assert summary["hidden"]["passed"] is False


def test_exercise_tests_with_boolean_and_none_expected(tmp_path):
    # Test cases whose input/expected values are booleans or None must grade
    # correctly instead of crashing with a NameError on `true`/`false`/`null`.
    job = {
        "mode": "exercise_tests",
        "source": (
            "def classify(x):\n"
            "    if x is None:\n"
            "        return None\n"
            "    return x % 2 == 0\n"
        ),
        "function_name": "classify",
        "stdin": None,
        "tests": [
            {"name": "even", "visibility": "public", "input": 4, "expected": True},
            {"name": "odd", "visibility": "public", "input": 3, "expected": False},
            {"name": "none", "visibility": "validation", "input": None, "expected": None},
        ],
        "limits": _default_limits(),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "passed"
    assert result["passed"] == 3
    assert result["failed"] == 0
    assert result["error_type"] is None


def test_wall_clock_timeout(tmp_path):
    job = {
        "mode": "playground",
        "source": "import time\ntime.sleep(5)\n",
        "function_name": None,
        "stdin": None,
        "tests": [],
        "limits": _default_limits(timeout_seconds=1),
    }
    result = run_job(job, tmp_path)
    assert result["status"] == "timeout"
    assert result["timed_out"] is True
