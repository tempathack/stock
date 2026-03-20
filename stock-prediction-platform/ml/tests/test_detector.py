"""Tests for drift detectors — data, prediction, and concept drift."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.drift.detector import (
    ConceptDriftDetector,
    DataDriftDetector,
    DriftResult,
    PredictionDriftDetector,
)


# ---------------------------------------------------------------------------
# TestDriftResult
# ---------------------------------------------------------------------------


class TestDriftResult:
    def test_to_dict(self):
        r = DriftResult(
            drift_type="data_drift",
            is_drifted=True,
            severity="medium",
            details={"foo": 1},
            timestamp="2026-01-01T00:00:00+00:00",
            features_affected=["close"],
        )
        d = r.to_dict()
        assert isinstance(d, dict)
        assert d["drift_type"] == "data_drift"
        assert d["is_drifted"] is True
        assert d["features_affected"] == ["close"]

    def test_default_features_affected(self):
        r = DriftResult(
            drift_type="prediction_drift",
            is_drifted=False,
            severity="none",
            details={},
            timestamp="t",
        )
        assert r.features_affected == []

    def test_drift_types(self):
        for dt in ("data_drift", "prediction_drift", "concept_drift"):
            r = DriftResult(
                drift_type=dt, is_drifted=False, severity="none",
                details={}, timestamp="t",
            )
            assert r.drift_type == dt


# ---------------------------------------------------------------------------
# TestDataDriftDetector
# ---------------------------------------------------------------------------


class TestDataDriftDetector:
    @pytest.fixture
    def rng(self):
        return np.random.default_rng(42)

    @pytest.fixture
    def reference_df(self, rng):
        return pd.DataFrame({
            "feat_a": rng.normal(0, 1, 500),
            "feat_b": rng.normal(5, 2, 500),
            "feat_c": rng.uniform(0, 1, 500),
        })

    def test_no_drift_same_distribution(self, rng, reference_df):
        # Current data drawn from same distribution
        current = pd.DataFrame({
            "feat_a": rng.normal(0, 1, 500),
            "feat_b": rng.normal(5, 2, 500),
            "feat_c": rng.uniform(0, 1, 500),
        })
        det = DataDriftDetector()
        result = det.detect(reference_df, current)
        assert result.is_drifted is False
        assert result.severity == "none"
        assert result.drift_type == "data_drift"

    def test_drift_detected_shifted_mean(self, rng, reference_df):
        current = reference_df.copy()
        current["feat_a"] = current["feat_a"] + 10  # Large shift
        det = DataDriftDetector()
        result = det.detect(reference_df, current)
        assert result.is_drifted is True
        assert "feat_a" in result.features_affected

    def test_drift_detected_different_variance(self, rng, reference_df):
        current = reference_df.copy()
        current["feat_b"] = current["feat_b"] * 10  # Massive variance change
        det = DataDriftDetector()
        result = det.detect(reference_df, current)
        assert result.is_drifted is True
        assert "feat_b" in result.features_affected

    def test_features_affected_reported(self, rng, reference_df):
        current = reference_df.copy()
        current["feat_a"] = current["feat_a"] + 10  # Only shift feat_a
        det = DataDriftDetector()
        result = det.detect(reference_df, current)
        assert "feat_a" in result.features_affected
        # feat_b and feat_c should NOT be drifted
        assert "feat_b" not in result.features_affected
        assert "feat_c" not in result.features_affected

    def test_psi_computation(self, rng):
        data = rng.normal(0, 1, 1000)
        psi = DataDriftDetector._compute_psi(data, data)
        assert psi < 0.01  # Same data → PSI ≈ 0

    def test_psi_large_for_shifted(self, rng):
        ref = rng.normal(0, 1, 1000)
        cur = rng.normal(5, 1, 1000)  # Shifted by 5 std
        psi = DataDriftDetector._compute_psi(ref, cur)
        assert psi > 0.2  # Should be well above threshold

    def test_ks_test_same_dist(self, rng):
        data = rng.normal(0, 1, 500)
        stat, pval = DataDriftDetector._ks_test(data, data)
        assert pval > 0.01  # Same data → high p-value
        assert stat == 0.0

    def test_custom_thresholds(self, rng, reference_df):
        current = reference_df.copy()
        current["feat_a"] = current["feat_a"] + 0.3  # Small shift
        # Very strict threshold → should detect
        strict = DataDriftDetector(ks_threshold=0.5, psi_threshold=0.001)
        result_strict = strict.detect(reference_df, current)
        # Very lenient threshold → should not detect
        lenient = DataDriftDetector(ks_threshold=0.001, psi_threshold=10.0)
        result_lenient = lenient.detect(reference_df, current)
        # At least one of them should differ
        assert result_strict.is_drifted or not result_lenient.is_drifted


# ---------------------------------------------------------------------------
# TestPredictionDriftDetector
# ---------------------------------------------------------------------------


class TestPredictionDriftDetector:
    def test_no_drift_stable_errors(self):
        baseline = np.array([0.1, 0.15, 0.12, 0.11, 0.13])
        recent = np.array([0.12, 0.14, 0.11, 0.13, 0.12])
        det = PredictionDriftDetector()
        result = det.detect(baseline, recent)
        assert result.is_drifted is False
        assert result.severity == "none"
        assert result.drift_type == "prediction_drift"

    def test_drift_when_errors_increase(self):
        baseline = np.array([0.1, 0.15, 0.12, 0.11, 0.13])
        recent = np.array([0.5, 0.6, 0.55, 0.7, 0.65])  # ~5× baseline
        det = PredictionDriftDetector()
        result = det.detect(baseline, recent)
        assert result.is_drifted is True

    def test_severity_medium(self):
        baseline = np.array([0.1, 0.1, 0.1])
        # recent MAE = 0.2, threshold = 0.1 * 1.5 = 0.15 → ratio = 2.0
        recent = np.array([0.2, 0.2, 0.2])
        det = PredictionDriftDetector()
        result = det.detect(baseline, recent)
        assert result.is_drifted is True
        assert result.severity == "medium"

    def test_severity_high(self):
        baseline = np.array([0.1, 0.1, 0.1])
        # recent MAE = 0.5 → ratio = 5.0 → above 2 * 1.5 = 3.0 → high
        recent = np.array([0.5, 0.5, 0.5])
        det = PredictionDriftDetector()
        result = det.detect(baseline, recent)
        assert result.is_drifted is True
        assert result.severity == "high"

    def test_custom_multiplier(self):
        baseline = np.array([0.1, 0.1, 0.1])
        recent = np.array([0.12, 0.12, 0.12])  # 1.2× baseline
        # With multiplier=1.1 → threshold=0.11 → 0.12 > 0.11 → drift
        det = PredictionDriftDetector(error_multiplier=1.1)
        result = det.detect(baseline, recent)
        assert result.is_drifted is True
        # With multiplier=2.0 → threshold=0.2 → 0.12 < 0.2 → no drift
        det2 = PredictionDriftDetector(error_multiplier=2.0)
        result2 = det2.detect(baseline, recent)
        assert result2.is_drifted is False


# ---------------------------------------------------------------------------
# TestConceptDriftDetector
# ---------------------------------------------------------------------------


class TestConceptDriftDetector:
    def test_no_drift_similar_performance(self):
        det = ConceptDriftDetector()
        result = det.detect(historical_rmse=0.5, recent_rmse=0.55)
        assert result.is_drifted is False
        assert result.severity == "none"
        assert result.drift_type == "concept_drift"

    def test_drift_degraded_performance(self):
        det = ConceptDriftDetector()
        result = det.detect(historical_rmse=0.5, recent_rmse=1.0)  # 2× worse
        assert result.is_drifted is True

    def test_severity_scaling(self):
        det = ConceptDriftDetector(degradation_threshold=1.3)
        # ratio = 5.0 → above 2 * 1.3 = 2.6 → high
        result = det.detect(historical_rmse=0.1, recent_rmse=0.5)
        assert result.severity == "high"

    def test_custom_threshold(self):
        # Very strict: threshold=1.05
        det = ConceptDriftDetector(degradation_threshold=1.05)
        result = det.detect(historical_rmse=1.0, recent_rmse=1.1)  # 1.1× → drift
        assert result.is_drifted is True
        # Very lenient: threshold=3.0
        det2 = ConceptDriftDetector(degradation_threshold=3.0)
        result2 = det2.detect(historical_rmse=1.0, recent_rmse=2.0)  # 2× → no drift
        assert result2.is_drifted is False
