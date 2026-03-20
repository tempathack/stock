"""Tests for ml.pipelines.components.model_selector."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.models.model_configs import TrainingResult
from ml.models.registry import ModelRegistry
from ml.pipelines.components.model_selector import select_and_persist_winner


# ---------------------------------------------------------------------------
# Fixtures
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


def _make_pipeline() -> Pipeline:
    rng = np.random.default_rng(0)
    X = rng.normal(size=(20, 4))
    y = rng.normal(size=20)
    pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
    pipe.fit(X, y)
    return pipe


@pytest.fixture
def sample_training_results() -> list[TrainingResult]:
    return [
        _make_result("ridge", "standard", 1.0, 60.0, 0.1),
        _make_result("lasso", "standard", 1.0, 55.0, 1.5),
        _make_result("rf", "robust", 2.0, 80.0, 0.2),
        _make_result("gbr", "minmax", 1.5, 65.0, 0.5),
        _make_result("svr", "standard", 3.0, 50.0, 0.3),
    ]


@pytest.fixture
def mock_pipelines() -> dict[str, Pipeline]:
    return {
        "ridge_standard": _make_pipeline(),
        "lasso_standard": _make_pipeline(),
        "rf_robust": _make_pipeline(),
        "gbr_minmax": _make_pipeline(),
        "svr_standard": _make_pipeline(),
    }


@pytest.fixture
def sample_features() -> list[str]:
    return ["close", "rsi_14", "sma_20", "volume"]


# ---------------------------------------------------------------------------
# TestSelectAndPersistWinner
# ---------------------------------------------------------------------------


class TestSelectAndPersistWinner:
    def test_returns_winner_info(self, tmp_path, sample_training_results, mock_pipelines, sample_features):
        result = select_and_persist_winner(
            sample_training_results, mock_pipelines, sample_features, registry_dir=str(tmp_path / "reg"),
        )
        assert "winner_name" in result
        assert "winner_score" in result
        assert "registry_path" in result
        assert "margin" in result
        assert "total_candidates" in result
        assert result["total_candidates"] == 5

    def test_winner_saved_to_registry(self, tmp_path, sample_training_results, mock_pipelines, sample_features):
        reg_dir = str(tmp_path / "reg")
        select_and_persist_winner(
            sample_training_results, mock_pipelines, sample_features, registry_dir=reg_dir,
        )
        registry = ModelRegistry(base_dir=reg_dir)
        winner = registry.get_winner()
        assert winner is not None
        assert winner["is_winner"] is True

    def test_winner_pipeline_in_registry(self, tmp_path, sample_training_results, mock_pipelines, sample_features):
        reg_dir = str(tmp_path / "reg")
        info = select_and_persist_winner(
            sample_training_results, mock_pipelines, sample_features, registry_dir=reg_dir,
        )
        # Parse winner name to load
        name, scaler = info["winner_name"].rsplit("_", 1)
        registry = ModelRegistry(base_dir=reg_dir)
        loaded = registry.load_model(name, scaler)
        rng = np.random.default_rng(1)
        preds = loaded["pipeline"].predict(rng.normal(size=(3, 4)))
        assert preds.shape == (3,)

    def test_top5_saved(self, tmp_path, sample_training_results, mock_pipelines, sample_features):
        reg_dir = str(tmp_path / "reg")
        select_and_persist_winner(
            sample_training_results, mock_pipelines, sample_features, registry_dir=reg_dir,
        )
        registry = ModelRegistry(base_dir=reg_dir)
        models = registry.list_models()
        assert len(models) == 5  # winner + 4 runners-up

    def test_empty_results_raises(self, tmp_path, mock_pipelines, sample_features):
        with pytest.raises(ValueError):
            select_and_persist_winner([], mock_pipelines, sample_features, registry_dir=str(tmp_path / "reg"))
