"""Error envelope and exception handlers (spec: Error semantics, lines 942-954).

Every error response is ``{"error": {"code", "message", "details"}}`` with a
code from the fixed set. Runner-broker connection failures map to
``runner_unavailable``.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from learn_code_api.contracts import ErrorEnvelope
from learn_code_api.runner_broker.client import RunnerUnavailableError


class APIError(Exception):
    """Base for errors that render as the standard envelope."""

    code = "internal_error"
    status_code = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ContentNotFoundError(APIError):
    code = "content_not_found"
    status_code = 404


def _envelope(
    status_code: int, code: str, message: str, details: dict[str, Any] | None = None
) -> JSONResponse:
    body = ErrorEnvelope.model_validate(
        {"error": {"code": code, "message": message, "details": details or {}}}
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def _handle_api_error(_: Request, exc: APIError) -> JSONResponse:
        return _envelope(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RunnerUnavailableError)
    async def _handle_runner_unavailable(_: Request, exc: RunnerUnavailableError) -> JSONResponse:
        return _envelope(503, "runner_unavailable", str(exc))

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"loc": [str(part) for part in err.get("loc", [])], "message": err.get("msg", "")}
            for err in exc.errors()
        ]
        return _envelope(
            422, "validation_error", "Request payload failed validation.", {"errors": errors}
        )
