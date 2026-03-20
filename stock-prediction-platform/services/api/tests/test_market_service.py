"""Tests for market_service module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.services.market_service import get_market_overview, get_ticker_indicators


class TestGetMarketOverview:
    def test_returns_empty_when_no_db_url(self):
        result = get_market_overview(db_url=None)
        assert result == []

    def test_returns_empty_when_empty_string(self):
        result = get_market_overview(db_url="")
        assert result == []


class TestGetTickerIndicators:
    def test_with_ohlcv_dataframe(self):
        np.random.seed(42)
        n = 250
        dates = pd.bdate_range("2025-01-01", periods=n)
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        df = pd.DataFrame({
            "date": dates,
            "open": close - np.random.rand(n) * 0.5,
            "high": close + np.random.rand(n) * 1.0,
            "low": close - np.random.rand(n) * 1.0,
            "close": close,
            "volume": np.random.randint(1_000_000, 10_000_000, n),
        })

        result = get_ticker_indicators("AAPL", ohlcv_df=df)
        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["count"] == n
        assert result["latest"] is not None
        assert "rsi_14" in result["latest"]
        assert "macd_line" in result["latest"]
        assert "sma_20" in result["latest"]

    def test_returns_none_when_no_data(self):
        result = get_ticker_indicators("AAPL", ohlcv_df=None, db_url=None)
        assert result is None

    def test_returns_none_for_empty_df(self):
        empty_df = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        result = get_ticker_indicators("AAPL", ohlcv_df=empty_df)
        assert result is None

    def test_series_length_matches_input(self):
        np.random.seed(42)
        n = 50
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        df = pd.DataFrame({
            "date": pd.bdate_range("2025-01-01", periods=n),
            "open": close - 0.5,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": np.random.randint(1_000_000, 10_000_000, n),
        })
        result = get_ticker_indicators("MSFT", ohlcv_df=df)
        assert result is not None
        assert result["count"] == n
        assert len(result["series"]) == n

    def test_handles_uppercase_columns(self):
        np.random.seed(42)
        n = 50
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)
        df = pd.DataFrame({
            "Date": pd.bdate_range("2025-01-01", periods=n),
            "Open": close - 0.5,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": np.random.randint(1_000_000, 10_000_000, n),
        })
        result = get_ticker_indicators("TSLA", ohlcv_df=df)
        assert result is not None
        assert result["ticker"] == "TSLA"
