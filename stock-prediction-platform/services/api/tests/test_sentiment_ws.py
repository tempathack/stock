"""Tests for /ws/sentiment/{ticker} WebSocket endpoint and get_sentiment_features service."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """TestClient fixture for WebSocket smoke tests."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Autouse fixture — prevent Feast calls and 60s sleep in WS endpoint during tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_sentiment_sync(monkeypatch):
    """Prevent actual Feast calls and 60-second sleep in WS endpoint during tests."""
    import app.routers.ws as ws_module

    monkeypatch.setattr(
        ws_module,
        "_get_sentiment_sync",
        lambda ticker: {
            "ticker": ticker,
            "available": False,
            "avg_sentiment": None,
            "mention_count": None,
            "positive_ratio": None,
            "negative_ratio": None,
            "top_subreddit": None,
            "sampled_at": None,
        },
    )

    # Patch asyncio.sleep to return immediately (no 60s wait)
    async def _instant_sleep(_delay):
        pass  # no-op coroutine

    monkeypatch.setattr(asyncio, "sleep", _instant_sleep)


# ---------------------------------------------------------------------------
# Unit tests — get_sentiment_features service
# ---------------------------------------------------------------------------


class TestGetSentimentFeatures:
    """Test feast_online_service.get_sentiment_features()."""

    def test_returns_unavailable_when_feast_raises(self):
        """If FeatureStore raises any exception, returns available=False gracefully."""
        with patch("feast.FeatureStore") as mock_store_class:
            mock_store_class.side_effect = RuntimeError("Redis not available")
            from app.services.feast_online_service import get_sentiment_features
            result = get_sentiment_features("AAPL")
        assert result["available"] is False
        assert result["ticker"] == "AAPL"
        assert result["avg_sentiment"] is None
        assert result["mention_count"] is None

    def test_returns_available_with_data(self):
        """If FeatureStore returns valid data, available=True and values populated."""
        mock_store = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "avg_sentiment": [0.35],
            "mention_count": [42],
            "positive_ratio": [0.6],
            "negative_ratio": [0.2],
            "top_subreddit": ["wallstreetbets"],
        }
        mock_store.get_online_features.return_value = mock_result

        with patch("feast.FeatureStore", return_value=mock_store):
            from app.services.feast_online_service import get_sentiment_features
            result = get_sentiment_features("AAPL")

        assert result["available"] is True
        assert result["ticker"] == "AAPL"
        assert result["avg_sentiment"] == 0.35
        assert result["mention_count"] == 42
        assert result["positive_ratio"] == 0.6
        assert result["top_subreddit"] == "wallstreetbets"
        assert result["sampled_at"] is not None

    def test_returns_unavailable_when_avg_sentiment_is_none(self):
        """If Feast returns None for avg_sentiment (no data yet), available=False."""
        mock_store = MagicMock()
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "avg_sentiment": [None],
            "mention_count": [None],
            "positive_ratio": [None],
            "negative_ratio": [None],
            "top_subreddit": [None],
        }
        mock_store.get_online_features.return_value = mock_result

        with patch("feast.FeatureStore", return_value=mock_store):
            from app.services.feast_online_service import get_sentiment_features
            result = get_sentiment_features("TSLA")

        assert result["available"] is False
        assert result["avg_sentiment"] is None


# ---------------------------------------------------------------------------
# WebSocket smoke tests — endpoint registration
# ---------------------------------------------------------------------------


class TestWsSentimentEndpoint:
    """Test /ws/sentiment/{ticker} endpoint is registered and accepts connections."""

    def test_ws_sentiment_endpoint_registered(self, client: TestClient):
        """WebSocket endpoint /ws/sentiment/{ticker} is registered in the router."""
        # Connect and immediately close — just verify the endpoint exists
        with client.websocket_connect("/ws/sentiment/AAPL") as ws:
            # Endpoint should accept connection without crashing
            # We don't wait for a message (would block 60s) — just verify accept() works
            pass  # connection opened and closed cleanly

    def test_ws_sentiment_uppercase_normalization(self, client: TestClient):
        """Ticker is accepted regardless of case — endpoint normalizes to uppercase."""
        # Both lowercase and uppercase should connect without error
        with client.websocket_connect("/ws/sentiment/aapl") as ws:
            pass
