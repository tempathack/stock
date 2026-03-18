"""Health check router for the stock prediction API."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""

    service: str
    version: str
    status: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health status for K8s liveness/readiness probes."""
    return HealthResponse(
        service=settings.SERVICE_NAME,
        version=settings.APP_VERSION,
        status="ok",
    )
