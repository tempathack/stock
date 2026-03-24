"""Market router — /market/overview and /market/indicators/{ticker} endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.cache import (
    MARKET_INDICATORS_TTL,
    MARKET_OVERVIEW_TTL,
    build_key,
    cache_get,
    cache_set,
)
from app.models.schemas import (
    IndicatorValues,
    MarketOverviewEntry,
    MarketOverviewResponse,
    TickerIndicatorsResponse,
)
from app.services.market_service import get_market_overview, get_ticker_indicators

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/overview", response_model=MarketOverviewResponse)
async def market_overview() -> MarketOverviewResponse:
    """Return treemap data: ticker, sector, market_cap, daily change for all stocks."""
    key = build_key("market", "overview")
    cached = await cache_get(key)
    if cached is not None:
        return MarketOverviewResponse(**cached)

    raw = await get_market_overview()
    entries = [
        MarketOverviewEntry(
            ticker=s.get("ticker", ""),
            company_name=s.get("company_name"),
            sector=s.get("sector"),
            market_cap=s.get("market_cap"),
            last_close=s.get("last_close"),
            daily_change_pct=s.get("daily_change_pct"),
        )
        for s in raw
    ]
    response = MarketOverviewResponse(stocks=entries, count=len(entries))
    await cache_set(key, response.model_dump(), MARKET_OVERVIEW_TTL)
    return response


@router.get("/indicators/{ticker}", response_model=TickerIndicatorsResponse)
async def market_indicators(ticker: str) -> TickerIndicatorsResponse:
    """Return technical indicators for a single ticker."""
    key = build_key("market", "indicators", ticker.upper())
    cached = await cache_get(key)
    if cached is not None:
        return TickerIndicatorsResponse(**cached)

    result = await get_ticker_indicators(ticker=ticker)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data available for ticker '{ticker.upper()}'",
        )
    response = TickerIndicatorsResponse(
        ticker=result["ticker"],
        latest=IndicatorValues(**result["latest"]) if result["latest"] else None,
        series=[IndicatorValues(**row) for row in result["series"]],
        count=result["count"],
    )
    await cache_set(key, response.model_dump(), MARKET_INDICATORS_TTL)
    return response
