"""Environment-driven configuration for the runner-broker service."""

from __future__ import annotations

import os
from pathlib import Path


def _default_content_root() -> Path:
    # services/runner-broker/app/settings.py -> repo root -> content/python
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "content" / "python"


class Settings:
    def __init__(self) -> None:
        self.python_runner_image = os.environ.get(
            "PYTHON_RUNNER_IMAGE", "learn-code-python-runner:local"
        )
        # Resolve the default lazily: computing it eagerly (as an `os.environ.get`
        # default argument) would call `_default_content_root()` even when the
        # env var is set, and that walk (`parents[3]`) raises IndexError from the
        # container layout `/srv/app/settings.py`, crashing import at startup.
        env_content_root = os.environ.get("LEARN_CODE_CONTENT_ROOT")
        self.content_root = Path(env_content_root) if env_content_root else _default_content_root()
        self.workspace_root = (
            Path(os.environ["RUNNER_WORKSPACE_ROOT"])
            if "RUNNER_WORKSPACE_ROOT" in os.environ
            else None
        )
        self.docker_timeout_buffer_seconds = float(
            os.environ.get("RUNNER_TIMEOUT_BUFFER_SECONDS", "2")
        )


settings = Settings()
