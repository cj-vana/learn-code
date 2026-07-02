"""Application dependency container and request-scoped wiring.

The API owns the SQLite database and is its only writer (spec rule). A fresh
``ProgressRepository`` is opened per request against the injected ``db_path``;
this is a single-user local app so there is no cross-request connection sharing
to worry about. The runner-broker and Ollama clients are injected here so tests
can supply fakes through the app factory.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import Request

from learn_code_api.content.loader import load_catalog
from learn_code_api.content.models import ContentCatalog
from learn_code_api.ollama.client import HttpOllamaClient, OllamaClient, OllamaSettings
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.runner_broker.client import HttpRunnerBrokerClient, RunnerClient

DEFAULT_CONTENT_ROOT = Path("content/python")
DEFAULT_DATABASE_PATH = Path("/data/learn-code.sqlite3")
DEFAULT_RUNNER_BROKER_URL = "http://runner-broker:8080"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AppDependencies:
    catalog: ContentCatalog
    runner_client: RunnerClient
    ollama_client: OllamaClient
    db_path: Path
    session_id: str = field(default_factory=lambda: str(uuid4()))
    clock: Callable[[], datetime] = _utcnow


def _database_path_from_env() -> Path:
    url = os.environ.get("LEARN_CODE_DATABASE_URL")
    if not url:
        return DEFAULT_DATABASE_PATH
    # sqlite:///rel -> relative path; sqlite:////abs -> absolute path.
    if url.startswith("sqlite:///"):
        remainder = url[len("sqlite://") :]  # keeps the leading slash of an absolute path
        if remainder.startswith("//"):
            return Path(remainder[1:])
        return Path(remainder.lstrip("/"))
    return Path(url)


def build_default_dependencies() -> AppDependencies:
    """Wire production dependencies from environment configuration."""
    content_root = Path(os.environ.get("LEARN_CODE_CONTENT_ROOT", str(DEFAULT_CONTENT_ROOT)))
    runner_url = os.environ.get("RUNNER_BROKER_URL", DEFAULT_RUNNER_BROKER_URL)
    return AppDependencies(
        catalog=load_catalog(content_root),
        runner_client=HttpRunnerBrokerClient(base_url=runner_url),
        ollama_client=HttpOllamaClient(settings=OllamaSettings.from_env()),
        db_path=_database_path_from_env(),
    )


def get_deps(request: Request) -> AppDependencies:
    return request.app.state.deps


def get_repo(request: Request) -> Iterator[ProgressRepository]:
    """Open a request-scoped repository and always close it."""
    deps: AppDependencies = request.app.state.deps
    now = deps.clock()
    deps.db_path.parent.mkdir(parents=True, exist_ok=True)
    repo = ProgressRepository(deps.db_path, now=now)
    try:
        yield repo
    finally:
        repo.close()
