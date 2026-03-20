"""Tests for ml.pipelines.components.evaluator."""

from __future__ import annotations

import numpy as np
import pytest

from ml.evaluation.ranking import RankedModel
from ml.models.model_configs import TrainingResult
from ml.pipelines.components.evaluator import (
    evaluate_models,
    generate_comparison_report,
    generate_cv_report,
)


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


@pytest.fixture
def sample_training_results() -> list[TrainingResult]:
    return [
        _make_result("ridge", "standard", 1.0, 60.0, 0.1),
        _make_result("lasso", "standard", 1.0, 55.0, 1.5),
        _make_result("rf", "robust", 2.0, 80.0, 0.2),
        _make_result("gbr", "minmax", 1.5, 65.0, 0.5),
        _make_result("svr", "standard", 3.0, 50.0, 0.3),
    ]


# ---------------------------------------------------------------------------
# TestEvaluateModels
# ---------------------------------------------------------------------------


class TestEvaluateModels:
    def test_returns_ranked_models(self, sample_training_results):
        ranked = evaluate_models(sample_training_results)
        assert len(ranked) == 5
        assert all(isinstance(rm, RankedModel) for rm in ranked)

    def test_custom_weights_passed_through(self, sample_training_results):
        default = evaluate_models(sample_training_results)
        heavy = evaluate_models(sample_training_results, stability_penalty_weight=5.0)
        # With heavier penalty, the high-variance model should move further down
        default_scores = [rm.composite_score for rm in default]
        heavy_scores = [rm.composite_score for rm in heavy]
        assert default_scores != heavy_scores

    def test_empty_results_raises(self):
        with pytest.raises(ValueError):
            evaluate_models([])


# ---------------------------------------------------------------------------
# TestGenerateComparisonReport
# ---------------------------------------------------------------------------


class TestGenerateComparisonReport:
    def test_report_keys(self, sample_training_results):
        ranked = evaluate_models(sample_training_results)
        report = generate_comparison_report(ranked)
        assert set(report.keys()) == {"total_models", "ranking", "best_model", "worst_model"}

    def test_ranking_length(self, sample_training_results):
        ranked = evaluate_models(sample_training_results)
        report = generate_comparison_report(ranked)
        assert len(report["ranking"]) == 5

    def test_best_worst_model(self, sample_training_results):
        ranked = evaluate_models(sample_training_results)
        report = generate_comparison_report(ranked)
        assert report["best_model"] == f"{ranked[0].training_result.model_name}_{ranked[0].training_result.scaler_variant}"
        assert report["worst_model"] == f"{ranked[-1].training_result.model_name}_{ranked[-1].training_result.scaler_variant}"

    def test_ranking_entry_keys(self, sample_training_results):
        ranked = evaluate_models(sample_training_results)
        report = generate_comparison_report(ranked)
        expected_keys = {"rank", "model_name", "scaler_variant", "composite_score", "oos_metrics", "fold_stability", "variance_penalty"}
        for entry in report["ranking"]:
            assert set(entry.keys()) == expected_keys


# ---------------------------------------------------------------------------
# generate_cv_report helpers
# ---------------------------------------------------------------------------


def _make_cv_result(name: str, scaler: str, fold_rmses: list[float]) -> TrainingResult:
    """Create a TrainingResult with realistic multi-fold metrics."""
    fold_metrics = []
    for rmse in fold_rmses:
        fold_metrics.append({
            "rmse": rmse,
            "r2": max(0, 1 - rmse),
            "mae": rmse * 0.8,
            "mape": rmse * 10,
            "directional_accuracy": 50 + (1 / rmse) * 10,
        })
    mean_rmse = sum(fold_rmses) / len(fold_rmses)
    fold_stability = float(np.std(fold_rmses))
    return TrainingResult(
        model_name=name,
        scaler_variant=scaler,
        best_params={},
        fold_metrics=fold_metrics,
        oos_metrics={"rmse": mean_rmse, "directional_accuracy": 55.0},
        fold_stability=fold_stability,
    )


@pytest.fixture
def cv_training_results() -> list[TrainingResult]:
    return [
        _make_cv_result("ridge", "standard", [1.0, 1.1, 0.9, 1.05, 0.95]),
        _make_cv_result("lasso", "standard", [1.5, 2.0, 1.8, 1.6, 2.2]),
        _make_cv_result("rf", "minmax", [0.8, 0.85, 0.9, 0.82, 0.88]),
    ]


# ---------------------------------------------------------------------------
# TestGenerateCVReport
# ---------------------------------------------------------------------------


class TestGenerateCVReport:
    def test_returns_dict(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        assert isinstance(report, dict)

    def test_top_level_keys(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        assert set(report.keys()) == {"total_models", "n_folds", "models", "aggregate"}

    def test_total_models(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        assert report["total_models"] == 3

    def test_n_folds(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        assert report["n_folds"] == 5

    def test_models_list_length(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        assert len(report["models"]) == 3

    def test_model_entry_keys(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        expected = {"model_name", "scaler_variant", "fold_metrics", "mean_metrics", "std_metrics", "fold_stability"}
        for entry in report["models"]:
            assert set(entry.keys()) == expected

    def test_mean_metrics_values(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        ridge_entry = [m for m in report["models"] if m["model_name"] == "ridge"][0]
        expected_mean = np.mean([1.0, 1.1, 0.9, 1.05, 0.95])
        assert abs(ridge_entry["mean_metrics"]["rmse"] - expected_mean) < 1e-10

    def test_std_metrics_values(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        ridge_entry = [m for m in report["models"] if m["model_name"] == "ridge"][0]
        expected_std = float(np.std([1.0, 1.1, 0.9, 1.05, 0.95]))
        assert abs(ridge_entry["std_metrics"]["rmse"] - expected_std) < 1e-10

    def test_aggregate_best_cv_rmse(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        assert report["aggregate"]["best_cv_rmse"]["model"] == "rf_minmax"

    def test_aggregate_most_stable(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        # rf has lowest fold_stability (std of [0.8, 0.85, 0.9, 0.82, 0.88])
        assert report["aggregate"]["most_stable"]["model"] == "rf_minmax"

    def test_aggregate_least_stable(self, cv_training_results):
        report = generate_cv_report(cv_training_results)
        # lasso has highest fold_stability (std of [1.5, 2.0, 1.8, 1.6, 2.2])
        assert report["aggregate"]["least_stable"]["model"] == "lasso_standard"

    def test_empty_results_raises(self):
        with pytest.raises(ValueError):
            generate_cv_report([])
