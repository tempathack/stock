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

# ---------------------------------------------------------------------------
# Feast import — optional; gracefully degrade when feast is not installed
# ---------------------------------------------------------------------------
try:
    from ml.features.feast_store import get_historical_features as _feast_get_historical
    _FEAST_AVAILABLE = True
except ImportError:
    _FEAST_AVAILABLE = False
    _feast_get_historical = None  # type: ignore[assignment]

# Module-level alias used by tests to patch via
# `ml.pipelines.components.feature_engineer.get_historical_features`
get_historical_features = _feast_get_historical


def engineer_features(
    data: dict[str, pd.DataFrame],
    use_feature_store: bool = False,
    db_settings: "DBSettings | None" = None,
    use_feast: bool = False,
) -> dict[str, pd.DataFrame]:
    """Apply all technical indicators, lag features, and rolling stats per ticker.

    When *use_feature_store* is True and *db_settings* is provided, precomputed
    features are loaded from the feature_store table.  Tickers missing from the
    store fall back to on-the-fly computation.

    Pre-joined columns in *data* (e.g. FRED macro features: dgs2, dgs10, t10y2y, …,
    or yfinance macro: vix, spy_return, sector_return) are preserved automatically.
    The on-the-fly compute functions (compute_all_indicators, compute_lag_features,
    compute_rolling_stats) only *add* new named columns — they never drop or overwrite
    columns already present in the DataFrame.
    """
    if not data:
        return {}

    # ── Feast path (FEAST-06) ────────────────────────────────────────────────
    if use_feast and _FEAST_AVAILABLE and get_historical_features is not None:
        rows = []
        for ticker, df in data.items():
            for ts in df.index:
                rows.append({
                    "ticker": ticker,
                    "event_timestamp": pd.Timestamp(ts, tz="UTC"),
                })
        entity_df = pd.DataFrame(rows)
        try:
            feast_df = get_historical_features(entity_df)
            result: dict[str, pd.DataFrame] = {}
            for ticker in data.keys():
                t_df = feast_df[feast_df["ticker"] == ticker].set_index("event_timestamp")
                t_df.index.name = "date"
                result[ticker] = t_df.drop(columns=["ticker"], errors="ignore")
            return result
        except Exception as exc:
            logger.warning(
                "Feast get_historical_features failed (%s) — falling back to on-the-fly.", exc
            )
            # fall through to existing computation

    # ── Existing EAV feature store path (preserved) ─────────────────────────
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
