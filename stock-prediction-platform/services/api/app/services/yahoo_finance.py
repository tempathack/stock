"""Yahoo Finance data fetching service."""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pandas_datareader.data as pdr
import psycopg2
import requests
import yfinance as yf
from fredapi import Fred
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Macro / sector ETF constants
# ---------------------------------------------------------------------------

SECTOR_ETF_MAP: dict[str, list[str]] = {
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

# Invert: ticker -> sector ETF symbol
TICKER_TO_SECTOR_ETF: dict[str, str] = {
    t: etf for etf, tickers in SECTOR_ETF_MAP.items() for t in tickers
}

# Default ETF for tickers not present in SECTOR_ETF_MAP
DEFAULT_SECTOR_ETF = "SPY"

_SECTOR_ETFS = list(SECTOR_ETF_MAP.keys())  # 11 ETF symbols


def fetch_yfinance_macro(
    tickers: list[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch market-wide macro features from Yahoo Finance.

    Downloads ^VIX, SPY, and all 11 GICS sector ETFs for the given date range.
    Returns a wide DataFrame indexed by date with columns:
        vix, spy_return, xlk_return, xlf_return, xle_return, xlv_return,
        xli_return, xly_return, xlp_return, xlu_return, xlre_return,
        xlb_return, xlc_return.

    Args:
        tickers: Stock tickers to fetch macro data for (used only to determine
                 which sector ETFs are relevant; all ETFs are always fetched).
        start_date: ISO date string "YYYY-MM-DD" — window start.
        end_date:   ISO date string "YYYY-MM-DD" — window end.

    Returns:
        DataFrame with DatetimeIndex (date) and one row per trading day.
    """
    macro_symbols = ["^VIX", "SPY"] + _SECTOR_ETFS

    logger.info(
        "fetch_yfinance_macro_start",
        symbols=macro_symbols,
        start=start_date,
        end=end_date,
    )

    raw = yf.download(
        macro_symbols,
        start=start_date,
        end=end_date,
        interval="1d",
        progress=False,
        auto_adjust=True,
    )

    # yfinance returns MultiIndex columns: (field, symbol) — extract Close prices
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"].copy()
    else:
        # Single-symbol fallback (shouldn't happen with list input)
        close = raw[["Close"]].copy()

    # Normalize column names: "^VIX" -> "VIX", "SPY" -> "SPY", "XLK" -> "XLK", …
    close.columns = [str(c).lstrip("^") for c in close.columns]

    # Drop rows where every column is NaN (non-trading days)
    close = close.dropna(how="all")

    # Forward-fill to handle holidays / missing days
    close = close.ffill()

    # ---------- VIX ----------
    result = pd.DataFrame(index=close.index)
    result.index.name = "date"
    result["vix"] = close["VIX"]

    # ---------- SPY log-return ----------
    result["spy_return"] = np.log(close["SPY"] / close["SPY"].shift(1))

    # ---------- Sector ETF log-returns ----------
    for etf in _SECTOR_ETFS:
        col = etf.lower() + "_return"
        result[col] = np.log(close[etf] / close[etf].shift(1))

    # Drop first row which has NaN log-returns
    result = result.dropna(subset=["spy_return"])

    logger.info(
        "fetch_yfinance_macro_complete",
        rows=len(result),
        columns=list(result.columns),
    )

    return result


DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK-B", "JPM", "JNJ",
    "V", "PG", "UNH", "HD", "MA",
    "BAC", "XOM", "PFE", "ABBV", "CVX",
]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=3, min=5, max=30),
    retry=retry_if_exception_type(
        (requests.ConnectionError, requests.Timeout, requests.HTTPError, ValueError)
    ),
    reraise=True,
)
def _fetch_ticker_data(
    ticker: str, period: str, interval: str
) -> pd.DataFrame:
    """Fetch OHLCV data for a single ticker with retry."""
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    # yfinance >= 1.0 returns MultiIndex columns even for single ticker.
    # Drop all but the first level (Price field) to get flat column names.
    while isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(-1)
    # If duplicate columns remain after droplevel (e.g. Adj Close→Close clash),
    # keep only the first occurrence so row[col] always returns a scalar.
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def _fetch_ticker_stooq(ticker: str, period: str) -> pd.DataFrame:
    """Fallback: fetch daily OHLCV from Stooq via pandas-datareader.

    Stooq only supports daily bars, so this is used for historical mode only.
    Period is converted from yfinance-style (e.g. '5y') to a date range.
    """
    period_days = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
                   "1y": 365, "2y": 730, "5y": 1825, "10y": 3650}
    days = period_days.get(period, 365)
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days)
    df = pdr.DataReader(ticker, "stooq", start, end)
    # Stooq returns newest-first; normalize to ascending
    df = df.sort_index()
    return df


class YahooFinanceService:
    """Fetches and validates OHLCV data from Yahoo Finance."""

    def __init__(self) -> None:
        raw = settings.TICKER_SYMBOLS.strip()
        if raw:
            self.tickers: list[str] = [
                t.strip() for t in raw.split(",") if t.strip()
            ]
        else:
            self.tickers = list(DEFAULT_TICKERS)

    # ------------------------------------------------------------------
    # Public fetch methods
    # ------------------------------------------------------------------

    def fetch_intraday(
        self, tickers: list[str] | None = None
    ) -> list[dict]:
        """Fetch intraday (1-min) OHLCV for each ticker."""
        return self._fetch_and_validate(
            tickers=tickers or self.tickers,
            period="1d",
            interval="1m",
            fetch_mode="intraday",
        )

    def fetch_historical(
        self, tickers: list[str] | None = None
    ) -> list[dict]:
        """Fetch historical (daily) OHLCV for each ticker."""
        return self._fetch_and_validate(
            tickers=tickers or self.tickers,
            period="5y",
            interval="1d",
            fetch_mode="historical",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_and_validate(
        self,
        tickers: list[str],
        period: str,
        interval: str,
        fetch_mode: str,
    ) -> list[dict]:
        """Shared logic: fetch, validate, convert to records."""
        all_records: list[dict] = []

        for ticker in tickers:
            time.sleep(2.0)
            try:
                df = _fetch_ticker_data(ticker, period=period, interval=interval)
            except RetryError:
                logger.error(
                    "all_retries_exhausted",
                    ticker=ticker,
                    period=period,
                    interval=interval,
                )
                continue

            if df.empty:
                if fetch_mode == "historical":
                    logger.warning(
                        "yahoo_empty_trying_stooq",
                        ticker=ticker,
                        period=period,
                    )
                    try:
                        df = _fetch_ticker_stooq(ticker, period)
                    except Exception as exc:
                        logger.error(
                            "stooq_fallback_failed",
                            ticker=ticker,
                            error=str(exc),
                        )
                        continue
                if df.empty:
                    logger.info(
                        "empty_dataframe_skipped",
                        ticker=ticker,
                        period=period,
                        interval=interval,
                    )
                    continue

            try:
                valid_records, skip_count = self.validate_ohlcv(df, ticker)
            except Exception as exc:
                logger.error(
                    "validate_error_skipped",
                    ticker=ticker,
                    error=str(exc),
                )
                continue

            # Stamp fetch_mode and ingested_at on each valid record
            now = datetime.now(timezone.utc).isoformat()
            for rec in valid_records:
                rec["fetch_mode"] = fetch_mode
                rec["ingested_at"] = now

            logger.info(
                "ticker_fetch_complete",
                ticker=ticker,
                valid=len(valid_records),
                skipped=skip_count,
                fetch_mode=fetch_mode,
            )
            all_records.extend(valid_records)

        return all_records

    def validate_ohlcv(
        self, df: pd.DataFrame, ticker: str
    ) -> tuple[list[dict], int]:
        """Row-by-row OHLCV validation.

        Returns:
            Tuple of (valid_records, skip_count).
        """
        valid_records: list[dict] = []
        skip_count = 0

        for idx, row in df.iterrows():
            # 1. Reject NaN in OHLC
            if (
                pd.isna(row["Open"])
                or pd.isna(row["High"])
                or pd.isna(row["Low"])
                or pd.isna(row["Close"])
            ):
                logger.warning(
                    "invalid_record",
                    ticker=ticker,
                    timestamp=str(idx),
                    reason="null_ohlc",
                )
                skip_count += 1
                continue

            # 2. Reject NaN or negative volume (Volume=0 is valid)
            if pd.isna(row["Volume"]) or row["Volume"] < 0:
                logger.warning(
                    "invalid_record",
                    ticker=ticker,
                    timestamp=str(idx),
                    reason="invalid_volume",
                )
                skip_count += 1
                continue

            # 3. Reject High < Low
            if row["High"] < row["Low"]:
                logger.warning(
                    "invalid_record",
                    ticker=ticker,
                    timestamp=str(idx),
                    reason="high_lt_low",
                )
                skip_count += 1
                continue

            # Valid row — build record dict
            valid_records.append({
                "ticker": ticker,
                "timestamp": self._normalize_timestamp(idx),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]),
            })

        return valid_records, skip_count

    @staticmethod
    def _normalize_timestamp(idx_value: pd.Timestamp) -> str:
        """Convert pandas Timestamp to UTC ISO 8601 string."""
        ts = pd.Timestamp(idx_value)
        if ts.tzinfo is not None:
            ts = ts.tz_convert("UTC")
        else:
            ts = ts.tz_localize("UTC")
        return ts.isoformat()


# ---------------------------------------------------------------------------
# FRED macro feature collector — ingestion-service layer (Phase 94)
# ---------------------------------------------------------------------------

_FRED_SERIES: list[str] = [
    "DGS2", "DGS10", "T10Y2Y", "T10Y3M",
    "BAMLH0A0HYM2", "DBAA", "T10YIE",
    "DCOILWTICO", "DTWEXBGS", "DEXJPUS",
    "ICSA", "NFCI", "CPIAUCSL", "PCEPILFE",
]

_FRED_COLS: list[str] = [s.lower() for s in _FRED_SERIES]

_CREATE_FRED_MACRO_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS feast_fred_macro (
    ticker          VARCHAR(16)      NOT NULL DEFAULT 'MACRO',
    timestamp       TIMESTAMPTZ      NOT NULL,
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    dgs2            DOUBLE PRECISION,
    dgs10           DOUBLE PRECISION,
    t10y2y          DOUBLE PRECISION,
    t10y3m          DOUBLE PRECISION,
    bamlh0a0hym2    DOUBLE PRECISION,
    dbaa            DOUBLE PRECISION,
    t10yie          DOUBLE PRECISION,
    dcoilwtico      DOUBLE PRECISION,
    dtwexbgs        DOUBLE PRECISION,
    dexjpus         DOUBLE PRECISION,
    icsa            DOUBLE PRECISION,
    nfci            DOUBLE PRECISION,
    cpiaucsl        DOUBLE PRECISION,
    pcepilfe        DOUBLE PRECISION,
    PRIMARY KEY (ticker, timestamp)
);
SELECT create_hypertable('feast_fred_macro', 'timestamp', if_not_exists => TRUE);
"""

_UPSERT_FRED_SQL = (
    "INSERT INTO feast_fred_macro (ticker, timestamp, {cols}) "
    "VALUES ('MACRO', %s, {placeholders}) "
    "ON CONFLICT (ticker, timestamp) DO UPDATE SET {updates}, created_at = NOW();"
).format(
    cols=", ".join(_FRED_COLS),
    placeholders=", ".join(["%s"] * len(_FRED_COLS)),
    updates=", ".join(f"{c} = EXCLUDED.{c}" for c in _FRED_COLS),
)


def fetch_fred_macro(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch 14 FRED macro series; return wide daily DataFrame with forward-fill.

    Ingestion-service counterpart of the ML pipeline fetch_fred_macro(). Reads
    FRED_API_KEY from the environment; raises KeyError immediately if not set.

    Args:
        start_date: ISO date string "YYYY-MM-DD" — window start.
        end_date:   ISO date string "YYYY-MM-DD" — window end.

    Returns:
        DataFrame with DatetimeIndex (daily, name="date"), 14 columns.
        No NaN values — weekly/monthly series are forward-filled with no limit.
    """
    api_key = os.environ["FRED_API_KEY"]  # KeyError if not set — intentional
    fred = Fred(api_key=api_key)
    frames: dict[str, pd.Series] = {}
    for series_id in _FRED_SERIES:
        s = fred.get_series(
            series_id,
            observation_start=start_date,
            observation_end=end_date,
        )
        frames[series_id.lower()] = s
        time.sleep(0.5)  # Respect FRED rate limit (120 req/min for authenticated calls)

    wide = pd.DataFrame(frames)
    date_spine = pd.date_range(start=start_date, end=end_date, freq="D")
    wide = wide.reindex(date_spine).ffill()  # No limit — carry last value indefinitely
    wide.index.name = "date"
    return wide


def create_fred_macro_table() -> None:
    """Create the feast_fred_macro TimescaleDB hypertable if it does not exist.

    Uses DB connection settings from environment variables. Safe to call multiple
    times — uses IF NOT EXISTS and if_not_exists => TRUE.
    """
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgresql.storage.svc.cluster.local"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "stockdb"),
        user=os.environ.get("POSTGRES_USER", "stockuser"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(_CREATE_FRED_MACRO_TABLE_SQL)
        logger.info("create_fred_macro_table", status="feast_fred_macro ready")
    finally:
        conn.close()


def write_fred_macro_to_db(macro_df: pd.DataFrame) -> int:
    """Write FRED macro rows to feast_fred_macro, upserting on timestamp.

    Args:
        macro_df: DataFrame with DatetimeIndex (name="date") and 14 FRED columns.

    Returns:
        Number of rows upserted.
    """
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgresql.storage.svc.cluster.local"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "stockdb"),
        user=os.environ.get("POSTGRES_USER", "stockuser"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
    )
    df = macro_df.copy()
    if "date" not in df.columns:
        df = df.reset_index()
        df = df.rename(columns={"index": "date", 0: "date"})

    missing_cols = [c for c in _FRED_COLS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"macro_df missing FRED columns: {missing_cols}")

    rows_written = 0
    try:
        with conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    cur.execute(_UPSERT_FRED_SQL, tuple(
                        [row.get("date", row.name)] + [row[c] for c in _FRED_COLS]
                    ))
                    rows_written += 1
        logger.info("write_fred_macro_to_db", rows=rows_written)
    finally:
        conn.close()

    return rows_written
