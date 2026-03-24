"""Tests for /market/overview and /market/indicators/{ticker} endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_OVERVIEW = [
    {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "market_cap": 3000000000000,
        "last_close": 175.50,
        "daily_change_pct": 1.23,
    },
    {
        "ticker": "MSFT",
        "company_name": "Microsoft Corp.",
        "sector": "Technology",
        "market_cap": 2800000000000,
        "last_close": 420.10,
        "daily_change_pct": -0.45,
    },
]

SAMPLE_INDICATORS = {
    "ticker": "AAPL",
    "latest": {
        "date": "2026-03-20",
        "close": 175.5,
        "rsi_14": 55.3,
        "macd_line": 1.2,
        "macd_signal": 0.9,
        "macd_histogram": 0.3,
        "sma_20": 172.0,
        "sma_50": 168.0,
        "sma_200": 160.0,
    },
    "series": [
        {
            "date": "2026-03-19",
            "close": 174.0,
            "rsi_14": 52.1,
        },
        {
            "date": "2026-03-20",
            "close": 175.5,
            "rsi_14": 55.3,
        },
    ],
    "count": 2,
}


class TestMarketOverview:
    """Tests for GET /market/overview."""

    @patch("app.routers.market.get_market_overview", new_callable=AsyncMock)
    def test_returns_overview(self, mock_get):
        mock_get.return_value = SAMPLE_OVERVIEW
        resp = client.get("/market/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["stocks"][0]["ticker"] == "AAPL"
        assert data["stocks"][0]["sector"] == "Technology"

    @patch("app.routers.market.get_market_overview", new_callable=AsyncMock)
    def test_empty_when_no_db(self, mock_get):
        mock_get.return_value = []
        resp = client.get("/market/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["stocks"] == []

    @patch("app.routers.market.get_market_overview", new_callable=AsyncMock)
    def test_response_schema(self, mock_get):
        mock_get.return_value = SAMPLE_OVERVIEW
        resp = client.get("/market/overview")
        data = resp.json()
        assert set(data.keys()) == {"stocks", "count"}
        stock = data["stocks"][0]
        assert "ticker" in stock
        assert "sector" in stock
        assert "market_cap" in stock
        assert "daily_change_pct" in stock


class TestMarketIndicators:
    """Tests for GET /market/indicators/{ticker}."""

    @patch("app.routers.market.get_ticker_indicators", new_callable=AsyncMock)
    def test_returns_indicators(self, mock_get):
        mock_get.return_value = SAMPLE_INDICATORS
        resp = client.get("/market/indicators/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["count"] == 2
        assert data["latest"]["rsi_14"] == 55.3

    @patch("app.routers.market.get_ticker_indicators", new_callable=AsyncMock)
    def test_ticker_not_found(self, mock_get):
        mock_get.return_value = None
        resp = client.get("/market/indicators/ZZZZ")
        assert resp.status_code == 404
        assert "ZZZZ" in resp.json()["detail"]

    @patch("app.routers.market.get_ticker_indicators", new_callable=AsyncMock)
    def test_series_returned(self, mock_get):
        mock_get.return_value = SAMPLE_INDICATORS
        resp = client.get("/market/indicators/AAPL")
        data = resp.json()
        assert len(data["series"]) == 2
        assert data["series"][-1]["close"] == 175.5

    @patch("app.routers.market.get_ticker_indicators", new_callable=AsyncMock)
    def test_response_schema(self, mock_get):
        mock_get.return_value = SAMPLE_INDICATORS
        resp = client.get("/market/indicators/AAPL")
        data = resp.json()
        assert set(data.keys()) == {"ticker", "latest", "series", "count"}
