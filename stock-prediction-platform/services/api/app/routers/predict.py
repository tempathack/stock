"""Prediction router — /predict/{ticker}, /predict/bulk, /predict/horizons endpoints."""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException, Query

from app.cache import (
    BULK_PREDICTIONS_TTL,
    HORIZONS_TTL,
    SINGLE_PREDICTION_TTL,
    build_key,
    cache_get,
    cache_set,
)
from app.config import settings
from app.metrics import (
    model_inference_errors_total,
    prediction_latency_seconds,
    prediction_requests_total,
)
from app.models.schemas import (
    AvailableHorizonsResponse,
    BulkPredictionResponse,
    PredictionResponse,
)
from app.services.prediction_service import (
    get_bulk_live_predictions,
    get_live_prediction,
    get_prediction_for_ticker,
    load_available_horizons,
    load_cached_predictions,
    load_db_predictions,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["predictions"])


def _validate_horizon(horizon: int | None) -> None:
    """Raise 400 if horizon is not in the allowed list."""
    if horizon is not None and horizon not in settings.available_horizons_list:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid horizon {horizon}. Available: {settings.available_horizons_list}",
        )


@router.get("/horizons", response_model=AvailableHorizonsResponse)
async def predict_horizons() -> AvailableHorizonsResponse:
    """Return available prediction horizons."""
    key = build_key("predict", "horizons")
    cached = await cache_get(key)
    if cached is not None:
        return AvailableHorizonsResponse(**cached)

    data = load_available_horizons(serving_dir=settings.SERVING_DIR)
    response = AvailableHorizonsResponse(**data)
    await cache_set(key, response.model_dump(), HORIZONS_TTL)
    return response


@router.get("/bulk", response_model=BulkPredictionResponse)
async def predict_bulk(
    horizon: int | None = Query(default=None, description="Prediction horizon in days"),
) -> BulkPredictionResponse:
    """Return forecasts for all available tickers.

    Tries live inference first; falls back to cached predictions file.
    """
    _validate_horizon(horizon)
    tickers = [t.strip() for t in settings.TICKER_SYMBOLS.split(",") if t.strip()]

    # A/B model selection (same model for all tickers in bulk request)
    ab_model = None
    if settings.AB_TESTING_ENABLED:
        from app.services.ab_service import select_model_for_request

        ab_model = await select_model_for_request(horizon)

    # Check Redis cache first
    cache_key = build_key("predict", "bulk", str(horizon or settings.DEFAULT_HORIZON))
    cached = await cache_get(cache_key)
    if cached is not None:
        prediction_requests_total.labels(ticker="bulk", model="cached", status="cached").inc()
        return BulkPredictionResponse(**cached)

    # Attempt live inference
    start = time.monotonic()
    try:
        predictions = await get_bulk_live_predictions(
            tickers=tickers,
            serving_dir=settings.SERVING_DIR,
            horizon=horizon,
            ab_model=ab_model,
        )
    except Exception as exc:
        model_inference_errors_total.labels(
            ticker="bulk", error_type=type(exc).__name__,
        ).inc()
        raise
    duration = time.monotonic() - start

    status = "success"
    # Fallback to cached predictions
    if predictions is None:
        logger.info("Live bulk inference unavailable — using cached predictions")
        raw = load_cached_predictions(
            registry_dir=settings.MODEL_REGISTRY_DIR,
            horizon=horizon,
        )
        predictions = raw if raw else None
        status = "cached"

    # Last-resort DB fallback — serve stored predictions
    if not predictions:
        logger.info("File-based predictions unavailable — querying DB predictions table")
        predictions = await load_db_predictions(horizon=horizon)
        if predictions:
            status = "db_fallback"

    if not predictions:
        prediction_requests_total.labels(
            ticker="bulk", model="none", status="error",
        ).inc()
        raise HTTPException(
            status_code=404,
            detail="No predictions available. Run the training pipeline first.",
        )

    model_name = predictions[0].get("model_name") if predictions else None
    prediction_requests_total.labels(
        ticker="bulk", model=model_name or "unknown", status=status,
    ).inc()
    prediction_latency_seconds.labels(
        ticker="bulk", model=model_name or "unknown",
    ).observe(duration)

    response = BulkPredictionResponse(
        predictions=[PredictionResponse(**p) for p in predictions],
        model_name=model_name,
        generated_at=predictions[0].get("prediction_date") if predictions else None,
        count=len(predictions),
        horizon_days=horizon,
    )
    await cache_set(cache_key, response.model_dump(), BULK_PREDICTIONS_TTL)
    return response



@router.get("/{ticker}", response_model=PredictionResponse)
async def predict_ticker(
    ticker: str,
    horizon: int | None = Query(default=None, description="Prediction horizon in days"),
) -> PredictionResponse:
    """Return prediction for a single ticker.

    Tries live inference first; falls back to cached prediction.
    """
    _validate_horizon(horizon)

    # A/B model selection
    ab_model = None
    if settings.AB_TESTING_ENABLED:
        from app.services.ab_service import select_model_for_request

        ab_model = await select_model_for_request(horizon)

    # Check Redis cache first
    cache_key = build_key("predict", ticker.upper(), str(horizon or settings.DEFAULT_HORIZON))
    cached = await cache_get(cache_key)
    if cached is not None:
        prediction_requests_total.labels(ticker=ticker.upper(), model="cached", status="cached").inc()
        return PredictionResponse(**cached)

    # Attempt live inference
    start = time.monotonic()
    try:
        pred = await get_live_prediction(
            ticker=ticker,
            serving_dir=settings.SERVING_DIR,
            horizon=horizon,
            ab_model=ab_model,
        )
    except Exception as exc:
        model_inference_errors_total.labels(
            ticker=ticker.upper(), error_type=type(exc).__name__,
        ).inc()
        raise
    duration = time.monotonic() - start

    status = "success"
    model_name = pred.get("model_name") if pred else None

    # Fallback to cached prediction
    if pred is None:
        logger.info("Live inference unavailable for %s — using cached", ticker.upper())
        pred = get_prediction_for_ticker(
            ticker, registry_dir=settings.MODEL_REGISTRY_DIR, horizon=horizon,
        )
        status = "cached"
        model_name = pred.get("model_name") if pred else None

    # Last-resort DB fallback — find ticker in stored predictions
    if pred is None:
        logger.info("File-based prediction unavailable for %s — querying DB", ticker.upper())
        db_preds = await load_db_predictions(horizon=horizon)
        if db_preds:
            ticker_upper = ticker.upper()
            matching = [p for p in db_preds if p["ticker"] == ticker_upper]
            if matching:
                pred = matching[0]
                status = "db_fallback"
                model_name = pred.get("model_name")

    if pred is None:
        prediction_requests_total.labels(
            ticker=ticker.upper(), model="none", status="error",
        ).inc()
        raise HTTPException(
            status_code=404,
            detail=f"No prediction found for ticker '{ticker.upper()}'",
        )

    prediction_requests_total.labels(
        ticker=ticker.upper(), model=model_name or "unknown", status=status,
    ).inc()
    prediction_latency_seconds.labels(
        ticker=ticker.upper(), model=model_name or "unknown",
    ).observe(duration)

    if ab_model and pred:
        pred["assigned_model_id"] = ab_model["model_id"]

    response = PredictionResponse(**pred)
    await cache_set(cache_key, response.model_dump(), SINGLE_PREDICTION_TTL)
    return response
