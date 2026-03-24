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
    INSERT INTO stocks (ticker, company_name)
    VALUES %s
    ON CONFLICT (ticker) DO NOTHING
"""


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
                for r in records
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
        """Ensure all tickers exist in the stocks table (FK requirement)."""
        values = [(t, t) for t in tickers]
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
