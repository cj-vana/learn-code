from __future__ import annotations

from pathlib import Path

from learn_code_cli import docker_compose
from learn_code_cli.main import app


def test_bring_up_prints_command_when_docker_missing(tmp_path):
    outcome = docker_compose.bring_up(tmp_path, available=False)
    assert outcome.ran is False
    assert "docker compose up --build" in outcome.message


def test_bring_up_shells_out_when_available(tmp_path):
    calls = []

    class _Completed:
        returncode = 0

    def fake_run(cmd, cwd):
        calls.append((cmd, cwd))
        return _Completed()

    outcome = docker_compose.bring_up(tmp_path, run=fake_run, available=True)
    assert outcome.ran is True
    assert calls == [(["docker", "compose", "up", "--build"], str(tmp_path))]


def test_up_command_prints_hint_without_docker(runner, monkeypatch):
    monkeypatch.setattr(docker_compose, "is_available", lambda: False)
    result = runner.invoke(app, ["up"])
    assert result.exit_code == 0
    assert "docker compose up --build" in result.stdout


def test_up_command_uses_repo_root(runner, monkeypatch):
    seen = {}

    class _Completed:
        returncode = 0

    def fake_run(cmd, cwd):
        seen["cmd"] = cmd
        seen["cwd"] = cwd
        return _Completed()

    monkeypatch.setattr(docker_compose, "is_available", lambda: True)
    monkeypatch.setattr(docker_compose.subprocess, "run", fake_run)
    result = runner.invoke(app, ["up"])
    assert result.exit_code == 0
    assert seen["cmd"] == ["docker", "compose", "up", "--build"]
    # cwd is the repo checkout root, which contains the CLI package.
    assert (Path(seen["cwd"]) / "apps" / "cli").is_dir()
