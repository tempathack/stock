"""Tests for GET /market/candles endpoint — TSDB-01, TSDB-02, TSDB-06."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Sample candle rows as returned by get_candles()
SAMPLE_1H_CANDLES = [
    {"ts": "2026-03-29T10:00:00+00:00", "ticker": "AAPL",
     "open": 170.0, "high": 171.5, "low": 169.5, "close": 171.0,
     "volume": 500000, "vwap": 170.5},
    {"ts": "2026-03-29T09:00:00+00:00", "ticker": "AAPL",
     "open": 169.0, "high": 170.0, "low": 168.5, "close": 170.0,
     "volume": 450000, "vwap": 169.3},
    {"ts": "2026-03-29T08:00:00+00:00", "ticker": "AAPL",
     "open": 168.0, "high": 169.5, "low": 167.5, "close": 169.0,
     "volume": 380000, "vwap": 168.8},
]

SAMPLE_DAILY_CANDLES = [
    {"ts": "2026-03-28T00:00:00+00:00", "ticker": "AAPL",
     "open": 168.0, "high": 172.0, "low": 167.0, "close": 171.0,
     "volume": 5000000, "vwap": 169.5},
    {"ts": "2026-03-27T00:00:00+00:00", "ticker": "AAPL",
     "open": 166.0, "high": 169.0, "low": 165.5, "close": 168.0,
     "volume": 4800000, "vwap": 167.2},
]


class TestCandlesEndpoint:
    """Tests for GET /market/candles."""

    @patch("app.routers.market.get_candles", new_callable=AsyncMock)
    def test_candles_1h(self, mock_get):
        """TSDB-01: 1h interval returns rows from ohlcv_daily_1h_agg."""
        mock_get.return_value = SAMPLE_1H_CANDLES
        resp = client.get("/market/candles?ticker=AAPL&interval=1h")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["interval"] == "1h"
        assert data["count"] == 3
        assert len(data["candles"]) == 3
        first = data["candles"][0]
        assert "ts" in first
        assert "open" in first
        assert "high" in first
        assert "low" in first
        assert "close" in first
        assert "volume" in first

    @patch("app.routers.market.get_candles", new_callable=AsyncMock)
    def test_candles_daily(self, mock_get):
        """TSDB-02: 1d interval returns rows from ohlcv_daily_agg."""
        mock_get.return_value = SAMPLE_DAILY_CANDLES
        resp = client.get("/market/candles?ticker=AAPL&interval=1d")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["interval"] == "1d"
        assert data["count"] == 2

    @patch("app.routers.market.get_candles", new_callable=AsyncMock)
    def test_candles_endpoint_200(self, mock_get):
        """TSDB-06: Default interval returns 200 with candles list."""
        mock_get.return_value = SAMPLE_1H_CANDLES
        resp = client.get("/market/candles?ticker=AAPL&interval=1h")
        assert resp.status_code == 200
        data = resp.json()
        assert "candles" in data
        assert "count" in data
        assert "ticker" in data
        assert "interval" in data

    @patch("app.routers.market.get_candles", new_callable=AsyncMock)
    def test_candles_bad_interval(self, mock_get):
        """TSDB-06: Unsupported interval returns 400."""
        mock_get.return_value = None  # service returns None for unknown interval
        resp = client.get("/market/candles?ticker=AAPL&interval=5m")
        assert resp.status_code == 400
        assert "interval" in resp.json()["detail"].lower()

    @patch("app.routers.market.cache_get", new_callable=AsyncMock)
    @patch("app.routers.market.get_candles", new_callable=AsyncMock)
    def test_candles_cache_hit(self, mock_get, mock_cache_get):
        """TSDB-06: Redis cache hit bypasses DB query."""
        mock_cache_get.return_value = {
            "ticker": "AAPL",
            "interval": "1h",
            "candles": SAMPLE_1H_CANDLES,
            "count": 3,
        }
        resp = client.get("/market/candles?ticker=AAPL&interval=1h")
        assert resp.status_code == 200
        mock_get.assert_not_called()

    @patch("app.routers.market.get_candles", new_callable=AsyncMock)
    def test_candles_no_data(self, mock_get):
        """get_candles returns empty list -> 200 with count=0."""
        mock_get.return_value = []
        resp = client.get("/market/candles?ticker=ZZZZ&interval=1h")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["candles"] == []
