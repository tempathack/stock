"""Market router — /market/overview and /market/indicators/{ticker} endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
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
    raw = get_market_overview(db_url=settings.DATABASE_URL)
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
    return MarketOverviewResponse(stocks=entries, count=len(entries))


@router.get("/indicators/{ticker}", response_model=TickerIndicatorsResponse)
async def market_indicators(ticker: str) -> TickerIndicatorsResponse:
    """Return technical indicators for a single ticker."""
    result = get_ticker_indicators(
        ticker=ticker,
        db_url=settings.DATABASE_URL,
    )
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data available for ticker '{ticker.upper()}'",
        )
    return TickerIndicatorsResponse(
        ticker=result["ticker"],
        latest=IndicatorValues(**result["latest"]) if result["latest"] else None,
        series=[IndicatorValues(**row) for row in result["series"]],
        count=result["count"],
    )
