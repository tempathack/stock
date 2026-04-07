"""Health check router for the stock prediction API."""

from __future__ import annotations

import json
import subprocess
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.cache import get_redis
from app.config import settings
from app.models.database import get_pool_status
from app.services.health_service import check_db, run_deep_checks, run_detailed_checks


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


class DetailedDepCheck(BaseModel):
    """Per-dependency result for /health/detailed."""

    status: str
    latency_ms: float | None = None
    topic_count: int | None = None
    model_ready: bool | None = None
    message: str | None = None


class DetailedHealthResponse(BaseModel):
    """Response model for /health/detailed."""

    overall: str
    db: DetailedDepCheck
    redis: DetailedDepCheck
    kafka: DetailedDepCheck
    kserve: DetailedDepCheck


class K8sHealthResponse(BaseModel):
    """Response for Kubernetes cluster health (optional, graceful fallback)."""

    available: bool
    running_pods: int | None = None
    namespaces: list[str] = []


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


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def health_detailed() -> DetailedHealthResponse:
    """Detailed dependency health: DB+latency, Redis+latency, Kafka topic count, KServe readiness.

    Each check has a 3s timeout. overall is 'healthy' when all deps are ok/disabled,
    'degraded' when any dep reports error or warning.
    """
    result = await run_detailed_checks()
    return DetailedHealthResponse(
        overall=result["overall"],
        db=DetailedDepCheck(**result["db"]),
        redis=DetailedDepCheck(**result["redis"]),
        kafka=DetailedDepCheck(**result["kafka"]),
        kserve=DetailedDepCheck(**result["kserve"]),
    )


@router.get("/health/k8s", response_model=K8sHealthResponse)
async def health_k8s() -> K8sHealthResponse:
    """Return Kubernetes cluster health by querying kubectl.

    Returns ``available: false`` gracefully when kubectl is not installed or
    the API server is unreachable — this is an optional informational endpoint.
    """
    try:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "pods",
                "-A",
                "--field-selector=status.phase=Running",
                "-o",
                "json",
            ],
            capture_output=True,
            timeout=5,
            text=True,
        )
        if result.returncode != 0:
            return K8sHealthResponse(available=False)
        data = json.loads(result.stdout)
        pods = data.get("items", [])
        namespaces = sorted({p["metadata"]["namespace"] for p in pods})
        return K8sHealthResponse(
            available=True,
            running_pods=len(pods),
            namespaces=namespaces,
        )
    except Exception:
        return K8sHealthResponse(available=False)
