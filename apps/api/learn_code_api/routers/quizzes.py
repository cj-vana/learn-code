from __future__ import annotations

from fastapi import APIRouter, Depends

from learn_code_api.contracts import QuizAnswerRequest, QuizAnswerResponse
from learn_code_api.dependencies import AppDependencies, get_deps, get_repo
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.services.submissions import answer_quiz

router = APIRouter(tags=["quizzes"])


@router.post("/quizzes/answer", response_model=QuizAnswerResponse)
def quiz_answer(
    request: QuizAnswerRequest,
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> QuizAnswerResponse:
    return answer_quiz(deps.catalog, repo, request, session_id=deps.session_id, now=deps.clock())
