"""Tests for ml.evaluation.ranking — composite scoring, ranking, and winner selection."""

from __future__ import annotations

import pytest

from ml.evaluation.ranking import (
    RankedModel,
    WinnerResult,
    compute_composite_score,
    rank_models,
    select_winner,
)
from ml.models.model_configs import TrainingResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_result(
    name: str,
    scaler: str,
    oos_rmse: float,
    da: float,
    fold_stability: float,
) -> TrainingResult:
    """Shorthand factory for synthetic TrainingResult objects."""
    return TrainingResult(
        model_name=name,
        scaler_variant=scaler,
        best_params={},
        fold_metrics=[{"rmse": oos_rmse}],
        oos_metrics={"rmse": oos_rmse, "directional_accuracy": da},
        fold_stability=fold_stability,
    )


@pytest.fixture
def sample_training_results() -> list[TrainingResult]:
    """Five synthetic results covering a range of metric profiles."""
    return [
        _make_result("ridge", "standard", oos_rmse=1.0, da=60.0, fold_stability=0.1),
        _make_result("lasso", "standard", oos_rmse=1.0, da=55.0, fold_stability=1.5),
        _make_result("rf", "robust", oos_rmse=2.0, da=80.0, fold_stability=0.2),
        _make_result("gbr", "minmax", oos_rmse=1.5, da=65.0, fold_stability=0.5),
        _make_result("svr", "standard", oos_rmse=3.0, da=50.0, fold_stability=0.3),
    ]


# ---------------------------------------------------------------------------
# TestCompositeScore
# ---------------------------------------------------------------------------


class TestCompositeScore:
    def test_zero_penalty_equals_rmse(self):
        r = _make_result("ridge", "std", oos_rmse=1.0, da=60.0, fold_stability=0.5)
        score = compute_composite_score(r, stability_penalty_weight=0.0, directional_accuracy_weight=0.0)
        assert score == pytest.approx(1.0)

    def test_penalty_increases_score(self):
        low_var = _make_result("a", "s", oos_rmse=1.0, da=50.0, fold_stability=0.1)
        high_var = _make_result("b", "s", oos_rmse=1.0, da=50.0, fold_stability=2.0)
        assert compute_composite_score(low_var) < compute_composite_score(high_var)

    def test_directional_accuracy_bonus(self):
        low_da = _make_result("a", "s", oos_rmse=1.0, da=40.0, fold_stability=0.1)
        high_da = _make_result("b", "s", oos_rmse=1.0, da=90.0, fold_stability=0.1)
        assert compute_composite_score(high_da) < compute_composite_score(low_da)

    def test_custom_weights(self):
        r = _make_result("a", "s", oos_rmse=1.0, da=60.0, fold_stability=0.5)
        default_score = compute_composite_score(r)
        heavy_penalty = compute_composite_score(r, stability_penalty_weight=2.0)
        assert heavy_penalty > default_score


# ---------------------------------------------------------------------------
# TestRankModels
# ---------------------------------------------------------------------------


class TestRankModels:
    def test_returns_ranked_models(self, sample_training_results):
        ranked = rank_models(sample_training_results)
        assert len(ranked) == len(sample_training_results)
        assert all(isinstance(rm, RankedModel) for rm in ranked)

    def test_rank_order_ascending(self, sample_training_results):
        ranked = rank_models(sample_training_results)
        assert [rm.rank for rm in ranked] == [1, 2, 3, 4, 5]

    def test_best_model_first(self, sample_training_results):
        ranked = rank_models(sample_training_results)
        scores = [rm.composite_score for rm in ranked]
        assert scores == sorted(scores)

    def test_high_variance_penalized(self, sample_training_results):
        ranked = rank_models(sample_training_results)
        # "lasso_standard" has same RMSE as "ridge_standard" but fold_stability=1.5 vs 0.1
        ridge_rank = next(rm.rank for rm in ranked if rm.training_result.model_name == "ridge")
        lasso_rank = next(rm.rank for rm in ranked if rm.training_result.model_name == "lasso")
        assert ridge_rank < lasso_rank

    def test_empty_results_raises(self):
        with pytest.raises(ValueError, match="empty"):
            rank_models([])

    def test_single_result(self):
        r = _make_result("solo", "s", oos_rmse=1.0, da=50.0, fold_stability=0.1)
        ranked = rank_models([r])
        assert len(ranked) == 1
        assert ranked[0].rank == 1


# ---------------------------------------------------------------------------
# TestSelectWinner
# ---------------------------------------------------------------------------


class TestSelectWinner:
    def test_winner_is_rank_one(self, sample_training_results):
        result = select_winner(sample_training_results)
        assert result.winner.rank == 1

    def test_margin_positive(self, sample_training_results):
        result = select_winner(sample_training_results)
        assert result.margin > 0

    def test_runner_up_exists(self, sample_training_results):
        result = select_winner(sample_training_results)
        assert result.runner_up is not None
        assert isinstance(result.runner_up, RankedModel)

    def test_single_candidate_no_runner_up(self):
        r = _make_result("solo", "s", oos_rmse=1.0, da=50.0, fold_stability=0.1)
        result = select_winner([r])
        assert result.runner_up is None
        assert result.margin == 0.0

    def test_total_candidates_count(self, sample_training_results):
        result = select_winner(sample_training_results)
        assert result.total_candidates == len(sample_training_results)
