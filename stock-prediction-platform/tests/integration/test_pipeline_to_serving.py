"""TEST-02: ML pipeline → model registry → serving → prediction integration.

Validates the full 11-step training pipeline produces a deployable model,
serves it correctly, and generates valid predictions using synthetic data.
Also validates KServe serving flow integration (Phase 57).
"""

from __future__ import annotations

import json
import pickle
import subprocess
from pathlib import Path

import numpy as np
import pytest

try:
    import boto3
    from botocore.client import Config as BotoConfig

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import httpx

    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


pytestmark = pytest.mark.slow


class TestPipelineToServing:
    """Full ML pipeline round-trip: train → persist → deploy → predict."""

    # Run the pipeline once, share result across all tests in the class.
    @pytest.fixture(autouse=True, scope="class")
    def pipeline_result(self, synthetic_data_dict, tmp_path_factory):
        from ml.pipelines.training_pipeline import run_training_pipeline

        tmp = tmp_path_factory.mktemp("pipeline")
        registry_dir = tmp / "registry"
        serving_dir = tmp / "serving"
        registry_dir.mkdir()
        serving_dir.mkdir()

        result = run_training_pipeline(
            data_dict=synthetic_data_dict,
            registry_dir=str(registry_dir),
            serving_dir=str(serving_dir),
            skip_shap=True,
        )

        # Store on the class so every test method can access them.
        self.__class__._result = result
        self.__class__._registry_dir = registry_dir
        self.__class__._serving_dir = serving_dir
        self.__class__._data_dict = synthetic_data_dict

    @property
    def result(self):
        return self.__class__._result

    @property
    def registry_dir(self) -> Path:
        return self.__class__._registry_dir

    @property
    def serving_dir(self) -> Path:
        return self.__class__._serving_dir

    @property
    def data_dict(self):
        return self.__class__._data_dict

    # ── Test 1 ────────────────────────────────────────────────────────

    def test_full_pipeline_completes(self):
        assert self.result.status == "completed"
        assert len(self.result.steps_completed) == 11
        expected_steps = [
            "load_data",
            "engineer_features",
            "generate_labels",
            "prepare_training_data",
            "train_models",
            "cross_validation",
            "evaluate_models",
            "model_comparison",
            "explainability",
            "select_winner",
            "deploy_model",
        ]
        assert self.result.steps_completed == expected_steps

    # ── Test 2 ────────────────────────────────────────────────────────

    def test_pipeline_trains_multiple_models(self):
        assert self.result.n_models_trained >= 10
        assert self.result.n_tickers == 2

    # ── Test 3 ────────────────────────────────────────────────────────

    def test_winner_selected_and_persisted(self):
        assert self.result.winner_info is not None
        winner_name = self.result.winner_info.get("winner_name", "")
        assert len(winner_name) > 0

        # Winner directory should contain pipeline.pkl + metadata.json
        found_pkl = False
        found_meta = False
        for p in self.registry_dir.rglob("pipeline.pkl"):
            found_pkl = True
        for p in self.registry_dir.rglob("metadata.json"):
            found_meta = True
        assert found_pkl, "pipeline.pkl not found in registry"
        assert found_meta, "metadata.json not found in registry"

    # ── Test 4 ────────────────────────────────────────────────────────

    def test_serving_directory_populated(self):
        assert (self.serving_dir / "pipeline.pkl").exists()
        assert (self.serving_dir / "serving_config.json").exists()
        assert (self.serving_dir / "metadata.json").exists()
        assert (self.serving_dir / "features.json").exists()

    # ── Test 5 ────────────────────────────────────────────────────────

    def test_deployed_model_predicts(self):
        with open(self.serving_dir / "pipeline.pkl", "rb") as f:
            pipeline = pickle.load(f)  # noqa: S301

        with open(self.serving_dir / "features.json") as f:
            feature_names = json.load(f)

        # Create a dummy row with correct number of features
        X = np.zeros((1, len(feature_names)))
        preds = pipeline.predict(X)
        assert len(preds) == 1
        assert np.isfinite(preds[0])

    # ── Test 6 ────────────────────────────────────────────────────────

    def test_generate_predictions_from_serving(self):
        from ml.pipelines.components.predictor import generate_predictions

        predictions = generate_predictions(
            data_dict=self.data_dict,
            serving_dir=str(self.serving_dir),
        )

        assert isinstance(predictions, list)
        assert len(predictions) > 0

        required_keys = {
            "ticker",
            "predicted_price",
            "prediction_date",
            "predicted_date",
            "model_name",
        }
        tickers_seen = set()
        for pred in predictions:
            assert required_keys.issubset(pred.keys())
            assert np.isfinite(pred["predicted_price"])
            tickers_seen.add(pred["ticker"])

        assert tickers_seen == {"AAPL", "MSFT"}

    # ── Test 7 ────────────────────────────────────────────────────────

    def test_save_and_load_predictions(self):
        from ml.pipelines.components.predictor import (
            generate_predictions,
            save_predictions,
        )

        predictions = generate_predictions(
            data_dict=self.data_dict,
            serving_dir=str(self.serving_dir),
        )
        save_predictions(predictions, registry_dir=str(self.registry_dir))

        path = self.registry_dir / "predictions" / "latest.json"
        assert path.exists()

        with open(path) as f:
            loaded = json.load(f)
        assert len(loaded) == len(predictions)

    # ── Test 8 ────────────────────────────────────────────────────────

    def test_pipeline_run_result_audit_trail(self):
        assert len(self.result.run_id) == 12
        assert self.result.started_at
        assert self.result.completed_at
        assert self.result.pipeline_version == "1.0.0"

        # Run result JSON should be persisted
        runs_dir = self.registry_dir / "runs"
        assert runs_dir.exists()
        run_files = list(runs_dir.glob("pipeline_run_*.json"))
        assert len(run_files) >= 1


# =============================================================================
# Phase 57: KServe Serving Flow Integration Tests
# =============================================================================
# These tests validate the KServe-based serving architecture against a live
# Minikube cluster. They require: running cluster, deploy-all.sh executed,
# and a trained model in MinIO.


def _kubectl(*args: str) -> subprocess.CompletedProcess:
    """Run a kubectl command and return the CompletedProcess."""
    return subprocess.run(
        ["kubectl", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.integration
class TestKServeServingFlow:
    """Validate KServe InferenceService replaces legacy PVC-based serving."""

    def test_kserve_inference_service_exists(self):
        """Verify KServe InferenceService resource exists and is Ready."""
        result = _kubectl(
            "get", "inferenceservice", "stock-model-serving",
            "-n", "ml", "-o", "jsonpath={.status.conditions[?(@.type=='Ready')].status}",
        )
        assert result.returncode == 0, f"InferenceService not found: {result.stderr}"
        assert result.stdout.strip() == "True", (
            f"InferenceService not Ready: {result.stdout}"
        )

    def test_kserve_predictor_pod_running(self):
        """Verify KServe predictor pod is in Running state."""
        result = _kubectl(
            "get", "pods", "-n", "ml",
            "-l", "serving.kserve.io/inferenceservice=stock-model-serving",
            "-o", "jsonpath={.items[0].status.phase}",
        )
        assert result.returncode == 0, f"No predictor pods found: {result.stderr}"
        assert result.stdout.strip() == "Running", (
            f"Predictor pod not Running: {result.stdout}"
        )

    @pytest.mark.skipif(not HAS_BOTO3, reason="boto3 not installed")
    def test_model_artifact_in_minio(self):
        """Verify model artifact exists in MinIO serving bucket."""
        # Read MinIO credentials from K8s secret
        cred_result = _kubectl(
            "get", "secret", "minio-secrets", "-n", "storage",
            "-o", "jsonpath={.data.MINIO_ROOT_USER}",
        )
        if cred_result.returncode != 0:
            pytest.skip("MinIO secrets not available")

        import base64

        user_result = _kubectl(
            "get", "secret", "minio-secrets", "-n", "storage",
            "-o", "jsonpath={.data.MINIO_ROOT_USER}",
        )
        pwd_result = _kubectl(
            "get", "secret", "minio-secrets", "-n", "storage",
            "-o", "jsonpath={.data.MINIO_ROOT_PASSWORD}",
        )
        access_key = base64.b64decode(user_result.stdout.strip()).decode()
        secret_key = base64.b64decode(pwd_result.stdout.strip()).decode()

        # Get MinIO endpoint via minikube service URL or port-forward
        ep_result = _kubectl(
            "get", "svc", "minio", "-n", "storage",
            "-o", "jsonpath={.spec.clusterIP}",
        )
        minio_ip = ep_result.stdout.strip()
        endpoint_url = f"http://{minio_ip}:9000"

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=BotoConfig(signature_version="s3v4"),
        )
        objects = s3.list_objects_v2(
            Bucket="model-artifacts",
            Prefix="serving/active/",
        )
        keys = [obj["Key"] for obj in objects.get("Contents", [])]
        assert any("model-settings.json" in k for k in keys), (
            f"model-settings.json not found in MinIO serving/active/: {keys}"
        )

    @pytest.mark.skipif(not HAS_HTTPX, reason="httpx not installed")
    def test_predict_endpoint_uses_kserve(self):
        """Verify /predict/{ticker} returns valid prediction via KServe."""
        # Get API service endpoint
        svc_result = _kubectl(
            "get", "svc", "stock-api", "-n", "ingestion",
            "-o", "jsonpath={.spec.clusterIP}",
        )
        if svc_result.returncode != 0:
            pytest.skip("stock-api service not available")

        api_ip = svc_result.stdout.strip()
        response = httpx.get(f"http://{api_ip}:8000/predict/AAPL", timeout=30)
        assert response.status_code == 200, (
            f"Predict endpoint failed: {response.status_code} {response.text}"
        )
        data = response.json()
        assert "predicted_price" in data
        assert isinstance(data["predicted_price"], (int, float))
        assert data["predicted_price"] > 0

    def test_legacy_serving_deployment_absent(self):
        """Verify legacy model-serving Deployment no longer exists."""
        result = _kubectl(
            "get", "deployment", "model-serving", "-n", "ml",
        )
        assert result.returncode != 0, (
            "Legacy model-serving Deployment still exists — should have been removed"
        )

    def test_legacy_canary_deployment_absent(self):
        """Verify legacy model-serving-canary Deployment no longer exists."""
        result = _kubectl(
            "get", "deployment", "model-serving-canary", "-n", "ml",
        )
        assert result.returncode != 0, (
            "Legacy model-serving-canary Deployment still exists — should have been removed"
        )
