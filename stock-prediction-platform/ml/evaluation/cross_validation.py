"""TimeSeriesSplit cross-validation with no shuffling."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
from sklearn.base import clone
from sklearn.model_selection import TimeSeriesSplit

from ml.evaluation.metrics import compute_all_metrics, compute_fold_stability


def create_time_series_cv(n_splits: int = 5) -> TimeSeriesSplit:
    """Return a configured TimeSeriesSplit splitter.

    Parameters
    ----------
    n_splits:
        Number of folds.  Must be ≥ 2.

    Returns
    -------
    ``TimeSeriesSplit`` with no shuffling (inherent) and ``gap=0``.
    """
    return TimeSeriesSplit(n_splits=n_splits)


def walk_forward_evaluate(
    estimator: Any,
    X: np.ndarray,
    y: np.ndarray,
    cv: TimeSeriesSplit | None = None,
) -> dict:
    """Run walk-forward cross-validation and return per-fold + aggregated metrics.

    Parameters
    ----------
    estimator:
        An sklearn-compatible estimator (or ``Pipeline``).  Cloned per fold.
    X:
        Feature matrix.
    y:
        Target vector.
    cv:
        Splitter instance.  Defaults to ``create_time_series_cv()``.

    Returns
    -------
    dict with keys:
        - ``fold_metrics``: list of per-fold metric dicts
        - ``oos_metrics``: mean of per-fold metrics
        - ``fold_stability``: std of RMSE across folds
    """
    if cv is None:
        cv = create_time_series_cv()

    fold_metrics: list[dict] = []
    fold_rmses: list[float] = []

    for train_idx, test_idx in cv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model = clone(estimator)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        metrics = compute_all_metrics(y_test, y_pred)
        fold_metrics.append(metrics)
        fold_rmses.append(metrics["rmse"])

    # Aggregate: mean across folds
    metric_keys = fold_metrics[0].keys()
    oos_metrics = {
        key: float(np.mean([fm[key] for fm in fold_metrics])) for key in metric_keys
    }
    oos_metrics["fold_stability"] = compute_fold_stability(fold_rmses)

    return {
        "fold_metrics": fold_metrics,
        "oos_metrics": oos_metrics,
        "fold_stability": compute_fold_stability(fold_rmses),
    }
