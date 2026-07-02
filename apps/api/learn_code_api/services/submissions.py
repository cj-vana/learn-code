"""Progress-recording actions: exercise submission and quiz answers.

The API is the only SQLite writer. An exercise submission runs the validation
profile on the runner-broker, records an ``ExerciseSubmitted`` event, and
reports the real mastery delta read from the rollups before and after. If the
runner is unreachable the submission is not recorded -- the status cannot be
graded, so ``RunnerUnavailableError`` propagates to the ``runner_unavailable``
envelope.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from learn_code_api.contracts import (
    ExerciseSubmissionRequest,
    ProgressDelta,
    QuizAnswerRequest,
    QuizAnswerResponse,
    SubmissionResponse,
)
from learn_code_api.content.models import ContentCatalog
from learn_code_api.errors import ContentNotFoundError
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.progress.events import EventType, ProgressEvent, new_event_id
from learn_code_api.runner_broker.client import (
    RunMode,
    RunnerClient,
    RunnerRequest,
    TestProfile,
)
from learn_code_api.services import find_exercise, find_quiz
from learn_code_api.services.runs import to_run_result


def submit_exercise(
    catalog: ContentCatalog,
    repo: ProgressRepository,
    runner: RunnerClient,
    request: ExerciseSubmissionRequest,
    *,
    session_id: str,
    now: datetime,
) -> SubmissionResponse:
    exercise = find_exercise(catalog, request.exercise_id)

    runner_request = RunnerRequest(
        correlation_id=str(uuid4()),
        mode=RunMode.EXERCISE_TESTS,
        language="python",
        source=request.source,
        exercise_id=exercise.id,
        test_profile=TestProfile.VALIDATION,
    )
    # Raises RunnerUnavailableError if the broker is unreachable; nothing is
    # recorded in that case.
    run = runner.run(runner_request)

    before = repo.concept_mastery_map()
    event = repo.record_exercise_submission(
        exercise_id=exercise.id,
        content_version=exercise.version,
        concepts=list(exercise.concepts),
        status=run.status.value,
        session_id=session_id,
        now=now,
        confidence=request.confidence,
        predicted_pattern=request.predicted_pattern,
        hints_used=request.hints_used,
    )
    after = repo.concept_mastery_map()
    review_due = repo.review_due_map()

    concepts_changed = [
        concept for concept in exercise.concepts if after.get(concept, 0) != before.get(concept, 0)
    ]
    due_dates = [review_due[c] for c in exercise.concepts if c in review_due]
    review_due_at = min(due_dates).isoformat() if due_dates else None

    delta = ProgressDelta(
        concepts_changed=concepts_changed,
        mastery_before=_aggregate_mastery(before, exercise.concepts),
        mastery_after=_aggregate_mastery(after, exercise.concepts),
        review_due_at=review_due_at,
    )
    next_action = repo.summary(now=now).next_recommended_action
    return SubmissionResponse(
        submission_id=event.id,
        run=to_run_result(run),
        progress_delta=delta,
        next_actions=[next_action],
    )


def answer_quiz(
    catalog: ContentCatalog,
    repo: ProgressRepository,
    request: QuizAnswerRequest,
    *,
    session_id: str,
    now: datetime,
) -> QuizAnswerResponse:
    quiz = find_quiz(catalog, request.quiz_id)
    question = next(
        (item for item in quiz.questions if item.id == request.question_id), None
    )
    if question is None:
        raise ContentNotFoundError(
            f"quiz {quiz.id!r} has no question {request.question_id!r}",
            details={"quiz_id": quiz.id, "question_id": request.question_id},
        )

    correct = request.choice == question.correct_choice
    concepts = list(question.concepts) if question.concepts else list(quiz.concepts)

    before = repo.concept_mastery_map()
    repo.append_event(
        ProgressEvent(
            id=new_event_id(),
            type=EventType.QUIZ_ANSWERED,
            created_at=now,
            content_id=quiz.id,
            content_version=quiz.version,
            language="python",
            session_id=session_id,
            payload={
                "question_id": question.id,
                "correct": correct,
                "concepts": concepts,
            },
        )
    )
    after = repo.concept_mastery_map()
    review_due = repo.review_due_map()

    concepts_changed = [
        concept for concept in concepts if after.get(concept, 0) != before.get(concept, 0)
    ]
    due_dates = [review_due[c] for c in concepts if c in review_due]
    next_review_due_at = min(due_dates).isoformat() if due_dates else None

    return QuizAnswerResponse(
        question_id=question.id,
        correct=correct,
        explanation=question.explanation,
        concepts_changed=concepts_changed,
        next_review_due_at=next_review_due_at,
    )


def _aggregate_mastery(mastery_map: dict[str, int], concepts: list[str]) -> int:
    """Single mastery number for an exercise = mean mastery across its concepts.

    Matches the ``mastery_before``/``mastery_after`` scalar in the submission
    contract while reflecting the real per-concept rollup state.
    """
    if not concepts:
        return 0
    return round(sum(mastery_map.get(concept, 0) for concept in concepts) / len(concepts))
