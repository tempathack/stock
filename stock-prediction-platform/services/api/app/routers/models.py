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
    FeatureDistributionEntry,
    FeatureDistributionResponse,
    HistogramBin,
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


@router.get("/comparison", response_model=ModelComparisonResponse, summary="Compare all registered models by metrics")
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


@router.get("/drift/rolling-performance", response_model=RollingPerformanceResponse, summary="Get rolling model performance metrics")
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


@router.get("/retrain-status", response_model=RetrainStatusResponse, summary="Get most recent model training status")
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


@router.get("/drift", response_model=DriftStatusResponse, summary="Get recent drift detection events")
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


@router.get("/drift/feature-distributions", response_model=FeatureDistributionResponse, summary="Get feature distribution comparison for drift monitoring")
async def drift_feature_distributions(n_features: int = 12, bins: int = 10) -> FeatureDistributionResponse:
    """Return training vs recent feature distributions for drift monitoring.

    Queries feature_store for training period (> 1 year ago) and recent period
    (last 60 days), computes histogram bins, and overlays KS/PSI stats from
    the most recent drift events.
    """
    from datetime import datetime, timedelta, timezone

    key = build_key("models", "feature-distributions", str(n_features), str(bins))
    cached = await cache_get(key)
    if cached is not None:
        return FeatureDistributionResponse(**cached)

    from app.models.database import get_async_session, get_engine  # lazy import

    if get_engine() is None:
        return FeatureDistributionResponse()

    try:
        import sqlalchemy as sa

        now = datetime.now(tz=timezone.utc)
        recent_cutoff = (now - timedelta(days=60)).date()
        training_cutoff = (now - timedelta(days=365)).date()

        # 1. Get drifted features from recent drift_logs (data_drift only)
        feature_stats: dict[str, dict] = {}
        async with get_async_session() as session:
            drift_rows = (await session.execute(sa.text("""
                SELECT details_json->'per_feature' AS per_feature
                FROM drift_logs
                WHERE drift_type = 'data_drift'
                ORDER BY detected_at DESC
                LIMIT 5
            """))).fetchall()

            for row in drift_rows:
                pf = row[0] or {}
                for feat, stats in pf.items():
                    if feat not in feature_stats:
                        feature_stats[feat] = stats

            # 2. Select features: drifted first, then fill from feature_store
            drifted = [f for f, s in feature_stats.items() if s.get("drifted")]
            stable: list[str] = []
            if len(drifted) < n_features:
                fill_rows = (await session.execute(sa.text("""
                    SELECT feature_name FROM feature_store
                    GROUP BY feature_name ORDER BY COUNT(*) DESC LIMIT :limit
                """), {"limit": n_features * 2})).fetchall()
                stable = [r[0] for r in fill_rows if r[0] not in drifted]

            selected = (drifted + stable)[:n_features]

            # 3. Compute histograms for each feature
            result_entries: list[FeatureDistributionEntry] = []
            for feature in selected:
                train_rows = (await session.execute(sa.text("""
                    SELECT feature_value FROM feature_store
                    WHERE feature_name = :fname AND date <= :cutoff
                      AND feature_value IS NOT NULL
                    ORDER BY RANDOM() LIMIT 2000
                """), {"fname": feature, "cutoff": training_cutoff})).fetchall()
                train_vals = [float(r[0]) for r in train_rows]

                recent_rows = (await session.execute(sa.text("""
                    SELECT feature_value FROM feature_store
                    WHERE feature_name = :fname AND date >= :cutoff
                      AND feature_value IS NOT NULL
                    ORDER BY date DESC LIMIT 2000
                """), {"fname": feature, "cutoff": recent_cutoff})).fetchall()
                recent_vals = [float(r[0]) for r in recent_rows]

                if not train_vals and not recent_vals:
                    continue

                all_vals = train_vals + recent_vals
                min_v, max_v = min(all_vals), max(all_vals)
                if min_v == max_v:
                    max_v = min_v + 1.0
                bin_width = (max_v - min_v) / bins
                edges = [min_v + i * bin_width for i in range(bins + 1)]

                def to_bins(vals: list[float], bw: float = bin_width, mn: float = min_v) -> list[HistogramBin]:
                    counts = [0] * bins
                    for v in vals:
                        idx = min(int((v - mn) / bw), bins - 1)
                        counts[idx] += 1
                    total = len(vals) or 1
                    return [
                        HistogramBin(
                            bin=f"{edges[i]:.2g}–{edges[i+1]:.2g}",
                            count=round(counts[i] / total * 100),
                        )
                        for i in range(bins)
                    ]

                fs = feature_stats.get(feature, {})
                result_entries.append(FeatureDistributionEntry(
                    feature=feature,
                    training_bins=to_bins(train_vals),
                    recent_bins=to_bins(recent_vals),
                    ks_stat=fs.get("ks_statistic"),
                    psi_value=fs.get("psi"),
                    is_drifted=bool(fs.get("drifted", False)),
                ))

        response = FeatureDistributionResponse(
            features=result_entries,
            training_period=f"≤ {training_cutoff.isoformat()}",
            recent_period=f"≥ {recent_cutoff.isoformat()}",
            count=len(result_entries),
        )
        await cache_set(key, response.model_dump(), DRIFT_STATUS_TTL)
        return response
    except Exception as exc:
        logger.warning("feature-distributions query failed: %s", exc)
        raise HTTPException(status_code=502, detail="Feature distribution query failed") from exc


@router.post("/cache/invalidate", summary="Invalidate prediction and model caches")
async def invalidate_cache() -> dict:
    """Invalidate prediction and model caches after retrain."""
    pred_count = await invalidate_predictions()
    model_count = await invalidate_models()
    total = pred_count + model_count
    logger.info("cache invalidated", extra={"keys_cleared": total})
    return {"invalidated_keys": total, "status": "ok"}


@router.get("/ab-results", response_model=ABResultsResponse, summary="Get A/B model testing accuracy comparison")
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
