"""Tests for the DriftMonitor orchestrator."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.drift.monitor import DriftCheckResult, DriftMonitor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_features(rng, n: int = 500, shift: float = 0.0) -> pd.DataFrame:
    return pd.DataFrame({
        "feat_a": rng.normal(0 + shift, 1, n),
        "feat_b": rng.normal(5, 2, n),
    })


# ---------------------------------------------------------------------------
# TestDriftCheckResult
# ---------------------------------------------------------------------------


class TestDriftCheckResult:
    def test_to_dict(self):
        from ml.drift.detector import DriftResult

        dr = DriftResult(
            drift_type="data_drift", is_drifted=False, severity="none",
            details={}, timestamp="t",
        )
        cr = DriftCheckResult(
            checked_at="t", data_drift=dr, prediction_drift=dr,
            concept_drift=dr, any_drift=False,
        )
        d = cr.to_dict()
        assert isinstance(d, dict)
        assert d["any_drift"] is False

    def test_any_drift_true_when_data_drifts(self):
        from ml.drift.detector import DriftResult

        dr_ok = DriftResult(
            drift_type="prediction_drift", is_drifted=False,
            severity="none", details={}, timestamp="t",
        )
        dr_bad = DriftResult(
            drift_type="data_drift", is_drifted=True,
            severity="high", details={}, timestamp="t",
        )
        cr = DriftCheckResult(
            checked_at="t", data_drift=dr_bad,
            prediction_drift=dr_ok, concept_drift=dr_ok, any_drift=True,
        )
        assert cr.any_drift is True


# ---------------------------------------------------------------------------
# TestDriftMonitor
# ---------------------------------------------------------------------------


class TestDriftMonitor:
    @pytest.fixture
    def rng(self):
        return np.random.default_rng(42)

    def test_no_drift_clean_data(self, rng):
        ref = _make_features(rng)
        cur = _make_features(rng)
        baseline_err = rng.uniform(0.05, 0.15, 100)
        recent_err = rng.uniform(0.05, 0.15, 100)

        monitor = DriftMonitor()
        result = monitor.check(
            reference_features=ref, current_features=cur,
            baseline_errors=baseline_err, recent_errors=recent_err,
            historical_rmse=0.1, recent_rmse=0.11,
        )
        assert result.any_drift is False
        assert result.data_drift.is_drifted is False
        assert result.prediction_drift.is_drifted is False
        assert result.concept_drift.is_drifted is False

    def test_data_drift_only(self, rng):
        ref = _make_features(rng)
        cur = _make_features(rng, shift=10)  # Large shift
        baseline_err = np.array([0.1, 0.1, 0.1])
        recent_err = np.array([0.1, 0.1, 0.1])

        monitor = DriftMonitor()
        result = monitor.check(
            reference_features=ref, current_features=cur,
            baseline_errors=baseline_err, recent_errors=recent_err,
            historical_rmse=0.1, recent_rmse=0.11,
        )
        assert result.any_drift is True
        assert result.data_drift.is_drifted is True
        assert result.prediction_drift.is_drifted is False
        assert result.concept_drift.is_drifted is False

    def test_prediction_drift_only(self, rng):
        ref = _make_features(rng)
        cur = _make_features(rng)
        baseline_err = np.array([0.1, 0.1, 0.1])
        recent_err = np.array([0.5, 0.6, 0.7])  # 5-7× baseline

        monitor = DriftMonitor()
        result = monitor.check(
            reference_features=ref, current_features=cur,
            baseline_errors=baseline_err, recent_errors=recent_err,
            historical_rmse=0.1, recent_rmse=0.11,
        )
        assert result.any_drift is True
        assert result.data_drift.is_drifted is False
        assert result.prediction_drift.is_drifted is True
        assert result.concept_drift.is_drifted is False

    def test_concept_drift_only(self, rng):
        ref = _make_features(rng)
        cur = _make_features(rng)
        baseline_err = np.array([0.1, 0.1, 0.1])
        recent_err = np.array([0.1, 0.1, 0.1])

        monitor = DriftMonitor()
        result = monitor.check(
            reference_features=ref, current_features=cur,
            baseline_errors=baseline_err, recent_errors=recent_err,
            historical_rmse=0.1, recent_rmse=0.5,  # 5× degradation
        )
        assert result.any_drift is True
        assert result.data_drift.is_drifted is False
        assert result.prediction_drift.is_drifted is False
        assert result.concept_drift.is_drifted is True

    def test_multiple_drifts(self, rng):
        ref = _make_features(rng)
        cur = _make_features(rng, shift=10)
        baseline_err = np.array([0.1, 0.1, 0.1])
        recent_err = np.array([0.5, 0.6, 0.7])

        monitor = DriftMonitor()
        result = monitor.check(
            reference_features=ref, current_features=cur,
            baseline_errors=baseline_err, recent_errors=recent_err,
            historical_rmse=0.1, recent_rmse=0.5,
        )
        assert result.any_drift is True
        assert result.data_drift.is_drifted is True
        assert result.prediction_drift.is_drifted is True
        assert result.concept_drift.is_drifted is True
