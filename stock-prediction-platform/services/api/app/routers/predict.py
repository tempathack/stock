"""Prediction router — /predict/{ticker} and /predict/bulk endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import BulkPredictionResponse, PredictionResponse
from app.services.prediction_service import (
    get_prediction_for_ticker,
    load_cached_predictions,
)

router = APIRouter(prefix="/predict", tags=["predictions"])


@router.get("/bulk", response_model=BulkPredictionResponse)
async def predict_bulk() -> BulkPredictionResponse:
    """Return forecasts for all available tickers."""
    predictions = load_cached_predictions(
        registry_dir=settings.MODEL_REGISTRY_DIR,
    )
    if not predictions:
        raise HTTPException(
            status_code=404,
            detail="No cached predictions available. Run the training pipeline first.",
        )
    model_name = predictions[0].get("model_name") if predictions else None
    return BulkPredictionResponse(
        predictions=[PredictionResponse(**p) for p in predictions],
        model_name=model_name,
        generated_at=predictions[0].get("prediction_date") if predictions else None,
        count=len(predictions),
    )


@router.get("/{ticker}", response_model=PredictionResponse)
async def predict_ticker(ticker: str) -> PredictionResponse:
    """Return 7-day forecast for a single ticker."""
    pred = get_prediction_for_ticker(
        ticker, registry_dir=settings.MODEL_REGISTRY_DIR,
    )
    if pred is None:
        raise HTTPException(
            status_code=404,
            detail=f"No prediction found for ticker '{ticker.upper()}'",
        )
    return PredictionResponse(**pred)
