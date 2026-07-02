from __future__ import annotations

from fastapi import APIRouter, Depends

from learn_code_api.content.models import ExerciseContent
from learn_code_api.contracts import ContentDetail, ContentSummary, PublicTestCase
from learn_code_api.dependencies import AppDependencies, get_deps
from learn_code_api.services import find_exercise

router = APIRouter(tags=["content"])


@router.get("/content", response_model=list[ContentSummary])
def list_content(deps: AppDependencies = Depends(get_deps)) -> list[ContentSummary]:
    return [_to_summary(exercise) for exercise in deps.catalog.exercises]


@router.get("/content/{exercise_id}", response_model=ContentDetail)
def content_detail(
    exercise_id: str, deps: AppDependencies = Depends(get_deps)
) -> ContentDetail:
    return _to_detail(find_exercise(deps.catalog, exercise_id))


def _to_summary(exercise: ExerciseContent) -> ContentSummary:
    return ContentSummary(
        id=exercise.id,
        kind=exercise.kind,
        title=exercise.title,
        slug=exercise.slug,
        difficulty=exercise.difficulty.value,
        concepts=list(exercise.concepts),
        prerequisites=list(exercise.prerequisites),
        estimated_time_minutes=exercise.estimated_time_minutes,
    )


def _to_detail(exercise: ExerciseContent) -> ContentDetail:
    return ContentDetail(
        id=exercise.id,
        kind=exercise.kind,
        version=exercise.version,
        language=exercise.language,
        title=exercise.title,
        slug=exercise.slug,
        difficulty=exercise.difficulty.value,
        concepts=list(exercise.concepts),
        prerequisites=list(exercise.prerequisites),
        estimated_time_minutes=exercise.estimated_time_minutes,
        prompt_markdown=exercise.prompt_markdown,
        starter_code=exercise.starter_code,
        function_name=exercise.function_name,
        input_mode=exercise.input_mode,
        hints=[{"level": hint.level, "text": hint.text} for hint in exercise.hints],
        public_tests=[
            PublicTestCase(name=case.name, input=case.input, expected=case.expected)
            for case in exercise.tests.public
        ],
        common_mistakes=list(exercise.common_mistakes),
    )
