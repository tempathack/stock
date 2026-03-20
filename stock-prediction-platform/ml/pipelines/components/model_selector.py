"""Kubeflow component — ranks models and selects winner."""

from __future__ import annotations

import logging

from sklearn.pipeline import Pipeline

from ml.evaluation.ranking import select_winner
from ml.models.model_configs import TrainingResult
from ml.models.registry import ModelRegistry

logger = logging.getLogger(__name__)


def select_and_persist_winner(
    results: list[TrainingResult],
    pipelines: dict[str, Pipeline],
    feature_names: list[str],
    registry_dir: str = "model_registry",
    stability_penalty_weight: float = 0.5,
    directional_accuracy_weight: float = 0.01,
) -> dict:
    """Select the best model and persist it (and top runners-up) to the registry.

    Parameters
    ----------
    results:
        Training results for all candidate models.
    pipelines:
        Fitted pipelines keyed by ``"{model_name}_{scaler_variant}"``.
    feature_names:
        Ordered list of feature column names.
    registry_dir:
        Base directory for the file-based model registry.
    stability_penalty_weight:
        Weight applied to fold stability in the composite score.
    directional_accuracy_weight:
        Weight applied to directional accuracy bonus.

    Returns
    -------
    dict with winner_name, winner_score, registry_path, margin, total_candidates.

    Raises ``ValueError`` if *results* is empty.
    """
    winner_result = select_winner(
        results,
        stability_penalty_weight=stability_penalty_weight,
        directional_accuracy_weight=directional_accuracy_weight,
    )

    registry = ModelRegistry(base_dir=registry_dir)

    # Save winner
    winner_tr = winner_result.winner.training_result
    winner_key = f"{winner_tr.model_name}_{winner_tr.scaler_variant}"
    winner_pipeline = pipelines[winner_key]
    winner_path = registry.save_winner(winner_result, winner_pipeline, feature_names)

    logger.info("Persisted winner %s → %s", winner_key, winner_path)

    # Save top-5 non-winner models as well
    from ml.evaluation.ranking import rank_models

    ranked = rank_models(
        results,
        stability_penalty_weight=stability_penalty_weight,
        directional_accuracy_weight=directional_accuracy_weight,
    )
    for rm in ranked[1:5]:
        tr = rm.training_result
        key = f"{tr.model_name}_{tr.scaler_variant}"
        if key in pipelines:
            registry.save_model(
                result=tr,
                pipeline=pipelines[key],
                feature_names=feature_names,
                rank=rm.rank,
                is_winner=False,
            )

    return {
        "winner_name": winner_key,
        "winner_score": winner_result.winner.composite_score,
        "registry_path": winner_path,
        "margin": winner_result.margin,
        "total_candidates": winner_result.total_candidates,
    }
