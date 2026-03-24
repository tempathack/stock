"""Feature store — precompute, persist, and read feature vectors from PostgreSQL."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

import pandas as pd
import psycopg2

from ml.features.indicators import compute_all_indicators
from ml.features.lag_features import (
    compute_lag_features,
    compute_rolling_stats,
    drop_incomplete_rows,
)
from ml.pipelines.components.data_loader import DBSettings, load_ticker_data

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------

_BATCH_SIZE = 5000


def compute_features_for_ticker(ticker: str, conn) -> pd.DataFrame:
    """Load OHLCV data and compute all features for a single ticker.

    Returns an enriched DataFrame with indicators, lag features, and rolling
    stats.  Warm-up rows with NaN are dropped.  Returns an empty DataFrame
    if no OHLCV data is available.
    """
    df = load_ticker_data(ticker, conn)
    if df.empty:
        logger.warning("No OHLCV data for %s — skipping feature computation.", ticker)
        return df

    enriched = compute_all_indicators(df.copy())
    enriched = compute_lag_features(enriched)
    enriched = compute_rolling_stats(enriched)
    enriched = drop_incomplete_rows(enriched)

    logger.info(
        "Computed %d features for %s (%d rows).",
        len(enriched.columns), ticker, len(enriched),
    )
    return enriched


# ---------------------------------------------------------------------------
# Write features to PostgreSQL
# ---------------------------------------------------------------------------

_UPSERT_SQL = """
    INSERT INTO feature_store (ticker, date, feature_name, feature_value)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (ticker, date, feature_name)
    DO UPDATE SET feature_value = EXCLUDED.feature_value,
                  computed_at   = NOW()
"""


def write_features(ticker: str, df: pd.DataFrame, conn) -> int:
    """Write feature DataFrame rows into the feature_store table.

    Uses batch INSERT … ON CONFLICT for idempotent upserts. Returns the
    total number of rows upserted.
    """
    feature_cols = [c for c in df.columns if c not in ("open", "high", "low", "close", "volume")]
    rows: list[tuple] = []
    for dt, row in df.iterrows():
        d = dt.date() if hasattr(dt, "date") else dt
        for col in feature_cols:
            val = row[col]
            if pd.notna(val):
                rows.append((ticker, d, col, float(val)))

    cursor = conn.cursor()
    count = 0
    for i in range(0, len(rows), _BATCH_SIZE):
        batch = rows[i : i + _BATCH_SIZE]
        cursor.executemany(_UPSERT_SQL, batch)
        count += len(batch)
    conn.commit()

    logger.info("Wrote %d feature rows for %s.", count, ticker)
    return count


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def compute_and_store(
    tickers: list[str],
    settings: DBSettings | None = None,
) -> dict[str, int]:
    """Compute and persist features for multiple tickers.

    Opens a single database connection, iterates tickers, and upserts
    features.  Returns a dict mapping ticker → row count written.
    If a single ticker fails, the error is logged and processing continues.
    """
    if settings is None:
        settings = DBSettings.from_env()

    conn = psycopg2.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.database,
        user=settings.user,
        password=settings.password,
    )
    result: dict[str, int] = {}
    try:
        for ticker in tickers:
            try:
                df = compute_features_for_ticker(ticker, conn)
                if df.empty:
                    result[ticker] = 0
                    continue
                result[ticker] = write_features(ticker, df, conn)
            except Exception:
                logger.exception("Failed to compute/store features for %s.", ticker)
                result[ticker] = 0
    finally:
        conn.close()

    total = sum(result.values())
    logger.info("Feature store updated: %d tickers, %d rows.", len(result), total)
    return result


# ---------------------------------------------------------------------------
# Read features from PostgreSQL
# ---------------------------------------------------------------------------


def read_features(
    tickers: list[str],
    settings: DBSettings | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, pd.DataFrame]:
    """Read precomputed features from the feature_store table.

    Pivots EAV rows into wide DataFrames (rows=dates, columns=feature_names).
    Returns a dict mapping ticker → DataFrame.
    """
    if settings is None:
        settings = DBSettings.from_env()

    conn = psycopg2.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.database,
        user=settings.user,
        password=settings.password,
    )
    result: dict[str, pd.DataFrame] = {}
    try:
        cursor = conn.cursor()
        for ticker in tickers:
            sql = (
                "SELECT date, feature_name, feature_value "
                "FROM feature_store WHERE ticker = %s"
            )
            params: list = [ticker]
            if start_date is not None:
                sql += " AND date >= %s"
                params.append(start_date)
            if end_date is not None:
                sql += " AND date <= %s"
                params.append(end_date)
            sql += " ORDER BY date"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            if not rows:
                continue

            raw = pd.DataFrame(rows, columns=["date", "feature_name", "feature_value"])
            wide = raw.pivot(
                index="date", columns="feature_name", values="feature_value",
            )
            wide.index = pd.to_datetime(wide.index)
            wide.columns.name = None
            result[ticker] = wide
            logger.info(
                "Read %d × %d from feature store for %s.",
                len(wide), len(wide.columns), ticker,
            )
    finally:
        conn.close()

    return result


# ---------------------------------------------------------------------------
# Feature freshness check
# ---------------------------------------------------------------------------


def get_feature_freshness(ticker: str, conn) -> date | None:
    """Return the most recent date in feature_store for a ticker, or None."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT MAX(date) FROM feature_store WHERE ticker = %s", (ticker,),
    )
    row = cursor.fetchone()
    return row[0] if row and row[0] is not None else None


# ---------------------------------------------------------------------------
# Active tickers helper
# ---------------------------------------------------------------------------


def _get_active_tickers(conn) -> list[str]:
    """Return all active ticker symbols from the stocks table."""
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM stocks WHERE is_active = true ORDER BY ticker")
    return [r[0] for r in cursor.fetchall()]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Compute and store features in the feature store",
    )
    parser.add_argument(
        "--compute-all",
        action="store_true",
        help="Compute features for all active tickers",
    )
    parser.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="Comma-separated list of specific tickers",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date filter for OHLCV data (ISO format)",
    )
    args = parser.parse_args()

    settings = DBSettings.from_env()

    if args.tickers:
        ticker_list = [t.strip() for t in args.tickers.split(",")]
    elif args.compute_all:
        conn = psycopg2.connect(
            host=settings.host,
            port=settings.port,
            dbname=settings.database,
            user=settings.user,
            password=settings.password,
        )
        try:
            ticker_list = _get_active_tickers(conn)
        finally:
            conn.close()
        logger.info("Found %d active tickers.", len(ticker_list))
    else:
        logger.error("Specify --compute-all or --tickers.")
        sys.exit(1)

    counts = compute_and_store(ticker_list, settings)
    total = sum(counts.values())
    logger.info("Done — %d tickers, %d total rows.", len(counts), total)
    sys.exit(0)
