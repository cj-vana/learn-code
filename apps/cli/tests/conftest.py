"""Shared fixtures for the CLI test suite.

All HTTP is intercepted with respx so the tests never require a live API,
Docker, or Ollama. ``api_base`` mirrors the CLI's default target so mocked
routes line up with what the client actually requests.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

API_BASE = "http://127.0.0.1:8000/api/v1"


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def api_base() -> str:
    return API_BASE
