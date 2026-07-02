from __future__ import annotations

from pathlib import Path

import pytest

from learn_code_api.content.loader import load_catalog
from learn_code_api.content.models import LessonContent, QuizContent
from learn_code_api.errors import ContentNotFoundError
from learn_code_api.services import find_content, find_lesson, find_quiz

REPO_ROOT = Path(__file__).resolve().parents[4]
CATALOG = load_catalog(REPO_ROOT / "content" / "python")

LESSON_ID = CATALOG.lessons[0].id
QUIZ_ID = CATALOG.quizzes[0].id
EXERCISE_ID = CATALOG.exercises[0].id


def test_find_lesson_returns_lesson():
    lesson = find_lesson(CATALOG, LESSON_ID)
    assert isinstance(lesson, LessonContent)
    assert lesson.id == LESSON_ID


def test_find_quiz_returns_quiz():
    quiz = find_quiz(CATALOG, QUIZ_ID)
    assert isinstance(quiz, QuizContent)
    assert quiz.id == QUIZ_ID


def test_find_lesson_missing_raises():
    with pytest.raises(ContentNotFoundError):
        find_lesson(CATALOG, "lesson.does-not-exist")


def test_find_quiz_missing_raises():
    with pytest.raises(ContentNotFoundError):
        find_quiz(CATALOG, "quiz.does-not-exist")


def test_find_content_dispatches_across_kinds():
    assert find_content(CATALOG, EXERCISE_ID).kind == "exercise"
    assert find_content(CATALOG, LESSON_ID).kind == "lesson"
    assert find_content(CATALOG, QUIZ_ID).kind == "quiz"


def test_find_content_missing_raises():
    with pytest.raises(ContentNotFoundError):
        find_content(CATALOG, "nope")
