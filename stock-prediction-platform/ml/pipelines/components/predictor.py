"""Prediction generator — use the active deployed model to forecast."""

from __future__ import annotations

import json
import logging
import pickle
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ml.pipelines.components.feature_engineer import engineer_features

logger = logging.getLogger(__name__)


def generate_predictions(
    data_dict: dict[str, pd.DataFrame],
    serving_dir: str = "/models/active",
    horizon: int = 7,
    horizons: list[int] | None = None,
) -> list[dict]:
    """Generate predictions for all tickers using the active model.

    Parameters
    ----------
    data_dict:
        Per-ticker OHLCV DataFrames (must have enough rows for feature engineering).
    serving_dir:
        Path to the serving directory containing pipeline.pkl, features.json,
        and metadata.json.
    horizon:
        Prediction horizon in days (used when *horizons* is ``None``).
    horizons:
        List of horizons for multi-horizon mode.  When provided, iterates
        each horizon and reads from ``{serving_dir}/horizon_{h}d/``.

    Returns
    -------
    list[dict]
        Each dict contains: ticker, prediction_date, predicted_date,
        predicted_price, model_name, confidence, and optionally horizon_days.
    """
    if horizons is not None:
        all_predictions: list[dict] = []
        for h in horizons:
            h_serving = f"{serving_dir}/horizon_{h}d"
            try:
                preds = _generate_predictions_single(data_dict, h_serving, h)
                for p in preds:
                    p["horizon_days"] = h
                all_predictions.extend(preds)
            except FileNotFoundError:
                logger.warning("Horizon %dd serving dir not found — skipping", h)
                continue
        return all_predictions
    return _generate_predictions_single(data_dict, serving_dir, horizon)


def _generate_predictions_single(
    data_dict: dict[str, pd.DataFrame],
    serving_dir: str,
    horizon: int,
) -> list[dict]:
    """Generate predictions for a single horizon from a specific serving directory."""
    srv = Path(serving_dir)

    # Load model artifacts
    pipeline_path = srv / "pipeline.pkl"
    features_path = srv / "features.json"
    metadata_path = srv / "metadata.json"

    if not srv.exists():
        raise FileNotFoundError(f"Serving directory does not exist: {srv}")
    if not pipeline_path.exists():
        raise FileNotFoundError(f"No pipeline found at {pipeline_path}")

    with open(pipeline_path, "rb") as f:
        pipeline = pickle.load(f)  # noqa: S301

    with open(features_path) as f:
        feature_names = json.load(f)

    with open(metadata_path) as f:
        metadata = json.load(f)

    model_name = metadata.get("model_name", "unknown")

    # Engineer features for all tickers
    enriched = engineer_features(data_dict)

    predictions: list[dict] = []
    today = date.today()
    predicted_date = today + timedelta(days=horizon)

    for ticker, df in enriched.items():
        if df.empty:
            continue

        # Get the latest row's features
        available = [c for c in feature_names if c in df.columns]
        if not available:
            logger.warning("Ticker %s: no matching features, skipping", ticker)
            continue

        latest = df[available].iloc[[-1]].values
        if np.any(np.isnan(latest)):
            # Fill NaN with 0 for prediction (feature warm-up edge case)
            latest = np.nan_to_num(latest, nan=0.0)

        try:
            pred_value = float(pipeline.predict(latest)[0])
        except Exception as exc:
            logger.warning("Ticker %s: prediction failed (%s)", ticker, exc)
            continue

        predictions.append({
            "ticker": ticker,
            "prediction_date": today.isoformat(),
            "predicted_date": predicted_date.isoformat(),
            "predicted_price": round(pred_value, 4),
            "model_name": model_name,
            "confidence": None,
        })

    logger.info(
        "Generated %d predictions using model %s", len(predictions), model_name,
    )
    return predictions


def save_predictions(
    predictions: list[dict],
    registry_dir: str = "model_registry",
    horizons: list[int] | None = None,
) -> Path:
    """Save predictions to ``{registry_dir}/predictions/latest.json``.

    When *horizons* is provided, also saves per-horizon files
    ``latest_{h}d.json`` and a combined ``latest.json``.
    """
    pred_dir = Path(registry_dir) / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)

    if horizons is not None:
        # Save per-horizon files
        for h in horizons:
            h_preds = [p for p in predictions if p.get("horizon_days") == h]
            h_path = pred_dir / f"latest_{h}d.json"
            with open(h_path, "w") as f:
                json.dump(h_preds, f, indent=2, default=str)
            logger.info("Saved %d predictions (horizon %dd) to %s", len(h_preds), h, h_path)

    # Always save combined latest.json for backward compat
    path = pred_dir / "latest.json"
    with open(path, "w") as f:
        json.dump(predictions, f, indent=2, default=str)
    logger.info("Saved %d predictions to %s", len(predictions), path)
    return path
