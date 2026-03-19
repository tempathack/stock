"""Tests for ml.evaluation.cross_validation."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression

from ml.evaluation.cross_validation import create_time_series_cv, walk_forward_evaluate


# ---------------------------------------------------------------------------
# create_time_series_cv
# ---------------------------------------------------------------------------


class TestCreateTimeSeriesCV:
    def test_default_splits(self):
        cv = create_time_series_cv()
        assert cv.n_splits == 5

    def test_custom_splits(self):
        cv = create_time_series_cv(n_splits=10)
        assert cv.n_splits == 10

    def test_no_shuffling(self):
        """Train indices must always be before test indices (no shuffling)."""
        cv = create_time_series_cv(n_splits=5)
        X = np.arange(100).reshape(-1, 1)
        for train_idx, test_idx in cv.split(X):
            assert train_idx.max() < test_idx.min()

    def test_fold_count(self):
        cv = create_time_series_cv(n_splits=5)
        X = np.arange(100).reshape(-1, 1)
        folds = list(cv.split(X))
        assert len(folds) == 5


# ---------------------------------------------------------------------------
# walk_forward_evaluate
# ---------------------------------------------------------------------------


class TestWalkForwardEvaluate:
    @pytest.fixture
    def synthetic_data(self):
        """Simple linear data for testing."""
        rng = np.random.default_rng(42)
        X = rng.normal(size=(200, 3))
        y = X @ np.array([1.0, 2.0, 3.0]) + rng.normal(scale=0.1, size=200)
        return X, y

    def test_returns_expected_keys(self, synthetic_data):
        X, y = synthetic_data
        result = walk_forward_evaluate(LinearRegression(), X, y)
        assert "fold_metrics" in result
        assert "oos_metrics" in result
        assert "fold_stability" in result

    def test_fold_count(self, synthetic_data):
        X, y = synthetic_data
        result = walk_forward_evaluate(LinearRegression(), X, y)
        assert len(result["fold_metrics"]) == 5

    def test_custom_cv(self, synthetic_data):
        X, y = synthetic_data
        cv = create_time_series_cv(n_splits=3)
        result = walk_forward_evaluate(LinearRegression(), X, y, cv=cv)
        assert len(result["fold_metrics"]) == 3

    def test_oos_metrics_keys(self, synthetic_data):
        X, y = synthetic_data
        result = walk_forward_evaluate(LinearRegression(), X, y)
        expected_keys = {"r2", "mae", "rmse", "mape", "directional_accuracy", "fold_stability"}
        assert expected_keys == set(result["oos_metrics"].keys())

    def test_fold_stability_is_float(self, synthetic_data):
        X, y = synthetic_data
        result = walk_forward_evaluate(LinearRegression(), X, y)
        assert isinstance(result["fold_stability"], float)
        assert result["fold_stability"] >= 0.0

    def test_linear_model_reasonable_r2(self, synthetic_data):
        X, y = synthetic_data
        result = walk_forward_evaluate(LinearRegression(), X, y)
        # Linear data with small noise — R² should be high
        assert result["oos_metrics"]["r2"] > 0.9
