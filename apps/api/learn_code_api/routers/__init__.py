"""Combines the endpoint routers under a single ``/api/v1`` router."""

from __future__ import annotations

from fastapi import APIRouter

from learn_code_api.routers import (
    content,
    exercises,
    health,
    plan,
    progress,
    quizzes,
    reviews,
    runs,
)

api_router = APIRouter(prefix="/api/v1")
for module in (health, content, plan, progress, exercises, runs, quizzes, reviews):
    api_router.include_router(module.router)
