from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends

from learn_code_api.content.models import (
    ExerciseContent,
    LessonContent,
    QuizContent,
)
from learn_code_api.contracts import (
    CheckpointDetail,
    ContentDetail,
    ContentSummary,
    LessonDetail,
    PublicTestCase,
    QuizDetail,
    QuizQuestionDetail,
)
from learn_code_api.dependencies import AppDependencies, get_deps
from learn_code_api.services import find_content

router = APIRouter(tags=["content"])

AnyContent = ExerciseContent | LessonContent | QuizContent
AnyDetail = ContentDetail | LessonDetail | QuizDetail


@router.get("/content", response_model=list[ContentSummary])
def list_content(
    kind: Literal["exercise", "lesson", "quiz"] | None = None,
    deps: AppDependencies = Depends(get_deps),
) -> list[ContentSummary]:
    items: list[AnyContent] = [
        *deps.catalog.exercises,
        *deps.catalog.lessons,
        *deps.catalog.quizzes,
    ]
    if kind is not None:
        items = [item for item in items if item.kind == kind]
    return [_to_summary(item) for item in sorted(items, key=lambda item: item.id)]


@router.get("/content/{content_id}", response_model=AnyDetail)
def content_detail(content_id: str, deps: AppDependencies = Depends(get_deps)) -> AnyDetail:
    item = find_content(deps.catalog, content_id)
    if isinstance(item, LessonContent):
        return _to_lesson_detail(item)
    if isinstance(item, QuizContent):
        return _to_quiz_detail(item)
    return _to_exercise_detail(item)


def _to_summary(item: AnyContent) -> ContentSummary:
    return ContentSummary(
        id=item.id,
        kind=item.kind,
        title=item.title,
        slug=item.slug,
        difficulty=item.difficulty.value,
        concepts=list(item.concepts),
        prerequisites=list(item.prerequisites),
        estimated_time_minutes=item.estimated_time_minutes,
    )


def _to_exercise_detail(exercise: ExerciseContent) -> ContentDetail:
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


def _to_lesson_detail(lesson: LessonContent) -> LessonDetail:
    return LessonDetail(
        id=lesson.id,
        kind="lesson",
        version=lesson.version,
        language=lesson.language,
        title=lesson.title,
        slug=lesson.slug,
        difficulty=lesson.difficulty.value,
        concepts=list(lesson.concepts),
        prerequisites=list(lesson.prerequisites),
        estimated_time_minutes=lesson.estimated_time_minutes,
        body_markdown=lesson.body_markdown,
        checkpoints=[
            CheckpointDetail(
                question=checkpoint.question,
                answer=checkpoint.answer,
                explanation=checkpoint.explanation,
            )
            for checkpoint in lesson.checkpoints
        ],
    )


def _to_quiz_detail(quiz: QuizContent) -> QuizDetail:
    return QuizDetail(
        id=quiz.id,
        kind="quiz",
        version=quiz.version,
        language=quiz.language,
        title=quiz.title,
        slug=quiz.slug,
        difficulty=quiz.difficulty.value,
        concepts=list(quiz.concepts),
        prerequisites=list(quiz.prerequisites),
        estimated_time_minutes=quiz.estimated_time_minutes,
        quiz_type=quiz.quiz_type,
        questions=[
            QuizQuestionDetail(
                id=question.id,
                prompt=question.prompt,
                choices=list(question.choices),
                concepts=list(question.concepts),
            )
            for question in quiz.questions
        ],
    )
