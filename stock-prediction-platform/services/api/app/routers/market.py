"""Market router — /market/overview and /market/indicators/{ticker} endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.cache import (
    MARKET_CANDLES_TTL,
    MARKET_INDICATORS_TTL,
    MARKET_OVERVIEW_TTL,
    build_key,
    cache_get,
    cache_set,
)
from app.models.schemas import (
    CandleBar,
    CandlesResponse,
    IndicatorValues,
    MarketOverviewEntry,
    MarketOverviewResponse,
    TickerIndicatorsResponse,
)
from app.services.market_service import get_candles, get_market_overview, get_ticker_indicators

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


SUPPORTED_CANDLE_INTERVALS = {"1h", "1d"}


@router.get("/candles", response_model=CandlesResponse)
async def market_candles(
    ticker: str,
    interval: str = "1h",
    limit: int = 200,
) -> CandlesResponse:
    """Return OHLCV candle bars from a TimescaleDB continuous aggregate.

    Supported intervals: 1h (from ohlcv_daily_1h_agg), 1d (from ohlcv_daily_agg).
    Results are cached in Redis for 30 seconds.
    """
    if interval not in SUPPORTED_CANDLE_INTERVALS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported interval '{interval}'. Supported: {sorted(SUPPORTED_CANDLE_INTERVALS)}",
        )

    key = build_key("market", "candles", ticker.upper(), interval)
    cached = await cache_get(key)
    if cached is not None:
        return CandlesResponse(**cached)

    rows = await get_candles(ticker=ticker, interval=interval, limit=limit)
    if rows is None:
        # get_candles returns None only for invalid interval (already guarded above)
        # or unexpected internal error — return empty response gracefully
        rows = []

    candles = [
        CandleBar(
            ts=str(row["ts"]),
            ticker=row["ticker"],
            open=row.get("open"),
            high=row.get("high"),
            low=row.get("low"),
            close=row.get("close"),
            volume=row.get("volume"),
            vwap=row.get("vwap"),
        )
        for row in rows
    ]
    response = CandlesResponse(
        ticker=ticker.upper(),
        interval=interval,
        candles=candles,
        count=len(candles),
    )
    await cache_set(key, response.model_dump(), MARKET_CANDLES_TTL)
    return response
