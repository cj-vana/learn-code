from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, model_validator


class ReviewStatus(StrEnum):
    BRIEFED = "briefed"
    DRAFTED = "drafted"
    REVIEWED_ORIGINALITY = "reviewed_originality"
    REVIEWED_PEDAGOGY = "reviewed_pedagogy"
    REVIEWED_CORRECTNESS = "reviewed_correctness"
    TESTS_VALIDATED = "tests_validated"
    PUBLISHED = "published"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class HintContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: int = Field(ge=1, le=3)
    text: str = Field(min_length=1)


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brief_id: str = Field(min_length=1)
    author: str = Field(min_length=1)
    generated_at: datetime
    inspiration_sources: list[str] = Field(default_factory=list)
    originality_notes: str = Field(min_length=1)


class FunctionTestCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    input: Any
    expected: Any


class ExerciseTests(BaseModel):
    model_config = ConfigDict(extra="forbid")

    public: list[FunctionTestCase]
    validation: list[FunctionTestCase]


class ExerciseContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    kind: Literal["exercise"]
    version: PositiveInt
    language: Literal["python"]
    title: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    difficulty: Difficulty
    concepts: list[str] = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    estimated_time_minutes: PositiveInt
    review_status: ReviewStatus
    source_status: Literal["original"]
    provenance: Provenance
    prompt_markdown: str = Field(min_length=1)
    starter_code: str = Field(min_length=1)
    function_name: str = Field(min_length=1)
    input_mode: Literal["function"]
    solution_sketch: str = Field(min_length=1)
    sample_solution: str = Field(min_length=1)
    hints: list[HintContent] = Field(min_length=1)
    tests: ExerciseTests
    explanation_markdown: str = Field(min_length=1)
    common_mistakes: list[str] = Field(default_factory=list)


class Checkpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    explanation: str = Field(min_length=1)


class LessonContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    kind: Literal["lesson"]
    version: PositiveInt
    language: Literal["python"]
    title: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    difficulty: Difficulty
    concepts: list[str] = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    estimated_time_minutes: PositiveInt
    review_status: ReviewStatus
    source_status: Literal["original"]
    provenance: Provenance
    body_markdown: str = Field(min_length=1)
    checkpoints: list[Checkpoint] = Field(min_length=1)


class QuizQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    choices: list[str] = Field(min_length=2)
    correct_choice: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    concepts: list[str] = Field(default_factory=list)


class QuizContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    kind: Literal["quiz"]
    version: PositiveInt
    language: Literal["python"]
    title: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    difficulty: Difficulty
    concepts: list[str] = Field(min_length=1)
    prerequisites: list[str] = Field(default_factory=list)
    estimated_time_minutes: PositiveInt
    review_status: ReviewStatus
    source_status: Literal["original"]
    provenance: Provenance
    quiz_type: Literal["pattern_recognition", "syntax", "mixed_review"]
    questions: list[QuizQuestion] = Field(min_length=1)


class PathUnit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    items: list[str] = Field(min_length=1)
    # Optional milestone label shown when the learner finishes this unit —
    # long career paths mark section boundaries so progress has waypoints.
    milestone: str | None = None


class PathContent(BaseModel):
    """A curated, ordered curriculum over existing lesson/quiz/exercise ids."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    kind: Literal["path"]
    path_type: Literal["career", "skill"]
    version: PositiveInt
    language: Literal["python"]
    title: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    description: str = Field(min_length=1)
    outcomes: list[str] = Field(min_length=1)
    estimated_hours: PositiveInt
    review_status: ReviewStatus
    source_status: Literal["original"]
    provenance: Provenance
    units: list[PathUnit] = Field(min_length=1)

    @model_validator(mode="after")
    def _reject_duplicate_items(self) -> "PathContent":
        seen: set[str] = set()
        for unit in self.units:
            for item_id in unit.items:
                if item_id in seen:
                    raise ValueError(f"duplicate path item: {item_id}")
                seen.add(item_id)
        return self


class ContentCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exercises: list[ExerciseContent]
    lessons: list[LessonContent] = Field(default_factory=list)
    quizzes: list[QuizContent] = Field(default_factory=list)
    paths: list[PathContent] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    message: str
    severity: Literal["error", "warning"] = "error"


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    catalog: ContentCatalog | None = None
