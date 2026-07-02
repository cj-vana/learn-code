"""httpx wrapper for the Learn Code API.

The CLI is HTTP-only for every learner action, so this module is the single
place that talks to the backend. Responses are returned as plain dicts (the CLI
does not import the API's pydantic models); the render layer formats them. The
API error envelope ``{"error": {"code", "message", "details"}}`` becomes an
``ApiError`` and any connection failure becomes an ``ApiConnectionError`` so the
command layer can print the ``docker compose up --build`` hint.
"""

from __future__ import annotations

from typing import Any

import httpx

from learn_code_cli import config


class ApiConnectionError(Exception):
    """The API could not be reached at all (connect/timeout/transport error)."""


class ApiError(Exception):
    """A structured error envelope returned by the API."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class ApiClient:
    """Small synchronous client over the ``/api/v1`` surface.

    ``transport`` is injectable for tests that prefer a mock transport over
    respx; production callers leave it ``None`` and use the real network.
    """

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = config.DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
    ):
        self._base_url = (base_url or config.api_base_url()).rstrip("/")
        self._timeout = timeout
        self._transport = transport

    # --- endpoints -------------------------------------------------------
    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def plan(self) -> list[dict[str, Any]]:
        return self._request("GET", "/plan")

    def progress(self) -> dict[str, Any]:
        return self._request("GET", "/progress")

    def content_detail(self, exercise_id: str) -> dict[str, Any]:
        return self._request("GET", f"/content/{exercise_id}")

    def run_exercise(self, exercise_id: str, source: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/exercises/run",
            json={"exercise_id": exercise_id, "language": "python", "source": source},
        )

    def submit_exercise(
        self,
        exercise_id: str,
        content_version: int,
        source: str,
        *,
        predicted_pattern: str | None = None,
        confidence: int | None = None,
        hints_used: int = 0,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/exercises/submit",
            json={
                "exercise_id": exercise_id,
                "content_version": content_version,
                "language": "python",
                "source": source,
                "predicted_pattern": predicted_pattern,
                "confidence": confidence,
                "hints_used": hints_used,
            },
        )

    def playground(self, source: str, stdin: str | None = None) -> dict[str, Any]:
        return self._request(
            "POST",
            "/runs",
            json={"language": "python", "source": source, "stdin": stdin},
        )

    def paths(self) -> list[dict[str, Any]]:
        return self._request("GET", "/paths")

    def path_detail(self, path_id: str) -> dict[str, Any]:
        return self._request("GET", f"/paths/{path_id}")

    def enroll_path(self, path_id: str) -> dict[str, Any]:
        return self._request("POST", f"/paths/{path_id}/enroll")

    def unenroll_path(self, path_id: str) -> dict[str, Any]:
        return self._request("POST", f"/paths/{path_id}/unenroll")

    def answer_quiz(self, quiz_id: str, question_id: str, choice: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/quizzes/answer",
            json={"quiz_id": quiz_id, "question_id": question_id, "choice": choice},
        )

    def review(
        self,
        exercise_id: str,
        source: str,
        test_result_summary: str = "not provided",
        *,
        allow_solution_disclosure: bool = False,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/reviews",
            json={
                "exercise_id": exercise_id,
                "source": source,
                "test_result_summary": test_result_summary,
                "allow_solution_disclosure": allow_solution_disclosure,
            },
        )

    # --- transport -------------------------------------------------------
    def _request(self, method: str, path: str, json: Any | None = None) -> Any:
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                response = client.request(method, url, json=json)
        except httpx.RequestError as exc:
            raise ApiConnectionError(str(exc)) from exc
        if response.status_code >= 400:
            raise _to_api_error(response)
        return response.json()


def _to_api_error(response: httpx.Response) -> ApiError:
    try:
        error = response.json()["error"]
        return ApiError(error["code"], error["message"], error.get("details", {}))
    except (ValueError, KeyError, TypeError):
        return ApiError(
            "internal_error",
            f"API returned HTTP {response.status_code} with no error envelope.",
        )
