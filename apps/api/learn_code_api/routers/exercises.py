from __future__ import annotations

from fastapi import APIRouter, Depends

from learn_code_api.contracts import (
    ExerciseSubmissionRequest,
    PublicRunRequest,
    RunResult,
    SubmissionResponse,
)
from learn_code_api.dependencies import AppDependencies, get_deps, get_repo
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.services.runs import public_run
from learn_code_api.services.submissions import submit_exercise

router = APIRouter(tags=["exercises"])


@router.post("/exercises/run", response_model=RunResult)
def run_public(
    request: PublicRunRequest, deps: AppDependencies = Depends(get_deps)
) -> RunResult:
    return public_run(deps.catalog, deps.runner_client, request)


@router.post("/exercises/submit", response_model=SubmissionResponse)
def submit(
    request: ExerciseSubmissionRequest,
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> SubmissionResponse:
    return submit_exercise(
        deps.catalog,
        repo,
        deps.runner_client,
        request,
        session_id=deps.session_id,
        now=deps.clock(),
    )
