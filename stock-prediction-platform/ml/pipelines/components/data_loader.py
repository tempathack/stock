"""Kubeflow component — loads OHLCV data from PostgreSQL."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd
import psycopg2
import yfinance as yf

from ml.features.feast_store import _TRAINING_FEATURES, get_store

# ---------------------------------------------------------------------------
# Macro / sector ETF constants (mirrors yahoo_finance.py in the API service)
# ---------------------------------------------------------------------------

_SECTOR_ETF_MAP: dict[str, list[str]] = {
    "XLK":  ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "AMD", "QCOM", "TXN", "AMAT", "MU"],
    "XLF":  ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "SPGI", "BLK"],
    "XLE":  ["XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "PSX", "VLO", "HES"],
    "XLV":  ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "ISRG", "DHR", "SYK"],
    "XLI":  ["RTX", "HON", "UNP", "UPS", "CAT", "DE", "GE", "LMT", "ETN", "ITW"],
    "XLY":  ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "TJX", "BKNG", "MAR"],
    "XLP":  ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "MDLZ", "CL", "GIS"],
    "XLU":  ["NEE", "DUK", "SO", "D", "AEP", "EXC", "XEL", "SRE", "ED", "ES"],
    "XLRE": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "WELL", "AVB", "EQR"],
    "XLB":  ["LIN", "SHW", "APD", "FCX", "NEM", "NUE", "VMC", "MLM", "CE", "ALB"],
    "XLC":  ["META", "GOOGL", "GOOG", "NFLX", "DIS", "CMCSA", "T", "VZ", "EA", "TTWO"],
}

_TICKER_TO_SECTOR_ETF: dict[str, str] = {
    t: etf for etf, tickers in _SECTOR_ETF_MAP.items() for t in tickers
}

_DEFAULT_SECTOR_ETF = "SPY"
_SECTOR_ETFS = list(_SECTOR_ETF_MAP.keys())

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


# ---------------------------------------------------------------------------
# yfinance macro feature loader (Phase 93)
# ---------------------------------------------------------------------------


def _fetch_yfinance_macro_wide(start_date: str, end_date: str) -> pd.DataFrame:
    """Download VIX, SPY, and all 11 sector ETFs; return wide daily DataFrame.

    Columns: vix, spy_return, xlk_return, ..., xlc_return.
    Index: DatetimeIndex (business days in range).
    """
    macro_symbols = ["^VIX", "SPY"] + _SECTOR_ETFS

    raw = yf.download(
        macro_symbols,
        start=start_date,
        end=end_date,
        interval="1d",
        progress=False,
        auto_adjust=True,
    )

    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"].copy()
    else:
        close = raw[["Close"]].copy()

    # Normalize names: "^VIX" -> "VIX"
    close.columns = [str(c).lstrip("^") for c in close.columns]
    close = close.dropna(how="all").ffill()

    result = pd.DataFrame(index=close.index)
    result.index.name = "date"
    result["vix"] = close["VIX"]
    result["spy_return"] = np.log(close["SPY"] / close["SPY"].shift(1))

    for etf in _SECTOR_ETFS:
        col = etf.lower() + "_return"
        result[col] = np.log(close[etf] / close[etf].shift(1))

    # Drop first row (NaN log-returns from shift)
    result = result.dropna(subset=["spy_return"])
    return result


def load_yfinance_macro(
    tickers: list[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Load and join yfinance macro features for each (ticker, date) pair.

    For each ticker the function:
    1. Fetches VIX, SPY, and 11 sector ETF returns from Yahoo Finance.
    2. Maps each ticker to its GICS sector ETF via TICKER_TO_SECTOR_ETF.
    3. Computes 52-week high/low pct from the per-ticker OHLCV data already
       in PostgreSQL (loaded via load_ticker_data).

    Args:
        tickers:    List of stock ticker symbols.
        start_date: ISO date string "YYYY-MM-DD" — window start.
        end_date:   ISO date string "YYYY-MM-DD" — window end.

    Returns:
        DataFrame with columns:
            ticker, date, vix, spy_return, sector_return,
            high52w_pct, low52w_pct
        Indexed by (ticker, date) MultiIndex.
    """
    # --- 1. Fetch market-wide macro DataFrame ---
    macro_wide = _fetch_yfinance_macro_wide(start_date, end_date)

    # --- 2. Load per-ticker OHLCV for 52-week window ---
    db_settings = DBSettings.from_env()
    conn = psycopg2.connect(
        host=db_settings.host,
        port=db_settings.port,
        dbname=db_settings.database,
        user=db_settings.user,
        password=db_settings.password,
    )

    all_rows: list[pd.DataFrame] = []

    try:
        for ticker in tickers:
            ohlcv = load_ticker_data(ticker, conn, start_date=None, end_date=None)
            if ohlcv.empty:
                logger.warning("load_yfinance_macro: no OHLCV data for %s — skipping.", ticker)
                continue

            # Compute 52-week rolling high/low pct (252 trading days)
            ohlcv["high52w"] = ohlcv["close"].rolling(252, min_periods=20).max()
            ohlcv["low52w"]  = ohlcv["close"].rolling(252, min_periods=20).min()
            ohlcv["high52w_pct"] = (ohlcv["high52w"] - ohlcv["close"]) / ohlcv["high52w"]
            ohlcv["low52w_pct"]  = (ohlcv["close"] - ohlcv["low52w"])  / ohlcv["low52w"]

            # Filter to requested date range
            start_ts = pd.Timestamp(start_date)
            end_ts   = pd.Timestamp(end_date)
            ohlcv = ohlcv[(ohlcv.index >= start_ts) & (ohlcv.index <= end_ts)]

            # Join macro features by date
            merged = ohlcv[["high52w_pct", "low52w_pct"]].join(macro_wide, how="inner")

            # Pick sector ETF return for this ticker
            etf = _TICKER_TO_SECTOR_ETF.get(ticker, _DEFAULT_SECTOR_ETF)
            etf_col = etf.lower() + "_return"
            merged["sector_return"] = merged[etf_col] if etf_col in merged.columns else np.nan

            # Final columns
            merged["ticker"] = ticker
            merged["date"]   = merged.index
            result_cols = ["ticker", "date", "vix", "spy_return", "sector_return", "high52w_pct", "low52w_pct"]
            all_rows.append(merged[result_cols])
    finally:
        conn.close()

    if not all_rows:
        empty = pd.DataFrame(columns=["ticker", "date", "vix", "spy_return", "sector_return", "high52w_pct", "low52w_pct"])
        empty["date"] = pd.to_datetime(empty["date"])
        empty = empty.set_index("date")
        return empty

    final = pd.concat(all_rows, ignore_index=True)
    final["date"] = pd.to_datetime(final["date"])
    final = final.set_index("date")
    logger.info("load_yfinance_macro: %d rows for %d tickers", len(final), len(tickers))
    return final
