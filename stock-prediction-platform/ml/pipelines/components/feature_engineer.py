"""Kubeflow component — computes technical indicators and features."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

from ml.features.indicators import compute_all_indicators
from ml.features.lag_features import compute_lag_features, compute_rolling_stats

if TYPE_CHECKING:
    from ml.pipelines.components.data_loader import DBSettings

logger = logging.getLogger(__name__)


def engineer_features(
    data: dict[str, pd.DataFrame],
    use_feature_store: bool = False,
    db_settings: "DBSettings | None" = None,
) -> dict[str, pd.DataFrame]:
    """Apply all technical indicators, lag features, and rolling stats per ticker.

    When *use_feature_store* is True and *db_settings* is provided, precomputed
    features are loaded from the feature_store table.  Tickers missing from the
    store fall back to on-the-fly computation.
    """
    if not data:
        return {}

    # Attempt to load from feature store
    store_data: dict[str, pd.DataFrame] = {}
    if use_feature_store and db_settings is not None:
        try:
            from ml.features.store import read_features

            store_data = read_features(list(data.keys()), db_settings)
        except Exception as exc:
            logger.warning("Feature store read failed (%s) — falling back to on-the-fly.", exc)

    result: dict[str, pd.DataFrame] = {}
    for ticker, df in data.items():
        if ticker in store_data and len(store_data[ticker].columns) > 0:
            result[ticker] = store_data[ticker]
            logger.info(
                "Ticker %s: loaded from feature store (%d columns).",
                ticker, len(store_data[ticker].columns),
            )
        else:
            enriched = compute_all_indicators(df.copy())
            enriched = compute_lag_features(enriched)
            enriched = compute_rolling_stats(enriched)
            result[ticker] = enriched
            logger.info(
                "Ticker %s: computed on-the-fly (%d columns, %d added).",
                ticker, len(enriched.columns), len(enriched.columns) - len(df.columns),
            )

    return result
