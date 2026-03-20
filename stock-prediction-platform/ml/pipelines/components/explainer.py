"""Kubeflow component — SHAP explainability for top models."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from sklearn.pipeline import Pipeline

from ml.evaluation.ranking import rank_models

try:
    from ml.evaluation.shap_analysis import get_shap_summary
except ImportError:  # shap / numba not available in this environment
    get_shap_summary = None  # type: ignore[assignment]
from ml.models.model_configs import TrainingResult

logger = logging.getLogger(__name__)


def explain_top_models(
    results: list[TrainingResult],
    pipelines: dict[str, Pipeline],
    X: np.ndarray,
    feature_names: list[str],
    registry_dir: str = "model_registry",
    top_n: int = 5,
    max_samples: int = 200,
    stability_penalty_weight: float = 0.5,
    directional_accuracy_weight: float = 0.01,
) -> dict[str, dict]:
    """Compute SHAP values for the top-N ranked models and store in registry.

    Parameters
    ----------
    results:
        Training results for all candidate models.
    pipelines:
        Fitted pipelines keyed by ``"{model_name}_{scaler_variant}"``.
    X:
        Feature matrix for SHAP computation.
    feature_names:
        Ordered list of feature column names.
    registry_dir:
        Base directory for the file-based model registry.
    top_n:
        Number of top models to explain.
    max_samples:
        Maximum samples for KernelExplainer.
    stability_penalty_weight:
        Weight applied to fold stability in ranking.
    directional_accuracy_weight:
        Weight applied to directional accuracy bonus.

    Returns
    -------
    Dict keyed by model_key → ``{"feature_importance": [...], "shap_summary": {...}}``.
    """
    ranked = rank_models(
        results,
        stability_penalty_weight=stability_penalty_weight,
        directional_accuracy_weight=directional_accuracy_weight,
    )

    n = min(top_n, len(ranked))
    output: dict[str, dict] = {}

    for rm in ranked[:n]:
        tr = rm.training_result
        model_key = f"{tr.model_name}_{tr.scaler_variant}"

        if model_key not in pipelines:
            logger.warning("Pipeline for %s not found — skipping SHAP.", model_key)
            continue

        pipeline = pipelines[model_key]
        summary = get_shap_summary(pipeline, X, tr.model_name, feature_names, max_samples)

        # Find the latest version directory in the registry
        model_dir = Path(registry_dir) / model_key
        if model_dir.exists():
            versions = sorted(
                (d for d in model_dir.iterdir() if d.is_dir() and d.name.startswith("v")),
                key=lambda d: int(d.name[1:]),
            )
            if versions:
                ver_dir = versions[-1]
                with open(ver_dir / "shap_importance.json", "w") as f:
                    json.dump(summary["feature_importance"], f, indent=2)
                with open(ver_dir / "shap_values.json", "w") as f:
                    json.dump(summary, f, indent=2)
                logger.info("Stored SHAP results for %s → %s", model_key, ver_dir)

        output[model_key] = {
            "feature_importance": summary["feature_importance"],
            "shap_summary": summary,
        }

    logger.info("Computed SHAP for %d / %d top models.", len(output), n)
    return output
