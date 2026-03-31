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
