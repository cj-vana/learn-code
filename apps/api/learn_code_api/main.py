"""FastAPI application factory for the Learn Code API.

This is the only backend for the web app and CLI; every route lives under
``/api/v1``. Dependencies (content catalog, runner-broker client, Ollama client,
database path, clock) are injected through ``create_app`` so tests can supply
fakes without a live broker, Ollama, or shared database.
"""

from __future__ import annotations

from fastapi import FastAPI

from learn_code_api.dependencies import AppDependencies, build_default_dependencies
from learn_code_api.errors import register_error_handlers
from learn_code_api.routers import api_router


def create_app(deps: AppDependencies) -> FastAPI:
    app = FastAPI(title="learn-code-api")
    app.state.deps = deps
    register_error_handlers(app)
    app.include_router(api_router)
    return app


app = create_app(build_default_dependencies())
