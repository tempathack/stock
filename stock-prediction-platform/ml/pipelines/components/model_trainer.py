"""Model trainer — train sklearn regressors with TimeSeriesSplit CV and optional tuning."""

from __future__ import annotations

import json
import logging
import os
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline

from ml.evaluation.cross_validation import create_time_series_cv, walk_forward_evaluate
from ml.features.transformations import SCALER_VARIANTS, build_scaler_pipeline
from ml.models.model_configs import (
    BOOSTER_MODELS,
    DISTANCE_NEURAL_MODELS,
    LINEAR_MODELS,
    TREE_MODELS,
    ModelConfig,
    TrainingResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Single-model training
# ---------------------------------------------------------------------------


def _build_pipeline(config: ModelConfig, scaler_variant: str) -> Pipeline:
    """Create a ``Pipeline([scaler, model])`` for a given config and scaler."""
    scaler_pipe = build_scaler_pipeline(scaler_variant)
    scaler_step = scaler_pipe.steps[0]  # ("scaler", ScalerInstance)
    model = config.model_class(**config.default_params)
    return Pipeline([scaler_step, ("model", model)])


def train_single_model(
    config: ModelConfig,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    scaler_variant: str,
    n_splits: int = 5,
) -> TrainingResult:
    """Train one (model × scaler) combination with optional hyperparameter tuning.

    Parameters
    ----------
    config:
        Model configuration with class, default params, and optional search space.
    X_train, y_train:
        Training data.
    X_test, y_test:
        Hold-out test data for OOS metrics.
    scaler_variant:
        One of ``"standard"``, ``"quantile"``, ``"minmax"``.
    n_splits:
        Number of TimeSeriesSplit folds.

    Returns
    -------
    ``TrainingResult`` with fold metrics, OOS metrics, and best params.
    """
    cv = create_time_series_cv(n_splits=n_splits)
    pipeline = _build_pipeline(config, scaler_variant)

    best_params: dict[str, Any] = {}

    if config.search_space is not None:
        # Prefix keys with "model__" for pipeline parameter routing
        param_dist = {f"model__{k}": v for k, v in config.search_space.items()}
        search = RandomizedSearchCV(
            pipeline,
            param_distributions=param_dist,
            n_iter=min(config.n_iter, _search_space_size(param_dist)),
            cv=cv,
            scoring="neg_root_mean_squared_error",
            random_state=42,
            n_jobs=-1,
            error_score="raise",
        )
        search.fit(X_train, y_train)
        pipeline = search.best_estimator_
        # Strip "model__" prefix for clean output
        best_params = {
            k.replace("model__", ""): v for k, v in search.best_params_.items()
        }
        logger.info(
            "%s/%s tuning complete — best params: %s",
            config.name, scaler_variant, best_params,
        )
    else:
        pipeline.fit(X_train, y_train)

    # Walk-forward CV metrics (refit on train splits)
    cv_result = walk_forward_evaluate(pipeline, X_train, y_train, cv=cv)

    # OOS metrics on held-out test set
    from ml.evaluation.metrics import compute_all_metrics

    y_pred_test = pipeline.predict(X_test)
    oos_metrics = compute_all_metrics(y_test, y_pred_test)
    oos_metrics["fold_stability"] = cv_result["fold_stability"]

    return TrainingResult(
        model_name=config.name,
        scaler_variant=scaler_variant,
        best_params=best_params,
        fold_metrics=cv_result["fold_metrics"],
        oos_metrics=oos_metrics,
        fold_stability=cv_result["fold_stability"],
    )


def _search_space_size(param_dist: dict) -> int:
    """Compute the total number of combinations in a search space."""
    size = 1
    for v in param_dist.values():
        if hasattr(v, "__len__"):
            size *= len(v)
        else:
            size *= 10  # continuous distribution fallback
    return size


# ---------------------------------------------------------------------------
# Data preparation — multi-ticker → single temporal split
# ---------------------------------------------------------------------------


def prepare_training_data(
    data_dict: dict[str, pd.DataFrame],
    feature_names: list[str],
    target_col: str = "target_7d",
    test_ratio: float = 0.2,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Consolidate per-ticker DataFrames into a single temporal train/test split.

    Returns ``(X_train, y_train, X_test, y_test)`` as numpy arrays.

    Raises ``ValueError`` if *data_dict* is empty or produces zero rows.
    """
    if not data_dict:
        raise ValueError("data_dict must be non-empty.")

    combined = pd.concat(data_dict.values()).sort_index()

    if combined.empty:
        raise ValueError("All DataFrames are empty after concatenation.")

    y = combined[target_col].values
    X = combined[feature_names].values

    split_idx = int(len(combined) * (1 - test_ratio))
    if split_idx <= 0 or split_idx >= len(combined):
        raise ValueError(
            f"Invalid split: {split_idx} rows for train out of {len(combined)} total."
        )

    logger.info(
        "Prepared training data: %d total rows, %d train, %d test, %d features.",
        len(combined), split_idx, len(combined) - split_idx, len(feature_names),
    )

    return X[:split_idx], y[:split_idx], X[split_idx:], y[split_idx:]


# ---------------------------------------------------------------------------
# Batch training — all linear models × all scalers
# ---------------------------------------------------------------------------


def train_linear_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    n_splits: int = 5,
) -> list[TrainingResult]:
    """Train all 6 linear models × 3 scaler variants = 18 runs.

    Returns
    -------
    List of 18 ``TrainingResult`` objects sorted by OOS RMSE (ascending).
    """
    results: list[TrainingResult] = []

    for config in LINEAR_MODELS.values():
        for scaler in SCALER_VARIANTS:
            logger.info("Training %s with %s scaler...", config.name, scaler)
            result = train_single_model(
                config=config,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                scaler_variant=scaler,
                n_splits=n_splits,
            )
            results.append(result)

    # Sort by OOS RMSE ascending (best first)
    results.sort(key=lambda r: r.oos_metrics["rmse"])
    return results


# ---------------------------------------------------------------------------
# Batch training — all tree/ensemble + booster models × all scalers
# ---------------------------------------------------------------------------


def train_tree_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    n_splits: int = 5,
    include_boosters: bool = True,
) -> list[TrainingResult]:
    """Train all tree/ensemble models × 3 scaler variants.

    With boosters enabled and all three installed: 9 models × 3 scalers = 27 runs.
    Without boosters: 6 models × 3 scalers = 18 runs.

    Returns
    -------
    List of ``TrainingResult`` objects sorted by OOS RMSE (ascending).
    """
    configs: dict[str, ModelConfig] = dict(TREE_MODELS)
    if include_boosters:
        configs.update(BOOSTER_MODELS)

    results: list[TrainingResult] = []

    for config in configs.values():
        for scaler in SCALER_VARIANTS:
            logger.info("Training %s with %s scaler...", config.name, scaler)
            result = train_single_model(
                config=config,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                scaler_variant=scaler,
                n_splits=n_splits,
            )
            results.append(result)

    results.sort(key=lambda r: r.oos_metrics["rmse"])
    return results


# ---------------------------------------------------------------------------
# Batch training — distance, SVM & neural models × all scalers
# ---------------------------------------------------------------------------


def train_distance_neural_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    n_splits: int = 5,
) -> list[TrainingResult]:
    """Train all distance/SVM/neural models × 3 scaler variants = 9 runs.

    Returns
    -------
    List of 9 ``TrainingResult`` objects sorted by OOS RMSE (ascending).
    """
    results: list[TrainingResult] = []

    for config in DISTANCE_NEURAL_MODELS.values():
        for scaler in SCALER_VARIANTS:
            logger.info("Training %s with %s scaler...", config.name, scaler)
            result = train_single_model(
                config=config,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                scaler_variant=scaler,
                n_splits=n_splits,
            )
            results.append(result)

    results.sort(key=lambda r: r.oos_metrics["rmse"])
    return results


def train_all_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    n_splits: int = 5,
) -> list[TrainingResult]:
    """Train all model families (linear + tree + boosters + distance/neural) and return sorted results."""
    linear = train_linear_models(X_train, y_train, X_test, y_test, n_splits)
    tree = train_tree_models(X_train, y_train, X_test, y_test, n_splits)
    distance_neural = train_distance_neural_models(X_train, y_train, X_test, y_test, n_splits)
    combined = linear + tree + distance_neural
    combined.sort(key=lambda r: r.oos_metrics["rmse"])
    return combined


# ---------------------------------------------------------------------------
# Pipeline entry point — data dict → results + fitted pipelines
# ---------------------------------------------------------------------------


def train_all_models_pipeline(
    data_dict: dict[str, pd.DataFrame],
    feature_names: list[str],
    target_col: str = "target_7d",
    test_ratio: float = 0.2,
    n_splits: int = 5,
) -> tuple[list[TrainingResult], dict[str, Pipeline]]:
    """Pipeline entry point: prepare data, train all models, return results + pipelines.

    Returns ``(results, pipelines)`` — sorted results and fitted pipelines keyed
    by ``"{model_name}_{scaler_variant}"``.
    """
    X_train, y_train, X_test, y_test = prepare_training_data(
        data_dict, feature_names, target_col, test_ratio,
    )

    results = train_all_models(X_train, y_train, X_test, y_test, n_splits)

    all_configs: dict[str, ModelConfig] = {
        **LINEAR_MODELS, **TREE_MODELS, **BOOSTER_MODELS, **DISTANCE_NEURAL_MODELS,
    }

    pipelines: dict[str, Pipeline] = {}
    for result in results:
        config = all_configs[result.model_name]
        pipeline = _build_pipeline(config, result.scaler_variant)
        if result.best_params:
            pipeline.set_params(
                **{f"model__{k}": v for k, v in result.best_params.items()}
            )
        pipeline.fit(X_train, y_train)
        key = f"{result.model_name}_{result.scaler_variant}"
        pipelines[key] = pipeline

    logger.info(
        "Pipeline training complete: %d models, %d fitted pipelines.",
        len(results), len(pipelines),
    )

    return results, pipelines


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def save_training_results(
    results: list[TrainingResult],
    output_dir: str,
) -> None:
    """Persist training results as JSON summary + pickled pipelines.

    Creates:
    - ``{output_dir}/training_results.json`` — metrics and params
    - ``{output_dir}/pipelines/{model}_{scaler}.pkl`` — fitted pipelines
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    pipelines_dir = out / "pipelines"
    pipelines_dir.mkdir(exist_ok=True)

    serializable = []
    for r in results:
        serializable.append(r.to_dict())

    with open(out / "training_results.json", "w") as f:
        json.dump(serializable, f, indent=2, default=str)

    logger.info("Saved training results JSON to %s", out / "training_results.json")


def save_pipeline(
    pipeline: Pipeline,
    result: TrainingResult,
    output_dir: str,
) -> str:
    """Pickle a fitted pipeline and update the result's pipeline_path.

    Returns the path to the saved pickle file.
    """
    out = Path(output_dir) / "pipelines"
    out.mkdir(parents=True, exist_ok=True)
    filename = f"{result.model_name}_{result.scaler_variant}.pkl"
    path = out / filename
    with open(path, "wb") as f:
        pickle.dump(pipeline, f)
    result.pipeline_path = str(path)
    return str(path)
