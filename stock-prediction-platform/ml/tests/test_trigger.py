"""Tests for DriftLogger and evaluate_and_trigger."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from ml.drift.detector import DriftResult
from ml.drift.monitor import DriftCheckResult
from ml.drift.trigger import DriftLogger, evaluate_and_trigger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_drift_result(drifted: bool = True, dtype: str = "data_drift") -> DriftResult:
    return DriftResult(
        drift_type=dtype,
        is_drifted=drifted,
        severity="medium" if drifted else "none",
        details={"test": True},
        timestamp="2026-01-01T00:00:00+00:00",
        features_affected=["feat_a"] if drifted and dtype == "data_drift" else [],
    )


def _make_features(rng, n: int = 500, shift: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame({
        "feat_a": rng.normal(0 + shift, 1, n),
        "feat_b": rng.normal(5, 2, n),
    })


# ---------------------------------------------------------------------------
# TestDriftLogger
# ---------------------------------------------------------------------------


class TestDriftLogger:
    def test_log_event_creates_file(self, tmp_path):
        logger = DriftLogger(log_dir=str(tmp_path / "logs"))
        logger.log_event(_make_drift_result())
        assert logger.log_file.exists()

    def test_log_event_appends(self, tmp_path):
        logger = DriftLogger(log_dir=str(tmp_path / "logs"))
        logger.log_event(_make_drift_result())
        logger.log_event(_make_drift_result(dtype="prediction_drift"))
        with open(logger.log_file) as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_log_check_logs_all_results(self, tmp_path):
        logger = DriftLogger(log_dir=str(tmp_path / "logs"))
        dr_ok = _make_drift_result(drifted=False, dtype="prediction_drift")
        dr_bad1 = _make_drift_result(drifted=True, dtype="data_drift")
        dr_bad2 = _make_drift_result(drifted=True, dtype="concept_drift")
        check = DriftCheckResult(
            checked_at="t", data_drift=dr_bad1,
            prediction_drift=dr_ok, concept_drift=dr_bad2, any_drift=True,
        )
        logger.log_check(check)
        with open(logger.log_file) as f:
            lines = f.readlines()
        # Only drifted events are logged (data_drift + concept_drift)
        assert len(lines) == 2

    def test_get_recent_events(self, tmp_path):
        logger = DriftLogger(log_dir=str(tmp_path / "logs"))
        for i in range(5):
            logger.log_event(_make_drift_result())
        events = logger.get_recent_events(n=3)
        assert len(events) == 3

    def test_log_event_content(self, tmp_path):
        logger = DriftLogger(log_dir=str(tmp_path / "logs"))
        logger.log_event(_make_drift_result())
        with open(logger.log_file) as f:
            record = json.loads(f.readline())
        assert record["drift_type"] == "data_drift"
        assert record["is_drifted"] is True
        assert record["severity"] == "medium"
        assert "details" in record
        assert "timestamp" in record


# ---------------------------------------------------------------------------
# TestEvaluateAndTrigger
# ---------------------------------------------------------------------------


class TestEvaluateAndTrigger:
    @pytest.fixture
    def rng(self):
        return np.random.default_rng(42)

    def test_no_drift_no_retrain(self, rng, tmp_path):
        ref = _make_features(rng)
        cur = _make_features(rng)
        with patch("ml.drift.trigger.DriftLogger") as mock_logger_cls:
            mock_logger_cls.return_value = DriftLogger(log_dir=str(tmp_path / "logs"))
            result = evaluate_and_trigger(
                reference_features=ref, current_features=cur,
                baseline_errors=np.array([0.1, 0.1]),
                recent_errors=np.array([0.1, 0.1]),
                historical_rmse=0.1, recent_rmse=0.11,
                log_dir=str(tmp_path / "logs"),
                auto_retrain=True,
            )
        assert result.any_drift is False

    def test_drift_triggers_retrain(self, rng, tmp_path):
        ref = _make_features(rng)
        cur = _make_features(rng, shift=10)  # Data drift
        with patch("ml.pipelines.drift_pipeline.trigger_retraining") as mock_retrain:
            result = evaluate_and_trigger(
                reference_features=ref, current_features=cur,
                baseline_errors=np.array([0.1, 0.1]),
                recent_errors=np.array([0.1, 0.1]),
                historical_rmse=0.1, recent_rmse=0.11,
                log_dir=str(tmp_path / "logs"),
                auto_retrain=True,
            )
        assert result.any_drift is True
        mock_retrain.assert_called_once()

    def test_auto_retrain_false_skips_trigger(self, rng, tmp_path):
        ref = _make_features(rng)
        cur = _make_features(rng, shift=10)
        with patch("ml.pipelines.drift_pipeline.trigger_retraining") as mock_retrain:
            result = evaluate_and_trigger(
                reference_features=ref, current_features=cur,
                baseline_errors=np.array([0.1, 0.1]),
                recent_errors=np.array([0.1, 0.1]),
                historical_rmse=0.1, recent_rmse=0.11,
                log_dir=str(tmp_path / "logs"),
                auto_retrain=False,
            )
        assert result.any_drift is True
        mock_retrain.assert_not_called()

    def test_returns_drift_check_result(self, rng, tmp_path):
        ref = _make_features(rng)
        cur = _make_features(rng)
        result = evaluate_and_trigger(
            reference_features=ref, current_features=cur,
            baseline_errors=np.array([0.1, 0.1]),
            recent_errors=np.array([0.1, 0.1]),
            historical_rmse=0.1, recent_rmse=0.11,
            log_dir=str(tmp_path / "logs"),
        )
        assert isinstance(result, DriftCheckResult)

    def test_drift_triggers_retrain_and_predictions(self, rng, tmp_path):
        """When drift is detected and retrain succeeds, predictions are regenerated."""
        from ml.pipelines.training_pipeline import PipelineRunResult

        ref = _make_features(rng)
        cur = _make_features(rng, shift=10)  # Data drift
        data_dict = {"AAPL": pd.DataFrame({"close": rng.normal(100, 1, 50)})}

        mock_result = PipelineRunResult(
            run_id="test-run", pipeline_version="1.0",
            started_at="t", status="completed",
        )

        with patch("ml.pipelines.drift_pipeline.trigger_retraining", return_value=mock_result) as mock_retrain, \
             patch("ml.pipelines.components.predictor.generate_predictions", return_value=[{"ticker": "AAPL"}]) as mock_gen, \
             patch("ml.pipelines.components.predictor.save_predictions") as mock_save:
            evaluate_and_trigger(
                reference_features=ref, current_features=cur,
                baseline_errors=np.array([0.1, 0.1]),
                recent_errors=np.array([0.1, 0.1]),
                historical_rmse=0.1, recent_rmse=0.11,
                log_dir=str(tmp_path / "logs"),
                auto_retrain=True,
                regenerate_predictions=True,
                data_dict=data_dict,
            )
        mock_retrain.assert_called_once()
        mock_gen.assert_called_once()
        mock_save.assert_called_once()

    def test_regenerate_predictions_false_skips(self, rng, tmp_path):
        """When regenerate_predictions=False, predictions are not generated."""
        from ml.pipelines.training_pipeline import PipelineRunResult

        ref = _make_features(rng)
        cur = _make_features(rng, shift=10)  # Data drift
        data_dict = {"AAPL": pd.DataFrame({"close": rng.normal(100, 1, 50)})}

        mock_result = PipelineRunResult(
            run_id="test-run", pipeline_version="1.0",
            started_at="t", status="completed",
        )

        with patch("ml.pipelines.drift_pipeline.trigger_retraining", return_value=mock_result), \
             patch("ml.pipelines.components.predictor.generate_predictions") as mock_gen, \
             patch("ml.pipelines.components.predictor.save_predictions") as mock_save:
            evaluate_and_trigger(
                reference_features=ref, current_features=cur,
                baseline_errors=np.array([0.1, 0.1]),
                recent_errors=np.array([0.1, 0.1]),
                historical_rmse=0.1, recent_rmse=0.11,
                log_dir=str(tmp_path / "logs"),
                auto_retrain=True,
                regenerate_predictions=False,
                data_dict=data_dict,
            )
        mock_gen.assert_not_called()
        mock_save.assert_not_called()
