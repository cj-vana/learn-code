from __future__ import annotations

from fastapi import APIRouter, Depends

from learn_code_api.contracts import PathDetail, PathEnrollmentResponse, PathSummary
from learn_code_api.dependencies import AppDependencies, get_deps, get_repo
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.services import find_path
from learn_code_api.services.paths import completed_content_ids, path_detail, path_summary

router = APIRouter(tags=["paths"])


@router.get("/paths", response_model=list[PathSummary])
def list_paths(
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> list[PathSummary]:
    completed = completed_content_ids(deps.catalog, repo)
    active = repo.active_path_id()
    return [
        path_summary(path_content, completed=completed, active_path_id=active)
        for path_content in sorted(deps.catalog.paths, key=lambda item: item.id)
    ]


@router.get("/paths/{path_id}", response_model=PathDetail)
def get_path(
    path_id: str,
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> PathDetail:
    path_content = find_path(deps.catalog, path_id)
    completed = completed_content_ids(deps.catalog, repo)
    return path_detail(
        path_content,
        deps.catalog,
        completed=completed,
        active_path_id=repo.active_path_id(),
    )


@router.post("/paths/{path_id}/enroll", response_model=PathEnrollmentResponse)
def enroll(
    path_id: str,
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> PathEnrollmentResponse:
    path_content = find_path(deps.catalog, path_id)
    repo.record_path_enrolled(path_id=path_content.id, session_id=deps.session_id, now=deps.clock())
    return PathEnrollmentResponse(path_id=path_content.id, enrolled=True)


@router.post("/paths/{path_id}/unenroll", response_model=PathEnrollmentResponse)
def unenroll(
    path_id: str,
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> PathEnrollmentResponse:
    path_content = find_path(deps.catalog, path_id)
    repo.record_path_unenrolled(
        path_id=path_content.id, session_id=deps.session_id, now=deps.clock()
    )
    return PathEnrollmentResponse(path_id=path_content.id, enrolled=False)
