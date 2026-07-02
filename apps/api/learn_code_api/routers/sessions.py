from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends

from learn_code_api.contracts import TimedSessionRequest, TimedSessionResponse
from learn_code_api.dependencies import AppDependencies, get_deps, get_repo
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.services.timed import select_timed_exercises

router = APIRouter(tags=["sessions"])


@router.post("/sessions/timed", response_model=TimedSessionResponse)
def create_timed_session(
    request: TimedSessionRequest,
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> TimedSessionResponse:
    exercises = select_timed_exercises(
        deps.catalog,
        repo,
        concept_filter=request.concept_filter,
        count=request.count,
    )
    return TimedSessionResponse(
        session_id=str(uuid4()),
        minutes_per_problem=request.minutes_per_problem,
        exercises=exercises,
    )
