"""Unit tests for _get_argocd_sync_status() — K8s CRD approach in flink_service.py."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services.flink_service import _get_argocd_sync_status, get_analytics_summary


# ---------------------------------------------------------------------------
# _get_argocd_sync_status() — direct unit tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_argocd_sync_status_all_synced():
    """Returns 'Synced' when all ArgoCD Application CRDs have sync.status == 'Synced'."""
    mock_api = MagicMock()
    mock_api.list_namespaced_custom_object.return_value = {
        "items": [
            {"status": {"sync": {"status": "Synced"}}},
            {"status": {"sync": {"status": "Synced"}}},
        ]
    }

    with patch("app.services.flink_service.k8s_config") as mock_k8s_config, \
         patch("app.services.flink_service.k8s_client") as mock_k8s_client:
        mock_k8s_config.load_incluster_config = MagicMock()
        mock_k8s_client.CustomObjectsApi.return_value = mock_api
        result = await _get_argocd_sync_status()

    assert result == "Synced"


@pytest.mark.asyncio
async def test_argocd_sync_status_out_of_sync():
    """Returns 'OutOfSync' when any ArgoCD Application has sync.status == 'OutOfSync'."""
    mock_api = MagicMock()
    mock_api.list_namespaced_custom_object.return_value = {
        "items": [
            {"status": {"sync": {"status": "Synced"}}},
            {"status": {"sync": {"status": "OutOfSync"}}},
        ]
    }

    with patch("app.services.flink_service.k8s_config") as mock_k8s_config, \
         patch("app.services.flink_service.k8s_client") as mock_k8s_client:
        mock_k8s_config.load_incluster_config = MagicMock()
        mock_k8s_client.CustomObjectsApi.return_value = mock_api
        result = await _get_argocd_sync_status()

    assert result == "OutOfSync"


@pytest.mark.asyncio
async def test_argocd_sync_status_k8s_error_returns_none():
    """Returns None when the K8s API raises an exception (e.g., RBAC denial, unreachable)."""
    with patch("app.services.flink_service.k8s_config") as mock_k8s_config:
        mock_k8s_config.load_incluster_config.side_effect = Exception("no k8s")
        mock_k8s_config.ConfigException = Exception
        mock_k8s_config.load_kube_config.side_effect = Exception("no kubeconfig")
        result = await _get_argocd_sync_status()

    assert result is None


@pytest.mark.asyncio
async def test_argocd_sync_status_empty_items_returns_synced():
    """Returns 'Synced' when ArgoCD has no applications (empty items list)."""
    mock_api = MagicMock()
    mock_api.list_namespaced_custom_object.return_value = {"items": []}

    with patch("app.services.flink_service.k8s_config") as mock_k8s_config, \
         patch("app.services.flink_service.k8s_client") as mock_k8s_client:
        mock_k8s_config.load_incluster_config = MagicMock()
        mock_k8s_client.CustomObjectsApi.return_value = mock_api
        result = await _get_argocd_sync_status()

    assert result == "Synced"


# ---------------------------------------------------------------------------
# get_analytics_summary() — Feast latency wired via cached helper
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_analytics_summary_feast_latency_wired():
    """get_analytics_summary() returns feast_online_latency_ms from _get_feast_online_latency_cached()."""
    with patch("app.services.flink_service.get_flink_jobs", new_callable=AsyncMock) as mock_flink, \
         patch("app.services.flink_service._get_argocd_sync_status", new_callable=AsyncMock) as mock_argocd, \
         patch("app.services.flink_service._get_feast_online_latency_cached", new_callable=AsyncMock) as mock_feast, \
         patch("app.services.flink_service.get_engine", return_value=None, create=True):

        from app.models.schemas import FlinkJobsResponse
        mock_flink.return_value = FlinkJobsResponse(jobs=[], total_running=2, total_failed=0)
        mock_argocd.return_value = "Synced"
        mock_feast.return_value = 12.5

        result = await get_analytics_summary()

    assert result.feast_online_latency_ms == 12.5
    assert result.argocd_sync_status == "Synced"
    assert result.flink_running_jobs == 2
