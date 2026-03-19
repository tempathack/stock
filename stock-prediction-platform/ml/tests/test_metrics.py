"""Tests for ml.evaluation.metrics."""

from __future__ import annotations

import numpy as np
import pytest

from ml.evaluation.metrics import (
    compute_all_metrics,
    compute_directional_accuracy,
    compute_fold_stability,
    compute_mae,
    compute_mape,
    compute_r2,
    compute_rmse,
)


# ---------------------------------------------------------------------------
# R²
# ---------------------------------------------------------------------------


class TestR2:
    def test_perfect_predictions(self):
        y = np.array([1.0, 2.0, 3.0])
        assert compute_r2(y, y) == pytest.approx(1.0)

    def test_known_value(self):
        y_true = np.array([3.0, -0.5, 2.0, 7.0])
        y_pred = np.array([2.5, 0.0, 2.0, 8.0])
        assert compute_r2(y_true, y_pred) == pytest.approx(0.9486, abs=1e-3)

    def test_negative_r2(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([10.0, 20.0, 30.0])
        assert compute_r2(y_true, y_pred) < 0


# ---------------------------------------------------------------------------
# MAE
# ---------------------------------------------------------------------------


class TestMAE:
    def test_perfect(self):
        y = np.array([1.0, 2.0, 3.0])
        assert compute_mae(y, y) == pytest.approx(0.0)

    def test_known_value(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.5, 2.5, 3.5])
        assert compute_mae(y_true, y_pred) == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# RMSE
# ---------------------------------------------------------------------------


class TestRMSE:
    def test_perfect(self):
        y = np.array([1.0, 2.0, 3.0])
        assert compute_rmse(y, y) == pytest.approx(0.0)

    def test_known_value(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.1, 2.1, 3.1])
        assert compute_rmse(y_true, y_pred) == pytest.approx(0.1, abs=1e-6)


# ---------------------------------------------------------------------------
# MAPE
# ---------------------------------------------------------------------------


class TestMAPE:
    def test_perfect(self):
        y = np.array([1.0, 2.0, 3.0])
        assert compute_mape(y, y) == pytest.approx(0.0)

    def test_known_value(self):
        y_true = np.array([100.0, 200.0])
        y_pred = np.array([110.0, 180.0])
        # |10/100| + |20/200| = 0.1 + 0.1 = 0.2 / 2 = 0.1 => 10%
        assert compute_mape(y_true, y_pred) == pytest.approx(10.0)

    def test_zero_true_values_excluded(self):
        y_true = np.array([0.0, 100.0])
        y_pred = np.array([5.0, 110.0])
        # Only second element: |10/100| = 0.1 => 10%
        assert compute_mape(y_true, y_pred) == pytest.approx(10.0)

    def test_all_zeros_returns_zero(self):
        y_true = np.array([0.0, 0.0])
        y_pred = np.array([1.0, 2.0])
        assert compute_mape(y_true, y_pred) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Directional Accuracy
# ---------------------------------------------------------------------------


class TestDirectionalAccuracy:
    def test_perfect(self):
        y_true = np.array([1.0, -1.0, 1.0])
        y_pred = np.array([0.5, -2.0, 3.0])
        assert compute_directional_accuracy(y_true, y_pred) == pytest.approx(100.0)

    def test_fifty_percent(self):
        y_true = np.array([1.0, -1.0, 1.0, -1.0])
        y_pred = np.array([1.0, 1.0, 1.0, 1.0])
        assert compute_directional_accuracy(y_true, y_pred) == pytest.approx(50.0)

    def test_empty_returns_zero(self):
        assert compute_directional_accuracy(np.array([]), np.array([])) == 0.0


# ---------------------------------------------------------------------------
# Fold Stability
# ---------------------------------------------------------------------------


class TestFoldStability:
    def test_identical_folds(self):
        assert compute_fold_stability([1.0, 1.0, 1.0]) == pytest.approx(0.0)

    def test_single_fold(self):
        assert compute_fold_stability([1.5]) == 0.0

    def test_known_std(self):
        vals = [1.0, 3.0]
        expected_std = np.std(vals, ddof=1)
        assert compute_fold_stability(vals) == pytest.approx(expected_std)


# ---------------------------------------------------------------------------
# compute_all_metrics
# ---------------------------------------------------------------------------


class TestAllMetrics:
    def test_returns_all_keys(self):
        y_true = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.2, 2.9, 4.1, 5.0])
        result = compute_all_metrics(y_true, y_pred)
        assert set(result.keys()) == {"r2", "mae", "rmse", "mape", "directional_accuracy"}

    def test_values_are_floats(self):
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.1, 2.1, 3.1])
        result = compute_all_metrics(y_true, y_pred)
        for v in result.values():
            assert isinstance(v, float)
