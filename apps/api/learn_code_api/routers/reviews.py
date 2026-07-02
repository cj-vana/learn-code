from __future__ import annotations

from fastapi import APIRouter, Depends

from learn_code_api.contracts import ReviewRequest
from learn_code_api.dependencies import AppDependencies, get_deps
from learn_code_api.ollama.client import OllamaReview
from learn_code_api.services.reviews import review as run_review

router = APIRouter(tags=["reviews"])


@router.post("/reviews", response_model=OllamaReview)
def create_review(
    request: ReviewRequest, deps: AppDependencies = Depends(get_deps)
) -> OllamaReview:
    return run_review(deps.catalog, deps.ollama_client, request)
