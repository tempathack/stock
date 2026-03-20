"""Tests for ml.pipelines.components.model_trainer."""

from __future__ import annotations

import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.pipeline import Pipeline
from unittest.mock import patch

from ml.evaluation.cross_validation import create_time_series_cv
from ml.features.transformations import SCALER_VARIANTS
from ml.models.model_configs import BOOSTER_MODELS, DISTANCE_NEURAL_MODELS, LINEAR_MODELS, TREE_MODELS, ModelConfig, TrainingResult
from ml.pipelines.components.feature_engineer import engineer_features
from ml.pipelines.components.label_generator import generate_labels
from ml.pipelines.components.model_trainer import (
    _build_pipeline,
    prepare_training_data,
    save_training_results,
    train_all_models_pipeline,
    train_distance_neural_models,
    train_linear_models,
    train_single_model,
    train_tree_models,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_regression_data():
    """Small synthetic dataset for fast training tests."""
    rng = np.random.default_rng(42)
    n = 200
    X = rng.normal(size=(n, 5))
    y = X @ np.array([1.0, -0.5, 2.0, 0.3, -1.0]) + rng.normal(scale=0.2, size=n)
    # 80/20 split respecting time order
    split = int(n * 0.8)
    return X[:split], y[:split], X[split:], y[split:]


# ---------------------------------------------------------------------------
# _build_pipeline
# ---------------------------------------------------------------------------


class TestBuildPipeline:
    def test_pipeline_has_two_steps(self):
        cfg = LINEAR_MODELS["linear_regression"]
        pipe = _build_pipeline(cfg, "standard")
        assert len(pipe.steps) == 2
        assert pipe.steps[0][0] == "scaler"
        assert pipe.steps[1][0] == "model"

    @pytest.mark.parametrize("scaler", list(SCALER_VARIANTS))
    def test_all_scaler_variants(self, scaler):
        cfg = LINEAR_MODELS["ridge"]
        pipe = _build_pipeline(cfg, scaler)
        assert pipe.steps[0][0] == "scaler"


# ---------------------------------------------------------------------------
# train_single_model
# ---------------------------------------------------------------------------


class TestTrainSingleModel:
    def test_no_tuning(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = LINEAR_MODELS["linear_regression"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert result.model_name == "linear_regression"
        assert result.scaler_variant == "standard"
        assert result.best_params == {}
        assert len(result.fold_metrics) == 3
        assert "rmse" in result.oos_metrics

    def test_with_tuning(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = LINEAR_MODELS["ridge"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert "alpha" in result.best_params
        assert result.best_params["alpha"] > 0

    def test_oos_metrics_complete(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = LINEAR_MODELS["bayesian_ridge"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "minmax", n_splits=3)
        expected_keys = {"r2", "mae", "rmse", "mape", "directional_accuracy", "fold_stability"}
        assert expected_keys == set(result.oos_metrics.keys())

    def test_fold_stability_is_non_negative(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = LINEAR_MODELS["linear_regression"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert result.fold_stability >= 0.0


# ---------------------------------------------------------------------------
# train_linear_models
# ---------------------------------------------------------------------------


class TestTrainLinearModels:
    def test_returns_18_results(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_linear_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        assert len(results) == 18  # 6 models × 3 scalers

    def test_sorted_by_rmse(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_linear_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        rmses = [r.oos_metrics["rmse"] for r in results]
        assert rmses == sorted(rmses)

    def test_all_model_names_present(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_linear_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        names = {r.model_name for r in results}
        assert names == set(LINEAR_MODELS.keys())

    def test_all_scaler_variants_present(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_linear_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        scalers = {r.scaler_variant for r in results}
        assert scalers == set(SCALER_VARIANTS)


# ---------------------------------------------------------------------------
# save_training_results
# ---------------------------------------------------------------------------


class TestSaveTrainingResults:
    def test_saves_json(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = LINEAR_MODELS["linear_regression"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_training_results([result], tmpdir)
            json_path = os.path.join(tmpdir, "training_results.json")
            assert os.path.exists(json_path)
            with open(json_path) as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["model_name"] == "linear_regression"

    def test_json_has_expected_fields(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = LINEAR_MODELS["ridge"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "quantile", n_splits=3)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_training_results([result], tmpdir)
            with open(os.path.join(tmpdir, "training_results.json")) as f:
                data = json.load(f)
            entry = data[0]
            assert "model_name" in entry
            assert "scaler_variant" in entry
            assert "best_params" in entry
            assert "oos_metrics" in entry
            assert "fold_metrics" in entry


# ---------------------------------------------------------------------------
# train_single_model — tree models
# ---------------------------------------------------------------------------


class TestTrainSingleTreeModel:
    def test_random_forest_with_tuning(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = TREE_MODELS["random_forest"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert result.model_name == "random_forest"
        assert len(result.best_params) > 0

    def test_decision_tree(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = TREE_MODELS["decision_tree"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert "rmse" in result.oos_metrics

    @pytest.mark.skipif("xgboost" not in BOOSTER_MODELS, reason="xgboost not installed")
    def test_xgboost(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = BOOSTER_MODELS["xgboost"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert result.model_name == "xgboost"

    @pytest.mark.skipif("lightgbm" not in BOOSTER_MODELS, reason="lightgbm not installed")
    def test_lightgbm(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = BOOSTER_MODELS["lightgbm"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert result.model_name == "lightgbm"

    @pytest.mark.skipif("catboost" not in BOOSTER_MODELS, reason="catboost not installed")
    def test_catboost(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = BOOSTER_MODELS["catboost"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert result.model_name == "catboost"


# ---------------------------------------------------------------------------
# train_tree_models — batch
# ---------------------------------------------------------------------------


_EXPECTED_TREE_COUNT = (len(TREE_MODELS) + len(BOOSTER_MODELS)) * len(SCALER_VARIANTS)


class TestTrainTreeModels:
    def test_returns_correct_count(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_tree_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        assert len(results) == _EXPECTED_TREE_COUNT

    def test_without_boosters(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_tree_models(X_tr, y_tr, X_te, y_te, n_splits=3, include_boosters=False)
        assert len(results) == len(TREE_MODELS) * len(SCALER_VARIANTS)

    def test_sorted_by_rmse(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_tree_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        rmses = [r.oos_metrics["rmse"] for r in results]
        assert rmses == sorted(rmses)

    def test_all_tree_model_names_present(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_tree_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        names = {r.model_name for r in results}
        expected = set(TREE_MODELS.keys()) | set(BOOSTER_MODELS.keys())
        assert names == expected

    def test_all_scaler_variants_present(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_tree_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        scalers = {r.scaler_variant for r in results}
        assert scalers == set(SCALER_VARIANTS)


# ---------------------------------------------------------------------------
# train_single_model — distance/neural models
# ---------------------------------------------------------------------------


class TestTrainSingleDistanceNeuralModel:
    def test_knn_with_tuning(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = DISTANCE_NEURAL_MODELS["knn"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert result.model_name == "knn"
        assert "n_neighbors" in result.best_params

    def test_svr_with_tuning(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = DISTANCE_NEURAL_MODELS["svr"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert result.model_name == "svr"
        assert "C" in result.best_params

    def test_mlp_with_tuning(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = DISTANCE_NEURAL_MODELS["mlp"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        assert isinstance(result, TrainingResult)
        assert result.model_name == "mlp"
        assert "hidden_layer_sizes" in result.best_params

    def test_mlp_oos_metrics_complete(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        cfg = DISTANCE_NEURAL_MODELS["mlp"]
        result = train_single_model(cfg, X_tr, y_tr, X_te, y_te, "standard", n_splits=3)
        expected_keys = {"r2", "mae", "rmse", "mape", "directional_accuracy", "fold_stability"}
        assert expected_keys == set(result.oos_metrics.keys())


# ---------------------------------------------------------------------------
# train_distance_neural_models — batch
# ---------------------------------------------------------------------------


class TestTrainDistanceNeuralModels:
    def test_returns_9_results(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_distance_neural_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        assert len(results) == 9  # 3 models × 3 scalers

    def test_sorted_by_rmse(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_distance_neural_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        rmses = [r.oos_metrics["rmse"] for r in results]
        assert rmses == sorted(rmses)

    def test_all_model_names_present(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_distance_neural_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        names = {r.model_name for r in results}
        assert names == {"knn", "svr", "mlp"}

    def test_all_scaler_variants_present(self, synthetic_regression_data):
        X_tr, y_tr, X_te, y_te = synthetic_regression_data
        results = train_distance_neural_models(X_tr, y_tr, X_te, y_te, n_splits=3)
        scalers = {r.scaler_variant for r in results}
        assert scalers == set(SCALER_VARIANTS)


# ---------------------------------------------------------------------------
# Pipeline data fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def pipeline_data(sample_ohlcv_df):
    """Run sample OHLCV through feature engineering and label generation."""
    data_dict = {"AAPL": sample_ohlcv_df.copy(), "MSFT": sample_ohlcv_df.copy()}
    featured = engineer_features(data_dict)
    labelled, feature_names = generate_labels(featured)
    return labelled, feature_names


# ---------------------------------------------------------------------------
# prepare_training_data
# ---------------------------------------------------------------------------


class TestPrepareTrainingData:
    def test_returns_four_numpy_arrays(self, pipeline_data):
        data_dict, feature_names = pipeline_data
        result = prepare_training_data(data_dict, feature_names)
        assert len(result) == 4
        assert all(isinstance(arr, np.ndarray) for arr in result)

    def test_train_test_shapes(self, pipeline_data):
        data_dict, feature_names = pipeline_data
        X_train, y_train, X_test, y_test = prepare_training_data(data_dict, feature_names)
        assert X_train.shape[1] == X_test.shape[1]
        assert y_train.ndim == 1
        assert y_test.ndim == 1

    def test_default_split_ratio(self, pipeline_data):
        data_dict, feature_names = pipeline_data
        X_train, y_train, X_test, y_test = prepare_training_data(data_dict, feature_names)
        total = len(y_train) + len(y_test)
        assert 0.75 <= len(y_train) / total <= 0.85

    def test_custom_split_ratio(self, pipeline_data):
        data_dict, feature_names = pipeline_data
        X_train, y_train, X_test, y_test = prepare_training_data(
            data_dict, feature_names, test_ratio=0.3,
        )
        total = len(y_train) + len(y_test)
        assert 0.65 <= len(y_train) / total <= 0.75

    def test_feature_count_matches(self, pipeline_data):
        data_dict, feature_names = pipeline_data
        X_train, _, _, _ = prepare_training_data(data_dict, feature_names)
        assert X_train.shape[1] == len(feature_names)

    def test_temporal_ordering_preserved(self, pipeline_data):
        data_dict, feature_names = pipeline_data
        # With two tickers using the same dates, temporal ordering should
        # have interleaved rows — verify monotonic index on concatenation.
        combined = pd.concat(data_dict.values()).sort_index()
        X_train, _, X_test, _ = prepare_training_data(data_dict, feature_names)
        split = int(len(combined) * 0.8)
        np.testing.assert_array_equal(X_train, combined[feature_names].values[:split])
        np.testing.assert_array_equal(X_test, combined[feature_names].values[split:])

    def test_no_nan_in_output(self, pipeline_data):
        data_dict, feature_names = pipeline_data
        X_train, y_train, X_test, y_test = prepare_training_data(data_dict, feature_names)
        for arr in (X_train, y_train, X_test, y_test):
            assert not np.isnan(arr).any()

    def test_empty_dict_raises(self):
        with pytest.raises(ValueError):
            prepare_training_data({}, [])

    def test_custom_target_col(self, sample_ohlcv_df):
        data_dict = {"AAPL": sample_ohlcv_df.copy()}
        featured = engineer_features(data_dict)
        labelled, feature_names = generate_labels(featured, horizon=14)
        X_train, y_train, _, _ = prepare_training_data(
            labelled, feature_names, target_col="target_14d",
        )
        assert X_train.shape[0] > 0
        assert y_train.shape[0] > 0


# ---------------------------------------------------------------------------
# train_all_models_pipeline
# ---------------------------------------------------------------------------


def _make_mock_results() -> list[TrainingResult]:
    """Build minimal TrainingResult objects for two linear models × 1 scaler."""
    return [
        TrainingResult(
            model_name="linear_regression",
            scaler_variant="standard",
            best_params={},
            fold_metrics=[{"rmse": 1.0}],
            oos_metrics={"rmse": 1.0, "directional_accuracy": 55.0},
            fold_stability=0.1,
        ),
        TrainingResult(
            model_name="ridge",
            scaler_variant="standard",
            best_params={"alpha": 1.0},
            fold_metrics=[{"rmse": 0.9}],
            oos_metrics={"rmse": 0.9, "directional_accuracy": 58.0},
            fold_stability=0.08,
        ),
    ]


class TestTrainAllModelsPipeline:
    """Tests mock train_all_models to focus on pipeline reconstruction logic."""

    @patch("ml.pipelines.components.model_trainer.train_all_models")
    def test_returns_results_and_pipelines(self, mock_train, pipeline_data):
        mock_train.return_value = _make_mock_results()
        data_dict, feature_names = pipeline_data
        results, pipelines = train_all_models_pipeline(
            data_dict, feature_names, n_splits=3,
        )
        assert isinstance(results, list)
        assert isinstance(pipelines, dict)

    @patch("ml.pipelines.components.model_trainer.train_all_models")
    def test_results_are_training_results(self, mock_train, pipeline_data):
        mock_train.return_value = _make_mock_results()
        data_dict, feature_names = pipeline_data
        results, _ = train_all_models_pipeline(
            data_dict, feature_names, n_splits=3,
        )
        assert all(isinstance(r, TrainingResult) for r in results)

    @patch("ml.pipelines.components.model_trainer.train_all_models")
    def test_pipelines_keyed_correctly(self, mock_train, pipeline_data):
        mock_train.return_value = _make_mock_results()
        data_dict, feature_names = pipeline_data
        results, pipelines = train_all_models_pipeline(
            data_dict, feature_names, n_splits=3,
        )
        for r in results:
            key = f"{r.model_name}_{r.scaler_variant}"
            assert key in pipelines

    @patch("ml.pipelines.components.model_trainer.train_all_models")
    def test_pipelines_are_fitted(self, mock_train, pipeline_data):
        mock_train.return_value = _make_mock_results()
        data_dict, feature_names = pipeline_data
        results, pipelines = train_all_models_pipeline(
            data_dict, feature_names, n_splits=3,
        )
        X_train, _, X_test, _ = prepare_training_data(data_dict, feature_names)
        for pipe in pipelines.values():
            pred = pipe.predict(X_test)
            assert pred is not None

    @patch("ml.pipelines.components.model_trainer.train_all_models")
    def test_result_count_matches_pipeline_count(self, mock_train, pipeline_data):
        mock_train.return_value = _make_mock_results()
        data_dict, feature_names = pipeline_data
        results, pipelines = train_all_models_pipeline(
            data_dict, feature_names, n_splits=3,
        )
        assert len(results) == len(pipelines)

    @patch("ml.pipelines.components.model_trainer.train_all_models")
    def test_pipeline_predictions_shape(self, mock_train, pipeline_data):
        mock_train.return_value = _make_mock_results()
        data_dict, feature_names = pipeline_data
        results, pipelines = train_all_models_pipeline(
            data_dict, feature_names, n_splits=3,
        )
        X_train, _, X_test, _ = prepare_training_data(data_dict, feature_names)
        for pipe in pipelines.values():
            pred = pipe.predict(X_test)
            assert pred.shape == (X_test.shape[0],)
