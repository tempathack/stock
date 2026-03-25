"""Tests for model_metadata_cache — startup loader + in-memory cache."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.model_metadata_cache import (
    get_active_model_metadata,
    load_active_model_metadata,
)


SAMPLE_SERVING_CONFIG = {
    "model_name": "Ridge",
    "scaler_variant": "standard",
    "version": 3,
    "features": ["close", "rsi_14"],
    "artifact_path": "s3://model-artifacts/serving/active/",
    "deployed_at": "2026-03-25T00:00:00Z",
    "is_active": True,
    "oos_metrics": {"oos_rmse": 0.012},
}


class TestGetActiveModelMetadata:
    def test_returns_none_fields_before_load(self):
        """Before startup load, cache returns safe None defaults."""
        import app.services.model_metadata_cache as mod
        mod._active_metadata = None  # reset
        result = get_active_model_metadata()
        assert result["model_name"] is None
        assert result["scaler_variant"] is None
        assert result["version"] is None


class TestLoadActiveModelMetadata:
    def setup_method(self):
        import app.services.model_metadata_cache as mod
        mod._active_metadata = None  # reset cache before each test

    @patch("app.services.model_metadata_cache._sync_fetch_from_minio")
    @pytest.mark.asyncio
    async def test_minio_fetch_returns_model_name(self, mock_sync_fetch):
        mock_sync_fetch.return_value = SAMPLE_SERVING_CONFIG
        await load_active_model_metadata()
        result = get_active_model_metadata()
        assert result["model_name"] == "Ridge"
        assert result["scaler_variant"] == "standard"
        assert result["version"] == 3

    @patch("app.services.model_metadata_cache._sync_fetch_from_minio")
    @patch("app.services.model_metadata_cache._fetch_from_db")
    @pytest.mark.asyncio
    async def test_db_fallback_queries_active_model(self, mock_db, mock_minio):
        mock_minio.return_value = None  # MinIO fails
        mock_db.return_value = {"model_name": "Lasso", "scaler_variant": "quantile", "version": 2}
        await load_active_model_metadata()
        result = get_active_model_metadata()
        assert result["model_name"] == "Lasso"

    @patch("app.services.model_metadata_cache._sync_fetch_from_minio")
    @patch("app.services.model_metadata_cache._fetch_from_db")
    @pytest.mark.asyncio
    async def test_fallback_returns_none_model_name(self, mock_db, mock_minio):
        mock_minio.return_value = None
        mock_db.return_value = None
        await load_active_model_metadata()
        result = get_active_model_metadata()
        assert result["model_name"] is None

    @patch("app.services.model_metadata_cache._sync_fetch_from_minio")
    @patch("app.services.model_metadata_cache._fetch_from_db")
    @pytest.mark.asyncio
    async def test_startup_failure_does_not_raise(self, mock_db, mock_minio):
        mock_minio.side_effect = Exception("unexpected error")
        mock_db.side_effect = Exception("db also broken")
        # Must not raise
        await load_active_model_metadata()

    @patch("boto3.client")
    @pytest.mark.asyncio
    async def test_minio_fetch_uses_s3_path(self, mock_boto_client):
        import os
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps(SAMPLE_SERVING_CONFIG).encode())
        }
        with patch.dict(os.environ, {
            "MINIO_ENDPOINT": "http://minio.storage.svc.cluster.local:9000",
            "MINIO_ROOT_USER": "minioadmin",
            "MINIO_ROOT_PASSWORD": "minioadmin",
        }):
            import app.services.model_metadata_cache as mod
            result = mod._sync_fetch_from_minio()
        call_kwargs = mock_s3.get_object.call_args[1]
        assert call_kwargs["Bucket"] == "model-artifacts"
        assert call_kwargs["Key"] == "serving/active/serving_config.json"
