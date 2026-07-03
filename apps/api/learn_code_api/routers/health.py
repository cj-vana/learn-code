from __future__ import annotations

from fastapi import APIRouter

from learn_code_api import update_check
from learn_code_api.contracts import HealthResponse, UpdateStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/update", response_model=UpdateStatus)
def update() -> UpdateStatus:
    latest = update_check.latest_version()
    return UpdateStatus(
        current_version=update_check.CURRENT_VERSION,
        latest_version=latest,
        update_available=update_check.update_available(latest),
    )
