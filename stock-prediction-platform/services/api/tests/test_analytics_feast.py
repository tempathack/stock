"""Unit tests for feast_service — Feast freshness queries and online latency measurement."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import datetime
import pytest
from app.services.feast_service import get_feast_freshness

NOW = datetime.datetime(2026, 3, 30, 12, 0, 0, tzinfo=datetime.timezone.utc)
FRESH_TS = NOW - datetime.timedelta(minutes=5)     # 300s — fresh
STALE_TS = NOW - datetime.timedelta(hours=2)        # 7200s — stale

@pytest.mark.asyncio
async def test_get_feast_freshness_success():
    rows = [
        {"metadata_key": "ohlcv_stats_fv", "last_updated_timestamp": FRESH_TS},
        {"metadata_key": "technical_indicators_fv", "last_updated_timestamp": STALE_TS},
    ]

    mock_result = MagicMock()
    mock_result.mappings.return_value = rows

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None

    with patch("app.services.feast_service.get_engine", return_value=MagicMock()), \
         patch("app.services.feast_service.get_async_session", return_value=mock_session), \
         patch("app.services.feast_service.datetime") as mock_dt:
        mock_dt.datetime.now.return_value = NOW
        mock_dt.datetime.fromtimestamp = datetime.datetime.fromtimestamp
        mock_dt.timezone = datetime.timezone
        mock_dt.timedelta = datetime.timedelta
        result = await get_feast_freshness()

    assert result.registry_available is True
    assert len(result.views) >= 2

@pytest.mark.asyncio
async def test_get_feast_freshness_db_unavailable():
    with patch("app.services.feast_service.get_engine", return_value=None):
        result = await get_feast_freshness()
    assert result.registry_available is False
    assert result.views == []


# ---------------------------------------------------------------------------
# Tests for measure_feast_online_latency_ms()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_measure_feast_online_latency_ms_feast_unavailable():
    """When _FEAST_AVAILABLE is False, measure_feast_online_latency_ms() returns None."""
    from app.services.feast_service import measure_feast_online_latency_ms
    with patch("app.services.feast_service._FEAST_AVAILABLE", False), \
         patch("app.services.feast_service.get_online_features", None):
        result = await measure_feast_online_latency_ms()
    assert result is None


@pytest.mark.asyncio
async def test_measure_feast_online_latency_ms_feast_available():
    """When _FEAST_AVAILABLE is True and get_online_features() succeeds, returns a non-negative float."""
    from app.services.feast_service import measure_feast_online_latency_ms
    mock_gof = MagicMock(return_value={"feature": 1.0})
    with patch("app.services.feast_service._FEAST_AVAILABLE", True), \
         patch("app.services.feast_service.get_online_features", mock_gof):
        result = await measure_feast_online_latency_ms("AAPL")
    assert result is not None
    assert isinstance(result, float)
    assert result >= 0.0


@pytest.mark.asyncio
async def test_measure_feast_online_latency_ms_feast_raises():
    """When get_online_features() raises, measure_feast_online_latency_ms() swallows and returns None."""
    from app.services.feast_service import measure_feast_online_latency_ms
    mock_gof = MagicMock(side_effect=RuntimeError("redis unavailable"))
    with patch("app.services.feast_service._FEAST_AVAILABLE", True), \
         patch("app.services.feast_service.get_online_features", mock_gof):
        result = await measure_feast_online_latency_ms("AAPL")
    assert result is None
