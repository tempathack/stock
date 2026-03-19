"""Shared pytest fixtures for Kafka consumer tests."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest


def _make_kafka_message(record: dict, topic: str = "intraday-data") -> MagicMock:
    """Create a mock confluent_kafka.Message."""
    msg = MagicMock()
    msg.value.return_value = json.dumps(record).encode("utf-8")
    msg.key.return_value = record["ticker"].encode("utf-8")
    msg.topic.return_value = topic
    msg.partition.return_value = 0
    msg.offset.return_value = 0
    msg.error.return_value = None
    return msg


def _make_intraday_record(ticker: str = "AAPL") -> dict:
    """Create a valid intraday OHLCV record matching Phase 6 producer format."""
    return {
        "ticker": ticker,
        "timestamp": "2026-03-19T14:30:00+00:00",
        "open": 172.50,
        "high": 173.20,
        "low": 172.10,
        "close": 172.80,
        "volume": 1234567,
        "fetch_mode": "intraday",
        "ingested_at": "2026-03-19T15:01:00+00:00",
    }


def _make_historical_record(ticker: str = "AAPL") -> dict:
    """Create a valid historical OHLCV record matching Phase 6 producer format."""
    return {
        "ticker": ticker,
        "timestamp": "2026-03-19T00:00:00+00:00",
        "open": 170.00,
        "high": 173.20,
        "low": 169.50,
        "close": 172.80,
        "volume": 5500000,
        "fetch_mode": "historical",
        "ingested_at": "2026-03-19T15:01:00+00:00",
    }


@pytest.fixture
def intraday_record():
    """Single valid intraday OHLCV record."""
    return _make_intraday_record()


@pytest.fixture
def historical_record():
    """Single valid historical OHLCV record."""
    return _make_historical_record()


@pytest.fixture
def intraday_message(intraday_record):
    """Mock Kafka message containing an intraday record."""
    return _make_kafka_message(intraday_record, topic="intraday-data")


@pytest.fixture
def historical_message(historical_record):
    """Mock Kafka message containing a historical record."""
    return _make_kafka_message(historical_record, topic="historical-data")


@pytest.fixture
def intraday_batch():
    """Batch of 5 intraday records for different tickers."""
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    return [_make_intraday_record(t) for t in tickers]


@pytest.fixture
def historical_batch():
    """Batch of 5 historical records for different tickers."""
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
    return [_make_historical_record(t) for t in tickers]


@pytest.fixture
def mock_db_pool():
    """Mock psycopg2 connection pool with conn/cursor chain."""
    pool = MagicMock()
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    pool.getconn.return_value = conn
    return pool


@pytest.fixture
def mock_batch_writer():
    """Mock BatchWriter instance."""
    writer = MagicMock()
    writer.upsert_intraday_batch = MagicMock(return_value=5)
    writer.upsert_daily_batch = MagicMock(return_value=5)
    writer.close = MagicMock()
    return writer
