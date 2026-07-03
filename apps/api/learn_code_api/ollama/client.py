"""Optional local Ollama code review (spec lines 353-417).

Ollama is never required. When it is disabled or unreachable the review action
returns a friendly ``unavailable`` payload and the exercise is unaffected --
tests remain the source of truth for pass/fail. The exact unavailable payload
is fixed by the task brief and must not drift.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Literal, Protocol

import httpx
from pydantic import BaseModel, Field

CHAT_PATH = "/api/chat"

OllamaEnabled = Literal["auto", "true", "false"]


class OllamaReview(BaseModel):
    """Structured review response (spec: Ollama code review > return shape)."""

    status: Literal["available", "unavailable", "model_missing", "error"]
    summary: str
    correctness_notes: list[str] = Field(default_factory=list)
    readability_notes: list[str] = Field(default_factory=list)
    python_simplifications: list[str] = Field(default_factory=list)
    big_o_notes: str | None = None
    next_improvement: str | None = None
    encouragement: str | None = None
    solution_disclosed: bool = False


# Verbatim from the task brief; keep this exact.
UNAVAILABLE_REVIEW = OllamaReview(
    status="unavailable",
    summary="Ollama is not reachable. Tests still decide pass/fail.",
    correctness_notes=[],
    readability_notes=[],
    python_simplifications=[],
    big_o_notes=None,
    next_improvement=None,
    encouragement=None,
    solution_disclosed=False,
)


@dataclass(frozen=True)
class OllamaSettings:
    enabled: OllamaEnabled = "auto"
    host: str = "http://host.docker.internal:11434"
    model: str = "granite-code:8b"
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> "OllamaSettings":
        enabled = os.environ.get("OLLAMA_ENABLED", "auto").lower()
        if enabled not in ("auto", "true", "false"):
            enabled = "auto"
        return cls(
            enabled=enabled,  # type: ignore[arg-type]
            host=os.environ.get("OLLAMA_HOST", cls.host),
            model=os.environ.get("OLLAMA_MODEL", cls.model),
            timeout_seconds=int(os.environ.get("OLLAMA_TIMEOUT_SECONDS", cls.timeout_seconds)),
        )


@dataclass(frozen=True)
class ReviewContext:
    """Inputs a review request should carry (spec lines 386-393)."""

    exercise_prompt: str
    concepts: list[str]
    expected_pattern: str | None
    learner_code: str
    test_result_summary: str
    learner_level: str
    allow_solution_disclosure: bool


class OllamaClient(Protocol):
    def review(self, context: ReviewContext) -> OllamaReview: ...


class HttpOllamaClient:
    """Calls a local Ollama chat endpoint, degrading to a friendly payload.

    ``transport`` is injectable so the unreachable path can be tested without a
    running Ollama.
    """

    def __init__(
        self,
        *,
        settings: OllamaSettings,
        transport: httpx.BaseTransport | None = None,
    ):
        self._settings = settings
        self._transport = transport

    def review(self, context: ReviewContext) -> OllamaReview:
        if self._settings.enabled == "false":
            return UNAVAILABLE_REVIEW

        try:
            with httpx.Client(
                base_url=self._settings.host,
                timeout=self._settings.timeout_seconds,
                transport=self._transport,
            ) as client:
                response = client.post(CHAT_PATH, json=self._build_payload(context))
        except httpx.RequestError:
            return UNAVAILABLE_REVIEW

        if response.status_code == 404:
            return OllamaReview(
                status="model_missing",
                summary=(
                    f"Ollama model '{self._settings.model}' is not installed. "
                    f"Run: ollama pull {self._settings.model}"
                ),
            )
        if response.status_code >= 400:
            return OllamaReview(
                status="error",
                summary=f"Ollama returned HTTP {response.status_code}.",
            )

        return self._parse(response.json())

    def _build_payload(self, context: ReviewContext) -> dict:
        return {
            "model": self._settings.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _render_user_prompt(context)},
            ],
        }

    def _parse(self, body: dict) -> OllamaReview:
        content = (body.get("message") or {}).get("content")
        if not content:
            return OllamaReview(status="error", summary="Ollama returned an empty response.")
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return OllamaReview(status="error", summary="Ollama returned unparseable review JSON.")
        if not isinstance(data, dict):
            return OllamaReview(status="error", summary="Ollama review did not match the schema.")
        # The model is instructed to omit `status`; stamp it as available so the
        # required field validates instead of forcing the whole reply to error.
        try:
            review = OllamaReview.model_validate({**data, "status": "available"})
        except ValueError:
            return OllamaReview(status="error", summary="Ollama review did not match the schema.")
        return review


_SYSTEM_PROMPT = (
    "You are a supportive Python interview coach. Review the learner's code and "
    'reply ONLY with JSON matching this schema: {"summary": str, '
    '"correctness_notes": [str], "readability_notes": [str], '
    '"python_simplifications": [str], "big_o_notes": str|null, '
    '"next_improvement": str|null, "encouragement": str|null}. Do not reveal a '
    "full solution unless explicitly told disclosure is allowed."
)


def _render_user_prompt(context: ReviewContext) -> str:
    disclosure = "allowed" if context.allow_solution_disclosure else "not allowed"
    return (
        f"Exercise prompt:\n{context.exercise_prompt}\n\n"
        f"Concepts: {', '.join(context.concepts)}\n"
        f"Expected pattern: {context.expected_pattern or 'unspecified'}\n"
        f"Learner level: {context.learner_level}\n"
        f"Test results: {context.test_result_summary}\n"
        f"Full-solution disclosure is {disclosure}.\n\n"
        f"Learner code:\n{context.learner_code}\n"
    )
