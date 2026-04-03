"""Backtest service — join historical predictions with actual prices and compute accuracy metrics.

If no prediction/actual pairs exist for the requested range (e.g. all predictions are future-dated),
fall back to an on-the-fly synthetic backtest using ohlcv_daily + a naive SMA model.
Results are cached in backtest_results for subsequent requests.
"""

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


def _build_metrics_dict(actuals: list[float], predictions_list: list[float], series: list[dict]) -> dict:
    """Compute ML accuracy metrics from actuals vs predictions."""
    errors = np.array(actuals) - np.array(predictions_list)
    abs_errors = np.abs(errors)
    abs_actuals = np.abs(np.array(actuals))

    rmse = float(math.sqrt(np.mean(errors**2)))
    mae = float(np.mean(abs_errors))

    nonzero_mask = abs_actuals > 0
    if np.any(nonzero_mask):
        mape = float(np.mean(abs_errors[nonzero_mask] / abs_actuals[nonzero_mask]) * 100.0)
    else:
        mape = 0.0

    directional_accuracy = _compute_directional_accuracy(actuals, predictions_list)
    r2 = _compute_r2(actuals, predictions_list)

    return {
        "rmse": round(rmse, 6),
        "mae": round(mae, 6),
        "mape": round(mape, 4),
        "directional_accuracy": round(directional_accuracy, 2),
        "r2": round(r2, 6),
        "total_points": len(series),
    }


async def _store_backtest_result(
    ticker: str,
    start_date: str,
    end_date: str,
    horizon_days: int,
    metrics: dict,
    series: list[dict],
) -> None:
    """Cache computed backtest result in backtest_results table (best-effort)."""
    import datetime

    try:
        # Compute trading-style metrics from series for caching
        actuals = [p["actual_price"] for p in series]
        predictions_list = [p["predicted_price"] for p in series]
        n = len(series)

        # Total return: from first to last actual price
        total_return_pct = ((actuals[-1] - actuals[0]) / actuals[0] * 100.0) if actuals[0] != 0 else 0.0

        # Benchmark: buy-and-hold return
        benchmark_return_pct = total_return_pct

        # Win rate: fraction of periods where prediction direction was correct
        win_rate = metrics.get("directional_accuracy", 0.0)

        # Sharpe ratio approximation using daily returns
        daily_returns = [(actuals[i] - actuals[i - 1]) / actuals[i - 1] for i in range(1, len(actuals)) if actuals[i - 1] != 0]
        if len(daily_returns) > 1:
            mean_ret = float(np.mean(daily_returns))
            std_ret = float(np.std(daily_returns))
            sharpe = (mean_ret / std_ret * math.sqrt(252)) if std_ret > 0 else 0.0
        else:
            sharpe = 0.0

        # Max drawdown
        peak = actuals[0]
        max_dd = 0.0
        for price in actuals:
            if price > peak:
                peak = price
            dd = (peak - price) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        start_dt = datetime.date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
        end_dt = datetime.date.fromisoformat(end_date) if isinstance(end_date, str) else end_date

        store_query = text("""
            INSERT INTO backtest_results
                (ticker, start_date, end_date, horizon_days,
                 total_return_pct, benchmark_return_pct, sharpe_ratio,
                 max_drawdown, win_rate, trade_count)
            VALUES
                (:ticker, :start_date, :end_date, :horizon_days,
                 :total_return_pct, :benchmark_return_pct, :sharpe_ratio,
                 :max_drawdown, :win_rate, :trade_count)
            ON CONFLICT DO NOTHING
        """)  # noqa: S608

        async with get_async_session() as session:
            await session.execute(store_query, {
                "ticker": ticker,
                "start_date": start_dt,
                "end_date": end_dt,
                "horizon_days": horizon_days,
                "total_return_pct": round(total_return_pct, 4),
                "benchmark_return_pct": round(benchmark_return_pct, 4),
                "sharpe_ratio": round(sharpe, 4),
                "max_drawdown": round(max_dd * 100.0, 4),
                "win_rate": round(win_rate, 4),
                "trade_count": n,
            })
            await session.commit()
    except Exception:
        logger.debug("Could not cache backtest result (best-effort)", exc_info=True)


async def _compute_synthetic_backtest(
    ticker: str,
    start_date: str,
    end_date: str,
    horizon: int,
) -> dict | None:
    """Compute on-the-fly backtest from ohlcv_daily using a naive SMA model.

    Uses a rolling SMA window to generate predicted prices and compares with
    actual closes in the same date range. This provides a meaningful baseline
    when no prediction/actual pairs exist in the predictions table.
    """
    import datetime

    start_dt = datetime.date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
    end_dt = datetime.date.fromisoformat(end_date) if isinstance(end_date, str) else end_date

    horizon_days = horizon if horizon is not None else 7
    # Fetch extra rows before start_date to warm up the SMA window
    lookback_days = max(horizon_days * 3, 30)
    warm_start = start_dt - datetime.timedelta(days=lookback_days)

    ohlcv_query = text("""
        SELECT date, close
        FROM ohlcv_daily
        WHERE ticker = :ticker
          AND date >= :warm_start
          AND date <= :end_date
          AND close IS NOT NULL
        ORDER BY date ASC
    """)  # noqa: S608

    try:
        async with get_async_session() as session:
            result = await session.execute(ohlcv_query, {
                "ticker": ticker,
                "warm_start": warm_start,
                "end_date": end_dt,
            })
            rows = result.mappings().all()
    except Exception:
        logger.exception("Failed to fetch OHLCV for synthetic backtest of %s", ticker)
        return None

    if len(rows) < horizon_days + 2:
        return None

    # Convert to lists
    dates = [row["date"] for row in rows]
    closes = [float(row["close"]) for row in rows]

    # Build predicted series: predicted price at index i = SMA of closes[i-horizon_days : i]
    # We compare predicted_price (made horizon days earlier) vs actual close today
    series = []
    actuals_list: list[float] = []
    preds_list: list[float] = []

    for i in range(horizon_days, len(closes)):
        actual_date = dates[i]
        # Only include dates within the requested range
        if actual_date < start_dt:
            continue
        actual_price = closes[i]
        # Predicted price = SMA of the window ending horizon_days before today
        window_end = i - horizon_days
        window_start = max(0, window_end - horizon_days)
        predicted_price = float(np.mean(closes[window_start : window_end + 1]))

        error = actual_price - predicted_price
        error_pct = (error / actual_price) * 100.0 if actual_price != 0 else 0.0
        series.append({
            "date": str(actual_date),
            "actual_price": round(actual_price, 4),
            "predicted_price": round(predicted_price, 4),
            "error": round(error, 4),
            "error_pct": round(error_pct, 4),
        })
        actuals_list.append(actual_price)
        preds_list.append(predicted_price)

    if not series:
        return None

    metrics = _build_metrics_dict(actuals_list, preds_list, series)

    return {
        "ticker": ticker,
        "model_name": f"naive_sma{horizon_days}",
        "horizon": horizon_days,
        "start_date": series[0]["date"],
        "end_date": series[-1]["date"],
        "metrics": metrics,
        "series": series,
        "features_pit_correct": False,
    }


async def get_backtest_data(
    ticker: str,
    start_date: str,
    end_date: str,
    horizon: int | None = None,
    model_id: int | None = None,
) -> dict | None:
    """Query predictions joined with ohlcv_daily and compute backtest metrics.

    Falls back to on-the-fly synthetic backtest from ohlcv_daily when no
    prediction/actual pairs exist (e.g. all predictions are future-dated).
    """
    if get_engine() is None:
        return None

    # Build dynamic WHERE clauses
    where_clauses = [
        "p.ticker = :ticker",
        "p.predicted_date >= :start_date",
        "p.predicted_date <= :end_date",
    ]
    import datetime
    start_dt = datetime.date.fromisoformat(start_date) if isinstance(start_date, str) else start_date
    end_dt = datetime.date.fromisoformat(end_date) if isinstance(end_date, str) else end_date
    params: dict = {
        "ticker": ticker,
        "start_date": start_dt,
        "end_date": end_dt,
    }

    if horizon is not None:
        where_clauses.append("(p.predicted_date - p.prediction_date) = :horizon")
        params["horizon"] = horizon

    if model_id is not None:
        where_clauses.append("p.model_id = :model_id")
        params["model_id"] = model_id
    elif horizon is None:
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
    """)  # noqa: S608

    rows = []
    try:
        async with get_async_session() as session:
            result = await session.execute(query, params)
            rows = result.mappings().all()
    except Exception:
        logger.exception("Failed to fetch backtest data for %s", ticker)

    if rows:
        # Build series from DB prediction/actual pairs
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

        metrics = _build_metrics_dict(actuals, predictions_list, series)
        result_dict = {
            "ticker": ticker,
            "model_name": model_name,
            "horizon": horizon_days,
            "start_date": str(rows[0]["date"]),
            "end_date": str(rows[-1]["date"]),
            "metrics": metrics,
            "series": series,
            "features_pit_correct": False,
        }
        await _store_backtest_result(
            ticker, result_dict["start_date"], result_dict["end_date"],
            horizon_days, metrics, series,
        )
        return result_dict

    # No prediction/actual pairs — compute on-the-fly from OHLCV using naive SMA model
    logger.info(
        "No prediction/actual pairs for %s in [%s, %s] — using synthetic SMA backtest",
        ticker, start_date, end_date,
    )
    synthetic = await _compute_synthetic_backtest(ticker, start_date, end_date, horizon or 7)
    if synthetic is None:
        return None

    await _store_backtest_result(
        ticker, synthetic["start_date"], synthetic["end_date"],
        synthetic["horizon"], synthetic["metrics"], synthetic["series"],
    )
    return synthetic
