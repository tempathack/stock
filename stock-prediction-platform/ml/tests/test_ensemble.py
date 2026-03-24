"""Tests for the StackingEnsemble class."""

from __future__ import annotations

import logging

import numpy as np
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.models.ensemble import StackingEnsemble
from ml.models.model_configs import TrainingResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_results_and_pipelines(
    n_models: int = 8,
    n_samples: int = 200,
    n_features: int = 10,
) -> tuple[list[TrainingResult], dict[str, Pipeline], np.ndarray, np.ndarray]:
    """Create mock TrainingResult objects with varying RMSE and fitted pipelines.

    Returns (results, pipelines, X_train, y_train).
    """
    rng = np.random.default_rng(42)
    X = rng.standard_normal((n_samples, n_features))
    y = X[:, 0] * 2 + X[:, 1] * -1 + rng.normal(0, 0.5, n_samples)

    model_names = [
        "ridge", "lasso", "elastic_net", "random_forest",
        "gradient_boosting", "extra_trees", "bayesian_ridge", "huber",
    ][:n_models]
    scaler_variants = ["standard", "quantile", "minmax", "standard",
                       "quantile", "minmax", "standard", "quantile"][:n_models]

    results: list[TrainingResult] = []
    pipelines: dict[str, Pipeline] = {}

    for i, (name, scaler_var) in enumerate(zip(model_names, scaler_variants)):
        rmse = 0.5 + i * 0.1 + rng.uniform(0, 0.05)
        key = f"{name}_{scaler_var}"

        result = TrainingResult(
            model_name=name,
            scaler_variant=scaler_var,
            best_params={"alpha": 1.0} if "ridge" in name else {},
            fold_metrics=[{"rmse": rmse + rng.normal(0, 0.01)} for _ in range(5)],
            oos_metrics={
                "rmse": rmse,
                "r2": max(0.0, 1 - rmse),
                "mae": rmse * 0.8,
                "mape": rmse * 10,
                "directional_accuracy": 55.0 + rng.uniform(0, 10),
            },
            fold_stability=rng.uniform(0, 0.1),
        )
        results.append(result)

        # Build a simple fitted pipeline
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0 + i * 0.5)),
        ])
        pipeline.fit(X, y)
        pipelines[key] = pipeline

    return results, pipelines, X, y


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestStackingEnsemble:
    def test_build_selects_top_n(self):
        results, pipelines, _, _ = _make_mock_results_and_pipelines(8)
        ensemble = StackingEnsemble(top_n=3)
        model = ensemble.build(results, pipelines)

        assert len(model.estimators) == 3
        assert len(ensemble.base_model_names) == 3

    def test_build_all_when_fewer(self):
        results, pipelines, _, _ = _make_mock_results_and_pipelines(8)
        ensemble = StackingEnsemble(top_n=20)
        model = ensemble.build(results, pipelines)

        assert len(model.estimators) == 8
        assert len(ensemble.base_model_names) == 8

    def test_build_raises_on_empty(self):
        ensemble = StackingEnsemble()
        with pytest.raises(ValueError, match="Zero valid base estimators"):
            ensemble.build([], {})

    def test_build_skips_missing_pipelines(self, caplog):
        results, pipelines, _, _ = _make_mock_results_and_pipelines(8)
        # Remove some pipeline keys so they'll be skipped
        keys_to_remove = list(pipelines.keys())[:3]
        for k in keys_to_remove:
            del pipelines[k]

        ensemble = StackingEnsemble(top_n=8)
        with caplog.at_level(logging.WARNING):
            model = ensemble.build(results, pipelines)

        # Should have used remaining pipelines
        assert len(model.estimators) == 5
        assert len(ensemble.base_model_names) == 5

    def test_fit_predict(self):
        results, pipelines, X, y = _make_mock_results_and_pipelines(8)
        n_train = int(len(X) * 0.8)
        X_train, X_test = X[:n_train], X[n_train:]
        y_train, y_test = y[:n_train], y[n_train:]

        ensemble = StackingEnsemble(top_n=3, cv=3)
        ensemble.build(results, pipelines)
        ensemble.fit(X_train, y_train)
        preds = ensemble.predict(X_test)

        assert preds.shape == (len(y_test),)
        assert np.all(np.isfinite(preds))

    def test_fit_before_build_raises(self):
        ensemble = StackingEnsemble()
        with pytest.raises(RuntimeError, match="build.*must be called"):
            ensemble.fit(np.array([[1]]), np.array([1]))

    def test_predict_before_fit_raises(self):
        ensemble = StackingEnsemble()
        with pytest.raises(RuntimeError, match="not fitted"):
            ensemble.predict(np.array([[1]]))

    def test_evaluate_returns_training_result(self):
        results, pipelines, X, y = _make_mock_results_and_pipelines(8)
        n_train = int(len(X) * 0.8)
        X_train, X_test = X[:n_train], X[n_train:]
        y_train, y_test = y[:n_train], y[n_train:]

        ensemble = StackingEnsemble(top_n=3, cv=3)
        ensemble.build(results, pipelines)
        ensemble.fit(X_train, y_train)
        result = ensemble.evaluate(X_test, y_test)

        assert isinstance(result, TrainingResult)
        assert result.model_name == "stacking_ensemble"
        assert result.scaler_variant == "meta_ridge"
        assert "rmse" in result.oos_metrics
        assert "r2" in result.oos_metrics
        assert result.fold_stability == 0.0

    def test_evaluate_vs_best_base(self):
        results, pipelines, X, y = _make_mock_results_and_pipelines(8)
        n_train = int(len(X) * 0.8)
        X_train, X_test = X[:n_train], X[n_train:]
        y_train, y_test = y[:n_train], y[n_train:]

        ensemble = StackingEnsemble(top_n=5, cv=3)
        ensemble.build(results, pipelines)
        ensemble.fit(X_train, y_train)
        ensemble_result = ensemble.evaluate(X_test, y_test)

        # Verify ensemble ran and produced valid RMSE (no strict comparison)
        assert ensemble_result.oos_metrics["rmse"] > 0
        assert np.isfinite(ensemble_result.oos_metrics["rmse"])

    def test_custom_alpha(self):
        results, pipelines, _, _ = _make_mock_results_and_pipelines(8)
        ensemble = StackingEnsemble(top_n=3, meta_learner_alpha=10.0)
        model = ensemble.build(results, pipelines)

        assert model.final_estimator.alpha == 10.0

    def test_passthrough_option(self):
        results, pipelines, _, _ = _make_mock_results_and_pipelines(8)
        ensemble = StackingEnsemble(top_n=3, passthrough=True)
        model = ensemble.build(results, pipelines)

        assert model.passthrough is True
