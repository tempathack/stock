"""Unit tests for flink_service — Flink REST proxy."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services.flink_service import get_flink_jobs

SAMPLE_FLINK_RESPONSE = {
    "jobs": [
        {"jid": "abc123", "name": "ohlcv-normalizer", "state": "RUNNING",
         "start-time": 1711900000000, "duration": 3600000,
         "tasks": {"running": 2, "total": 2, "created": 0, "scheduled": 0,
                   "deploying": 0, "finished": 0, "canceling": 0, "canceled": 0,
                   "failed": 0, "reconciling": 0, "initializing": 0}}
    ]
}

@pytest.mark.asyncio
async def test_get_flink_jobs_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_FLINK_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    # Limit to one URL so mock returns exactly one job set
    with patch("app.services.flink_service.settings") as mock_settings, \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_settings.FLINK_REST_URLS = "http://flink-rest:8081"
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        result = await get_flink_jobs()

    assert result.total_running == 1
    assert result.total_failed == 0
    assert len(result.jobs) == 1
    assert result.jobs[0].name == "ohlcv-normalizer"
    assert result.jobs[0].state == "RUNNING"

@pytest.mark.asyncio
async def test_get_flink_jobs_unreachable():
    import httpx
    with patch("app.services.flink_service.settings") as mock_settings, \
         patch("httpx.AsyncClient") as mock_client_cls:
        mock_settings.FLINK_REST_URLS = "http://flink-rest:8081"
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("refused")
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        result = await get_flink_jobs()

    assert result.total_running == 0
    assert result.total_failed == 0
    assert result.jobs == []
