"""Unit tests for the Argo CD branch of flink_service.get_analytics_summary().

Updated for K8s CRD approach (Plan 03): ArgoCD sync no longer requires ARGOCD_TOKEN.
The ARGOCD_TOKEN-gated httpx branch is replaced by _get_argocd_sync_status().
These summary-level tests now patch _get_argocd_sync_status() and
_get_feast_online_latency_cached() directly. The K8s I/O unit tests are
in this file (lines 142+) and in test_analytics_argocd_k8s.py.
"""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services.flink_service import get_analytics_summary


@pytest.mark.asyncio
async def test_get_analytics_summary_argocd_synced():
    """When _get_argocd_sync_status returns 'Synced', argocd_sync_status == 'Synced'."""
    with patch("app.services.flink_service.get_flink_jobs", new_callable=AsyncMock) as mock_flink, \
         patch("app.services.flink_service._get_argocd_sync_status", new_callable=AsyncMock) as mock_argocd, \
         patch("app.services.flink_service._get_feast_online_latency_cached", new_callable=AsyncMock) as mock_feast, \
         patch("app.services.flink_service.get_engine", return_value=None, create=True):

        from app.models.schemas import FlinkJobsResponse
        mock_flink.return_value = FlinkJobsResponse(jobs=[], total_running=0, total_failed=0)
        mock_argocd.return_value = "Synced"
        mock_feast.return_value = None

        result = await get_analytics_summary()

    assert result.argocd_sync_status == "Synced"


@pytest.mark.asyncio
async def test_get_analytics_summary_argocd_out_of_sync():
    """When any app is OutOfSync, argocd_sync_status == 'OutOfSync'."""
    with patch("app.services.flink_service.get_flink_jobs", new_callable=AsyncMock) as mock_flink, \
         patch("app.services.flink_service._get_argocd_sync_status", new_callable=AsyncMock) as mock_argocd, \
         patch("app.services.flink_service._get_feast_online_latency_cached", new_callable=AsyncMock) as mock_feast, \
         patch("app.services.flink_service.get_engine", return_value=None, create=True):

        from app.models.schemas import FlinkJobsResponse
        mock_flink.return_value = FlinkJobsResponse(jobs=[], total_running=0, total_failed=0)
        mock_argocd.return_value = "OutOfSync"
        mock_feast.return_value = None

        result = await get_analytics_summary()

    assert result.argocd_sync_status == "OutOfSync"


@pytest.mark.asyncio
async def test_get_analytics_summary_argocd_no_token():
    """When K8s is unreachable (no kubeconfig/in-cluster), argocd_sync_status is None."""
    with patch("app.services.flink_service.get_flink_jobs", new_callable=AsyncMock) as mock_flink, \
         patch("app.services.flink_service._get_argocd_sync_status", new_callable=AsyncMock) as mock_argocd, \
         patch("app.services.flink_service._get_feast_online_latency_cached", new_callable=AsyncMock) as mock_feast, \
         patch("app.services.flink_service.get_engine", return_value=None, create=True):

        from app.models.schemas import FlinkJobsResponse
        mock_flink.return_value = FlinkJobsResponse(jobs=[], total_running=0, total_failed=0)
        mock_argocd.return_value = None  # K8s unreachable
        mock_feast.return_value = None

        result = await get_analytics_summary()

    assert result.argocd_sync_status is None


@pytest.mark.asyncio
async def test_get_analytics_summary_argocd_unreachable():
    """When K8s API is unreachable, argocd_sync_status is None (no exception raised to caller)."""
    with patch("app.services.flink_service.get_flink_jobs", new_callable=AsyncMock) as mock_flink, \
         patch("app.services.flink_service._get_argocd_sync_status", new_callable=AsyncMock) as mock_argocd, \
         patch("app.services.flink_service._get_feast_online_latency_cached", new_callable=AsyncMock) as mock_feast, \
         patch("app.services.flink_service.get_engine", return_value=None, create=True):

        from app.models.schemas import FlinkJobsResponse
        mock_flink.return_value = FlinkJobsResponse(jobs=[], total_running=0, total_failed=0)
        mock_argocd.return_value = None  # Exception swallowed inside _get_argocd_sync_status
        mock_feast.return_value = None

        result = await get_analytics_summary()

    assert result.argocd_sync_status is None


# ---------------------------------------------------------------------------
# K8s CRD path tests — targets _get_argocd_sync_status() (added in Plan 03)
# ---------------------------------------------------------------------------

SAMPLE_K8S_SYNCED = {
    "items": [
        {"status": {"sync": {"status": "Synced"}}},
        {"status": {"sync": {"status": "Synced"}}},
    ]
}

SAMPLE_K8S_OUT_OF_SYNC = {
    "items": [
        {"status": {"sync": {"status": "Synced"}}},
        {"status": {"sync": {"status": "OutOfSync"}}},
    ]
}


@pytest.mark.asyncio
async def test_get_argocd_sync_status_synced():
    """K8s CRD returns all Synced -> _get_argocd_sync_status() returns 'Synced'."""
    from app.services.flink_service import _get_argocd_sync_status
    with patch("app.services.flink_service.k8s_config") as mock_cfg, \
         patch("app.services.flink_service.k8s_client") as mock_k8s:
        mock_cfg.load_incluster_config.side_effect = Exception("not in cluster")
        mock_cfg.ConfigException = Exception
        mock_custom = MagicMock()
        mock_custom.list_namespaced_custom_object.return_value = SAMPLE_K8S_SYNCED
        mock_k8s.CustomObjectsApi.return_value = mock_custom
        result = await _get_argocd_sync_status()
    assert result == "Synced"


@pytest.mark.asyncio
async def test_get_argocd_sync_status_out_of_sync():
    """K8s CRD returns one OutOfSync -> _get_argocd_sync_status() returns 'OutOfSync'."""
    from app.services.flink_service import _get_argocd_sync_status
    with patch("app.services.flink_service.k8s_config") as mock_cfg, \
         patch("app.services.flink_service.k8s_client") as mock_k8s:
        mock_cfg.load_incluster_config.side_effect = Exception("not in cluster")
        mock_cfg.ConfigException = Exception
        mock_custom = MagicMock()
        mock_custom.list_namespaced_custom_object.return_value = SAMPLE_K8S_OUT_OF_SYNC
        mock_k8s.CustomObjectsApi.return_value = mock_custom
        result = await _get_argocd_sync_status()
    assert result == "OutOfSync"


@pytest.mark.asyncio
async def test_get_argocd_sync_status_error_returns_none():
    """When K8s raises an exception, _get_argocd_sync_status() returns None (no propagation)."""
    from app.services.flink_service import _get_argocd_sync_status
    with patch("app.services.flink_service.k8s_config") as mock_cfg, \
         patch("app.services.flink_service.k8s_client") as mock_k8s:
        mock_cfg.load_incluster_config.side_effect = Exception("not in cluster")
        mock_cfg.ConfigException = Exception
        mock_custom = MagicMock()
        mock_custom.list_namespaced_custom_object.side_effect = Exception("connection refused")
        mock_k8s.CustomObjectsApi.return_value = mock_custom
        result = await _get_argocd_sync_status()
    assert result is None


@pytest.mark.asyncio
async def test_get_argocd_sync_status_empty_items():
    """K8s CRD returns empty items list -> _get_argocd_sync_status() returns 'Synced'."""
    from app.services.flink_service import _get_argocd_sync_status
    with patch("app.services.flink_service.k8s_config") as mock_cfg, \
         patch("app.services.flink_service.k8s_client") as mock_k8s:
        mock_cfg.load_incluster_config.side_effect = Exception("not in cluster")
        mock_cfg.ConfigException = Exception
        mock_custom = MagicMock()
        mock_custom.list_namespaced_custom_object.return_value = {"items": []}
        mock_k8s.CustomObjectsApi.return_value = mock_custom
        result = await _get_argocd_sync_status()
    assert result == "Synced"
