"""Kubeflow component — computes technical indicators and features."""

from __future__ import annotations

import logging

import pandas as pd

from ml.features.indicators import compute_all_indicators
from ml.features.lag_features import compute_lag_features, compute_rolling_stats

logger = logging.getLogger(__name__)


def engineer_features(
    data: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Apply all technical indicators, lag features, and rolling stats per ticker.

    Each ticker's DataFrame is processed independently to prevent cross-ticker
    contamination in cumulative/rolling calculations.
    """
    if not data:
        return {}

    result: dict[str, pd.DataFrame] = {}
    for ticker, df in data.items():
        enriched = compute_all_indicators(df.copy())
        enriched = compute_lag_features(enriched)
        enriched = compute_rolling_stats(enriched)
        result[ticker] = enriched
        logger.info(
            "Ticker %s: %d columns (%d added).",
            ticker, len(enriched.columns), len(enriched.columns) - len(df.columns),
        )

    return result
