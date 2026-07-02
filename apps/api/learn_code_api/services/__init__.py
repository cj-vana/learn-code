"""Wiring layer between thin routers and the Task 2-4 domain modules."""

from __future__ import annotations

from learn_code_api.content.models import (
    ContentCatalog,
    ExerciseContent,
    LessonContent,
    QuizContent,
)
from learn_code_api.errors import ContentNotFoundError


def find_exercise(catalog: ContentCatalog, exercise_id: str) -> ExerciseContent:
    for exercise in catalog.exercises:
        if exercise.id == exercise_id:
            return exercise
    raise ContentNotFoundError(
        f"no published exercise with id {exercise_id!r}",
        details={"exercise_id": exercise_id},
    )


def find_lesson(catalog: ContentCatalog, lesson_id: str) -> LessonContent:
    for lesson in catalog.lessons:
        if lesson.id == lesson_id:
            return lesson
    raise ContentNotFoundError(
        f"no published lesson with id {lesson_id!r}",
        details={"lesson_id": lesson_id},
    )


def find_quiz(catalog: ContentCatalog, quiz_id: str) -> QuizContent:
    for quiz in catalog.quizzes:
        if quiz.id == quiz_id:
            return quiz
    raise ContentNotFoundError(
        f"no published quiz with id {quiz_id!r}",
        details={"quiz_id": quiz_id},
    )


def find_content(
    catalog: ContentCatalog, content_id: str
) -> ExerciseContent | LessonContent | QuizContent:
    for pool in (catalog.exercises, catalog.lessons, catalog.quizzes):
        for item in pool:
            if item.id == content_id:
                return item
    raise ContentNotFoundError(
        f"no published content with id {content_id!r}",
        details={"content_id": content_id},
    )
