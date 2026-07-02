from pathlib import Path

from app.contracts import RunLimits, RunMode
from app.executor import ContainerRunOutcome, DockerPyAdapter, Executor, build_container_options
from fakes import FakeDockerAdapter

EXERCISE_LIMITS = RunLimits.for_mode(RunMode.EXERCISE_TESTS)


def test_build_container_options_matches_security_baseline():
    options = build_container_options(EXERCISE_LIMITS)
    assert options == {
        "network_disabled": True,
        "mem_limit": "256m",
        "nano_cpus": 1_000_000_000,
        "pids_limit": 64,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "read_only": True,
        "user": "1000:1000",
        "remove": True,
    }


def test_build_container_options_enforces_cpu_quota():
    # The spec's "Runner default limits" mandate a 1 CPU quota; RunLimits.cpu_count
    # must actually be enforced on the container, not silently dropped.
    options = build_container_options(EXERCISE_LIMITS)
    assert options["nano_cpus"] == EXERCISE_LIMITS.cpu_count * 1_000_000_000


def test_executor_passes_security_options_to_adapter(tmp_path):
    adapter = FakeDockerAdapter()
    adapter.result_to_write = {
        "status": "passed",
        "passed": 1,
        "failed": 0,
        "stdout": "",
        "stderr": "",
        "duration_ms": 5,
        "timed_out": False,
        "memory_exceeded": False,
        "test_summary": [],
        "error_type": None,
    }
    executor = Executor(adapter=adapter, image="learn-code-python-runner:local", workspace_root=tmp_path)

    executor.execute(job={"mode": "playground", "source": "print(1)"}, limits=EXERCISE_LIMITS)

    assert len(adapter.calls) == 1
    call = adapter.calls[0]
    assert call.image == "learn-code-python-runner:local"
    assert call.options == {
        "network_disabled": True,
        "mem_limit": "256m",
        "nano_cpus": 1_000_000_000,
        "pids_limit": 64,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges"],
        "read_only": True,
        "user": "1000:1000",
        "remove": True,
    }


def test_executor_returns_parsed_result_from_workspace(tmp_path):
    adapter = FakeDockerAdapter()
    adapter.result_to_write = {
        "status": "passed",
        "passed": 2,
        "failed": 0,
        "stdout": "ok",
        "stderr": "",
        "duration_ms": 12,
        "timed_out": False,
        "memory_exceeded": False,
        "test_summary": [],
        "error_type": None,
    }
    executor = Executor(adapter=adapter, image="img", workspace_root=tmp_path)

    result = executor.execute(job={"mode": "playground", "source": "print(1)"}, limits=EXERCISE_LIMITS)

    assert result["status"] == "passed"
    assert result["stdout"] == "ok"


def test_executor_cleans_up_workspace_on_success(tmp_path):
    adapter = FakeDockerAdapter()
    adapter.result_to_write = {"status": "passed", "passed": 0, "failed": 0, "stdout": "",
                                "stderr": "", "duration_ms": 1, "timed_out": False,
                                "memory_exceeded": False, "test_summary": [], "error_type": None}
    executor = Executor(adapter=adapter, image="img", workspace_root=tmp_path)

    executor.execute(job={"mode": "playground", "source": "print(1)"}, limits=EXERCISE_LIMITS)

    workspace = Path(next(iter(adapter.calls[0].volumes.keys())))
    assert not workspace.exists()


def test_executor_cleans_up_workspace_even_when_adapter_raises(tmp_path):
    class ExplodingAdapter:
        def run(self, **kwargs):
            raise RuntimeError("docker daemon unavailable")

    executor = Executor(adapter=ExplodingAdapter(), image="img", workspace_root=tmp_path)

    before = set(tmp_path.iterdir())
    try:
        executor.execute(job={"mode": "playground", "source": "print(1)"}, limits=EXERCISE_LIMITS)
    except RuntimeError:
        pass
    after = set(tmp_path.iterdir())
    assert before == after


def test_executor_reports_timeout_from_adapter(tmp_path):
    adapter = FakeDockerAdapter()
    adapter.next_outcome = ContainerRunOutcome(exit_code=None, timed_out=True, oom_killed=False)
    executor = Executor(adapter=adapter, image="img", workspace_root=tmp_path)

    result = executor.execute(job={"mode": "playground", "source": "import time; time.sleep(5)"}, limits=EXERCISE_LIMITS)

    assert result["status"] == "timeout"
    assert result["timed_out"] is True


def test_executor_reports_memory_exceeded_from_adapter(tmp_path):
    adapter = FakeDockerAdapter()
    adapter.next_outcome = ContainerRunOutcome(exit_code=137, timed_out=False, oom_killed=True)
    executor = Executor(adapter=adapter, image="img", workspace_root=tmp_path)

    result = executor.execute(job={"mode": "playground", "source": "x = [0] * 10**9"}, limits=EXERCISE_LIMITS)

    assert result["status"] == "memory_exceeded"
    assert result["memory_exceeded"] is True


class _FakeNotFound(Exception):
    """Stand-in for docker.errors.NotFound raised when an auto-removed container is gone."""


class _FakeContainer:
    """Mimics an auto-removed (remove=True) container: reload() 404s post-exit."""

    def __init__(self, status_code: int):
        self._status_code = status_code
        self.attrs: dict = {}

    def start(self):
        pass

    def wait(self, timeout=None):
        return {"StatusCode": self._status_code}

    def reload(self):
        raise _FakeNotFound("container gone (auto-removed)")

    def kill(self):
        pass

    def remove(self, force=False):
        pass


class _FakeContainers:
    def __init__(self, container):
        self._container = container

    def create(self, **kwargs):
        return self._container


class _FakeClient:
    def __init__(self, container):
        self.containers = _FakeContainers(container)


def test_docker_adapter_infers_oom_when_autoremoved_container_exits_137():
    # Under AutoRemove (remove=True) the daemon deletes the container on exit,
    # so container.reload()/inspect races and cannot report OOMKilled. Exit
    # code 137 (128 + SIGKILL) must still surface as memory_exceeded.
    adapter = DockerPyAdapter()
    adapter._client = _FakeClient(_FakeContainer(status_code=137))

    outcome = adapter.run(
        image="img",
        command=["python3", "/app/harness.py"],
        volumes={},
        options={"remove": True},
        timeout_seconds=5.0,
    )

    assert outcome.timed_out is False
    assert outcome.exit_code == 137
    assert outcome.oom_killed is True


def test_executor_reports_internal_error_when_no_result_written(tmp_path):
    adapter = FakeDockerAdapter()  # no result_to_write configured, harness "crashed silently"
    executor = Executor(adapter=adapter, image="img", workspace_root=tmp_path)

    result = executor.execute(job={"mode": "playground", "source": "print(1)"}, limits=EXERCISE_LIMITS)

    assert result["status"] == "internal_error"
