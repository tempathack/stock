"""FastAPI router for /search/* endpoints — Elasticsearch-backed entity search."""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.cache import build_key, cache_get, cache_set
from app.models.schemas import (
    DriftEventSearchResponse,
    ModelSearchResponse,
    PredictionSearchResponse,
    StockSearchResponse,
)
from app.services.elasticsearch_service import (
    search_drift_events,
    search_models,
    search_predictions,
    search_stocks,
)

router = APIRouter(prefix="/search", tags=["search"])

SEARCH_TTL = 30  # 30s — search results change with CDC writes


@router.get("/predictions", response_model=PredictionSearchResponse)
async def search_predictions_endpoint(
    q: str | None = Query(None, description="Free-text search on notes/metadata"),
    ticker: str | None = Query(None, description="Filter by ticker symbol"),
    model_id: int | None = Query(None, description="Filter by model ID"),
    confidence_min: float | None = Query(None, ge=0.0, le=1.0, description="Minimum confidence"),
    date_from: str | None = Query(None, description="Start date ISO 8601"),
    date_to: str | None = Query(None, description="End date ISO 8601"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=500, description="Results per page"),
) -> PredictionSearchResponse:
    """Search predictions with optional free-text + structured filters."""
    key = build_key(
        "search", "predictions",
        str(q), str(ticker), str(model_id), str(confidence_min),
        str(date_from), str(date_to), str(page), str(page_size),
    )
    cached = await cache_get(key)
    if cached is not None:
        return PredictionSearchResponse(**cached)
    result = await search_predictions(
        q=q, ticker=ticker, model_id=model_id, confidence_min=confidence_min,
        date_from=date_from, date_to=date_to, page=page, page_size=page_size,
    )
    await cache_set(key, result.model_dump(), SEARCH_TTL)
    return result


@router.get("/models", response_model=ModelSearchResponse)
async def search_models_endpoint(
    q: str | None = Query(None, description="Free-text search on model name/version"),
    status: str | None = Query(None, description="Filter by status (winner, active, retired)"),
    r2_min: float | None = Query(None, description="Minimum R\u00b2 (OOS)"),
    rmse_max: float | None = Query(None, description="Maximum RMSE (OOS)"),
    mae_max: float | None = Query(None, description="Maximum MAE (OOS)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> ModelSearchResponse:
    """Search model registry with optional metric threshold filters."""
    key = build_key(
        "search", "models",
        str(q), str(status), str(r2_min), str(rmse_max), str(mae_max),
        str(page), str(page_size),
    )
    cached = await cache_get(key)
    if cached is not None:
        return ModelSearchResponse(**cached)
    result = await search_models(
        q=q, status=status, r2_min=r2_min, rmse_max=rmse_max, mae_max=mae_max,
        page=page, page_size=page_size,
    )
    await cache_set(key, result.model_dump(), SEARCH_TTL)
    return result


@router.get("/drift-events", response_model=DriftEventSearchResponse)
async def search_drift_events_endpoint(
    q: str | None = Query(None, description="Free-text search on drift type/details"),
    drift_type: str | None = Query(None, description="Filter by drift type"),
    severity: str | None = Query(None, description="Filter by severity (high, medium, low)"),
    ticker: str | None = Query(None, description="Filter by ticker symbol"),
    date_from: str | None = Query(None, description="Start date ISO 8601"),
    date_to: str | None = Query(None, description="End date ISO 8601"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> DriftEventSearchResponse:
    """Search drift events with optional type/severity/ticker/date filters."""
    key = build_key(
        "search", "drift",
        str(q), str(drift_type), str(severity), str(ticker),
        str(date_from), str(date_to), str(page), str(page_size),
    )
    cached = await cache_get(key)
    if cached is not None:
        return DriftEventSearchResponse(**cached)
    result = await search_drift_events(
        q=q, drift_type=drift_type, severity=severity, ticker=ticker,
        date_from=date_from, date_to=date_to, page=page, page_size=page_size,
    )
    await cache_set(key, result.model_dump(), SEARCH_TTL)
    return result


@router.get("/stocks", response_model=StockSearchResponse)
async def search_stocks_endpoint(
    q: str | None = Query(None, description="Free-text search on company name, sector, industry"),
    sector: str | None = Query(None, description="Filter by sector"),
    exchange: str | None = Query(None, description="Filter by exchange"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> StockSearchResponse:
    """Full-text search on stocks (company name, sector, industry)."""
    key = build_key(
        "search", "stocks",
        str(q), str(sector), str(exchange), str(page), str(page_size),
    )
    cached = await cache_get(key)
    if cached is not None:
        return StockSearchResponse(**cached)
    result = await search_stocks(q=q, sector=sector, exchange=exchange, page=page, page_size=page_size)
    await cache_set(key, result.model_dump(), SEARCH_TTL)
    return result
