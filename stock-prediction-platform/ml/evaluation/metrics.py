"""Evaluation metrics — R², MAE, RMSE, MAPE, directional accuracy, fold stability."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Coefficient of determination (R²)."""
    return float(r2_score(y_true, y_pred))


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(mean_absolute_error(y_true, y_pred))


def compute_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def compute_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Percentage Error (as percentage).

    Returns 0.0 when all true values are zero to avoid division errors.
    Rows where ``y_true == 0`` are excluded from the calculation.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    mask = y_true != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def compute_directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Percentage of predictions matching the sign of the actual value.

    Compares ``sign(y_pred)`` with ``sign(y_true)``.  Zeros in either
    array are treated as their own sign (``np.sign(0) == 0``).
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    if len(y_true) == 0:
        return 0.0
    return float(np.mean(np.sign(y_true) == np.sign(y_pred)) * 100)


def compute_fold_stability(fold_rmses: list[float]) -> float:
    """Standard deviation of RMSE values across CV folds.

    Lower values indicate more stable model performance.
    Returns 0.0 for a single fold.
    """
    if len(fold_rmses) <= 1:
        return 0.0
    return float(np.std(fold_rmses, ddof=1))


def compute_all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute all five point metrics and return as a dict."""
    return {
        "r2": compute_r2(y_true, y_pred),
        "mae": compute_mae(y_true, y_pred),
        "rmse": compute_rmse(y_true, y_pred),
        "mape": compute_mape(y_true, y_pred),
        "directional_accuracy": compute_directional_accuracy(y_true, y_pred),
    }
