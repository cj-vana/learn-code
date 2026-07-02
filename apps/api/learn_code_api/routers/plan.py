from __future__ import annotations

from fastapi import APIRouter, Depends

from learn_code_api.adaptive_plan.planner import PlanItem
from learn_code_api.dependencies import AppDependencies, get_deps, get_repo
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.services.planning import today_plan

router = APIRouter(tags=["plan"])


@router.get("/plan", response_model=list[PlanItem])
def get_plan(
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> list[PlanItem]:
    return today_plan(deps.catalog, repo, now=deps.clock())
