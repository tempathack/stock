"""Market data service — treemap data, technical indicators."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def get_market_overview(db_url: str | None = None) -> list[dict]:
    """Return market overview data for all tracked stocks.

    Reads from PostgreSQL when *db_url* is provided.  Returns empty list when
    the database is unavailable.
    """
    if not db_url:
        return []

    try:
        import psycopg2  # noqa: F811
    except ImportError:
        logger.warning("psycopg2 not available — returning empty overview")
        return []

    query = """
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
    """

    try:
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                cols = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
        return [dict(zip(cols, row)) for row in rows]
    except Exception:
        logger.exception("Failed to fetch market overview from DB")
        return []


def get_ticker_indicators(
    ticker: str,
    ohlcv_df: pd.DataFrame | None = None,
    db_url: str | None = None,
    lookback: int = 250,
) -> dict[str, Any] | None:
    """Compute technical indicators for a single ticker.

    Accepts either a pre-loaded *ohlcv_df* or fetches from DB via *db_url*.
    Returns ``None`` when no data is available.
    """
    if ohlcv_df is None and db_url:
        ohlcv_df = _load_ohlcv_from_db(ticker, db_url, lookback)

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


def _load_ohlcv_from_db(
    ticker: str, db_url: str, lookback: int,
) -> pd.DataFrame | None:
    """Load recent OHLCV bars from PostgreSQL."""
    try:
        import psycopg2
    except ImportError:
        return None

    query = """
        SELECT date, open, high, low, close, volume
        FROM ohlcv_daily
        WHERE ticker = %s
        ORDER BY date DESC
        LIMIT %s
    """

    try:
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (ticker.upper(), lookback))
                cols = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=cols)
        df = df.sort_values("date").reset_index(drop=True)
        return df
    except Exception:
        logger.exception("Failed to load OHLCV from DB for %s", ticker)
        return None
