from __future__ import annotations

from fastapi import APIRouter, Depends

from learn_code_api.contracts import PlaygroundRunRequest, RunResult
from learn_code_api.dependencies import AppDependencies, get_deps
from learn_code_api.services.runs import playground_run

router = APIRouter(tags=["runs"])


@router.post("/runs", response_model=RunResult)
def run_playground(
    request: PlaygroundRunRequest, deps: AppDependencies = Depends(get_deps)
) -> RunResult:
    return playground_run(deps.runner_client, request)
