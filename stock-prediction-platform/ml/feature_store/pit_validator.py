"""Point-in-time correctness validation helpers for Feast feature retrieval.

Provides utilities to:
  1. Validate that get_historical_features() returns no feature rows with
     timestamps in the future relative to each entity's event_timestamp.
  2. Construct entity DataFrames for backtesting using market-close time as
     the PIT cutoff (16:00 America/New_York).

Usage::

    from ml.feature_store.pit_validator import (
        assert_no_future_leakage,
        build_entity_df_for_backtest,
    )

    entity_df = build_entity_df_for_backtest("AAPL", ["2024-01-15", "2024-01-16"])
    result_df = get_historical_features(entity_df)
    assert_no_future_leakage(result_df, entity_df)   # raises AssertionError on leakage
"""
from __future__ import annotations

import pandas as pd

# Market close time used as the PIT cutoff for all backtest entity timestamps.
# 16:00 Eastern = 21:00 UTC during EST (UTC-5). Using America/New_York handles
# DST transitions automatically.
_MARKET_CLOSE_TIME = "16:00:00"
_MARKET_TZ = "America/New_York"


def build_entity_df_for_backtest(
    ticker: str,
    prediction_dates: list[str],
) -> pd.DataFrame:
    """Construct a Feast entity DataFrame for point-in-time backtest queries.

    For each prediction_date, sets event_timestamp to market close time
    (16:00 America/New_York). This ensures that Feast's temporal join
    will only return features with timestamp <= market close on that date,
    preventing features from prediction_date+1 or later from leaking in.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        prediction_dates: List of ISO date strings (YYYY-MM-DD) representing
            the dates when predictions were made (NOT the predicted future date).

    Returns:
        DataFrame with columns: ``ticker`` (str), ``event_timestamp`` (timezone-aware).

    Example::
        entity_df = build_entity_df_for_backtest("AAPL", ["2024-01-15"])
        # entity_df["event_timestamp"][0] == Timestamp("2024-01-15 21:00:00+00:00")
    """
    rows = []
    for date_str in prediction_dates:
        rows.append({
            "ticker": ticker,
            "event_timestamp": pd.Timestamp(
                f"{date_str} {_MARKET_CLOSE_TIME}", tz=_MARKET_TZ
            ).tz_convert("UTC"),
        })
    return pd.DataFrame(rows)


def assert_no_future_leakage(
    result_df: pd.DataFrame,
    entity_df: pd.DataFrame,
) -> None:
    """Assert that Feast historical features contain no future-timestamped rows.

    For each (ticker, event_timestamp) row in entity_df, checks that all
    corresponding rows in result_df have a ``timestamp`` column value that
    is <= the entity's event_timestamp. This validates that Feast's point-in-time
    join guarantee was respected and no look-ahead leakage occurred.

    Args:
        result_df: DataFrame returned by get_historical_features(entity_df).
            Must have columns: ``ticker``, ``timestamp`` (timezone-aware).
        entity_df: Entity DataFrame used for the Feast query.
            Must have columns: ``ticker``, ``event_timestamp`` (timezone-aware).

    Raises:
        AssertionError: If any row in result_df has timestamp > event_timestamp
            for its entity. The message includes the leaking row details.
        ValueError: If result_df is missing the ``timestamp`` column.
    """
    if result_df.empty:
        # Empty result is valid — no data in the offline store for this entity
        return

    if "timestamp" not in result_df.columns:
        raise ValueError(
            "result_df must have a 'timestamp' column to validate PIT correctness. "
            f"Got columns: {list(result_df.columns)}"
        )

    for _, entity_row in entity_df.iterrows():
        ticker = entity_row["ticker"]
        cutoff = entity_row["event_timestamp"]

        # Normalise cutoff timezone to UTC for comparison
        if hasattr(cutoff, "tzinfo") and cutoff.tzinfo is not None:
            cutoff_utc = cutoff.tz_convert("UTC")
        else:
            cutoff_utc = pd.Timestamp(cutoff, tz="UTC")

        ticker_rows = result_df[result_df["ticker"] == ticker]

        for _, feat_row in ticker_rows.iterrows():
            feat_ts = feat_row["timestamp"]
            if hasattr(feat_ts, "tzinfo") and feat_ts.tzinfo is not None:
                feat_ts_utc = feat_ts.tz_convert("UTC")
            else:
                feat_ts_utc = pd.Timestamp(feat_ts, tz="UTC")

            assert feat_ts_utc <= cutoff_utc, (
                f"PIT leakage detected for ticker={ticker!r}: "
                f"feature timestamp {feat_ts_utc} > event_timestamp {cutoff_utc}. "
                "This means a future feature value was used in training/backtest."
            )
