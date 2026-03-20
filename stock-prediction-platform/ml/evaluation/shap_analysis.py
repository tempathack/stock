"""SHAP value computation — TreeExplainer, LinearExplainer, and KernelExplainer fallback."""

from __future__ import annotations

import logging

import numpy as np
import shap
from sklearn.pipeline import Pipeline

from ml.models.model_configs import BOOSTER_MODELS, LINEAR_MODELS, TREE_MODELS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Explainer routing constants
# ---------------------------------------------------------------------------

_TREE_NAMES: set[str] = set(TREE_MODELS.keys()) | set(BOOSTER_MODELS.keys())
_LINEAR_NAMES: set[str] = set(LINEAR_MODELS.keys())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_explainer_type(model_name: str) -> str:
    """Return the SHAP explainer type for a given model name.

    Returns ``"tree"``, ``"linear"``, or ``"kernel"`` (fallback).
    """
    if model_name in _TREE_NAMES:
        return "tree"
    if model_name in _LINEAR_NAMES:
        return "linear"
    return "kernel"


def compute_shap_values(
    pipeline: Pipeline,
    X: np.ndarray,
    model_name: str,
    feature_names: list[str],
    max_samples: int = 200,
    background_samples: int = 50,
) -> tuple[np.ndarray, list[str]]:
    """Compute SHAP values for a fitted pipeline.

    Parameters
    ----------
    pipeline:
        Fitted sklearn Pipeline with optional scaler + ``"model"`` step.
    X:
        Raw feature matrix (pre-scaling is handled internally).
    model_name:
        Name used to select the explainer type.
    feature_names:
        Feature column names matching ``X.shape[1]``.
    max_samples:
        Maximum samples for KernelExplainer explanation.
    background_samples:
        Number of background samples for KernelExplainer.

    Returns
    -------
    Tuple of ``(shap_values, feature_names)`` where ``shap_values`` has
    shape ``(n_samples, n_features)``.
    """
    model = pipeline.named_steps["model"]

    # Transform X through all pipeline steps *except* the final model
    steps_before_model = pipeline[:-1]
    if len(steps_before_model) > 0:
        X_transformed = steps_before_model.transform(X)
    else:
        X_transformed = np.asarray(X)

    explainer_type = get_explainer_type(model_name)
    logger.info("Computing SHAP values for %s using %s explainer.", model_name, explainer_type)

    if explainer_type == "tree":
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_transformed)

    elif explainer_type == "linear":
        explainer = shap.LinearExplainer(model, X_transformed)
        shap_values = explainer.shap_values(X_transformed)

    else:  # kernel fallback
        bg_k = min(background_samples, len(X_transformed))
        background = shap.kmeans(X_transformed, bg_k)
        explainer = shap.KernelExplainer(model.predict, background)

        if len(X_transformed) > max_samples:
            rng = np.random.default_rng(42)
            indices = rng.choice(len(X_transformed), size=max_samples, replace=False)
            X_explain = X_transformed[indices]
        else:
            X_explain = X_transformed

        shap_values = explainer.shap_values(X_explain)

    shap_values = np.asarray(shap_values)
    return shap_values, list(feature_names)


def compute_feature_importance(
    shap_values: np.ndarray,
    feature_names: list[str],
) -> list[dict]:
    """Compute mean |SHAP| per feature, sorted descending.

    Returns a list of ``{"feature": str, "mean_abs_shap": float}``.
    """
    mean_abs = np.mean(np.abs(shap_values), axis=0)
    importance = [
        {"feature": name, "mean_abs_shap": float(val)}
        for name, val in zip(feature_names, mean_abs)
    ]
    importance.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
    return importance


def get_shap_summary(
    pipeline: Pipeline,
    X: np.ndarray,
    model_name: str,
    feature_names: list[str],
    max_samples: int = 200,
) -> dict:
    """Compute SHAP values and feature importance for a model.

    Returns a dict with ``shap_values`` (list of lists), ``feature_names``,
    ``n_samples``, and ``feature_importance``.
    """
    shap_vals, names = compute_shap_values(
        pipeline, X, model_name, feature_names, max_samples=max_samples,
    )
    importance = compute_feature_importance(shap_vals, names)

    return {
        "shap_values": shap_vals.tolist(),
        "feature_names": names,
        "n_samples": len(shap_vals),
        "feature_importance": importance,
    }
