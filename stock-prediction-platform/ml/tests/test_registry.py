"""Tests for ml.models.registry — ModelRegistry save / load / list / delete."""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.evaluation.ranking import RankedModel, WinnerResult
from ml.models.model_configs import TrainingResult
from ml.models.registry import ModelRegistry


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def registry(tmp_path) -> ModelRegistry:
    return ModelRegistry(base_dir=str(tmp_path / "registry"))


@pytest.fixture
def sample_pipeline() -> Pipeline:
    """Minimal fitted pipeline for testing."""
    rng = np.random.default_rng(0)
    X = rng.normal(size=(20, 4))
    y = rng.normal(size=20)
    pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
    pipe.fit(X, y)
    return pipe


@pytest.fixture
def sample_result() -> TrainingResult:
    return TrainingResult(
        model_name="ridge",
        scaler_variant="standard",
        best_params={"alpha": 1.0},
        fold_metrics=[{"rmse": 0.9}, {"rmse": 1.1}],
        oos_metrics={"rmse": 1.0, "directional_accuracy": 60.0},
        fold_stability=0.14,
    )


@pytest.fixture
def sample_features() -> list[str]:
    return ["close", "rsi_14", "sma_20", "volume"]


# ---------------------------------------------------------------------------
# TestSaveModel
# ---------------------------------------------------------------------------


class TestSaveModel:
    def test_save_creates_files(self, registry, sample_result, sample_pipeline, sample_features):
        path = registry.save_model(sample_result, sample_pipeline, sample_features)
        from pathlib import Path

        p = Path(path)
        assert (p / "pipeline.pkl").exists()
        assert (p / "metadata.json").exists()
        assert (p / "features.json").exists()

    def test_metadata_contents(self, registry, sample_result, sample_pipeline, sample_features):
        import json
        from pathlib import Path

        path = registry.save_model(sample_result, sample_pipeline, sample_features, rank=1, is_winner=True)
        with open(Path(path) / "metadata.json") as f:
            meta = json.load(f)
        assert meta["model_name"] == "ridge"
        assert meta["scaler_variant"] == "standard"
        assert meta["is_winner"] is True
        assert meta["rank"] == 1
        assert "saved_at" in meta
        assert meta["oos_metrics"]["rmse"] == 1.0

    def test_features_contents(self, registry, sample_result, sample_pipeline, sample_features):
        import json
        from pathlib import Path

        path = registry.save_model(sample_result, sample_pipeline, sample_features)
        with open(Path(path) / "features.json") as f:
            loaded = json.load(f)
        assert loaded == sample_features

    def test_auto_version_increment(self, registry, sample_result, sample_pipeline, sample_features):
        p1 = registry.save_model(sample_result, sample_pipeline, sample_features)
        p2 = registry.save_model(sample_result, sample_pipeline, sample_features)
        assert p1.endswith("v1")
        assert p2.endswith("v2")

    def test_explicit_version(self, registry, sample_result, sample_pipeline, sample_features):
        path = registry.save_model(sample_result, sample_pipeline, sample_features, version=5)
        assert path.endswith("v5")


# ---------------------------------------------------------------------------
# TestLoadModel
# ---------------------------------------------------------------------------


class TestLoadModel:
    def test_load_latest_version(self, registry, sample_result, sample_pipeline, sample_features):
        registry.save_model(sample_result, sample_pipeline, sample_features)
        registry.save_model(sample_result, sample_pipeline, sample_features)
        loaded = registry.load_model("ridge", "standard")
        assert loaded["version"] == 2

    def test_load_specific_version(self, registry, sample_result, sample_pipeline, sample_features):
        registry.save_model(sample_result, sample_pipeline, sample_features)
        registry.save_model(sample_result, sample_pipeline, sample_features)
        loaded = registry.load_model("ridge", "standard", version=1)
        assert loaded["version"] == 1

    def test_loaded_pipeline_predicts(self, registry, sample_result, sample_pipeline, sample_features):
        registry.save_model(sample_result, sample_pipeline, sample_features)
        loaded = registry.load_model("ridge", "standard")
        rng = np.random.default_rng(1)
        X_test = rng.normal(size=(5, 4))
        preds = loaded["pipeline"].predict(X_test)
        assert preds.shape == (5,)

    def test_load_nonexistent_raises(self, registry):
        with pytest.raises(FileNotFoundError):
            registry.load_model("nonexistent", "standard")


# ---------------------------------------------------------------------------
# TestListModels
# ---------------------------------------------------------------------------


class TestListModels:
    def test_list_empty_registry(self, registry):
        assert registry.list_models() == []

    def test_list_multiple_models(self, registry, sample_pipeline, sample_features):
        r1 = TrainingResult("ridge", "standard", {}, [], {"rmse": 1.0}, 0.1)
        r2 = TrainingResult("lasso", "standard", {}, [], {"rmse": 2.0}, 0.2)
        registry.save_model(r1, sample_pipeline, sample_features)
        registry.save_model(r2, sample_pipeline, sample_features)
        models = registry.list_models()
        assert len(models) == 2
        # sorted by RMSE ascending
        assert models[0]["oos_rmse"] <= models[1]["oos_rmse"]

    def test_list_contains_expected_fields(self, registry, sample_result, sample_pipeline, sample_features):
        registry.save_model(sample_result, sample_pipeline, sample_features)
        models = registry.list_models()
        entry = models[0]
        for key in ("model_name", "scaler_variant", "version", "is_winner", "oos_rmse", "path"):
            assert key in entry


# ---------------------------------------------------------------------------
# TestGetWinner
# ---------------------------------------------------------------------------


class TestGetWinner:
    def test_no_winner_returns_none(self, registry):
        assert registry.get_winner() is None

    def test_winner_found(self, registry, sample_result, sample_pipeline, sample_features):
        registry.save_model(sample_result, sample_pipeline, sample_features, is_winner=True)
        winner = registry.get_winner()
        assert winner is not None
        assert winner["is_winner"] is True

    def test_multiple_saves_latest_winner(self, registry, sample_result, sample_pipeline, sample_features):
        registry.save_model(sample_result, sample_pipeline, sample_features, is_winner=True)
        registry.save_model(sample_result, sample_pipeline, sample_features, is_winner=True)
        winner = registry.get_winner()
        assert winner["version"] == 2


# ---------------------------------------------------------------------------
# TestDeleteModel
# ---------------------------------------------------------------------------


class TestDeleteModel:
    def test_delete_specific_version(self, registry, sample_result, sample_pipeline, sample_features):
        registry.save_model(sample_result, sample_pipeline, sample_features)
        registry.save_model(sample_result, sample_pipeline, sample_features)
        assert registry.delete_model("ridge", "standard", version=1)
        # v2 still accessible
        loaded = registry.load_model("ridge", "standard", version=2)
        assert loaded["version"] == 2

    def test_delete_all_versions(self, registry, sample_result, sample_pipeline, sample_features):
        registry.save_model(sample_result, sample_pipeline, sample_features)
        registry.save_model(sample_result, sample_pipeline, sample_features)
        assert registry.delete_model("ridge", "standard")
        assert registry.list_models() == []

    def test_delete_nonexistent_returns_false(self, registry):
        assert registry.delete_model("nope", "nope") is False


# ---------------------------------------------------------------------------
# TestSaveWinner
# ---------------------------------------------------------------------------


class TestSaveWinner:
    def _make_winner_result(self, sample_result: TrainingResult) -> WinnerResult:
        ranked = RankedModel(
            rank=1,
            training_result=sample_result,
            composite_score=1.05,
            raw_rmse=1.0,
            directional_accuracy=60.0,
            fold_stability=0.14,
            variance_penalty=0.07,
        )
        return WinnerResult(winner=ranked, runner_up=None, margin=0.0, total_candidates=1)

    def test_save_winner_sets_flag(self, registry, sample_result, sample_pipeline, sample_features):
        wr = self._make_winner_result(sample_result)
        registry.save_winner(wr, sample_pipeline, sample_features)
        winner = registry.get_winner()
        assert winner is not None
        assert winner["is_winner"] is True

    def test_save_winner_sets_rank(self, registry, sample_result, sample_pipeline, sample_features):
        import json
        from pathlib import Path

        wr = self._make_winner_result(sample_result)
        path = registry.save_winner(wr, sample_pipeline, sample_features)
        with open(Path(path) / "metadata.json") as f:
            meta = json.load(f)
        assert meta["rank"] == 1


# ---------------------------------------------------------------------------
# TestActivation
# ---------------------------------------------------------------------------


class TestActivation:
    """Tests for activate_model / deactivate_all / get_active_model."""

    @staticmethod
    def _make_result(name: str, scaler: str, oos_rmse: float) -> TrainingResult:
        return TrainingResult(
            model_name=name,
            scaler_variant=scaler,
            best_params={},
            fold_metrics=[{"rmse": oos_rmse}],
            oos_metrics={"rmse": oos_rmse, "directional_accuracy": 55.0},
            fold_stability=0.1,
        )

    def test_activate_model(self, registry, sample_pipeline, sample_features):
        import json
        from pathlib import Path

        result = self._make_result("ridge", "standard", 1.0)
        path = registry.save_model(result, sample_pipeline, sample_features)
        registry.activate_model("ridge", "standard", 1)
        with open(Path(path) / "metadata.json") as f:
            meta = json.load(f)
        assert meta["is_active"] is True

    def test_activate_nonexistent_raises(self, registry):
        with pytest.raises(FileNotFoundError):
            registry.activate_model("nonexistent", "standard", 1)

    def test_deactivate_all(self, registry, sample_pipeline, sample_features):
        import json
        from pathlib import Path

        r1 = self._make_result("ridge", "standard", 1.0)
        r2 = self._make_result("lasso", "standard", 1.5)
        r3 = self._make_result("rf", "robust", 2.0)
        registry.save_model(r1, sample_pipeline, sample_features)
        registry.save_model(r2, sample_pipeline, sample_features)
        registry.save_model(r3, sample_pipeline, sample_features)
        registry.activate_model("ridge", "standard", 1)
        count = registry.deactivate_all()
        assert count == 1
        # All metadata should have is_active=False
        for entry in registry.list_models():
            with open(Path(entry["path"]) / "metadata.json") as f:
                meta = json.load(f)
            assert meta.get("is_active", False) is False

    def test_deactivate_all_empty_registry(self, tmp_path):
        reg = ModelRegistry(base_dir=str(tmp_path / "empty_reg"))
        assert reg.deactivate_all() == 0

    def test_get_active_model(self, registry, sample_pipeline, sample_features):
        result = self._make_result("ridge", "standard", 1.0)
        registry.save_model(result, sample_pipeline, sample_features)
        registry.activate_model("ridge", "standard", 1)
        active = registry.get_active_model()
        assert active is not None
        assert active["model_name"] == "ridge"
        assert active["is_active"] is True

    def test_get_active_model_none(self, registry, sample_pipeline, sample_features):
        result = self._make_result("ridge", "standard", 1.0)
        registry.save_model(result, sample_pipeline, sample_features)
        assert registry.get_active_model() is None

    def test_activate_then_deactivate(self, registry, sample_pipeline, sample_features):
        result = self._make_result("ridge", "standard", 1.0)
        registry.save_model(result, sample_pipeline, sample_features)
        registry.activate_model("ridge", "standard", 1)
        registry.deactivate_all()
        assert registry.get_active_model() is None

    def test_activate_updates_only_target(self, registry, sample_pipeline, sample_features):
        r1 = self._make_result("ridge", "standard", 1.0)
        r2 = self._make_result("lasso", "standard", 1.5)
        registry.save_model(r1, sample_pipeline, sample_features)
        registry.save_model(r2, sample_pipeline, sample_features)
        registry.activate_model("ridge", "standard", 1)
        registry.activate_model("lasso", "standard", 1)
        # Both are active — activation doesn't implicitly deactivate others
        active = registry.get_active_model()
        assert active is not None
