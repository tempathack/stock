"""Tests for ml.pipelines.components.deployer — deploy_winner_model."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.linear_model import Lasso, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.models.model_configs import TrainingResult
from ml.models.registry import ModelRegistry
from ml.pipelines.components.deployer import deploy_winner_model
from ml.pipelines.components.model_selector import select_and_persist_winner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(
    name: str, scaler: str, oos_rmse: float, da: float = 55.0, fs: float = 0.1,
) -> TrainingResult:
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
    X, y = rng.normal(size=(20, 4)), rng.normal(size=20)
    pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
    pipe.fit(X, y)
    return pipe


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_results() -> list[TrainingResult]:
    return [
        _make_result("ridge", "standard", 1.0, 60.0, 0.1),
        _make_result("lasso", "standard", 1.2, 55.0, 0.2),
        _make_result("rf", "robust", 1.5, 80.0, 0.3),
        _make_result("gbr", "minmax", 2.0, 65.0, 0.5),
        _make_result("svr", "standard", 3.0, 50.0, 0.3),
    ]


@pytest.fixture()
def mock_pipelines() -> dict[str, Pipeline]:
    return {
        "ridge_standard": _make_pipeline(),
        "lasso_standard": _make_pipeline(),
        "rf_robust": _make_pipeline(),
        "gbr_minmax": _make_pipeline(),
        "svr_standard": _make_pipeline(),
    }


@pytest.fixture()
def sample_features() -> list[str]:
    return ["close", "rsi_14", "sma_20", "volume"]


@pytest.fixture()
def populated_registry(tmp_path, sample_results, mock_pipelines, sample_features) -> str:
    """Pre-populate a registry with winner + runners-up via model_selector."""
    reg_dir = str(tmp_path / "reg")
    select_and_persist_winner(
        sample_results, mock_pipelines, sample_features, registry_dir=reg_dir,
    )
    return reg_dir


@pytest.fixture()
def serving_dir(tmp_path) -> str:
    return str(tmp_path / "serving")


# ---------------------------------------------------------------------------
# TestDeployWinnerModel
# ---------------------------------------------------------------------------


class TestDeployWinnerModel:
    def test_returns_deployment_info(self, populated_registry, serving_dir):
        info = deploy_winner_model(
            registry_dir=populated_registry, serving_dir=serving_dir,
        )
        for key in ("model_name", "scaler_variant", "version", "serving_path", "deployed_at"):
            assert key in info, f"Missing key: {key}"

    def test_serving_config_created(self, populated_registry, serving_dir):
        deploy_winner_model(registry_dir=populated_registry, serving_dir=serving_dir)
        assert (Path(serving_dir) / "serving_config.json").exists()

    def test_serving_config_content(self, populated_registry, serving_dir):
        deploy_winner_model(registry_dir=populated_registry, serving_dir=serving_dir)
        with open(Path(serving_dir) / "serving_config.json") as f:
            config = json.load(f)
        assert config["is_active"] is True
        assert "model_name" in config
        assert "scaler_variant" in config
        assert "version" in config
        assert "features" in config
        assert "deployed_at" in config
        assert isinstance(config["features"], list)

    def test_pipeline_copied(self, populated_registry, serving_dir):
        deploy_winner_model(registry_dir=populated_registry, serving_dir=serving_dir)
        assert (Path(serving_dir) / "pipeline.pkl").exists()

    def test_metadata_copied(self, populated_registry, serving_dir):
        deploy_winner_model(registry_dir=populated_registry, serving_dir=serving_dir)
        assert (Path(serving_dir) / "metadata.json").exists()

    def test_features_copied(self, populated_registry, serving_dir):
        deploy_winner_model(registry_dir=populated_registry, serving_dir=serving_dir)
        assert (Path(serving_dir) / "features.json").exists()

    def test_model_marked_active(self, populated_registry, serving_dir):
        deploy_winner_model(registry_dir=populated_registry, serving_dir=serving_dir)
        registry = ModelRegistry(base_dir=populated_registry)
        active = registry.get_active_model()
        assert active is not None
        assert active["is_active"] is True

    def test_previous_active_deactivated(self, tmp_path, sample_features):
        """Deploy twice with different winners — only second is active."""
        reg_dir = str(tmp_path / "reg")
        srv_dir = str(tmp_path / "srv")

        # First deploy with ridge winning
        results_1 = [
            _make_result("ridge", "standard", 1.0, 60.0, 0.1),
            _make_result("lasso", "standard", 2.0, 55.0, 0.2),
        ]
        pipes_1 = {
            "ridge_standard": _make_pipeline(),
            "lasso_standard": _make_pipeline(),
        }
        select_and_persist_winner(results_1, pipes_1, sample_features, registry_dir=reg_dir)
        deploy_winner_model(registry_dir=reg_dir, serving_dir=srv_dir)

        # Second deploy with lasso winning (different registry)
        reg_dir2 = str(tmp_path / "reg2")
        results_2 = [
            _make_result("lasso", "standard", 0.5, 70.0, 0.1),
            _make_result("ridge", "standard", 2.0, 55.0, 0.2),
        ]
        pipes_2 = {
            "lasso_standard": _make_pipeline(),
            "ridge_standard": _make_pipeline(),
        }
        select_and_persist_winner(results_2, pipes_2, sample_features, registry_dir=reg_dir2)
        deploy_winner_model(registry_dir=reg_dir2, serving_dir=srv_dir)

        registry2 = ModelRegistry(base_dir=reg_dir2)
        active = registry2.get_active_model()
        assert active is not None
        assert active["model_name"] == "lasso"

    def test_no_winner_raises(self, tmp_path):
        reg_dir = str(tmp_path / "empty_reg")
        ModelRegistry(base_dir=reg_dir)  # creates empty registry
        with pytest.raises(FileNotFoundError):
            deploy_winner_model(registry_dir=reg_dir, serving_dir=str(tmp_path / "srv"))

    def test_idempotent_redeploy(self, populated_registry, serving_dir):
        deploy_winner_model(registry_dir=populated_registry, serving_dir=serving_dir)
        # Deploy again — should succeed without error
        info = deploy_winner_model(registry_dir=populated_registry, serving_dir=serving_dir)
        assert (Path(serving_dir) / "serving_config.json").exists()
        assert info["model_name"]
