"""Market data service — treemap data, technical indicators."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import text

from app.models.database import get_async_session, get_engine

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

    # Replace NaN/inf with None
    subset = subset.replace([np.inf, -np.inf], np.nan)
    records = subset.where(subset.notna(), None).to_dict(orient="records")

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
        return df
    except Exception:
        logger.exception("Failed to load OHLCV for %s", ticker)
        return None
