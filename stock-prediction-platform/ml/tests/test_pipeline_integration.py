"""Integration tests — KF-09 → KF-12 pipeline flow (select → explain → deploy)."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso, Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

from ml.models.model_configs import TrainingResult
from ml.models.registry import ModelRegistry
from ml.pipelines.components.deployer import deploy_winner_model
from ml.pipelines.components.explainer import explain_top_models, get_shap_summary
from ml.pipelines.components.model_selector import select_and_persist_winner

_shap_available = get_shap_summary is not None


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


@pytest.fixture()
def pipeline_artifacts(tmp_path):
    """Create 5 synthetic TrainingResults + fitted Pipelines for integration."""
    results = [
        _make_result("ridge", "standard", 1.0, 60.0, 0.1),
        _make_result("lasso", "standard", 1.2, 55.0, 0.2),
        _make_result("random_forest", "robust", 1.5, 80.0, 0.3),
        _make_result("knn", "minmax", 2.0, 65.0, 0.5),
        _make_result("knn", "standard", 3.0, 50.0, 0.3),
    ]
    pipelines = {
        "ridge_standard": _make_pipeline(Ridge()),
        "lasso_standard": _make_pipeline(Lasso(max_iter=10_000)),
        "random_forest_robust": _make_pipeline(
            RandomForestRegressor(n_estimators=10, random_state=42),
        ),
        "knn_minmax": _make_pipeline(KNeighborsRegressor(n_neighbors=3)),
        "knn_standard": _make_pipeline(KNeighborsRegressor(n_neighbors=3)),
    }
    features = ["close", "rsi_14", "sma_20", "volume"]
    X = np.random.default_rng(42).normal(size=(60, 4))

    return {
        "results": results,
        "pipelines": pipelines,
        "features": features,
        "X": X,
        "registry_dir": str(tmp_path / "registry"),
        "serving_dir": str(tmp_path / "serving"),
    }


# ---------------------------------------------------------------------------
# TestPipelineSelectionToDeployment
# ---------------------------------------------------------------------------


class TestPipelineSelectionToDeployment:
    def test_full_pipeline_flow(self, pipeline_artifacts):
        """Chain: select_winner → explain → deploy → verify serving."""
        arts = pipeline_artifacts

        # Step 1: KF-10/KF-11 — Winner selection + persistence
        winner_info = select_and_persist_winner(
            arts["results"], arts["pipelines"], arts["features"],
            registry_dir=arts["registry_dir"],
        )
        assert winner_info["total_candidates"] == 5
        registry = ModelRegistry(base_dir=arts["registry_dir"])
        assert registry.get_winner() is not None
        assert len(registry.list_models()) == 5

        # Step 2: KF-09 — Explainability (skip if shap unavailable)
        if _shap_available:
            shap_output = explain_top_models(
                arts["results"], arts["pipelines"], arts["X"], arts["features"],
                registry_dir=arts["registry_dir"], top_n=5,
            )
            assert len(shap_output) >= 1
            shap_files = list(Path(arts["registry_dir"]).rglob("shap_importance.json"))
            assert len(shap_files) >= 1

        # Step 3: KF-12 — Deployment
        deploy_info = deploy_winner_model(
            registry_dir=arts["registry_dir"],
            serving_dir=arts["serving_dir"],
        )
        assert "model_name" in deploy_info
        assert "deployed_at" in deploy_info

        # Verify serving directory
        serving = Path(arts["serving_dir"])
        assert (serving / "serving_config.json").exists()
        assert (serving / "pipeline.pkl").exists()
        assert (serving / "metadata.json").exists()
        assert (serving / "features.json").exists()

        # Verify serving config
        with open(serving / "serving_config.json") as f:
            config = json.load(f)
        assert config["is_active"] is True
        assert config["model_name"] == deploy_info["model_name"]

        # Verify model is active in registry
        active = registry.get_active_model()
        assert active is not None
        assert active["is_active"] is True

        # Round-trip: load deployed pipeline and predict
        with open(serving / "pipeline.pkl", "rb") as f:
            loaded_pipeline = pickle.load(f)  # noqa: S301
        preds = loaded_pipeline.predict(arts["X"][:5])
        assert preds.shape == (5,)
        assert not np.any(np.isnan(preds))


# ---------------------------------------------------------------------------
# TestPipelineDeploymentIdempotency
# ---------------------------------------------------------------------------


class TestPipelineDeploymentIdempotency:
    def test_redeploy_after_retrain(self, pipeline_artifacts):
        """Run full flow twice — second deployment succeeds, only one active."""
        arts = pipeline_artifacts

        # First run
        select_and_persist_winner(
            arts["results"], arts["pipelines"], arts["features"],
            registry_dir=arts["registry_dir"],
        )
        if _shap_available:
            explain_top_models(
                arts["results"], arts["pipelines"], arts["X"], arts["features"],
                registry_dir=arts["registry_dir"], top_n=5,
            )
        deploy_winner_model(
            registry_dir=arts["registry_dir"], serving_dir=arts["serving_dir"],
        )

        # Second run (simulating retrain)
        select_and_persist_winner(
            arts["results"], arts["pipelines"], arts["features"],
            registry_dir=arts["registry_dir"],
        )
        if _shap_available:
            explain_top_models(
                arts["results"], arts["pipelines"], arts["X"], arts["features"],
                registry_dir=arts["registry_dir"], top_n=5,
            )
        deploy_info = deploy_winner_model(
            registry_dir=arts["registry_dir"], serving_dir=arts["serving_dir"],
        )

        # Only one active model in registry
        registry = ModelRegistry(base_dir=arts["registry_dir"])
        active = registry.get_active_model()
        assert active is not None
        assert active["model_name"] == deploy_info["model_name"]

        # Serving directory valid
        serving = Path(arts["serving_dir"])
        assert (serving / "serving_config.json").exists()
        assert (serving / "pipeline.pkl").exists()


# ---------------------------------------------------------------------------
# TestPipelineDeploymentWithoutExplainer
# ---------------------------------------------------------------------------


class TestPipelineDeploymentWithoutExplainer:
    def test_deploy_without_shap(self, pipeline_artifacts):
        """Select → deploy (skip explain) — deployment works, no SHAP in serving."""
        arts = pipeline_artifacts

        select_and_persist_winner(
            arts["results"], arts["pipelines"], arts["features"],
            registry_dir=arts["registry_dir"],
        )
        deploy_info = deploy_winner_model(
            registry_dir=arts["registry_dir"], serving_dir=arts["serving_dir"],
        )

        serving = Path(arts["serving_dir"])
        assert (serving / "pipeline.pkl").exists()
        assert (serving / "metadata.json").exists()
        assert (serving / "features.json").exists()
        assert not (serving / "shap_importance.json").exists()
        assert deploy_info["model_name"]
