"""Tests for ml.evaluation.shap_analysis."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.evaluation.shap_analysis import (
    compute_feature_importance,
    compute_shap_values,
    get_explainer_type,
    get_shap_summary,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(42)


@pytest.fixture
def sample_X(rng) -> np.ndarray:
    return rng.normal(size=(100, 4))


@pytest.fixture
def feature_names() -> list[str]:
    return ["close", "rsi_14", "sma_20", "volume"]


@pytest.fixture
def fitted_ridge_pipeline(rng, sample_X) -> Pipeline:
    y = rng.normal(size=len(sample_X))
    pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
    pipe.fit(sample_X, y)
    return pipe


@pytest.fixture
def fitted_rf_pipeline(rng, sample_X) -> Pipeline:
    y = rng.normal(size=len(sample_X))
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestRegressor(n_estimators=10, random_state=42)),
    ])
    pipe.fit(sample_X, y)
    return pipe


@pytest.fixture
def fitted_knn_pipeline(rng, sample_X) -> Pipeline:
    y = rng.normal(size=len(sample_X))
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("model", KNeighborsRegressor(n_neighbors=3)),
    ])
    pipe.fit(sample_X, y)
    return pipe


# ---------------------------------------------------------------------------
# TestGetExplainerType
# ---------------------------------------------------------------------------


class TestGetExplainerType:
    def test_tree_model_returns_tree(self):
        assert get_explainer_type("random_forest") == "tree"

    def test_linear_model_returns_linear(self):
        assert get_explainer_type("ridge") == "linear"

    def test_kernel_model_returns_kernel(self):
        assert get_explainer_type("knn") == "kernel"

    def test_unknown_model_returns_kernel(self):
        assert get_explainer_type("unknown_model") == "kernel"


# ---------------------------------------------------------------------------
# TestComputeShapValues
# ---------------------------------------------------------------------------


class TestComputeShapValues:
    def test_tree_model_shap_shape(self, fitted_rf_pipeline, sample_X, feature_names):
        shap_vals, names = compute_shap_values(
            fitted_rf_pipeline, sample_X, "random_forest", feature_names,
        )
        assert shap_vals.shape == (len(sample_X), len(feature_names))

    def test_linear_model_shap_shape(self, fitted_ridge_pipeline, sample_X, feature_names):
        shap_vals, names = compute_shap_values(
            fitted_ridge_pipeline, sample_X, "ridge", feature_names,
        )
        assert shap_vals.shape == (len(sample_X), len(feature_names))

    def test_kernel_model_shap_shape(self, fitted_knn_pipeline, sample_X, feature_names):
        shap_vals, names = compute_shap_values(
            fitted_knn_pipeline, sample_X, "knn", feature_names,
        )
        # Kernel may subsample, so rows ≤ original
        assert shap_vals.shape[1] == len(feature_names)
        assert shap_vals.shape[0] <= len(sample_X)

    def test_kernel_max_samples_respected(self, rng, feature_names):
        X_large = rng.normal(size=(300, 4))
        y = rng.normal(size=300)
        pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("model", KNeighborsRegressor(n_neighbors=3)),
        ])
        pipe.fit(X_large, y)
        shap_vals, _ = compute_shap_values(
            pipe, X_large, "knn", feature_names, max_samples=50,
        )
        assert shap_vals.shape[0] <= 50

    def test_feature_names_match(self, fitted_rf_pipeline, sample_X, feature_names):
        _, names = compute_shap_values(
            fitted_rf_pipeline, sample_X, "random_forest", feature_names,
        )
        assert names == feature_names


# ---------------------------------------------------------------------------
# TestComputeFeatureImportance
# ---------------------------------------------------------------------------


class TestComputeFeatureImportance:
    def test_returns_sorted_descending(self, fitted_rf_pipeline, sample_X, feature_names):
        shap_vals, _ = compute_shap_values(
            fitted_rf_pipeline, sample_X, "random_forest", feature_names,
        )
        importance = compute_feature_importance(shap_vals, feature_names)
        values = [entry["mean_abs_shap"] for entry in importance]
        assert values == sorted(values, reverse=True)

    def test_all_features_present(self, fitted_rf_pipeline, sample_X, feature_names):
        shap_vals, _ = compute_shap_values(
            fitted_rf_pipeline, sample_X, "random_forest", feature_names,
        )
        importance = compute_feature_importance(shap_vals, feature_names)
        assert len(importance) == len(feature_names)

    def test_importance_non_negative(self, fitted_rf_pipeline, sample_X, feature_names):
        shap_vals, _ = compute_shap_values(
            fitted_rf_pipeline, sample_X, "random_forest", feature_names,
        )
        importance = compute_feature_importance(shap_vals, feature_names)
        for entry in importance:
            assert entry["mean_abs_shap"] >= 0


# ---------------------------------------------------------------------------
# TestGetShapSummary
# ---------------------------------------------------------------------------


class TestGetShapSummary:
    def test_summary_keys(self, fitted_rf_pipeline, sample_X, feature_names):
        summary = get_shap_summary(
            fitted_rf_pipeline, sample_X, "random_forest", feature_names,
        )
        assert "shap_values" in summary
        assert "feature_names" in summary
        assert "n_samples" in summary
        assert "feature_importance" in summary

    def test_shap_values_shape(self, fitted_rf_pipeline, sample_X, feature_names):
        summary = get_shap_summary(
            fitted_rf_pipeline, sample_X, "random_forest", feature_names,
        )
        vals = summary["shap_values"]
        assert len(vals) == summary["n_samples"]
        assert len(vals[0]) == len(feature_names)

    def test_feature_importance_sorted(self, fitted_rf_pipeline, sample_X, feature_names):
        summary = get_shap_summary(
            fitted_rf_pipeline, sample_X, "random_forest", feature_names,
        )
        values = [e["mean_abs_shap"] for e in summary["feature_importance"]]
        assert values == sorted(values, reverse=True)

    def test_feature_names_match(self, fitted_rf_pipeline, sample_X, feature_names):
        summary = get_shap_summary(
            fitted_rf_pipeline, sample_X, "random_forest", feature_names,
        )
        assert summary["feature_names"] == feature_names
