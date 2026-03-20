"""Tests for ml.pipelines.components.explainer."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.models.model_configs import TrainingResult
from ml.pipelines.components.explainer import explain_top_models
from ml.pipelines.components.model_selector import select_and_persist_winner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(name: str, scaler: str, oos_rmse: float, da: float, fs: float) -> TrainingResult:
    return TrainingResult(
        model_name=name,
        scaler_variant=scaler,
        best_params={},
        fold_metrics=[{"rmse": oos_rmse}],
        oos_metrics={"rmse": oos_rmse, "directional_accuracy": da},
        fold_stability=fs,
    )


def _make_pipeline(model) -> Pipeline:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(60, 4))
    y = rng.normal(size=60)
    pipe = Pipeline([("scaler", StandardScaler()), ("model", model)])
    pipe.fit(X, y)
    return pipe


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_training_results() -> list[TrainingResult]:
    return [
        _make_result("ridge", "standard", 1.0, 60.0, 0.1),
        _make_result("lasso", "standard", 1.2, 55.0, 0.2),
        _make_result("random_forest", "robust", 1.5, 80.0, 0.3),
        _make_result("knn", "minmax", 2.0, 65.0, 0.5),
        _make_result("knn", "standard", 3.0, 50.0, 0.3),
    ]


@pytest.fixture
def mock_pipelines() -> dict[str, Pipeline]:
    return {
        "ridge_standard": _make_pipeline(Ridge()),
        "lasso_standard": _make_pipeline(Lasso(max_iter=10_000)),
        "random_forest_robust": _make_pipeline(
            RandomForestRegressor(n_estimators=10, random_state=42),
        ),
        "knn_minmax": _make_pipeline(KNeighborsRegressor(n_neighbors=3)),
        "knn_standard": _make_pipeline(KNeighborsRegressor(n_neighbors=3)),
    }


@pytest.fixture
def sample_X() -> np.ndarray:
    return np.random.default_rng(42).normal(size=(60, 4))


@pytest.fixture
def sample_features() -> list[str]:
    return ["close", "rsi_14", "sma_20", "volume"]


@pytest.fixture
def populated_registry(tmp_path, sample_training_results, mock_pipelines, sample_features):
    """Create a registry with the top-5 models pre-saved by model_selector."""
    reg_dir = str(tmp_path / "reg")
    select_and_persist_winner(
        sample_training_results,
        mock_pipelines,
        sample_features,
        registry_dir=reg_dir,
    )
    return reg_dir


# ---------------------------------------------------------------------------
# TestExplainTopModels
# ---------------------------------------------------------------------------


class TestExplainTopModels:
    def test_returns_dict_per_model(
        self, populated_registry, sample_training_results, mock_pipelines, sample_X, sample_features,
    ):
        result = explain_top_models(
            sample_training_results, mock_pipelines, sample_X, sample_features,
            registry_dir=populated_registry, top_n=5,
        )
        assert isinstance(result, dict)
        assert len(result) <= 5
        assert len(result) >= 1

    def test_each_result_has_keys(
        self, populated_registry, sample_training_results, mock_pipelines, sample_X, sample_features,
    ):
        result = explain_top_models(
            sample_training_results, mock_pipelines, sample_X, sample_features,
            registry_dir=populated_registry, top_n=5,
        )
        for key, val in result.items():
            assert "feature_importance" in val, f"Missing feature_importance for {key}"
            assert "shap_summary" in val, f"Missing shap_summary for {key}"

    def test_importance_stored_in_registry(
        self, populated_registry, sample_training_results, mock_pipelines, sample_X, sample_features,
    ):
        explain_top_models(
            sample_training_results, mock_pipelines, sample_X, sample_features,
            registry_dir=populated_registry, top_n=5,
        )
        reg = Path(populated_registry)
        # At least one model should have shap_importance.json
        shap_files = list(reg.rglob("shap_importance.json"))
        assert len(shap_files) >= 1
        # Validate JSON structure
        with open(shap_files[0]) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert "feature" in data[0]
        assert "mean_abs_shap" in data[0]

    def test_summary_stored_in_registry(
        self, populated_registry, sample_training_results, mock_pipelines, sample_X, sample_features,
    ):
        explain_top_models(
            sample_training_results, mock_pipelines, sample_X, sample_features,
            registry_dir=populated_registry, top_n=5,
        )
        reg = Path(populated_registry)
        shap_files = list(reg.rglob("shap_values.json"))
        assert len(shap_files) >= 1
        with open(shap_files[0]) as f:
            data = json.load(f)
        assert "shap_values" in data
        assert "feature_names" in data
        assert "n_samples" in data

    def test_top_n_respected(
        self, populated_registry, sample_training_results, mock_pipelines, sample_X, sample_features,
    ):
        result = explain_top_models(
            sample_training_results, mock_pipelines, sample_X, sample_features,
            registry_dir=populated_registry, top_n=3,
        )
        assert len(result) <= 3
