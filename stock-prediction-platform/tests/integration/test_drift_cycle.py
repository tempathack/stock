"""TEST-04: Drift detection → retraining → redeployment → prediction cycle.

Validates the full automated drift response: detect drift, trigger
retraining, deploy new model, and regenerate predictions.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.drift.monitor import DriftMonitor
from ml.drift.trigger import DriftLogger, evaluate_and_trigger
from ml.pipelines.components.feature_engineer import engineer_features
from ml.pipelines.training_pipeline import run_training_pipeline

pytestmark = pytest.mark.slow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def baseline_environment(synthetic_data_dict, tmp_path_factory):
    """Train an initial model to establish the pre-drift baseline."""
    tmp = tmp_path_factory.mktemp("drift_cycle")
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
    assert result.status == "completed"

    return {
        "registry_dir": registry_dir,
        "serving_dir": serving_dir,
        "data_dict": synthetic_data_dict,
        "result": result,
    }


@pytest.fixture
def drifted_features(synthetic_data_dict):
    """Split features into reference/current and shift current to cause drift."""
    enriched = engineer_features(synthetic_data_dict)

    # Stack all tickers into a single DataFrame
    all_frames = []
    for ticker, df in enriched.items():
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        all_frames.append(df[numeric_cols].dropna())

    combined = pd.concat(all_frames, ignore_index=True)
    split = int(len(combined) * 0.7)
    reference = combined.iloc[:split]
    current = combined.iloc[split:].copy()

    # Inject systematic shift to trigger data drift
    for col in current.columns:
        current[col] = current[col] * 1.3 + 5.0

    return reference, current


@pytest.fixture
def drifted_errors():
    """Error arrays that trigger prediction + concept drift."""
    rng = np.random.RandomState(42)
    baseline_errors = rng.normal(0, 0.02, 100)
    recent_errors = rng.normal(0.05, 0.04, 100)

    historical_rmse = float(np.sqrt(np.mean(baseline_errors**2)))
    recent_rmse = float(np.sqrt(np.mean(recent_errors**2)))

    return baseline_errors, recent_errors, historical_rmse, recent_rmse


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDriftCycle:
    """TEST-04: Full drift → retrain → redeploy → predict cycle."""

    # ── Test 1 ────────────────────────────────────────────────────────

    def test_drift_detection_triggers(self, drifted_features, drifted_errors):
        reference, current = drifted_features
        baseline_errors, recent_errors, hist_rmse, rec_rmse = drifted_errors

        monitor = DriftMonitor()
        check_result = monitor.check(
            reference_features=reference,
            current_features=current,
            baseline_errors=baseline_errors,
            recent_errors=recent_errors,
            historical_rmse=hist_rmse,
            recent_rmse=rec_rmse,
        )

        assert check_result.any_drift is True
        drifted_types = []
        if check_result.data_drift.is_drifted:
            drifted_types.append("data_drift")
        if check_result.prediction_drift.is_drifted:
            drifted_types.append("prediction_drift")
        if check_result.concept_drift.is_drifted:
            drifted_types.append("concept_drift")
        assert len(drifted_types) >= 1

    # ── Test 2 ────────────────────────────────────────────────────────

    def test_drift_logger_persists_events(
        self, drifted_features, drifted_errors, tmp_path,
    ):
        reference, current = drifted_features
        baseline_errors, recent_errors, hist_rmse, rec_rmse = drifted_errors

        monitor = DriftMonitor()
        check_result = monitor.check(
            reference, current, baseline_errors, recent_errors, hist_rmse, rec_rmse,
        )

        log_dir = tmp_path / "drift_logs"
        drift_logger = DriftLogger(log_dir=str(log_dir))
        drift_logger.log_check(check_result)

        log_file = log_dir / "drift_events.jsonl"
        assert log_file.exists()

        with open(log_file) as f:
            lines = f.readlines()
        assert len(lines) >= 1

        for line in lines:
            event = json.loads(line)
            for key in ("drift_type", "is_drifted", "severity", "details", "timestamp"):
                assert key in event

    # ── Test 3 ────────────────────────────────────────────────────────

    def test_evaluate_and_trigger_runs_retraining(
        self, baseline_environment, drifted_features, drifted_errors,
    ):
        env = baseline_environment
        reference, current = drifted_features
        baseline_errors, recent_errors, hist_rmse, rec_rmse = drifted_errors

        check_result = evaluate_and_trigger(
            reference_features=reference,
            current_features=current,
            baseline_errors=baseline_errors,
            recent_errors=recent_errors,
            historical_rmse=hist_rmse,
            recent_rmse=rec_rmse,
            data_dict=env["data_dict"],
            registry_dir=str(env["registry_dir"]),
            serving_dir=str(env["serving_dir"]),
            log_dir=str(env["registry_dir"] / "drift_logs"),
            auto_retrain=True,
            regenerate_predictions=True,
            skip_shap=True,
        )

        assert check_result.any_drift is True

    # ── Test 4 ────────────────────────────────────────────────────────

    def test_retraining_produces_new_model(self, baseline_environment):
        env = baseline_environment
        runs_dir = env["registry_dir"] / "runs"
        assert runs_dir.exists()
        run_files = list(runs_dir.glob("pipeline_run_*.json"))
        # At least 2: initial training + retrain from Test 3
        assert len(run_files) >= 2

        # Newest run should be completed
        newest = max(run_files, key=lambda p: p.stat().st_mtime)
        with open(newest) as f:
            run_data = json.load(f)
        assert run_data["status"] == "completed"

    # ── Test 5 ────────────────────────────────────────────────────────

    def test_serving_directory_updated_after_retrain(self, baseline_environment):
        env = baseline_environment
        serving_dir = env["serving_dir"]

        assert (serving_dir / "pipeline.pkl").exists()
        assert (serving_dir / "serving_config.json").exists()

    # ── Test 6 ────────────────────────────────────────────────────────

    def test_predictions_regenerated_after_retrain(self, baseline_environment):
        env = baseline_environment
        pred_path = env["registry_dir"] / "predictions" / "latest.json"
        assert pred_path.exists()

        with open(pred_path) as f:
            predictions = json.load(f)

        tickers_seen = {p["ticker"] for p in predictions}
        assert tickers_seen == {"AAPL", "MSFT"}

    # ── Test 7 ────────────────────────────────────────────────────────

    def test_retraining_log_records_drift_reason(self, baseline_environment):
        env = baseline_environment
        log_path = env["registry_dir"] / "runs" / "retraining_log.jsonl"
        assert log_path.exists()

        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) >= 1

        entry = json.loads(lines[-1])
        assert entry["reason"] in ("data_drift", "prediction_drift", "concept_drift")
        assert entry["status"] == "completed"
        assert "run_id" in entry

    # ── Test 8 ────────────────────────────────────────────────────────

    def test_full_cycle_idempotent(
        self, baseline_environment, drifted_features, drifted_errors,
    ):
        """Running the drift cycle twice should not error."""
        env = baseline_environment
        reference, current = drifted_features
        baseline_errors, recent_errors, hist_rmse, rec_rmse = drifted_errors

        # Second run (first was Test 3)
        check_result = evaluate_and_trigger(
            reference_features=reference,
            current_features=current,
            baseline_errors=baseline_errors,
            recent_errors=recent_errors,
            historical_rmse=hist_rmse,
            recent_rmse=rec_rmse,
            data_dict=env["data_dict"],
            registry_dir=str(env["registry_dir"]),
            serving_dir=str(env["serving_dir"]),
            log_dir=str(env["registry_dir"] / "drift_logs"),
            auto_retrain=True,
            regenerate_predictions=True,
            skip_shap=True,
        )

        assert check_result.any_drift is True

        # Retraining log should have multiple entries
        log_path = env["registry_dir"] / "runs" / "retraining_log.jsonl"
        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) >= 2
