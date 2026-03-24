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


def generate_multi_horizon_labels(
    data: dict[str, pd.DataFrame],
    horizons: list[int] | None = None,
) -> dict:
    """Create forward-return targets for multiple horizons simultaneously.

    For each horizon *h*, adds a ``target_{h}d`` column.  Incomplete rows
    (NaN in **any** target) are dropped once after all targets are generated.

    Returns a dict with keys:
    - ``"data"``: ``dict[str, pd.DataFrame]``
    - ``"feature_names"``: ``list[str]``
    - ``"target_cols"``: ``list[str]`` sorted by horizon
    """
    if horizons is None:
        horizons = [1, 7, 30]

    target_cols = sorted([f"target_{h}d" for h in horizons], key=lambda c: int(c.split("_")[1].rstrip("d")))

    if not data:
        return {"data": {}, "feature_names": [], "target_cols": target_cols}

    result: dict[str, pd.DataFrame] = {}
    for ticker, df in data.items():
        labelled = df.copy()
        for h in horizons:
            labelled = generate_target(labelled, horizon=h)
        labelled = drop_incomplete_rows(labelled)
        if labelled.empty:
            logger.warning("Ticker %s has 0 rows after multi-horizon cleanup — skipping.", ticker)
            continue
        result[ticker] = labelled
        logger.info("Ticker %s: %d rows after multi-horizon cleanup.", ticker, len(labelled))

    # Extract feature names excluding ALL target columns
    feature_names: list[str] = []
    for df in result.values():
        feature_names = [col for col in df.columns if col not in target_cols]
        break

    logger.info(
        "Multi-horizon labels: %d tickers, horizons=%s, %d features",
        len(result), horizons, len(feature_names),
    )
    return {"data": result, "feature_names": feature_names, "target_cols": target_cols}
