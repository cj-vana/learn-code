from __future__ import annotations

from fastapi import APIRouter, Depends

from learn_code_api.dependencies import AppDependencies, get_deps, get_repo
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.progress.rollups import ProgressSummary

router = APIRouter(tags=["progress"])


@router.get("/progress", response_model=ProgressSummary)
def get_progress(
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> ProgressSummary:
    return repo.summary(now=deps.clock())
