"""S3 integration tests — S3Storage client, deployer, DriftLogger, pipeline persistence.

All tests use moto to mock S3 (no real MinIO/AWS needed).
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.models.model_configs import TrainingResult
from ml.models.registry import ModelRegistry
from ml.models.s3_storage import S3Storage
from ml.models.storage_backends import S3StorageBackend


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(
    name: str = "ridge",
    scaler: str = "standard",
    oos_rmse: float = 1.0,
) -> TrainingResult:
    return TrainingResult(
        model_name=name,
        scaler_variant=scaler,
        best_params={"alpha": 1.0},
        fold_metrics=[{"rmse": oos_rmse}],
        oos_metrics={"rmse": oos_rmse, "directional_accuracy": 60.0},
        fold_stability=0.1,
    )


def _make_pipeline() -> Pipeline:
    rng = np.random.default_rng(0)
    X, y = rng.normal(size=(20, 4)), rng.normal(size=20)
    pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
    pipe.fit(X, y)
    return pipe


FEATURES = ["close", "rsi_14", "sma_20", "volume"]


@pytest.fixture
def s3_raw(mock_s3):
    """Return a raw S3Storage client (no endpoint_url, works with moto)."""
    return S3Storage(
        endpoint_url="https://s3.us-east-1.amazonaws.com",
        access_key="testing",
        secret_key="testing",
        region="us-east-1",
    )


@pytest.fixture
def s3_registry_with_winner(mock_s3):
    """Return a ModelRegistry on S3 pre-populated with a winner model."""
    backend = S3StorageBackend(bucket="model-artifacts", prefix="model_registry")
    registry = ModelRegistry(base_dir="model_registry", backend=backend)
    result = _make_result()
    pipeline = _make_pipeline()
    registry.save_model(result, pipeline, FEATURES, is_winner=True)
    return registry


# ---------------------------------------------------------------------------
# TestS3Storage
# ---------------------------------------------------------------------------


class TestS3Storage:
    """Tests for the low-level S3Storage wrapper (s3_storage.py)."""

    def test_upload_download_bytes(self, s3_raw):
        s3_raw.upload_bytes(b"hello-s3", "model-artifacts", "test.bin")
        data = s3_raw.download_bytes("model-artifacts", "test.bin")
        assert data == b"hello-s3"

    def test_upload_download_file(self, s3_raw, tmp_path):
        src = tmp_path / "upload.txt"
        src.write_text("file-content")
        s3_raw.upload_file(src, "model-artifacts", "files/upload.txt")

        dst = tmp_path / "download.txt"
        s3_raw.download_file("model-artifacts", "files/upload.txt", dst)
        assert dst.read_text() == "file-content"

    def test_list_objects(self, s3_raw):
        s3_raw.upload_bytes(b"a", "model-artifacts", "prefix/a.txt")
        s3_raw.upload_bytes(b"b", "model-artifacts", "prefix/b.txt")
        s3_raw.upload_bytes(b"c", "model-artifacts", "other/c.txt")
        keys = s3_raw.list_objects("model-artifacts", "prefix/")
        assert sorted(keys) == ["prefix/a.txt", "prefix/b.txt"]

    def test_object_exists_true(self, s3_raw):
        s3_raw.upload_bytes(b"x", "model-artifacts", "exists.txt")
        assert s3_raw.object_exists("model-artifacts", "exists.txt") is True

    def test_object_exists_false(self, s3_raw):
        assert s3_raw.object_exists("model-artifacts", "nope.txt") is False

    def test_delete_object(self, s3_raw):
        s3_raw.upload_bytes(b"x", "model-artifacts", "del.txt")
        s3_raw.delete_object("model-artifacts", "del.txt")
        assert s3_raw.object_exists("model-artifacts", "del.txt") is False

    def test_delete_prefix(self, s3_raw):
        for i in range(3):
            s3_raw.upload_bytes(b"x", "model-artifacts", f"pfx/{i}.txt")
        deleted = s3_raw.delete_prefix("model-artifacts", "pfx/")
        assert deleted == 3
        assert s3_raw.list_objects("model-artifacts", "pfx/") == []

    def test_copy_object(self, s3_raw):
        s3_raw.upload_bytes(b"original", "model-artifacts", "src.txt")
        s3_raw.copy_object("model-artifacts", "src.txt", "dst.txt")
        assert s3_raw.download_bytes("model-artifacts", "dst.txt") == b"original"

    def test_copy_prefix(self, s3_raw):
        s3_raw.upload_bytes(b"a", "model-artifacts", "from/a.txt")
        s3_raw.upload_bytes(b"b", "model-artifacts", "from/b.txt")
        count = s3_raw.copy_prefix("model-artifacts", "from/", "to/")
        assert count == 2
        assert s3_raw.download_bytes("model-artifacts", "to/a.txt") == b"a"
        assert s3_raw.download_bytes("model-artifacts", "to/b.txt") == b"b"


# ---------------------------------------------------------------------------
# TestDeployerS3
# ---------------------------------------------------------------------------


class TestDeployerS3:
    """Tests for deploy_winner_model in S3 mode."""

    def test_deploy_winner_s3_returns_info(self, s3_registry_with_winner):
        from ml.pipelines.components.deployer import deploy_winner_model

        info = deploy_winner_model(
            registry_dir="model_registry",
            serving_dir="serving/active",
        )
        for key in ("model_name", "scaler_variant", "version", "serving_path", "deployed_at"):
            assert key in info
        assert info["serving_path"].startswith("s3://")

    def test_deploy_winner_s3_writes_serving_config(self, s3_registry_with_winner):
        from ml.pipelines.components.deployer import deploy_winner_model

        deploy_winner_model(
            registry_dir="model_registry",
            serving_dir="serving/active",
        )
        s3 = S3Storage(
            endpoint_url="https://s3.us-east-1.amazonaws.com",
            access_key="testing",
            secret_key="testing",
        )
        assert s3.object_exists("model-artifacts", "serving/active/serving_config.json")
        config = json.loads(
            s3.download_bytes("model-artifacts", "serving/active/serving_config.json"),
        )
        assert config["is_active"] is True
        assert config["model_name"] == "ridge"

    def test_deploy_winner_s3_copies_artifacts(self, s3_registry_with_winner):
        from ml.pipelines.components.deployer import deploy_winner_model

        deploy_winner_model(
            registry_dir="model_registry",
            serving_dir="serving/active",
        )
        s3 = S3Storage(
            endpoint_url="https://s3.us-east-1.amazonaws.com",
            access_key="testing",
            secret_key="testing",
        )
        assert s3.object_exists("model-artifacts", "serving/active/pipeline.pkl")
        assert s3.object_exists("model-artifacts", "serving/active/metadata.json")
        assert s3.object_exists("model-artifacts", "serving/active/features.json")

    def test_deploy_no_winner_raises(self, mock_s3):
        from ml.pipelines.components.deployer import deploy_winner_model

        with pytest.raises(FileNotFoundError):
            deploy_winner_model(
                registry_dir="model_registry",
                serving_dir="serving/active",
            )

    def test_deploy_multi_horizon_s3(self, mock_s3):
        from ml.pipelines.components.deployer import deploy_multi_horizon_winners

        # Populate one horizon with a winner
        backend = S3StorageBackend(
            bucket="model-artifacts", prefix="model_registry/horizon_7d",
        )
        registry = ModelRegistry(
            base_dir="model_registry/horizon_7d", backend=backend,
        )
        registry.save_model(_make_result(), _make_pipeline(), FEATURES, is_winner=True)

        results = deploy_multi_horizon_winners(
            registry_dir="model_registry",
            serving_dir="serving/active",
            horizons=[7],
        )
        assert 7 in results

        s3 = S3Storage(
            endpoint_url="https://s3.us-east-1.amazonaws.com",
            access_key="testing",
            secret_key="testing",
        )
        assert s3.object_exists(
            "model-artifacts", "serving/active/horizons.json",
        )


# ---------------------------------------------------------------------------
# TestDriftLoggerS3
# ---------------------------------------------------------------------------


class TestDriftLoggerS3:
    """Tests for DriftLogger S3 backend in trigger.py."""

    def test_log_event_s3(self, mock_s3):
        from ml.drift.detector import DriftResult
        from ml.drift.trigger import DriftLogger

        logger = DriftLogger(log_dir="drift_logs")
        event = DriftResult(
            drift_type="data",
            is_drifted=True,
            severity="high",
            details={"stat": 0.05},
            timestamp="2026-03-24T00:00:00Z",
            features_affected=["rsi_14"],
        )
        logger.log_event(event)

        s3 = S3Storage(
            endpoint_url="https://s3.us-east-1.amazonaws.com",
            access_key="testing",
            secret_key="testing",
        )
        assert s3.object_exists("drift-logs", "drift_logs/drift_events.jsonl")
        data = s3.download_bytes("drift-logs", "drift_logs/drift_events.jsonl")
        record = json.loads(data.decode().strip())
        assert record["drift_type"] == "data"
        assert record["is_drifted"] is True

    def test_get_recent_events_s3(self, mock_s3):
        from ml.drift.detector import DriftResult
        from ml.drift.trigger import DriftLogger

        logger = DriftLogger(log_dir="drift_logs")
        for i in range(5):
            event = DriftResult(
                drift_type="data",
                is_drifted=True,
                severity="medium",
                details={"idx": i},
                timestamp=f"2026-03-{20 + i}T00:00:00Z",
                features_affected=[],
            )
            logger.log_event(event)

        events = logger.get_recent_events(n=3)
        assert len(events) == 3
        assert events[-1]["details"]["idx"] == 4

    def test_get_recent_events_empty_s3(self, mock_s3):
        from ml.drift.trigger import DriftLogger

        logger = DriftLogger(log_dir="drift_logs")
        assert logger.get_recent_events() == []

    def test_log_file_returns_s3_uri(self, mock_s3):
        from ml.drift.trigger import DriftLogger

        logger = DriftLogger(log_dir="drift_logs")
        assert str(logger.log_file).startswith("s3://")


# ---------------------------------------------------------------------------
# TestSaveRunResultS3
# ---------------------------------------------------------------------------


class TestSaveRunResultS3:
    """Tests for _save_run_result in training_pipeline.py with S3 backend."""

    def test_save_run_result_s3(self, mock_s3):
        from ml.pipelines.training_pipeline import PipelineRunResult, _save_run_result

        result = PipelineRunResult(
            run_id="abc123",
            pipeline_version="1.2.0",
            started_at="2026-03-24T00:00:00Z",
            completed_at="2026-03-24T01:00:00Z",
            status="completed",
        )
        uri = _save_run_result(result, "model_registry")
        assert uri.startswith("s3://")
        assert "pipeline_run_abc123.json" in uri

        s3 = S3Storage(
            endpoint_url="https://s3.us-east-1.amazonaws.com",
            access_key="testing",
            secret_key="testing",
        )
        data = json.loads(
            s3.download_bytes(
                "model-artifacts", "model_registry/runs/pipeline_run_abc123.json",
            ),
        )
        assert data["run_id"] == "abc123"
        assert data["status"] == "completed"


# ---------------------------------------------------------------------------
# TestAppendRetrainingLogS3
# ---------------------------------------------------------------------------


class TestAppendRetrainingLogS3:
    """Tests for _append_retraining_log in drift_pipeline.py with S3 backend."""

    def test_append_retraining_log_s3(self, mock_s3):
        from ml.pipelines.drift_pipeline import _append_retraining_log
        from ml.pipelines.training_pipeline import PipelineRunResult

        result = PipelineRunResult(
            run_id="run001",
            pipeline_version="1.2.0",
            started_at="2026-03-24T00:00:00Z",
            completed_at="2026-03-24T01:00:00Z",
            status="completed",
            winner_info={"winner_name": "ridge_standard"},
        )
        _append_retraining_log(result, "data_drift", "model_registry")

        s3 = S3Storage(
            endpoint_url="https://s3.us-east-1.amazonaws.com",
            access_key="testing",
            secret_key="testing",
        )
        data = s3.download_bytes(
            "model-artifacts", "model_registry/runs/retraining_log.jsonl",
        )
        record = json.loads(data.decode().strip())
        assert record["reason"] == "data_drift"
        assert record["run_id"] == "run001"

    def test_append_multiple_entries_s3(self, mock_s3):
        from ml.pipelines.drift_pipeline import _append_retraining_log
        from ml.pipelines.training_pipeline import PipelineRunResult

        for i in range(3):
            result = PipelineRunResult(
                run_id=f"run{i:03d}",
                pipeline_version="1.2.0",
                started_at="2026-03-24T00:00:00Z",
                status="completed",
            )
            _append_retraining_log(result, "scheduled", "model_registry")

        s3 = S3Storage(
            endpoint_url="https://s3.us-east-1.amazonaws.com",
            access_key="testing",
            secret_key="testing",
        )
        data = s3.download_bytes(
            "model-artifacts", "model_registry/runs/retraining_log.jsonl",
        )
        lines = data.decode().strip().splitlines()
        assert len(lines) == 3
        assert json.loads(lines[0])["run_id"] == "run000"
        assert json.loads(lines[2])["run_id"] == "run002"
