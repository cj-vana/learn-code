"""Request/response models for the stable ``/api/v1`` contract (spec 851-957).

Shapes reused verbatim from prior tasks (``PlanItem``, ``ProgressSummary``) are
re-exported here so routers depend on a single contract surface. New shapes for
content, runs, submissions, quizzes, and errors are defined below.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from learn_code_api.adaptive_plan.planner import PlanItem, Rationale
from learn_code_api.progress.rollups import ConceptSummary, ProgressSummary
from learn_code_api.runner_broker.client import RunStatus, TestSummaryEntry

__all__ = [
    "PlanItem",
    "Rationale",
    "ProgressSummary",
    "ConceptSummary",
    "HealthResponse",
    "PublicTestCase",
    "ContentSummary",
    "ContentDetail",
    "RunResult",
    "PublicRunRequest",
    "PlaygroundRunRequest",
    "ExerciseSubmissionRequest",
    "ProgressDelta",
    "SubmissionResponse",
    "QuizAnswerRequest",
    "QuizAnswerResponse",
    "ReviewRequest",
    "ErrorEnvelope",
    "CheckpointDetail",
    "LessonDetail",
    "QuizQuestionDetail",
    "QuizDetail",
    "LessonCompletionResponse",
]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class PublicTestCase(BaseModel):
    """A public example case; validation cases are never exposed (spec line 351)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    input: Any
    expected: Any


class ContentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: str
    title: str
    slug: str
    difficulty: str
    concepts: list[str]
    prerequisites: list[str]
    estimated_time_minutes: int


class ContentDetail(BaseModel):
    """Everything a learner needs to attempt an exercise.

    Deliberately omits ``sample_solution``, ``solution_sketch``,
    ``explanation_markdown`` and the validation test cases so the API does not
    disclose the answer before submission (spec lines 351, 415).
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    kind: str
    version: int
    language: str
    title: str
    slug: str
    difficulty: str
    concepts: list[str]
    prerequisites: list[str]
    estimated_time_minutes: int
    prompt_markdown: str
    starter_code: str
    function_name: str
    input_mode: str
    hints: list[dict[str, Any]]
    public_tests: list[PublicTestCase]
    common_mistakes: list[str]


class CheckpointDetail(BaseModel):
    """Ungraded self-check; the UI hides answer/explanation behind a reveal."""

    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str
    explanation: str


class LessonDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["lesson"]
    version: int
    language: str
    title: str
    slug: str
    difficulty: str
    concepts: list[str]
    prerequisites: list[str]
    estimated_time_minutes: int
    body_markdown: str
    checkpoints: list[CheckpointDetail]


class LessonCompletionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lesson_id: str
    completed_at: str


class QuizQuestionDetail(BaseModel):
    """One quiz question as shown to the learner: never the answer or its
    explanation (spec: quiz detail must not leak ``correct_choice``)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    prompt: str
    choices: list[str]
    concepts: list[str]


class QuizDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["quiz"]
    version: int
    language: str
    title: str
    slug: str
    difficulty: str
    concepts: list[str]
    prerequisites: list[str]
    estimated_time_minutes: int
    quiz_type: str
    questions: list[QuizQuestionDetail]


class RunResult(BaseModel):
    """The public-safe view of a runner-broker execution."""

    model_config = ConfigDict(extra="forbid")

    status: RunStatus
    passed: int
    failed: int
    stdout: str
    stderr: str
    duration_ms: int
    test_summary: list[TestSummaryEntry]


class PublicRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise_id: str
    language: Literal["python"] = "python"
    source: str


class PlaygroundRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Literal["python"] = "python"
    source: str
    stdin: str | None = None


class ExerciseSubmissionRequest(BaseModel):
    """Spec: Stable API contracts > Exercise submission request."""

    model_config = ConfigDict(extra="forbid")

    exercise_id: str
    content_version: int
    language: Literal["python"] = "python"
    source: str
    predicted_pattern: str | None = None
    confidence: int | None = None
    hints_used: int = Field(default=0, ge=0)


class ProgressDelta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concepts_changed: list[str]
    mastery_before: int
    mastery_after: int
    review_due_at: str | None


class SubmissionResponse(BaseModel):
    """Spec: Stable API contracts > Exercise submission response."""

    model_config = ConfigDict(extra="forbid")

    submission_id: str
    run: RunResult
    progress_delta: ProgressDelta
    next_actions: list[str]


class QuizAnswerRequest(BaseModel):
    """The learner's chosen answer; the API grades it against the catalog."""

    model_config = ConfigDict(extra="forbid")

    quiz_id: str
    question_id: str
    choice: str


class QuizAnswerResponse(BaseModel):
    """Spec: Stable API contracts > Quiz answer response."""

    model_config = ConfigDict(extra="forbid")

    question_id: str
    correct: bool
    explanation: str
    concepts_changed: list[str]
    next_review_due_at: str | None


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercise_id: str
    source: str
    test_result_summary: str = "not provided"
    allow_solution_disclosure: bool = False


class _ErrorBody(BaseModel):
    code: Literal[
        "content_not_found",
        "validation_error",
        "runner_unavailable",
        "ollama_unavailable",
        "internal_error",
    ]
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    """Spec: Stable API contracts > Error semantics."""

    error: _ErrorBody
