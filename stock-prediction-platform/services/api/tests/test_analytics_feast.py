"""Unit tests for feast_service — Feast freshness queries."""
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
