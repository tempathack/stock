"""A/B model testing — traffic-weighted model selection and assignment logging."""

from __future__ import annotations

import logging
import random

from sqlalchemy import select

from app.config import settings
from app.models.database import get_async_session, get_engine
from app.models.orm import ABTestAssignment, ModelRegistry

logger = logging.getLogger(__name__)


async def select_model_for_request(horizon: int | None = None) -> dict | None:
    """Select a model via weighted random based on traffic_weight.

    Returns dict with model_id, model_name, version, traffic_weight,
    serving_path, or None if no A/B models configured.
    """
    if get_engine() is None:
        return None

    try:
        async with get_async_session() as session:
            stmt = (
                select(
                    ModelRegistry.model_id,
                    ModelRegistry.model_name,
                    ModelRegistry.version,
                    ModelRegistry.traffic_weight,
                )
                .where(ModelRegistry.is_active.is_(True))
                .where(ModelRegistry.traffic_weight > 0)
                .order_by(ModelRegistry.traffic_weight.desc())
            )
            result = await session.execute(stmt)
            rows = result.all()
    except Exception:
        logger.exception("Failed to query A/B models")
        return None

    if not rows:
        return None

    if len(rows) == 1:
        row = rows[0]
    else:
        row = random.choices(
            rows,
            weights=[float(r.traffic_weight) for r in rows],
            k=1,
        )[0]

    result = {
        "model_id": row.model_id,
        "model_name": row.model_name,
        "version": row.version,
        "traffic_weight": float(row.traffic_weight),
        "serving_path": f"/models/active/{row.model_name}_{row.version}",
    }

    # Add KServe routing info when enabled
    if settings.KSERVE_ENABLED:
        is_primary = row is rows[0] if len(rows) > 1 else True
        if is_primary:
            result["kserve_url"] = settings.KSERVE_INFERENCE_URL
            result["kserve_model_name"] = settings.KSERVE_MODEL_NAME
        else:
            result["kserve_url"] = settings.KSERVE_CANARY_URL
            result["kserve_model_name"] = "stock-model-serving-canary"

    return result


async def log_ab_assignment(
    ticker: str,
    model_id: int,
    model_name: str,
    predicted_price: float,
    horizon_days: int = 7,
) -> None:
    """Log an A/B test assignment to the database (fire-and-forget)."""
    if not settings.AB_LOG_ASSIGNMENTS or not settings.DATABASE_URL:
        return
    if get_engine() is None:
        return
    try:
        async with get_async_session() as session:
            assignment = ABTestAssignment(
                ticker=ticker,
                model_id=model_id,
                model_name=model_name,
                predicted_price=predicted_price,
                horizon_days=horizon_days,
            )
            session.add(assignment)
    except Exception:
        logger.exception("Failed to log A/B assignment for %s", ticker)


async def get_ab_active_models() -> list[dict]:
    """Return all models with traffic_weight > 0."""
    if get_engine() is None:
        return []

    try:
        async with get_async_session() as session:
            stmt = (
                select(
                    ModelRegistry.model_id,
                    ModelRegistry.model_name,
                    ModelRegistry.version,
                    ModelRegistry.traffic_weight,
                    ModelRegistry.trained_at,
                )
                .where(ModelRegistry.traffic_weight > 0)
                .order_by(ModelRegistry.traffic_weight.desc())
            )
            result = await session.execute(stmt)
            rows = result.all()
    except Exception:
        logger.exception("Failed to query A/B active models")
        return []

    return [
        {
            "model_id": r.model_id,
            "model_name": r.model_name,
            "version": r.version,
            "traffic_weight": float(r.traffic_weight),
            "trained_at": r.trained_at.isoformat() if r.trained_at else None,
        }
        for r in rows
    ]
