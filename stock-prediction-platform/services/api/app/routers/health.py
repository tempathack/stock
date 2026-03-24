"""Health check router for the stock prediction API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.cache import get_redis
from app.config import settings
from app.models.database import get_pool_status
from app.services.health_service import check_db, run_deep_checks


class PoolStatus(BaseModel):
    """Connection pool metrics."""

    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: str


class ComponentCheck(BaseModel):
    """Result of a single component health check."""

    status: str
    message: str | None = None
    trained_at: str | None = None
    age_days: int | None = None
    last_prediction_at: str | None = None
    age_hours: float | None = None
    brokers: int | None = None


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""

    service: str
    version: str
    status: str
    db_pool: PoolStatus | None = None
    redis_status: str | None = None


class DeepHealthResponse(BaseModel):
    """Response model for the deep health check endpoint."""

    service: str
    version: str
    status: str
    components: dict[str, ComponentCheck]
    db_pool: PoolStatus | None = None
    redis_status: str | None = None


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return service health status for K8s liveness/readiness probes.

    Returns ``degraded`` when DB is unreachable, ``ok`` otherwise.
    """
    pool = get_pool_status()

    redis_status = "disabled"
    client = get_redis()
    if client is not None:
        try:
            await client.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"

    # Determine status: degraded if DB is down
    db_result = await check_db()
    status = "ok" if db_result["status"] == "ok" else "degraded"

    return HealthResponse(
        service=settings.SERVICE_NAME,
        version=settings.APP_VERSION,
        status=status,
        db_pool=PoolStatus(**pool) if pool else None,
        redis_status=redis_status,
    )


@router.get("/health/deep", response_model=DeepHealthResponse)
async def health_deep() -> DeepHealthResponse:
    """Comprehensive health check: DB, Kafka, model freshness, prediction staleness."""
    pool = get_pool_status()

    redis_status = "disabled"
    client = get_redis()
    if client is not None:
        try:
            await client.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"

    result = await run_deep_checks()

    components = {
        name: ComponentCheck(**data)
        for name, data in result["components"].items()
    }

    return DeepHealthResponse(
        service=settings.SERVICE_NAME,
        version=settings.APP_VERSION,
        status=result["status"],
        components=components,
        db_pool=PoolStatus(**pool) if pool else None,
        redis_status=redis_status,
    )
