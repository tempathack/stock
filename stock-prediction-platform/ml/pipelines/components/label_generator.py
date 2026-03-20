"""Kubeflow component — generates t+7 target labels with no leakage."""

from __future__ import annotations

import logging

import pandas as pd

from ml.features.lag_features import drop_incomplete_rows, generate_target

logger = logging.getLogger(__name__)


def generate_labels(
    data: dict[str, pd.DataFrame],
    horizon: int = 7,
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Create forward-return target and drop NaN rows for each ticker.

    Returns a ``(data_dict, feature_names)`` tuple.  Tickers whose DataFrames
    become empty after dropping incomplete rows are omitted with a warning.
    """
    if not data:
        return {}, []

    result: dict[str, pd.DataFrame] = {}
    for ticker, df in data.items():
        labelled = generate_target(df.copy(), horizon=horizon)
        labelled = drop_incomplete_rows(labelled)
        if labelled.empty:
            logger.warning("Ticker %s has 0 rows after cleanup — skipping.", ticker)
            continue
        result[ticker] = labelled
        logger.info("Ticker %s: %d rows after cleanup.", ticker, len(labelled))

    # Extract feature names from the first available DataFrame
    feature_names: list[str] = []
    target_col = f"target_{horizon}d"
    for df in result.values():
        feature_names = [col for col in df.columns if col != target_col]
        break

    return result, feature_names
