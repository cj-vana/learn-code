"""The ``up`` action: bring the stack up with Docker Compose.

This is one of only two local (non-HTTP) actions the CLI performs. When Docker
is unavailable the exact command is printed instead of shelling out, so the same
hint is reachable from ``status`` when the API can't be reached.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

COMPOSE_COMMAND = ("docker", "compose", "up", "--build")
COMPOSE_HINT = "docker compose up --build"


@dataclass(frozen=True)
class UpOutcome:
    ran: bool
    message: str
    returncode: int = 0


def is_available() -> bool:
    """True when the ``docker`` executable is on ``PATH``."""
    return shutil.which("docker") is not None


def bring_up(
    cwd: Path,
    *,
    run: Callable[..., subprocess.CompletedProcess] | None = None,
    available: bool | None = None,
) -> UpOutcome:
    """Run ``docker compose up --build`` from ``cwd`` or print the command.

    ``run`` and ``available`` are injectable so tests never touch Docker;
    ``run`` is resolved at call time so ``subprocess.run`` stays monkeypatchable.
    """
    can_run = is_available() if available is None else available
    if not can_run:
        return UpOutcome(
            ran=False,
            message=(
                "Docker isn't available on PATH. Start the stack yourself from the "
                f"repo root:\n  {COMPOSE_HINT}"
            ),
        )
    runner = subprocess.run if run is None else run
    completed = runner(list(COMPOSE_COMMAND), cwd=str(cwd))
    return UpOutcome(ran=True, message="", returncode=completed.returncode)
