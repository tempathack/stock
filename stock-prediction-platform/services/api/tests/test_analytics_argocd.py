"""Unit tests for the Argo CD branch of flink_service.get_analytics_summary()."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services.flink_service import get_analytics_summary

SAMPLE_ARGOCD_RESPONSE = {
    "items": [
        {"status": {"sync": {"status": "Synced"}}},
        {"status": {"sync": {"status": "Synced"}}},
    ]
}

SAMPLE_ARGOCD_OUT_OF_SYNC = {
    "items": [
        {"status": {"sync": {"status": "Synced"}}},
        {"status": {"sync": {"status": "OutOfSync"}}},
    ]
}


@pytest.mark.asyncio
async def test_get_analytics_summary_argocd_synced():
    """When ARGOCD_TOKEN is set and all apps are Synced, argocd_sync_status == 'Synced'."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_ARGOCD_RESPONSE
    mock_resp.raise_for_status = MagicMock()

    with patch("app.services.flink_service.settings") as mock_settings, \
         patch("app.services.flink_service.get_flink_jobs", new_callable=AsyncMock) as mock_flink, \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_settings.ARGOCD_TOKEN = "test-token"
        mock_settings.ARGOCD_URL = "http://argocd"
        mock_settings.FLINK_REST_URLS = ""

        from app.models.schemas import FlinkJobsResponse
        mock_flink.return_value = FlinkJobsResponse(jobs=[], total_running=0, total_failed=0)

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Patch out DB branch
        with patch("app.services.flink_service.get_engine", return_value=None, create=True):
            result = await get_analytics_summary()

    assert result.argocd_sync_status == "Synced"


@pytest.mark.asyncio
async def test_get_analytics_summary_argocd_out_of_sync():
    """When any app is OutOfSync, argocd_sync_status == 'OutOfSync'."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_ARGOCD_OUT_OF_SYNC
    mock_resp.raise_for_status = MagicMock()

    with patch("app.services.flink_service.settings") as mock_settings, \
         patch("app.services.flink_service.get_flink_jobs", new_callable=AsyncMock) as mock_flink, \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_settings.ARGOCD_TOKEN = "test-token"
        mock_settings.ARGOCD_URL = "http://argocd"
        mock_settings.FLINK_REST_URLS = ""

        from app.models.schemas import FlinkJobsResponse
        mock_flink.return_value = FlinkJobsResponse(jobs=[], total_running=0, total_failed=0)

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with patch("app.services.flink_service.get_engine", return_value=None, create=True):
            result = await get_analytics_summary()

    assert result.argocd_sync_status == "OutOfSync"


@pytest.mark.asyncio
async def test_get_analytics_summary_argocd_no_token():
    """When ARGOCD_TOKEN is empty string, argocd_sync_status is None (skipped)."""
    with patch("app.services.flink_service.settings") as mock_settings, \
         patch("app.services.flink_service.get_flink_jobs", new_callable=AsyncMock) as mock_flink:

        mock_settings.ARGOCD_TOKEN = ""
        mock_settings.FLINK_REST_URLS = ""

        from app.models.schemas import FlinkJobsResponse
        mock_flink.return_value = FlinkJobsResponse(jobs=[], total_running=0, total_failed=0)

        with patch("app.services.flink_service.get_engine", return_value=None, create=True):
            result = await get_analytics_summary()

    assert result.argocd_sync_status is None


@pytest.mark.asyncio
async def test_get_analytics_summary_argocd_unreachable():
    """When Argo CD is unreachable, argocd_sync_status is None (no exception raised)."""
    import httpx
    with patch("app.services.flink_service.settings") as mock_settings, \
         patch("app.services.flink_service.get_flink_jobs", new_callable=AsyncMock) as mock_flink, \
         patch("httpx.AsyncClient") as mock_client_cls:

        mock_settings.ARGOCD_TOKEN = "test-token"
        mock_settings.ARGOCD_URL = "http://argocd"
        mock_settings.FLINK_REST_URLS = ""

        from app.models.schemas import FlinkJobsResponse
        mock_flink.return_value = FlinkJobsResponse(jobs=[], total_running=0, total_failed=0)

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("refused")
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        with patch("app.services.flink_service.get_engine", return_value=None, create=True):
            result = await get_analytics_summary()

    assert result.argocd_sync_status is None
