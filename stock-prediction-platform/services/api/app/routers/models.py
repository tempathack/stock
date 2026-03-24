"""Models router — /models/comparison, /models/drift, and /models/ab-results endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from app.cache import (
    DRIFT_STATUS_TTL,
    MODEL_COMPARISON_TTL,
    build_key,
    cache_get,
    cache_set,
    invalidate_models,
    invalidate_predictions,
)
from app.config import settings
from app.models.schemas import (
    ABResultsModelEntry,
    ABResultsResponse,
    DriftEventEntry,
    DriftStatusResponse,
    ModelComparisonEntry,
    ModelComparisonResponse,
    RetrainStatusResponse,
    RollingPerformanceResponse,
    RollingPerfEntry,
)
from app.services.prediction_service import (
    get_retrain_status_from_db,
    load_ab_results_from_db,
    load_drift_events,
    load_drift_events_from_db,
    load_model_comparison,
    load_model_comparison_from_db,
    load_rolling_performance_from_db,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/comparison", response_model=ModelComparisonResponse)
async def models_comparison() -> ModelComparisonResponse:
    """Return model metrics comparison sorted by OOS RMSE.

    Queries model_registry table when DB engine is available;
    falls back to file-based model registry.
    """
    key = build_key("models", "comparison")
    cached = await cache_get(key)
    if cached is not None:
        return ModelComparisonResponse(**cached)

    # Try DB first
    raw_models = await load_model_comparison_from_db()

    # Fallback to file-based registry
    if raw_models is None:
        logger.info("DB unavailable for models comparison — using file registry")
        raw_models = load_model_comparison(registry_dir=settings.MODEL_REGISTRY_DIR)

    entries = [
        ModelComparisonEntry(
            model_name=m.get("model_name", "unknown"),
            scaler_variant=m.get("scaler_variant", "unknown"),
            version=m.get("version"),
            is_winner=m.get("is_winner", False),
            is_active=m.get("is_active", False),
            traffic_weight=m.get("traffic_weight", 0.0),
            oos_metrics=m.get("oos_metrics", {}),
            fold_stability=m.get("fold_stability"),
            best_params=m.get("best_params", {}),
            saved_at=m.get("saved_at"),
        )
        for m in raw_models
    ]
    winner = next((e for e in entries if e.is_winner), None)
    response = ModelComparisonResponse(
        models=entries,
        winner=winner,
        count=len(entries),
    )
    await cache_set(key, response.model_dump(), MODEL_COMPARISON_TTL)
    return response


@router.get("/drift/rolling-performance", response_model=RollingPerformanceResponse)
async def drift_rolling_performance(days: int = 30) -> RollingPerformanceResponse:
    """Return rolling prediction error metrics for the active model."""
    key = build_key("models", "rolling-perf", str(days))
    cached = await cache_get(key)
    if cached is not None:
        return RollingPerformanceResponse(**cached)

    result = await load_rolling_performance_from_db(days=days)
    if result is None:
        return RollingPerformanceResponse(entries=[], count=0)

    entries = [RollingPerfEntry(**e) for e in result.get("entries", [])]
    response = RollingPerformanceResponse(
        entries=entries,
        model_name=result.get("model_name"),
        period_days=days,
        count=len(entries),
    )
    await cache_set(key, response.model_dump(), DRIFT_STATUS_TTL)
    return response


@router.get("/retrain-status", response_model=RetrainStatusResponse)
async def retrain_status() -> RetrainStatusResponse:
    """Return metadata about the most recent model training event."""
    key = build_key("models", "retrain-status")
    cached = await cache_get(key)
    if cached is not None:
        return RetrainStatusResponse(**cached)

    result = await get_retrain_status_from_db()
    if result is None:
        return RetrainStatusResponse()
    response = RetrainStatusResponse(**result)
    await cache_set(key, response.model_dump(), DRIFT_STATUS_TTL)
    return response


@router.get("/drift", response_model=DriftStatusResponse)
async def models_drift() -> DriftStatusResponse:
    """Return recent drift detection events.

    Queries drift_logs table when DB engine is available;
    falls back to file-based JSONL drift log.
    """
    key = build_key("models", "drift")
    cached = await cache_get(key)
    if cached is not None:
        return DriftStatusResponse(**cached)

    # Try DB first
    raw_events = await load_drift_events_from_db()

    # Fallback to file-based drift log
    if raw_events is None:
        logger.info("DB unavailable for drift events — using file log")
        raw_events = load_drift_events(log_dir=settings.DRIFT_LOG_DIR)

    events = [
        DriftEventEntry(
            drift_type=e.get("drift_type", "unknown"),
            is_drifted=e.get("is_drifted", False),
            severity=e.get("severity", "none"),
            details=e.get("details", {}),
            timestamp=e.get("timestamp"),
            features_affected=e.get("features_affected", []),
        )
        for e in raw_events
    ]
    any_recent = any(e.is_drifted for e in events)
    latest = events[0] if events else None
    response = DriftStatusResponse(
        events=events,
        any_recent_drift=any_recent,
        latest_event=latest,
        count=len(events),
    )
    await cache_set(key, response.model_dump(), DRIFT_STATUS_TTL)
    return response


@router.post("/cache/invalidate")
async def invalidate_cache() -> dict:
    """Invalidate prediction and model caches after retrain."""
    pred_count = await invalidate_predictions()
    model_count = await invalidate_models()
    total = pred_count + model_count
    logger.info("cache invalidated", extra={"keys_cleared": total})
    return {"invalidated_keys": total, "status": "ok"}


@router.get("/ab-results", response_model=ABResultsResponse)
async def ab_results(request: Request, days: int = 30) -> ABResultsResponse:
    """Return A/B model testing accuracy comparison."""
    if not settings.AB_TESTING_ENABLED:
        raise HTTPException(status_code=404, detail="A/B testing is not enabled")

    data = await load_ab_results_from_db(days)
    if data is None:
        raise HTTPException(status_code=503, detail="A/B results unavailable")

    # Enrich with current traffic weights
    from app.services.ab_service import get_ab_active_models

    active = await get_ab_active_models()
    weight_map = {m["model_id"]: m for m in active}

    models = []
    for m in data["models"]:
        entry = ABResultsModelEntry(
            model_id=m["model_id"],
            model_name=m["model_name"],
            traffic_weight=weight_map.get(m["model_id"], {}).get("traffic_weight", 0.0),
            version=weight_map.get(m["model_id"], {}).get("version"),
            n_assignments=m["n_assignments"],
            n_evaluated=m["n_evaluated"],
            mae=m.get("mae"),
            rmse=m.get("rmse"),
            directional_accuracy=m.get("directional_accuracy"),
        )
        models.append(entry)

    return ABResultsResponse(
        models=models,
        total_assignments=data["total_assignments"],
        total_evaluated=data["total_evaluated"],
        period_start=data.get("period_start"),
        period_end=data.get("period_end"),
    )
