"""Database writer — idempotent upsert of OHLCV records to PostgreSQL."""

from __future__ import annotations

import time as _time
from datetime import datetime

import psycopg2
import psycopg2.pool
from psycopg2.extras import execute_values
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from consumer.config import settings
from consumer.logging import get_logger
from consumer.metrics import batch_write_duration_seconds

try:
    import yfinance as yf
    _YFINANCE_AVAILABLE = True
except ImportError:
    _YFINANCE_AVAILABLE = False

logger = get_logger(__name__)

_INTRADAY_UPSERT_SQL = """
    INSERT INTO ohlcv_intraday (ticker, timestamp, open, high, low, close, volume)
    VALUES %s
    ON CONFLICT (ticker, timestamp) DO UPDATE SET
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume
"""

_DAILY_UPSERT_SQL = """
    INSERT INTO ohlcv_daily (ticker, date, open, high, low, close, volume)
    VALUES %s
    ON CONFLICT (ticker, date) DO UPDATE SET
        open = EXCLUDED.open,
        high = EXCLUDED.high,
        low = EXCLUDED.low,
        close = EXCLUDED.close,
        volume = EXCLUDED.volume
"""

_ENSURE_TICKERS_SQL = """
    INSERT INTO stocks (ticker, company_name, sector)
    VALUES %s
    ON CONFLICT (ticker) DO UPDATE SET
        company_name = CASE
            WHEN EXCLUDED.company_name IS NOT NULL AND EXCLUDED.company_name != EXCLUDED.ticker
            THEN EXCLUDED.company_name
            ELSE stocks.company_name
        END,
        sector = CASE
            WHEN EXCLUDED.sector IS NOT NULL
            THEN EXCLUDED.sector
            ELSE stocks.sector
        END
"""


def _fetch_ticker_metadata(ticker: str) -> tuple[str | None, str | None]:
    """Fetch company_name and sector for a ticker from yfinance.

    Returns (company_name, sector) tuple. Returns (None, None) on failure.
    """
    if not _YFINANCE_AVAILABLE:
        return None, None
    try:
        info = yf.Ticker(ticker).info
        company_name = info.get("longName") or info.get("shortName")
        sector = info.get("sector")
        return company_name, sector
    except Exception:
        logger.warning("yfinance lookup failed for %s — falling back to ticker symbol", ticker)
        return None, None


class BatchWriter:
    """Writes batches of OHLCV records to PostgreSQL with idempotent upserts."""

    def __init__(self, pool=None):
        if pool is not None:
            self._pool = pool
        else:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1, maxconn=5, dsn=settings.DATABASE_URL
            )

    def upsert_intraday_batch(self, records: list[dict]) -> int:
        """Upsert intraday OHLCV records into ohlcv_intraday."""
        conn = self._pool.getconn()
        try:
            tickers = {r["ticker"] for r in records}
            self._ensure_tickers(tickers, conn)
            values = [
                (r["ticker"], r["timestamp"], r["open"], r["high"], r["low"], r["close"], r["volume"])
                for r in records
            ]
            start = _time.monotonic()
            self._execute_upsert(_INTRADAY_UPSERT_SQL, values, conn)
            batch_write_duration_seconds.labels(table="ohlcv_intraday").observe(
                _time.monotonic() - start
            )
        except Exception as exc:
            conn.rollback()
            self._dead_letter(records, exc)
            raise
        finally:
            self._pool.putconn(conn)
        return len(records)

    def upsert_daily_batch(self, records: list[dict]) -> int:
        """Upsert daily OHLCV records into ohlcv_daily."""
        conn = self._pool.getconn()
        try:
            tickers = {r["ticker"] for r in records}
            self._ensure_tickers(tickers, conn)
            # Deduplicate by (ticker, date): keep last record per day to avoid
            # CardinalityViolation when yfinance returns multiple intraday bars
            # for the same partial day (e.g., today's open bar).
            seen: dict[tuple, dict] = {}
            for r in records:
                key = (r["ticker"], datetime.fromisoformat(r["timestamp"]).date())
                seen[key] = r
            values = [
                (
                    r["ticker"],
                    datetime.fromisoformat(r["timestamp"]).date(),
                    r["open"],
                    r["high"],
                    r["low"],
                    r["close"],
                    r["volume"],
                )
                for r in seen.values()
            ]
            start = _time.monotonic()
            self._execute_upsert(_DAILY_UPSERT_SQL, values, conn)
            batch_write_duration_seconds.labels(table="ohlcv_daily").observe(
                _time.monotonic() - start
            )
        except Exception as exc:
            conn.rollback()
            self._dead_letter(records, exc)
            raise
        finally:
            self._pool.putconn(conn)
        return len(records)

    def _ensure_tickers(self, tickers: set[str], conn) -> None:
        """Ensure all tickers exist in the stocks table (FK requirement).

        Fetches company_name and sector from yfinance for enriched inserts.
        Falls back to ticker symbol as company_name if yfinance is unavailable.
        """
        values = []
        for t in tickers:
            company_name, sector = _fetch_ticker_metadata(t)
            values.append((t, company_name or t, sector))
        with conn.cursor() as cur:
            execute_values(cur, _ENSURE_TICKERS_SQL, values)
        conn.commit()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        retry=retry_if_exception_type((psycopg2.OperationalError, psycopg2.InterfaceError)),
        reraise=True,
    )
    def _execute_upsert(self, sql: str, values: list[tuple], conn) -> None:
        """Execute a batch upsert with retry on transient DB errors."""
        with conn.cursor() as cur:
            execute_values(cur, sql, values)
        conn.commit()

    def _dead_letter(self, records: list[dict], error: Exception) -> None:
        """Log failed records at ERROR level for dead-letter handling."""
        for record in records:
            logger.error(
                "dead_letter_record",
                ticker=record.get("ticker"),
                timestamp=record.get("timestamp"),
                fetch_mode=record.get("fetch_mode"),
                error=str(error),
                record=record,
            )

    def close(self) -> None:
        """Close the connection pool."""
        self._pool.closeall()
