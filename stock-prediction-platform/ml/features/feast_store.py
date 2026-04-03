"""Feast wrapper module — historical and online feature retrieval.

Provides:
    get_store()                 -- constructs FeatureStore pointing at feature_store.yaml
    get_historical_features()   -- point-in-time correct DataFrame for training
    get_online_features()       -- sub-millisecond dict for inference (from Redis)

Usage::

    from ml.features.feast_store import get_historical_features, get_online_features

    # Training
    training_df = get_historical_features(entity_df)

    # Inference
    features = get_online_features("AAPL")
"""
from __future__ import annotations

import os

import pandas as pd
from feast import FeatureStore

FEAST_REPO_PATH = os.environ.get(
    "FEAST_REPO_PATH",
    os.path.join(os.path.dirname(__file__), "..", "feature_store"),
)

# All training features spanning the three FeatureViews
_TRAINING_FEATURES: list[str] = [
    "ohlcv_stats_fv:open",
    "ohlcv_stats_fv:high",
    "ohlcv_stats_fv:low",
    "ohlcv_stats_fv:close",
    "ohlcv_stats_fv:volume",
    "ohlcv_stats_fv:daily_return",
    "ohlcv_stats_fv:vwap",
    "technical_indicators_fv:rsi_14",
    "technical_indicators_fv:macd_line",
    "technical_indicators_fv:macd_signal",
    "technical_indicators_fv:bb_upper",
    "technical_indicators_fv:bb_lower",
    "technical_indicators_fv:atr_14",
    "technical_indicators_fv:adx_14",
    "technical_indicators_fv:ema_20",
    "technical_indicators_fv:obv",
    "lag_features_fv:lag_1",
    "lag_features_fv:lag_2",
    "lag_features_fv:lag_3",
    "lag_features_fv:lag_5",
    "lag_features_fv:lag_7",
    "lag_features_fv:lag_10",
    "lag_features_fv:lag_14",
    "lag_features_fv:lag_21",
    "lag_features_fv:rolling_mean_5",
    "lag_features_fv:rolling_mean_10",
    "lag_features_fv:rolling_mean_21",
    "lag_features_fv:rolling_std_5",
    "lag_features_fv:rolling_std_10",
    "lag_features_fv:rolling_std_21",
    "reddit_sentiment_fv:avg_sentiment",
    "reddit_sentiment_fv:mention_count",
    "reddit_sentiment_fv:positive_ratio",
    "reddit_sentiment_fv:negative_ratio",
]

# Key features for real-time inference from Redis
_ONLINE_FEATURES: list[str] = [
    "ohlcv_stats_fv:close",
    "ohlcv_stats_fv:daily_return",
    "technical_indicators_fv:rsi_14",
    "technical_indicators_fv:macd_line",
    "lag_features_fv:lag_1",
    "lag_features_fv:rolling_mean_5",
]


def get_store() -> FeatureStore:
    """Construct and return a FeatureStore pointed at the feature_store.yaml repo.

    The repo path defaults to ml/feature_store/ resolved relative to this file,
    or is overridden by the FEAST_REPO_PATH environment variable.
    """
    return FeatureStore(repo_path=FEAST_REPO_PATH)


def get_historical_features(entity_df: pd.DataFrame) -> pd.DataFrame:
    """Point-in-time correct feature retrieval for model training.

    Performs a temporal join: for each (ticker, event_timestamp) row in entity_df,
    returns the most recent feature values where feature.timestamp <= event_timestamp
    and within the FeatureView TTL window (365 days).

    Args:
        entity_df: DataFrame with columns ``ticker`` (str) and
            ``event_timestamp`` (timezone-aware UTC datetime).

    Returns:
        Wide-format DataFrame with entity columns plus all training feature columns.
    """
    store = get_store()
    return store.get_historical_features(
        entity_df=entity_df,
        features=_TRAINING_FEATURES,
    ).to_df()


def get_online_features(ticker: str) -> dict:
    """Sub-millisecond feature retrieval from Redis for real-time inference.

    Reads the latest materialized features for the given ticker from the Redis
    online store. Returns all features in _ONLINE_FEATURES.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").

    Returns:
        dict with feature keys in the format ``{view_name}__{field_name}``.
        Example: {"ohlcv_stats_fv__close": [182.5], "lag_features_fv__lag_1": [0.012]}
    """
    store = get_store()
    return store.get_online_features(
        features=_ONLINE_FEATURES,
        entity_rows=[{"ticker": ticker}],
    ).to_dict()
