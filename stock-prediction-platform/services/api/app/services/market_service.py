"""Market data service — treemap data, technical indicators."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text

from app.models.database import get_async_session, get_engine
from app.models.schemas import MacroHistoryPoint, MacroLatestResponse

logger = logging.getLogger(__name__)


async def get_market_overview() -> list[dict]:
    """Return market overview data for all tracked stocks.

    Uses async SQLAlchemy session from the connection pool.
    Returns empty list when the database is unavailable.
    """
    if get_engine() is None:
        return []

    query = text("""
        SELECT s.ticker, s.company_name, s.sector, s.market_cap,
               d.close AS last_close,
               CASE WHEN d.open > 0
                    THEN ((d.close - d.open) / d.open) * 100
                    ELSE NULL
               END AS daily_change_pct
        FROM stocks s
        LEFT JOIN LATERAL (
            SELECT close, open FROM ohlcv_daily
            WHERE ticker = s.ticker
            ORDER BY date DESC LIMIT 1
        ) d ON TRUE
        WHERE s.is_active = true
        ORDER BY s.market_cap DESC NULLS LAST
    """)

    try:
        async with get_async_session() as session:
            result = await session.execute(query)
            rows = result.mappings().all()
        return [dict(row) for row in rows]
    except Exception:
        logger.exception("Failed to fetch market overview from DB")
        return []


async def get_ticker_indicators(
    ticker: str,
    ohlcv_df: pd.DataFrame | None = None,
    lookback: int = 250,
) -> dict[str, Any] | None:
    """Compute technical indicators for a single ticker.

    Accepts either a pre-loaded *ohlcv_df* or fetches from DB via async session.
    Returns ``None`` when no data is available.
    """
    if ohlcv_df is None and get_engine() is not None:
        ohlcv_df = await _load_ohlcv_from_db(ticker, lookback)

    if ohlcv_df is None or ohlcv_df.empty:
        return None

    from ml.features.indicators import compute_all_indicators

    # Ensure lowercase column names matching indicator functions
    ohlcv_df.columns = [c.lower() for c in ohlcv_df.columns]

    enriched = compute_all_indicators(ohlcv_df.copy())

    # Build series as list of dicts (replace NaN with None for JSON)
    indicator_cols = [
        "close", "rsi_14", "macd_line", "macd_signal", "macd_histogram",
        "stoch_k", "stoch_d", "sma_20", "sma_50", "sma_200",
        "ema_12", "ema_26", "adx", "bb_upper", "bb_middle", "bb_lower",
        "atr", "rolling_volatility_21", "obv", "vwap", "volume_sma_20",
        "ad_line", "return_1d", "return_5d", "return_21d", "log_return",
    ]

    available_cols = [c for c in indicator_cols if c in enriched.columns]
    subset = enriched[available_cols].copy()

    # Add date column
    if "date" in enriched.columns:
        subset.insert(0, "date", enriched["date"].astype(str))
    elif hasattr(enriched.index, "strftime"):
        subset.insert(0, "date", enriched.index.astype(str))
    else:
        subset.insert(0, "date", None)

    # Replace NaN/inf with None (pandas pass + Python float guard)
    import math
    subset = subset.replace([np.inf, -np.inf], np.nan)
    records = subset.where(subset.notna(), None).to_dict(orient="records")
    records = [
        {k: (None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
         for k, v in row.items()}
        for row in records
    ]

    latest = records[-1] if records else None

    return {
        "ticker": ticker.upper(),
        "latest": latest,
        "series": records,
        "count": len(records),
    }


async def _load_ohlcv_from_db(
    ticker: str, lookback: int,
) -> pd.DataFrame | None:
    """Load recent OHLCV bars from PostgreSQL via async session."""
    query = text("""
        SELECT date, open, high, low, close, volume
        FROM ohlcv_daily
        WHERE ticker = :ticker
        ORDER BY date DESC
        LIMIT :lookback
    """)
    try:
        async with get_async_session() as session:
            result = await session.execute(
                query, {"ticker": ticker.upper(), "lookback": lookback},
            )
            rows = result.mappings().all()
        if not rows:
            return None
        df = pd.DataFrame([dict(r) for r in rows])
        df = df.sort_values("date").reset_index(drop=True)
        for col in ("open", "high", "low", "close", "volume"):
            if col in df.columns:
                df[col] = df[col].astype(float)
        return df
    except Exception:
        logger.exception("Failed to load OHLCV for %s", ticker)
        return None


# Valid continuous aggregate views per interval key
_CANDLE_VIEW_MAP: dict[str, str] = {
    "1h": "ohlcv_daily_1h_agg",
    "1d": "ohlcv_daily_agg",
}


async def get_candles(
    ticker: str,
    interval: str,
    limit: int = 200,
) -> list[dict] | None:
    """Query the continuous aggregate view for OHLCV candle bars.

    Returns:
        list[dict] with keys ts/ticker/open/high/low/close/volume/vwap on success.
        None if interval is unsupported or DB is unavailable.
        Empty list [] if no rows found for ticker.

    NOTE: Backfills of data older than compress_after (3d intraday, 7d daily)
    will fail on ON CONFLICT into compressed chunks — normal real-time writes
    are unaffected (write current data only).
    """
    view = _CANDLE_VIEW_MAP.get(interval)
    if view is None:
        return None

    if get_engine() is None:
        return []

    # Use text() with named bind parameters — no string interpolation of view name
    # View name comes from the validated _CANDLE_VIEW_MAP dict, not user input
    query = text(f"""
        SELECT
            bucket::text  AS ts,
            ticker,
            open::float   AS open,
            high::float   AS high,
            low::float    AS low,
            close::float  AS close,
            volume::bigint AS volume,
            vwap::float   AS vwap
        FROM {view}
        WHERE ticker = :ticker
        ORDER BY bucket DESC
        LIMIT :limit
    """)
    try:
        async with get_async_session() as session:
            result = await session.execute(
                query, {"ticker": ticker.upper(), "limit": limit},
            )
            rows = result.mappings().all()
        return [dict(row) for row in rows]
    except Exception:
        logger.exception("Failed to fetch candles for %s from %s", ticker, view)
        return []


async def get_sentiment_timeseries(ticker: str, hours: int = 10) -> list[dict]:
    """Query sentiment_timeseries table for rolling window history.

    Returns list of dicts with keys: timestamp, avg_sentiment, mention_count,
    positive_ratio, negative_ratio. At 2-min intervals, 10h = up to 300 rows.
    """
    query = text("""
        SELECT
            window_start AT TIME ZONE 'UTC' AS timestamp,
            avg_sentiment,
            mention_count,
            positive_ratio,
            negative_ratio
        FROM sentiment_timeseries
        WHERE ticker = :ticker
          AND window_start >= NOW() - (:hours * INTERVAL '1 hour')
        ORDER BY window_start ASC
    """)
    try:
        async with get_async_session() as session:
            result = await session.execute(query, {"ticker": ticker.upper(), "hours": hours})
            rows = result.fetchall()
        return [
            {
                "timestamp": (
                    row._mapping["timestamp"].isoformat()
                    if hasattr(row._mapping["timestamp"], "isoformat")
                    else str(row._mapping["timestamp"])
                ),
                "avg_sentiment": row._mapping["avg_sentiment"],
                "mention_count": row._mapping["mention_count"],
                "positive_ratio": row._mapping["positive_ratio"],
                "negative_ratio": row._mapping["negative_ratio"],
            }
            for row in rows
        ]
    except Exception:
        logger.exception("Failed to fetch sentiment timeseries for %s", ticker)
        return []


async def get_macro_history(days: int = 90) -> list[MacroHistoryPoint]:
    """Fetch daily FRED macro timeseries for the last *days* calendar days.

    Returns a list of MacroHistoryPoint sorted ascending by as_of_date.
    Returns [] when the table is empty or DB is unavailable.
    """
    if get_engine() is None:
        return []

    query = text("""
        SELECT as_of_date,
               dgs2, dgs10, t10y2y, t10y3m,
               bamlh0a0hym2, dbaa, t10yie,
               dcoilwtico, dtwexbgs, dexjpus,
               icsa, nfci, cpiaucsl, pcepilfe
        FROM macro_fred_daily
        ORDER BY as_of_date ASC
        LIMIT :days
    """)

    try:
        async with get_async_session() as session:
            result = await session.execute(query, {"days": days})
            rows = result.mappings().all()
        return [
            MacroHistoryPoint(
                as_of_date=str(row["as_of_date"]),
                dgs2=row.get("dgs2"),
                dgs10=row.get("dgs10"),
                t10y2y=row.get("t10y2y"),
                t10y3m=row.get("t10y3m"),
                bamlh0a0hym2=row.get("bamlh0a0hym2"),
                dbaa=row.get("dbaa"),
                t10yie=row.get("t10yie"),
                dcoilwtico=row.get("dcoilwtico"),
                dtwexbgs=row.get("dtwexbgs"),
                dexjpus=row.get("dexjpus"),
                icsa=row.get("icsa"),
                nfci=row.get("nfci"),
                cpiaucsl=row.get("cpiaucsl"),
                pcepilfe=row.get("pcepilfe"),
            )
            for row in rows
        ]
    except Exception:
        logger.exception("Failed to fetch macro_fred_daily history")
        return []


async def get_macro_latest() -> MacroLatestResponse:
    """Fetch the latest macro indicator snapshot for the Dashboard macro panel.

    Queries two tables:
    - macro_fred_daily: FRED series (DGS10, T10Y2Y, BAML HY OAS, WTI, USD, ICSA, Core PCE, DGS2, T10YIE)
    - feast_yfinance_macro: VIX and SPY return (ticker='SPY')

    Returns MacroLatestResponse with all-null values when tables are empty — never raises.
    The as_of_date is taken from macro_fred_daily (FRED) when available, otherwise from feast_yfinance_macro.
    """
    if get_engine() is None:
        return MacroLatestResponse()

    fred_query = text("""
        SELECT as_of_date,
               dgs2, dgs10, t10y2y, t10y3m,
               bamlh0a0hym2 AS baml_hy_oas,
               dbaa,
               t10yie,
               dcoilwtico   AS wti_crude,
               dtwexbgs     AS usd_broad,
               dexjpus,
               icsa,
               nfci,
               cpiaucsl,
               pcepilfe     AS core_pce
        FROM macro_fred_daily
        ORDER BY as_of_date DESC
        LIMIT 1
    """)

    yfinance_query = text("""
        SELECT timestamp::date AS as_of_date, vix, spy_return, sector_return, high52w_pct, low52w_pct
        FROM feast_yfinance_macro
        WHERE ticker = 'SPY'
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    fred_row: dict = {}
    yf_row: dict = {}

    # Use separate sessions for each query — a failing query aborts the PG transaction,
    # which would cause subsequent queries in the same session to also fail.
    try:
        async with get_async_session() as session:
            result = await session.execute(fred_query)
            row = result.mappings().first()
            if row:
                fred_row = dict(row)
    except Exception:
        logger.warning("macro_fred_daily not available — returning nulls for FRED fields")

    try:
        async with get_async_session() as session:
            result = await session.execute(yfinance_query)
            row = result.mappings().first()
            if row:
                yf_row = dict(row)
    except Exception:
        logger.warning("feast_yfinance_macro not available — returning nulls for VIX/SPY fields")

    # Determine as_of_date: prefer FRED date, fall back to yfinance date
    as_of: date | None = fred_row.get("as_of_date") or yf_row.get("as_of_date")

    return MacroLatestResponse(
        as_of_date=as_of,
        vix=yf_row.get("vix"),
        spy_return=yf_row.get("spy_return"),
        sector_return=yf_row.get("sector_return"),
        high52w_pct=yf_row.get("high52w_pct"),
        low52w_pct=yf_row.get("low52w_pct"),
        dgs2=fred_row.get("dgs2"),
        dgs10=fred_row.get("dgs10"),
        t10y2y=fred_row.get("t10y2y"),
        t10y3m=fred_row.get("t10y3m"),
        baml_hy_oas=fred_row.get("baml_hy_oas"),
        dbaa=fred_row.get("dbaa"),
        t10yie=fred_row.get("t10yie"),
        wti_crude=fred_row.get("wti_crude"),
        usd_broad=fred_row.get("usd_broad"),
        dexjpus=fred_row.get("dexjpus"),
        icsa=fred_row.get("icsa"),
        nfci=fred_row.get("nfci"),
        cpiaucsl=fred_row.get("cpiaucsl"),
        core_pce=fred_row.get("core_pce"),
    )
