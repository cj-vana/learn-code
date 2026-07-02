from __future__ import annotations

from fastapi import APIRouter, Depends

from learn_code_api.contracts import LessonCompletionResponse
from learn_code_api.dependencies import AppDependencies, get_deps, get_repo
from learn_code_api.progress.db import ProgressRepository
from learn_code_api.services import find_lesson

router = APIRouter(tags=["lessons"])


@router.post("/lessons/{lesson_id}/complete", response_model=LessonCompletionResponse)
def complete_lesson(
    lesson_id: str,
    deps: AppDependencies = Depends(get_deps),
    repo: ProgressRepository = Depends(get_repo),
) -> LessonCompletionResponse:
    lesson = find_lesson(deps.catalog, lesson_id)
    event = repo.record_lesson_completed(
        lesson_id=lesson.id,
        content_version=lesson.version,
        session_id=deps.session_id,
        now=deps.clock(),
    )
    return LessonCompletionResponse(
        lesson_id=lesson.id, completed_at=event.created_at.isoformat()
    )
