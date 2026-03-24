"""Backtest service — join historical predictions with actual prices and compute accuracy metrics."""

from __future__ import annotations

import logging
import math

import numpy as np
from sqlalchemy import text

from app.models.database import get_async_session, get_engine

logger = logging.getLogger(__name__)


def _compute_directional_accuracy(actuals: list[float], predictions: list[float]) -> float:
    """Compute % of periods where predicted direction matches actual direction."""
    if len(actuals) < 2:
        return 0.0
    correct = 0
    total = 0
    for i in range(1, len(actuals)):
        actual_dir = actuals[i] - actuals[i - 1]
        pred_dir = predictions[i] - predictions[i - 1]
        if (actual_dir > 0 and pred_dir > 0) or (actual_dir < 0 and pred_dir < 0) or (actual_dir == 0 and pred_dir == 0):
            correct += 1
        total += 1
    return (correct / total) * 100.0 if total > 0 else 0.0


def _compute_r2(actuals: list[float], predictions: list[float]) -> float:
    """Compute R² score. Returns 0.0 if SS_tot is zero."""
    a = np.array(actuals)
    p = np.array(predictions)
    ss_res = float(np.sum((a - p) ** 2))
    ss_tot = float(np.sum((a - np.mean(a)) ** 2))
    if ss_tot == 0:
        return 0.0
    return 1.0 - ss_res / ss_tot


async def get_backtest_data(
    ticker: str,
    start_date: str,
    end_date: str,
    horizon: int | None = None,
    model_id: int | None = None,
) -> dict | None:
    """Query predictions joined with ohlcv_daily and compute backtest metrics."""
    if get_engine() is None:
        return None

    # Build dynamic WHERE clauses
    where_clauses = [
        "p.ticker = :ticker",
        "p.predicted_date >= :start_date",
        "p.predicted_date <= :end_date",
    ]
    params: dict = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
    }

    if horizon is not None:
        where_clauses.append("(p.predicted_date - p.prediction_date) = :horizon")
        params["horizon"] = horizon

    if model_id is not None:
        where_clauses.append("p.model_id = :model_id")
        params["model_id"] = model_id
    elif horizon is None:
        # Default: use the active model
        where_clauses.append("m.is_active = true")

    where_sql = " AND ".join(where_clauses)

    query = text(f"""
        SELECT p.predicted_date AS date,
               o.close          AS actual_price,
               p.predicted_price,
               m.model_name,
               (p.predicted_date - p.prediction_date) AS horizon_days
        FROM predictions p
        JOIN ohlcv_daily o ON o.ticker = p.ticker AND o.date = p.predicted_date
        JOIN model_registry m ON m.model_id = p.model_id
        WHERE {where_sql}
        ORDER BY p.predicted_date ASC
    """)  # noqa: S608 — all user inputs are parameterised

    try:
        async with get_async_session() as session:
            result = await session.execute(query, params)
            rows = result.mappings().all()
    except Exception:
        logger.exception("Failed to fetch backtest data for %s", ticker)
        return None

    if not rows:
        return None

    # Build series
    series = []
    actuals: list[float] = []
    predictions_list: list[float] = []
    model_name = str(rows[0]["model_name"])
    horizon_days = int(rows[0]["horizon_days"])

    for row in rows:
        actual = float(row["actual_price"])
        predicted = float(row["predicted_price"])
        error = actual - predicted
        error_pct = (error / actual) * 100.0 if actual != 0 else 0.0
        series.append({
            "date": str(row["date"]),
            "actual_price": actual,
            "predicted_price": predicted,
            "error": round(error, 4),
            "error_pct": round(error_pct, 4),
        })
        actuals.append(actual)
        predictions_list.append(predicted)

    # Compute aggregate metrics
    errors = np.array(actuals) - np.array(predictions_list)
    abs_errors = np.abs(errors)
    abs_actuals = np.abs(np.array(actuals))

    rmse = float(math.sqrt(np.mean(errors**2)))
    mae = float(np.mean(abs_errors))

    # MAPE: skip zero actuals
    nonzero_mask = abs_actuals > 0
    if np.any(nonzero_mask):
        mape = float(np.mean(abs_errors[nonzero_mask] / abs_actuals[nonzero_mask]) * 100.0)
    else:
        mape = 0.0

    directional_accuracy = _compute_directional_accuracy(actuals, predictions_list)
    r2 = _compute_r2(actuals, predictions_list)

    return {
        "ticker": ticker,
        "model_name": model_name,
        "horizon": horizon_days,
        "start_date": str(rows[0]["date"]),
        "end_date": str(rows[-1]["date"]),
        "metrics": {
            "rmse": round(rmse, 6),
            "mae": round(mae, 6),
            "mape": round(mape, 4),
            "directional_accuracy": round(directional_accuracy, 2),
            "r2": round(r2, 6),
            "total_points": len(series),
        },
        "series": series,
    }
