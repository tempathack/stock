"""Deep health check service — validates DB, Kafka, model freshness, prediction staleness."""

from __future__ import annotations

import asyncio
import datetime
import time
from typing import Any

from sqlalchemy import func, select, text

from app.config import settings
from app.models.database import get_async_session, get_engine
from app.models.orm import ModelRegistry, Prediction
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def check_db() -> dict[str, Any]:
    """Check database connectivity by executing SELECT 1."""
    if get_engine() is None:
        return {"status": "error", "message": "Engine not initialised"}
    try:
        async with get_async_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:
        logger.warning("health_check_db_failed", error=str(exc))
        return {"status": "error", "message": str(exc)}


async def check_kafka() -> dict[str, Any]:
    """Check Kafka broker reachability via metadata request with timeout."""
    try:
        from confluent_kafka.admin import AdminClient

        admin = AdminClient({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
        metadata = admin.list_topics(timeout=5)
        return {"status": "ok", "brokers": len(metadata.brokers)}
    except Exception as exc:
        logger.warning("health_check_kafka_failed", error=str(exc))
        return {"status": "error", "message": str(exc)}


async def check_model_freshness() -> dict[str, Any]:
    """Check that the active model was trained within the freshness threshold."""
    if get_engine() is None:
        return {"status": "warning", "message": "DB not available"}
    try:
        async with get_async_session() as session:
            result = await session.execute(
                select(func.max(ModelRegistry.trained_at)).where(
                    ModelRegistry.is_active.is_(True)
                )
            )
            latest = result.scalar_one_or_none()

        if latest is None:
            return {"status": "warning", "message": "No active model found"}

        now = datetime.datetime.now(datetime.timezone.utc)
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=datetime.timezone.utc)
        age = now - latest
        threshold = datetime.timedelta(days=settings.MODEL_FRESHNESS_THRESHOLD_DAYS)

        if age > threshold:
            return {
                "status": "warning",
                "message": f"Model stale: trained {age.days}d ago (threshold: {settings.MODEL_FRESHNESS_THRESHOLD_DAYS}d)",
                "trained_at": latest.isoformat(),
                "age_days": age.days,
            }
        return {"status": "ok", "trained_at": latest.isoformat(), "age_days": age.days}
    except Exception as exc:
        logger.warning("health_check_model_freshness_failed", error=str(exc))
        return {"status": "error", "message": str(exc)}


async def check_prediction_staleness() -> dict[str, Any]:
    """Check that the most recent prediction was generated within the staleness threshold."""
    if get_engine() is None:
        return {"status": "warning", "message": "DB not available"}
    try:
        async with get_async_session() as session:
            result = await session.execute(
                select(func.max(Prediction.created_at))
            )
            latest = result.scalar_one_or_none()

        if latest is None:
            return {"status": "warning", "message": "No predictions found"}

        now = datetime.datetime.now(datetime.timezone.utc)
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=datetime.timezone.utc)
        age = now - latest
        threshold = datetime.timedelta(hours=settings.PREDICTION_STALENESS_HOURS)

        if age > threshold:
            return {
                "status": "warning",
                "message": f"Predictions stale: last {age.total_seconds() / 3600:.1f}h ago (threshold: {settings.PREDICTION_STALENESS_HOURS}h)",
                "last_prediction_at": latest.isoformat(),
                "age_hours": round(age.total_seconds() / 3600, 1),
            }
        return {
            "status": "ok",
            "last_prediction_at": latest.isoformat(),
            "age_hours": round(age.total_seconds() / 3600, 1),
        }
    except Exception as exc:
        logger.warning("health_check_prediction_staleness_failed", error=str(exc))
        return {"status": "error", "message": str(exc)}


async def run_deep_checks() -> dict[str, Any]:
    """Run all health checks and compute overall status.

    Returns:
        Dict with ``status`` (ok | degraded | unhealthy) and per-component results.
    """
    db = await check_db()
    kafka = await check_kafka()
    model = await check_model_freshness()
    predictions = await check_prediction_staleness()

    components = {
        "database": db,
        "kafka": kafka,
        "model_freshness": model,
        "prediction_staleness": predictions,
    }

    statuses = [c["status"] for c in components.values()]

    if db["status"] == "error":
        overall = "unhealthy"
    elif any(s == "error" for s in statuses) or any(s == "warning" for s in statuses):
        overall = "degraded"
    else:
        overall = "ok"

    return {"status": overall, "components": components}


# ── /health/detailed helpers ─────────────────────────────────────────────────

async def check_db_detailed() -> dict[str, Any]:
    """Check DB connectivity with latency measurement, max 3s timeout."""
    if get_engine() is None:
        return {"status": "error", "message": "Engine not initialised", "latency_ms": None}
    try:
        t0 = time.monotonic()
        async with asyncio.timeout(3.0):
            async with get_async_session() as session:
                await session.execute(text("SELECT 1"))
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "latency_ms": None}


async def check_redis_detailed() -> dict[str, Any]:
    """Check Redis connectivity with latency measurement, max 3s timeout."""
    from app.cache import get_redis  # lazy to avoid circular import
    client = get_redis()
    if client is None:
        return {"status": "disabled", "latency_ms": None}
    try:
        t0 = time.monotonic()
        async with asyncio.timeout(3.0):
            await client.ping()
        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "latency_ms": None}


async def check_kafka_detailed() -> dict[str, Any]:
    """Check Kafka with topic count, max 3s timeout."""
    try:
        async with asyncio.timeout(3.0):
            from confluent_kafka.admin import AdminClient  # noqa: PLC0415
            admin = AdminClient({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
            metadata = admin.list_topics(timeout=2)
        topic_count = len([t for t in metadata.topics if not t.startswith("__")])
        return {"status": "ok", "topic_count": topic_count}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "topic_count": None}


async def check_kserve_detailed() -> dict[str, Any]:
    """Check KServe InferenceService readiness, max 3s timeout."""
    if not settings.KSERVE_ENABLED or not settings.KSERVE_INFERENCE_URL:
        return {"status": "disabled", "model_ready": False}
    try:
        import httpx  # noqa: PLC0415
        async with asyncio.timeout(3.0):
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.KSERVE_INFERENCE_URL.rstrip('/')}/v2/health/ready",
                    timeout=2.5,
                )
        model_ready = resp.status_code == 200
        return {"status": "ok" if model_ready else "degraded", "model_ready": model_ready}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "model_ready": False}


async def run_detailed_checks() -> dict[str, Any]:
    """Run all /health/detailed checks concurrently."""
    db, redis, kafka, kserve = await asyncio.gather(
        check_db_detailed(),
        check_redis_detailed(),
        check_kafka_detailed(),
        check_kserve_detailed(),
    )

    statuses = [db["status"], redis["status"], kafka["status"], kserve["status"]]
    if any(s == "error" for s in statuses):
        overall = "degraded"
    elif any(s == "warning" for s in statuses):
        overall = "degraded"
    else:
        overall = "healthy"

    return {
        "overall": overall,
        "db": db,
        "redis": redis,
        "kafka": kafka,
        "kserve": kserve,
    }
