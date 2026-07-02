"""Runtime configuration for the CLI.

The API base URL comes from ``LEARN_CODE_API_URL`` (default
``http://127.0.0.1:8000``); every request targets the stable ``/api/v1`` prefix.
Path helpers locate the repo root so ``validate-content`` and ``up`` operate on
the checkout rather than the current working directory.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_API_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"
DEFAULT_TIMEOUT_SECONDS = 30.0


def api_root() -> str:
    """The API origin with no path, honouring ``LEARN_CODE_API_URL``."""
    return os.environ.get("LEARN_CODE_API_URL", DEFAULT_API_URL).rstrip("/")


def api_base_url() -> str:
    """The versioned base every endpoint hangs off, e.g. ``.../api/v1``."""
    return f"{api_root()}{API_PREFIX}"


def repo_root() -> Path:
    """Repo checkout root: ``apps/cli/src/learn_code_cli/config.py`` -> up 4."""
    return Path(__file__).resolve().parents[4]


def default_content_root() -> Path:
    """Published Python content tree used by ``validate-content``."""
    return repo_root() / "content" / "python"
