"""Unit tests for feast_online_service and the /market/streaming-features/{ticker} route."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Feast mock — must happen before importing feast_online_service
# ---------------------------------------------------------------------------

def _make_feast_mock(ema: float | None, rsi: float | None, macd: float | None) -> MagicMock:
    mock_feast = MagicMock()
    mock_feast.FeatureStore.return_value.get_online_features.return_value.to_dict.return_value = {
        "ema_20": [ema],
        "rsi_14": [rsi],
        "macd_signal": [macd],
    }
    return mock_feast


# ---------------------------------------------------------------------------
# Service unit tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_streaming_features_returns_values():
    """Happy path — Feast returns all three feature values."""
    mock_feast = _make_feast_mock(155.32, 62.4, 0.073)
    with patch.dict(sys.modules, {"feast": mock_feast}):
        from app.services import feast_online_service
        import importlib
        importlib.reload(feast_online_service)
        from app.services.feast_online_service import get_streaming_features

        result = await get_streaming_features("AAPL")

    assert result.ticker == "AAPL"
    assert result.ema_20 == pytest.approx(155.32)
    assert result.rsi_14 == pytest.approx(62.4)
    assert result.macd_signal == pytest.approx(0.073)
    assert result.available is True
    assert result.source == "flink-indicator-stream"
    assert result.sampled_at is not None


@pytest.mark.asyncio
async def test_get_streaming_features_unavailable():
    """When Feast raises any exception, available=False and all values are None."""
    mock_feast = MagicMock()
    mock_feast.FeatureStore.side_effect = Exception("Redis unavailable")
    with patch.dict(sys.modules, {"feast": mock_feast}):
        from app.services import feast_online_service
        import importlib
        importlib.reload(feast_online_service)
        from app.services.feast_online_service import get_streaming_features

        result = await get_streaming_features("MSFT")

    assert result.available is False
    assert result.ema_20 is None
    assert result.rsi_14 is None
    assert result.macd_signal is None
    assert result.ticker == "MSFT"


@pytest.mark.asyncio
async def test_get_streaming_features_all_none_values():
    """When Feast returns None for all features, available=False (Flink job not running yet)."""
    mock_feast = _make_feast_mock(None, None, None)
    with patch.dict(sys.modules, {"feast": mock_feast}):
        from app.services import feast_online_service
        import importlib
        importlib.reload(feast_online_service)
        from app.services.feast_online_service import get_streaming_features

        result = await get_streaming_features("GOOGL")

    assert result.available is False
    assert result.ema_20 is None
    assert result.rsi_14 is None
    assert result.macd_signal is None


# ---------------------------------------------------------------------------
# Router integration test
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_streaming_features_endpoint_happy_path():
    """Router returns 200 with StreamingFeaturesResponse JSON on success."""
    from unittest.mock import AsyncMock
    from app.main import app
    from app.models.schemas import StreamingFeaturesResponse as SFR

    mock_result = SFR(
        ticker="AAPL",
        ema_20=155.32,
        rsi_14=62.4,
        macd_signal=0.073,
        available=True,
        source="flink-indicator-stream",
        sampled_at="2026-03-30T12:00:00+00:00",
    )

    with patch("app.routers.market.get_streaming_features", new=AsyncMock(return_value=mock_result)), \
         patch("app.routers.market.cache_get", new=AsyncMock(return_value=None)), \
         patch("app.routers.market.cache_set", new=AsyncMock()):
        client = TestClient(app)
        response = client.get("/market/streaming-features/AAPL")

    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "AAPL"
    assert body["available"] is True
    assert body["ema_20"] == pytest.approx(155.32)


@pytest.mark.asyncio
async def test_streaming_features_endpoint_lowercase_ticker():
    """Router normalises lowercase ticker to uppercase in both service call and cache key."""
    from unittest.mock import AsyncMock, call
    from app.main import app
    from app.models.schemas import StreamingFeaturesResponse as SFR

    mock_result = SFR(ticker="AAPL", available=False, source="flink-indicator-stream")

    with patch("app.routers.market.get_streaming_features", new=AsyncMock(return_value=mock_result)) as mock_svc, \
         patch("app.routers.market.cache_get", new=AsyncMock(return_value=None)), \
         patch("app.routers.market.cache_set", new=AsyncMock()):
        client = TestClient(app)
        client.get("/market/streaming-features/aapl")

    mock_svc.assert_called_once_with("AAPL")
