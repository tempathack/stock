"""Yahoo Finance data fetching service."""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import pandas_datareader.data as pdr
import requests
import yfinance as yf
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
    # yfinance >= 1.0 returns MultiIndex columns even for single ticker
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
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

            valid_records, skip_count = self.validate_ohlcv(df, ticker)

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
