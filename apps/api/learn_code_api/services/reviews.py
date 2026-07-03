"""Optional Ollama code review orchestration.

Builds a review context from the exercise plus the learner's code and asks the
injected Ollama client. The client returns a friendly ``unavailable`` payload
when Ollama is disabled or unreachable, so this never fails the request and
never blocks an exercise (spec: Ollama code review > rules).
"""

from __future__ import annotations

from learn_code_api.contracts import ReviewRequest
from learn_code_api.content.models import ContentCatalog
from learn_code_api.ollama.client import OllamaClient, OllamaReview, ReviewContext
from learn_code_api.services import find_exercise

# The first concept is treated as the exercise's primary expected pattern.
_EXPECTED_PATTERN_INDEX = 0


def review(catalog: ContentCatalog, ollama: OllamaClient, request: ReviewRequest) -> OllamaReview:
    exercise = find_exercise(catalog, request.exercise_id)
    expected_pattern = exercise.concepts[_EXPECTED_PATTERN_INDEX] if exercise.concepts else None
    context = ReviewContext(
        exercise_prompt=exercise.prompt_markdown,
        concepts=list(exercise.concepts),
        expected_pattern=expected_pattern,
        learner_code=request.source,
        test_result_summary=request.test_result_summary,
        learner_level=exercise.difficulty.value,
        allow_solution_disclosure=request.allow_solution_disclosure,
    )
    return ollama.review(context)
