"""Kubeflow component — computes all evaluation metrics per model."""

from __future__ import annotations

import logging

import numpy as np

from ml.evaluation.ranking import RankedModel, rank_models
from ml.models.model_configs import TrainingResult

logger = logging.getLogger(__name__)


def evaluate_models(
    results: list[TrainingResult],
    stability_penalty_weight: float = 0.5,
    directional_accuracy_weight: float = 0.01,
) -> list[RankedModel]:
    """Rank all training results by composite score.

    Raises ``ValueError`` if *results* is empty.
    """
    ranked = rank_models(
        results,
        stability_penalty_weight=stability_penalty_weight,
        directional_accuracy_weight=directional_accuracy_weight,
    )

    logger.info("Evaluated %d models.", len(ranked))
    for rm in ranked[:3]:
        logger.info(
            "  #%d %s_%s  score=%.6f",
            rm.rank,
            rm.training_result.model_name,
            rm.training_result.scaler_variant,
            rm.composite_score,
        )
    if ranked:
        worst = ranked[-1]
        logger.info(
            "  Worst: #%d %s_%s  score=%.6f",
            worst.rank,
            worst.training_result.model_name,
            worst.training_result.scaler_variant,
            worst.composite_score,
        )

    return ranked


def generate_comparison_report(ranked: list[RankedModel]) -> dict:
    """Build a summary dict suitable for API / frontend consumption."""
    ranking_entries = [
        {
            "rank": rm.rank,
            "model_name": rm.training_result.model_name,
            "scaler_variant": rm.training_result.scaler_variant,
            "composite_score": rm.composite_score,
            "oos_metrics": rm.training_result.oos_metrics,
            "fold_stability": rm.fold_stability,
            "variance_penalty": rm.variance_penalty,
        }
        for rm in ranked
    ]

    best = ranked[0] if ranked else None
    worst = ranked[-1] if ranked else None

    return {
        "total_models": len(ranked),
        "ranking": ranking_entries,
        "best_model": f"{best.training_result.model_name}_{best.training_result.scaler_variant}" if best else None,
        "worst_model": f"{worst.training_result.model_name}_{worst.training_result.scaler_variant}" if worst else None,
    }


def generate_cv_report(results: list[TrainingResult]) -> dict:
    """Extract per-model, per-fold cross-validation metrics into a structured report.

    Raises ``ValueError`` if *results* is empty.
    """
    if not results:
        raise ValueError("results must be non-empty.")

    n_folds = len(results[0].fold_metrics)

    models: list[dict] = []
    for r in results:
        # Compute mean and std for each metric key across folds
        metric_keys = set()
        for fm in r.fold_metrics:
            metric_keys.update(fm.keys())
        # Only include keys present in ALL folds
        common_keys = metric_keys.copy()
        for fm in r.fold_metrics:
            common_keys &= set(fm.keys())

        mean_metrics: dict[str, float] = {}
        std_metrics: dict[str, float] = {}
        for key in sorted(common_keys):
            values = [fm[key] for fm in r.fold_metrics]
            mean_metrics[key] = float(np.mean(values))
            std_metrics[key] = float(np.std(values))

        models.append({
            "model_name": r.model_name,
            "scaler_variant": r.scaler_variant,
            "fold_metrics": r.fold_metrics,
            "mean_metrics": mean_metrics,
            "std_metrics": std_metrics,
            "fold_stability": r.fold_stability,
        })

    # Aggregate statistics
    best_cv = min(models, key=lambda m: m["mean_metrics"].get("rmse", float("inf")))
    most_stable = min(models, key=lambda m: m["fold_stability"])
    least_stable = max(models, key=lambda m: m["fold_stability"])

    aggregate = {
        "best_cv_rmse": {
            "model": f"{best_cv['model_name']}_{best_cv['scaler_variant']}",
            "value": best_cv["mean_metrics"].get("rmse", float("inf")),
        },
        "most_stable": {
            "model": f"{most_stable['model_name']}_{most_stable['scaler_variant']}",
            "value": most_stable["fold_stability"],
        },
        "least_stable": {
            "model": f"{least_stable['model_name']}_{least_stable['scaler_variant']}",
            "value": least_stable["fold_stability"],
        },
    }

    logger.info(
        "CV report: %d models, %d folds, best CV RMSE: %s",
        len(results), n_folds, aggregate["best_cv_rmse"]["model"],
    )

    return {
        "total_models": len(results),
        "n_folds": n_folds,
        "models": models,
        "aggregate": aggregate,
    }
