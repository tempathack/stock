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
    MacroHistoryPoint,
    MacroLatestResponse,
    MarketOverviewEntry,
    MarketOverviewResponse,
    SentimentDataPoint,
    SentimentTimeseriesResponse,
    StreamingFeaturesResponse,
    TickerIndicatorsResponse,
)
from app.services.feast_online_service import get_streaming_features
from app.services.market_service import get_candles, get_macro_history, get_macro_latest, get_market_overview, get_sentiment_timeseries, get_ticker_indicators

STREAMING_FEATURES_TTL = 5  # 5s — matches frontend poll interval
SENTIMENT_TIMESERIES_TTL = 120  # 2 minutes — matches 2-min window emission rate

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


@router.get("/streaming-features/{ticker}", response_model=StreamingFeaturesResponse)
async def streaming_features(ticker: str) -> StreamingFeaturesResponse:
    """Return live Flink-computed streaming features (EMA-20, RSI-14, MACD signal) for a ticker.

    Reads from the Feast Redis online store populated by the Phase 67 feast_writer job.
    Returns available=False with null values when Feast is unavailable — never raises 500.
    Cache TTL is 5s to match the frontend poll interval.
    """
    upper_ticker = ticker.upper()
    key = build_key("market", "streaming-features", upper_ticker)
    cached = await cache_get(key)
    if cached is not None:
        return StreamingFeaturesResponse(**cached)
    result = await get_streaming_features(upper_ticker)
    await cache_set(key, result.model_dump(), STREAMING_FEATURES_TTL)
    return result


@router.get("/sentiment/{ticker}/timeseries", response_model=SentimentTimeseriesResponse)
async def get_sentiment_timeseries_endpoint(
    ticker: str, hours: int = 10
) -> SentimentTimeseriesResponse:
    """Return 10h rolling window of 2-minute sentiment averages for a ticker.

    Source: sentiment_timeseries TimescaleDB hypertable (written by Flink JDBC sink).
    Cache TTL: 120s (aligns with 2-minute window interval).
    """
    upper = ticker.upper()
    key = build_key("market", "sentiment-ts", upper, str(hours))
    cached = await cache_get(key)
    if cached is not None:
        return SentimentTimeseriesResponse(**cached)
    data = await get_sentiment_timeseries(ticker=upper, hours=hours)
    response = SentimentTimeseriesResponse(
        ticker=upper,
        points=[SentimentDataPoint(**p) for p in data],
        count=len(data),
        window_hours=hours,
    )
    await cache_set(key, response.model_dump(), SENTIMENT_TIMESERIES_TTL)
    return response


MACRO_LATEST_TTL = 300   # 5 minutes — FRED/yfinance data changes at most daily
MACRO_HISTORY_TTL = 300  # 5 minutes — same cadence


@router.get("/macro/history", response_model=list[MacroHistoryPoint])
async def get_macro_history_endpoint(days: int = 90) -> list[MacroHistoryPoint]:
    """Return up to *days* rows from macro_fred_daily sorted ASC by as_of_date.

    Used by the MacroChart timeseries component on the Dashboard Macro View.
    Cache TTL: 5 minutes.
    """
    key = build_key("market", "macro-history", str(days))
    cached = await cache_get(key)
    if cached is not None:
        return [MacroHistoryPoint(**row) for row in cached]

    points = await get_macro_history(days=days)
    await cache_set(key, [p.model_dump() for p in points], MACRO_HISTORY_TTL)
    return points


@router.get("/macro/latest", response_model=MacroLatestResponse)
async def get_macro_latest_endpoint() -> MacroLatestResponse:
    """Return latest macro indicator snapshot for the Dashboard macro panel.

    Sources:
    - macro_fred_daily: FRED series (DGS10, T10Y2Y, BAML HY OAS, WTI, USD, ICSA, Core PCE, DGS2, T10YIE)
    - feast_yfinance_macro: VIX and SPY return (ticker='SPY')

    Returns all-null response when tables are empty — never raises 500.
    Cache TTL: 5 minutes.
    """
    key = build_key("market", "macro-latest")
    cached = await cache_get(key)
    if cached is not None:
        return MacroLatestResponse(**cached)

    response = await get_macro_latest()
    await cache_set(key, response.model_dump(), MACRO_LATEST_TTL)
    return response
