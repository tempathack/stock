"""Integration test — drift detection → retrain → prediction regeneration cycle."""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.drift.trigger import evaluate_and_trigger
from ml.pipelines.components.predictor import generate_predictions, save_predictions
from ml.pipelines.training_pipeline import PipelineRunResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rng():
    return np.random.default_rng(42)


@pytest.fixture
def reference_features(rng):
    """Stable reference features — no drift."""
    return pd.DataFrame({
        "feat_a": rng.normal(0, 1, 500),
        "feat_b": rng.normal(5, 2, 500),
    })


@pytest.fixture
def drifted_features(rng):
    """Features with large shift to guarantee data drift detection."""
    return pd.DataFrame({
        "feat_a": rng.normal(10, 1, 500),  # Mean shifted from 0 → 10
        "feat_b": rng.normal(5, 2, 500),
    })


@pytest.fixture
def synthetic_ohlcv(rng):
    """OHLCV data suitable for feature engineering and prediction."""
    dates = pd.bdate_range("2020-01-01", periods=300)
    data = {}
    for ticker in ["AAPL", "MSFT"]:
        close = 100 + np.cumsum(rng.normal(0, 1, 300))
        close = np.maximum(close, 1.0)
        data[ticker] = pd.DataFrame({
            "open": close + rng.normal(0, 0.5, 300),
            "high": close + abs(rng.normal(0, 1, 300)),
            "low": close - abs(rng.normal(0, 1, 300)),
            "close": close,
            "volume": rng.integers(1_000_000, 10_000_000, 300).astype(float),
        }, index=dates)
    return data


@pytest.fixture
def serving_setup(tmp_path, synthetic_ohlcv):
    """Create serving dir with a trained pipeline + registry dir."""
    from ml.pipelines.components.feature_engineer import engineer_features

    srv = tmp_path / "serving"
    srv.mkdir()

    enriched = engineer_features(synthetic_ohlcv)
    sample_df = list(enriched.values())[0]
    feature_names = [
        c for c in sample_df.columns
        if c not in ("open", "high", "low", "close", "volume")
        and sample_df[c].dtype in (np.float64, np.float32, np.int64)
    ]
    if not feature_names:
        feature_names = ["close", "volume"]

    clean = sample_df[feature_names].dropna()
    X = clean.values
    y = np.random.default_rng(99).normal(0, 1, len(X))
    pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
    pipe.fit(X, y)

    with open(srv / "pipeline.pkl", "wb") as f:
        pickle.dump(pipe, f)
    with open(srv / "features.json", "w") as f:
        json.dump(feature_names, f)
    with open(srv / "metadata.json", "w") as f:
        json.dump({"model_name": "ridge_v1", "version": 1}, f)

    registry = tmp_path / "registry"
    registry.mkdir()

    return str(srv), str(registry)


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


class TestDriftRetrainPredictCycle:
    """End-to-end: synthetic drift → retrain (mocked) → predictions generated."""

    def test_drift_retrain_predict_cycle(
        self, reference_features, drifted_features, synthetic_ohlcv, serving_setup,
        tmp_path,
    ):
        serving_dir, registry_dir = serving_setup

        completed_result = PipelineRunResult(
            run_id="int-test-001",
            pipeline_version="1.0",
            started_at="2026-01-01T00:00:00+00:00",
            status="completed",
        )

        with patch(
            "ml.pipelines.drift_pipeline.trigger_retraining",
            return_value=completed_result,
        ) as mock_retrain:
            check_result = evaluate_and_trigger(
                reference_features=reference_features,
                current_features=drifted_features,
                baseline_errors=np.array([0.1, 0.1]),
                recent_errors=np.array([0.1, 0.1]),
                historical_rmse=0.1,
                recent_rmse=0.11,
                data_dict=synthetic_ohlcv,
                registry_dir=registry_dir,
                serving_dir=serving_dir,
                log_dir=str(tmp_path / "logs"),
                auto_retrain=True,
                regenerate_predictions=True,
            )

        # 1. Drift was detected
        assert check_result.any_drift is True

        # 2. Retraining was triggered
        mock_retrain.assert_called_once()
        call_kwargs = mock_retrain.call_args
        assert call_kwargs.kwargs.get("reason") == "data_drift"

        # 3. Predictions were saved to registry
        pred_file = Path(registry_dir) / "predictions" / "latest.json"
        assert pred_file.exists(), "Predictions file should have been created"

        with open(pred_file) as f:
            predictions = json.load(f)

        assert len(predictions) == 2  # AAPL + MSFT
        tickers = {p["ticker"] for p in predictions}
        assert tickers == {"AAPL", "MSFT"}

        # 4. Each prediction has the right structure
        for pred in predictions:
            assert "predicted_price" in pred
            assert isinstance(pred["predicted_price"], float)
            assert pred["model_name"] == "ridge_v1"

    def test_no_drift_skips_retrain_and_predict(
        self, reference_features, synthetic_ohlcv, serving_setup, tmp_path, rng,
    ):
        """When no drift is detected, neither retrain nor predict is called."""
        serving_dir, registry_dir = serving_setup
        stable_current = pd.DataFrame({
            "feat_a": rng.normal(0, 1, 500),
            "feat_b": rng.normal(5, 2, 500),
        })

        with patch(
            "ml.pipelines.drift_pipeline.trigger_retraining",
        ) as mock_retrain:
            check_result = evaluate_and_trigger(
                reference_features=reference_features,
                current_features=stable_current,
                baseline_errors=np.array([0.1, 0.1]),
                recent_errors=np.array([0.1, 0.1]),
                historical_rmse=0.1,
                recent_rmse=0.11,
                data_dict=synthetic_ohlcv,
                registry_dir=registry_dir,
                serving_dir=serving_dir,
                log_dir=str(tmp_path / "logs"),
                auto_retrain=True,
                regenerate_predictions=True,
            )

        assert check_result.any_drift is False
        mock_retrain.assert_not_called()
        pred_file = Path(registry_dir) / "predictions" / "latest.json"
        assert not pred_file.exists()

    def test_failed_retrain_skips_predictions(
        self, reference_features, drifted_features, synthetic_ohlcv,
        serving_setup, tmp_path,
    ):
        """When retrain fails, predictions are not regenerated."""
        serving_dir, registry_dir = serving_setup

        failed_result = PipelineRunResult(
            run_id="int-test-fail",
            pipeline_version="1.0",
            started_at="2026-01-01T00:00:00+00:00",
            status="failed",
            error="training error",
        )

        with patch(
            "ml.pipelines.drift_pipeline.trigger_retraining",
            return_value=failed_result,
        ):
            evaluate_and_trigger(
                reference_features=reference_features,
                current_features=drifted_features,
                baseline_errors=np.array([0.1, 0.1]),
                recent_errors=np.array([0.1, 0.1]),
                historical_rmse=0.1,
                recent_rmse=0.11,
                data_dict=synthetic_ohlcv,
                registry_dir=registry_dir,
                serving_dir=serving_dir,
                log_dir=str(tmp_path / "logs"),
                auto_retrain=True,
                regenerate_predictions=True,
            )

        pred_file = Path(registry_dir) / "predictions" / "latest.json"
        assert not pred_file.exists(), "Predictions should not be saved on failed retrain"
