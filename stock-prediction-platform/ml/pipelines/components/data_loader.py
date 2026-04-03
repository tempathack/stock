"""Kubeflow component — loads OHLCV data from PostgreSQL."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date

import pandas as pd
import psycopg2

from ml.features.feast_store import _TRAINING_FEATURES, get_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class DBSettings:
    """PostgreSQL connection settings with env-var defaults."""

    host: str = field(
        default_factory=lambda: os.environ.get(
            "POSTGRES_HOST", "postgresql.storage.svc.cluster.local"
        )
    )
    port: int = field(
        default_factory=lambda: int(os.environ.get("POSTGRES_PORT", "5432"))
    )
    database: str = field(
        default_factory=lambda: os.environ.get("POSTGRES_DB", "stockdb")
    )
    user: str = field(
        default_factory=lambda: os.environ.get("POSTGRES_USER", "stockuser")
    )
    password: str = field(
        default_factory=lambda: os.environ.get("POSTGRES_PASSWORD", "")
    )

    @classmethod
    def from_env(cls) -> "DBSettings":
        """Create an instance populated entirely from environment variables."""
        return cls()

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


# ---------------------------------------------------------------------------
# Per-ticker data loading
# ---------------------------------------------------------------------------

_COLUMNS = ["open", "high", "low", "close", "volume"]


def load_ticker_data(
    ticker: str,
    conn,
    start_date: date | None = None,
    end_date: date | None = None,
) -> pd.DataFrame:
    """Load OHLCV rows for a single *ticker* from PostgreSQL.

    Returns a DataFrame with a DatetimeIndex and columns ``open, high, low,
    close, volume``.  An empty DataFrame (with the correct columns) is
    returned when the query yields no rows.
    """
    sql = "SELECT date, open, high, low, close, volume FROM ohlcv_daily WHERE ticker = %s"
    params: list = [ticker]

    if start_date is not None:
        sql += " AND date >= %s"
        params.append(start_date)
    if end_date is not None:
        sql += " AND date <= %s"
        params.append(end_date)

    sql += " ORDER BY date ASC"

    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()

    if not rows:
        return pd.DataFrame(columns=_COLUMNS)

    df = pd.DataFrame(rows, columns=["date"] + _COLUMNS)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    # Cast NUMERIC columns from decimal.Decimal to float64 for arithmetic ops
    for col in _COLUMNS:
        df[col] = df[col].astype(float)
    return df


# ---------------------------------------------------------------------------
# Multi-ticker orchestration
# ---------------------------------------------------------------------------


def load_data(
    tickers: list[str],
    settings: DBSettings | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, pd.DataFrame]:
    """Load OHLCV data for multiple *tickers* and return per-ticker DataFrames.

    Tickers that return zero rows are logged and omitted from the result.
    The database connection is always closed, even on error.
    """
    if not isinstance(tickers, list):
        raise TypeError(f"tickers must be a list, got {type(tickers).__name__}")

    if settings is None:
        settings = DBSettings.from_env()

    conn = psycopg2.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.database,
        user=settings.user,
        password=settings.password,
    )

    try:
        result: dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            df = load_ticker_data(ticker, conn, start_date=start_date, end_date=end_date)
            if df.empty:
                logger.warning("Ticker %s returned 0 rows — skipping.", ticker)
                continue
            result[ticker] = df
            logger.info("Loaded %d rows for %s.", len(df), ticker)
        return result
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Feast offline data loading (Phase 92)
# ---------------------------------------------------------------------------

_SENTIMENT_COLS = ["avg_sentiment", "mention_count", "positive_ratio", "negative_ratio"]


def load_feast_data(
    tickers: list[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Load historical training features from Feast offline (PostgreSQL) store.

    Replaces load_data() + engineer_features() for the Feast training path.
    Returns a flat DataFrame with one row per (ticker, date) and 34 feature columns.
    Entity/timestamp columns (ticker, event_timestamp) are dropped before return.
    Null sentiment values (sparse Reddit coverage) are filled with 0.0.

    Args:
        tickers: List of ticker symbols (e.g. ["AAPL", "MSFT"]).
        start_date: ISO date string "YYYY-MM-DD" — training window start.
        end_date: ISO date string "YYYY-MM-DD" — training window end.

    Returns:
        DataFrame with columns matching _TRAINING_FEATURES bare names (34 columns),
        plus "ticker" column for grouping. event_timestamp is dropped.
    """
    dates = pd.date_range(start=start_date, end=end_date, freq="B")
    rows = [
        {"ticker": t, "event_timestamp": pd.Timestamp(d, tz="UTC")}
        for t in tickers
        for d in dates
    ]
    entity_df = pd.DataFrame(rows)

    store = get_store()
    df = store.get_historical_features(
        entity_df=entity_df,
        features=_TRAINING_FEATURES,
    ).to_df()

    # Fill sparse sentiment columns first (most commonly None)
    for col in _SENTIMENT_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)

    # Fill any remaining NaN (e.g. warm-up period for lag features)
    df = df.fillna(0.0)

    # Drop entity/timestamp columns — keep ticker for grouping in training pipeline
    df = df.drop(columns=["event_timestamp"], errors="ignore")

    logger.info("load_feast_data: %d rows for %d tickers", len(df), len(tickers))
    return df
