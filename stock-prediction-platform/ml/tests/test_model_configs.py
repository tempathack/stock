"""Tests for ml.models.model_configs."""

from __future__ import annotations

import pytest
from sklearn.base import RegressorMixin

from ml.models.model_configs import (
    BOOSTER_MODELS,
    DISTANCE_NEURAL_MODELS,
    LINEAR_MODELS,
    TREE_MODELS,
    ModelConfig,
    TrainingResult,
    get_all_model_configs,
    get_model_configs,
    register_model_family,
)


# ---------------------------------------------------------------------------
# LINEAR_MODELS registry
# ---------------------------------------------------------------------------


class TestLinearModels:
    def test_six_models_present(self):
        assert len(LINEAR_MODELS) == 6

    def test_expected_names(self):
        expected = {
            "linear_regression",
            "ridge",
            "lasso",
            "elastic_net",
            "bayesian_ridge",
            "huber",
        }
        assert set(LINEAR_MODELS.keys()) == expected

    @pytest.mark.parametrize("name", list(LINEAR_MODELS.keys()))
    def test_model_class_is_sklearn_regressor(self, name):
        cfg = LINEAR_MODELS[name]
        instance = cfg.model_class(**cfg.default_params)
        assert isinstance(instance, RegressorMixin)

    @pytest.mark.parametrize("name", list(LINEAR_MODELS.keys()))
    def test_config_is_model_config(self, name):
        assert isinstance(LINEAR_MODELS[name], ModelConfig)

    def test_ridge_has_search_space(self):
        assert LINEAR_MODELS["ridge"].search_space is not None
        assert "alpha" in LINEAR_MODELS["ridge"].search_space

    def test_lasso_has_search_space(self):
        assert LINEAR_MODELS["lasso"].search_space is not None
        assert "alpha" in LINEAR_MODELS["lasso"].search_space

    def test_elastic_net_has_two_params(self):
        space = LINEAR_MODELS["elastic_net"].search_space
        assert space is not None
        assert "alpha" in space
        assert "l1_ratio" in space

    def test_linear_regression_no_search_space(self):
        assert LINEAR_MODELS["linear_regression"].search_space is None

    def test_bayesian_ridge_no_search_space(self):
        assert LINEAR_MODELS["bayesian_ridge"].search_space is None

    def test_huber_has_search_space(self):
        assert LINEAR_MODELS["huber"].search_space is not None
        assert "epsilon" in LINEAR_MODELS["huber"].search_space


# ---------------------------------------------------------------------------
# TREE_MODELS registry
# ---------------------------------------------------------------------------


class TestTreeModels:
    def test_six_models_present(self):
        assert len(TREE_MODELS) == 6

    def test_expected_names(self):
        expected = {
            "random_forest",
            "gradient_boosting",
            "hist_gradient_boosting",
            "extra_trees",
            "decision_tree",
            "adaboost",
        }
        assert set(TREE_MODELS.keys()) == expected

    @pytest.mark.parametrize("name", list(TREE_MODELS.keys()))
    def test_model_class_is_sklearn_regressor(self, name):
        cfg = TREE_MODELS[name]
        instance = cfg.model_class(**cfg.default_params)
        assert isinstance(instance, RegressorMixin)

    @pytest.mark.parametrize("name", list(TREE_MODELS.keys()))
    def test_all_have_random_state(self, name):
        cfg = TREE_MODELS[name]
        assert "random_state" in cfg.default_params or "random_seed" in cfg.default_params

    def test_random_forest_search_space(self):
        space = TREE_MODELS["random_forest"].search_space
        assert space is not None
        assert {"n_estimators", "max_depth", "min_samples_split", "max_features"} == set(space.keys())

    def test_gradient_boosting_search_space(self):
        space = TREE_MODELS["gradient_boosting"].search_space
        assert space is not None
        assert "learning_rate" in space
        assert "subsample" in space

    def test_rf_and_gbm_have_higher_n_iter(self):
        assert TREE_MODELS["random_forest"].n_iter == 50
        assert TREE_MODELS["gradient_boosting"].n_iter == 50

    @pytest.mark.parametrize("name", list(TREE_MODELS.keys()))
    def test_all_have_search_space(self, name):
        assert TREE_MODELS[name].search_space is not None


# ---------------------------------------------------------------------------
# BOOSTER_MODELS registry (conditional)
# ---------------------------------------------------------------------------


class TestBoosterModels:
    def test_booster_dict_exists(self):
        assert isinstance(BOOSTER_MODELS, dict)

    @pytest.mark.skipif("xgboost" not in BOOSTER_MODELS, reason="xgboost not installed")
    def test_xgboost_config(self):
        cfg = BOOSTER_MODELS["xgboost"]
        assert isinstance(cfg, ModelConfig)
        assert cfg.default_params.get("verbosity") == 0
        assert cfg.search_space is not None
        assert "colsample_bytree" in cfg.search_space

    @pytest.mark.skipif("lightgbm" not in BOOSTER_MODELS, reason="lightgbm not installed")
    def test_lightgbm_config(self):
        cfg = BOOSTER_MODELS["lightgbm"]
        assert isinstance(cfg, ModelConfig)
        assert cfg.default_params.get("verbose") == -1
        assert cfg.search_space is not None
        assert "num_leaves" in cfg.search_space

    @pytest.mark.skipif("catboost" not in BOOSTER_MODELS, reason="catboost not installed")
    def test_catboost_config(self):
        cfg = BOOSTER_MODELS["catboost"]
        assert isinstance(cfg, ModelConfig)
        assert cfg.default_params.get("verbose") == 0
        assert cfg.search_space is not None
        assert "depth" in cfg.search_space

    @pytest.mark.skipif(not BOOSTER_MODELS, reason="no boosters installed")
    def test_booster_models_are_regressors(self):
        for name, cfg in BOOSTER_MODELS.items():
            instance = cfg.model_class(**cfg.default_params)
            # CatBoost/XGBoost/LightGBM may not inherit RegressorMixin
            assert hasattr(instance, "fit") and hasattr(instance, "predict")


# ---------------------------------------------------------------------------
# DISTANCE_NEURAL_MODELS registry
# ---------------------------------------------------------------------------


class TestDistanceNeuralModels:
    def test_three_models_present(self):
        assert len(DISTANCE_NEURAL_MODELS) == 3

    def test_expected_names(self):
        assert set(DISTANCE_NEURAL_MODELS.keys()) == {"knn", "svr", "mlp"}

    @pytest.mark.parametrize("name", list(DISTANCE_NEURAL_MODELS.keys()))
    def test_model_class_is_sklearn(self, name):
        cfg = DISTANCE_NEURAL_MODELS[name]
        instance = cfg.model_class(**cfg.default_params)
        assert hasattr(instance, "fit") and hasattr(instance, "predict")

    def test_knn_search_space(self):
        space = DISTANCE_NEURAL_MODELS["knn"].search_space
        assert space is not None
        assert {"n_neighbors", "weights", "metric"} == set(space.keys())

    def test_svr_search_space(self):
        space = DISTANCE_NEURAL_MODELS["svr"].search_space
        assert space is not None
        assert {"C", "gamma", "epsilon"} == set(space.keys())

    def test_svr_default_kernel(self):
        assert DISTANCE_NEURAL_MODELS["svr"].default_params["kernel"] == "rbf"

    def test_mlp_search_space(self):
        space = DISTANCE_NEURAL_MODELS["mlp"].search_space
        assert space is not None
        assert {"hidden_layer_sizes", "alpha", "learning_rate_init"} == set(space.keys())

    def test_mlp_early_stopping(self):
        assert DISTANCE_NEURAL_MODELS["mlp"].default_params["early_stopping"] is True

    def test_mlp_max_iter_bounded(self):
        assert DISTANCE_NEURAL_MODELS["mlp"].default_params["max_iter"] <= 500


# ---------------------------------------------------------------------------
# TrainingResult
# ---------------------------------------------------------------------------


class TestTrainingResult:
    def test_to_dict(self):
        result = TrainingResult(
            model_name="ridge",
            scaler_variant="standard",
            best_params={"alpha": 1.0},
            fold_metrics=[{"r2": 0.9}],
            oos_metrics={"r2": 0.88},
            fold_stability=0.02,
            pipeline_path="/tmp/ridge.pkl",
        )
        d = result.to_dict()
        assert d["model_name"] == "ridge"
        assert d["scaler_variant"] == "standard"
        assert d["best_params"] == {"alpha": 1.0}
        assert d["pipeline_path"] == "/tmp/ridge.pkl"

    def test_to_dict_json_serializable(self):
        import json

        result = TrainingResult(
            model_name="lasso",
            scaler_variant="minmax",
            best_params={"alpha": 0.01},
            fold_metrics=[{"r2": 0.8, "rmse": 0.5}],
            oos_metrics={"r2": 0.78, "rmse": 0.55},
            fold_stability=0.03,
        )
        serialized = json.dumps(result.to_dict())
        assert isinstance(serialized, str)


# ---------------------------------------------------------------------------
# get_model_configs / get_all_model_configs
# ---------------------------------------------------------------------------


class TestGetModelConfigs:
    def test_get_linear(self):
        configs = get_model_configs("linear")
        assert len(configs) == 6

    def test_get_tree(self):
        configs = get_model_configs("tree")
        assert len(configs) == 6

    @pytest.mark.skipif(not BOOSTER_MODELS, reason="no boosters installed")
    def test_get_booster(self):
        configs = get_model_configs("booster")
        assert len(configs) == len(BOOSTER_MODELS)

    def test_unknown_family_raises(self):
        with pytest.raises(ValueError, match="Unknown family"):
            get_model_configs("nonexistent")

    def test_get_all_includes_linear(self):
        all_configs = get_all_model_configs()
        assert "ridge" in all_configs
        assert "linear_regression" in all_configs

    def test_get_all_includes_tree(self):
        all_configs = get_all_model_configs()
        assert "random_forest" in all_configs
        assert "decision_tree" in all_configs

    @pytest.mark.skipif(not BOOSTER_MODELS, reason="no boosters installed")
    def test_get_all_includes_boosters(self):
        all_configs = get_all_model_configs()
        for name in BOOSTER_MODELS:
            assert name in all_configs

    def test_register_new_family(self):
        from sklearn.tree import DecisionTreeRegressor

        dummy = {
            "dt": ModelConfig(name="dt", model_class=DecisionTreeRegressor)
        }
        register_model_family("test_tree", dummy)
        configs = get_model_configs("test_tree")
        assert "dt" in configs
        # Cleanup
        from ml.models.model_configs import _MODEL_FAMILIES
        del _MODEL_FAMILIES["test_tree"]

    def test_get_distance_neural(self):
        configs = get_model_configs("distance_neural")
        assert len(configs) == 3

    def test_get_all_includes_distance_neural(self):
        all_configs = get_all_model_configs()
        assert "knn" in all_configs
        assert "svr" in all_configs
        assert "mlp" in all_configs
