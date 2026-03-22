"""Shared fixtures for cross-service integration tests."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# sys.path manipulation — make both service packages importable
# ---------------------------------------------------------------------------

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
_API_DIR = str(Path(_REPO_ROOT) / "services" / "api")
_CONSUMER_DIR = str(Path(_REPO_ROOT) / "services" / "kafka-consumer")

for _p in (_REPO_ROOT, _API_DIR, _CONSUMER_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ---------------------------------------------------------------------------
# OHLCV fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_ohlcv_records() -> list[dict]:
    """15 realistic OHLCV dicts — 3 tickers × 5 days, daily (historical)."""
    records = []
    tickers = ["AAPL", "MSFT", "GOOGL"]
    base_prices = {"AAPL": 178.50, "MSFT": 425.30, "GOOGL": 175.20}
    start_date = date(2026, 3, 10)

    for ticker in tickers:
        price = base_prices[ticker]
        for day_offset in range(5):
            d = start_date + timedelta(days=day_offset)
            if d.weekday() >= 5:
                d += timedelta(days=7 - d.weekday())
            open_ = round(price * 1.001, 4)
            close_ = round(price * 0.999, 4)
            high_ = round(max(open_, close_) * 1.003, 4)
            low_ = round(min(open_, close_) * 0.997, 4)
            records.append(
                {
                    "ticker": ticker,
                    "timestamp": f"{d.isoformat()}T16:00:00+00:00",
                    "date": d.isoformat(),
                    "open": open_,
                    "high": high_,
                    "low": low_,
                    "close": close_,
                    "adj_close": close_,
                    "volume": 5_000_000 + day_offset * 100_000,
                    "fetch_mode": "historical",
                    "ingested_at": "2026-03-19T12:00:00+00:00",
                }
            )
            price = close_
    return records


@pytest.fixture
def sample_intraday_records() -> list[dict]:
    """6 intraday OHLCV dicts — 2 tickers × 3 bars."""
    records = []
    for idx, ticker in enumerate(["AAPL", "MSFT"]):
        base = 178.50 if ticker == "AAPL" else 425.30
        for bar in range(3):
            ts = f"2026-03-19T14:{30 + bar * 5:02d}:00+00:00"
            records.append(
                {
                    "ticker": ticker,
                    "timestamp": ts,
                    "open": round(base + bar * 0.1, 4),
                    "high": round(base + bar * 0.1 + 0.5, 4),
                    "low": round(base + bar * 0.1 - 0.3, 4),
                    "close": round(base + bar * 0.1 + 0.2, 4),
                    "volume": 10_000 + bar * 1_000,
                    "fetch_mode": "intraday",
                    "ingested_at": "2026-03-19T12:00:00+00:00",
                }
            )
    return records


# ---------------------------------------------------------------------------
# Mock Kafka message factory
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_kafka_message_factory():
    """Return a factory that creates mock confluent_kafka Message objects."""

    def _factory(record: dict, topic: str = "historical-data") -> MagicMock:
        msg = MagicMock()
        msg.value.return_value = json.dumps(record).encode("utf-8")
        msg.topic.return_value = topic
        msg.error.return_value = None
        msg.key.return_value = record.get("ticker", "").encode("utf-8")
        return msg

    return _factory


# ---------------------------------------------------------------------------
# Synthetic ML data
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def synthetic_data_dict() -> dict[str, pd.DataFrame]:
    """2 tickers × 300 rows of synthetic OHLCV for ML pipeline tests."""
    rng = np.random.default_rng(42)
    tickers = {"AAPL": 178.50, "MSFT": 425.30}
    data: dict[str, pd.DataFrame] = {}

    for ticker, base_price in tickers.items():
        n = 300
        dates = pd.bdate_range(end=pd.Timestamp.today() - pd.Timedelta(days=1), periods=n)
        # Cumulative sum random walk (more stable than cumprod with small n)
        close = base_price + np.cumsum(rng.normal(0, 1, n))
        close = np.maximum(close, 1.0)  # Floor at $1
        spread = np.abs(rng.normal(0, 1, n))
        high = close + spread
        low = close - np.abs(rng.normal(0, 0.8, n))
        open_ = close + rng.normal(0, 0.5, n)
        # Ensure OHLC invariants
        high = np.maximum(high, np.maximum(open_, close))
        low = np.minimum(low, np.minimum(open_, close))
        volume = rng.integers(1_000_000, 50_000_000, size=n).astype(float)

        data[ticker] = pd.DataFrame(
            {
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "adj_close": close,
                "volume": volume,
            },
            index=dates,
        )
    return data


@pytest.fixture
def pipeline_dirs(tmp_path):
    """Create temporary registry and serving directories."""
    registry_dir = tmp_path / "registry"
    serving_dir = tmp_path / "serving"
    registry_dir.mkdir()
    serving_dir.mkdir()
    return registry_dir, serving_dir
