"""Tests for point-in-time correctness validation.

Covers:
  PIT-01 — assert_no_future_leakage() correctly detects temporal leakage in
            get_historical_features() results
  PIT-04 — BacktestResponse includes features_pit_correct field (forward gate
            verified in Plan 03 when the field is added to the schema)

Run: cd stock-prediction-platform/services/api && pytest tests/test_pit_correctness.py -x -q
"""
from __future__ import annotations

import sys
import os

import pandas as pd
import pytest

# Add ml package root to path for pit_validator import.
# Path from tests/ (services/api/tests/): ../../../ml
_ML_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../ml")
)
# Platform root (stock-prediction-platform/) for absolute package imports.
# Path from tests/ (services/api/tests/): ../../..
_PLATFORM_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
if _ML_ROOT not in sys.path:
    sys.path.insert(0, _ML_ROOT)
if _PLATFORM_ROOT not in sys.path:
    sys.path.insert(0, _PLATFORM_ROOT)


# ── build_entity_df_for_backtest tests ────────────────────────────────────────

def test_build_entity_df_correct_timestamps():
    """event_timestamp for 2024-06-01 should be 20:00 UTC (16:00 EDT = UTC-4)."""
    from feature_store.pit_validator import build_entity_df_for_backtest

    df = build_entity_df_for_backtest("AAPL", ["2024-06-01"])

    assert len(df) == 1
    assert df.iloc[0]["ticker"] == "AAPL"

    ts = df.iloc[0]["event_timestamp"]
    assert ts.tzinfo is not None, "event_timestamp must be timezone-aware"
    # Convert to UTC for hour assertion
    ts_utc = ts.tz_convert("UTC")
    assert ts_utc.date() == pd.Timestamp("2024-06-01").date()
    # June 1 is EDT (UTC-4), so 16:00 EDT = 20:00 UTC
    assert ts_utc.hour == 20


def test_build_entity_df_multiple_dates():
    """Multiple prediction_dates produce one row per date, all UTC-aware."""
    from feature_store.pit_validator import build_entity_df_for_backtest

    df = build_entity_df_for_backtest("MSFT", ["2024-01-15", "2024-01-16"])

    assert len(df) == 2
    assert list(df["ticker"]) == ["MSFT", "MSFT"]
    for ts in df["event_timestamp"]:
        assert ts.tzinfo is not None
    # January is EST (UTC-5), so 16:00 EST = 21:00 UTC
    ts_utc = df.iloc[0]["event_timestamp"].tz_convert("UTC")
    assert ts_utc.hour == 21


# ── assert_no_future_leakage tests ────────────────────────────────────────────

def test_pit_no_future_leakage():
    """No exception when all feature rows have timestamp <= event_timestamp."""
    from feature_store.pit_validator import assert_no_future_leakage

    event_ts = pd.Timestamp("2024-01-15 21:00:00", tz="UTC")
    entity_df = pd.DataFrame([{"ticker": "AAPL", "event_timestamp": event_ts}])

    # Feature rows all BEFORE the cutoff — correct
    result_df = pd.DataFrame([
        {"ticker": "AAPL", "timestamp": pd.Timestamp("2024-01-14", tz="UTC"), "close": 185.0},
        {"ticker": "AAPL", "timestamp": pd.Timestamp("2024-01-13", tz="UTC"), "close": 183.0},
    ])

    # Must not raise
    assert_no_future_leakage(result_df, entity_df)


def test_pit_future_row_fails():
    """AssertionError raised when a feature row has timestamp > event_timestamp."""
    from feature_store.pit_validator import assert_no_future_leakage

    event_ts = pd.Timestamp("2024-01-15 21:00:00", tz="UTC")
    entity_df = pd.DataFrame([{"ticker": "AAPL", "event_timestamp": event_ts}])

    # One row is AFTER the cutoff — leakage!
    result_df = pd.DataFrame([
        {"ticker": "AAPL", "timestamp": pd.Timestamp("2024-01-14", tz="UTC"), "close": 185.0},
        {"ticker": "AAPL", "timestamp": pd.Timestamp("2024-01-20", tz="UTC"), "close": 190.0},  # future
    ])

    with pytest.raises(AssertionError, match="PIT leakage detected"):
        assert_no_future_leakage(result_df, entity_df)


def test_pit_empty_result_passes():
    """Empty result_df (no data in offline store) passes without error."""
    from feature_store.pit_validator import assert_no_future_leakage

    event_ts = pd.Timestamp("2024-01-15 21:00:00", tz="UTC")
    entity_df = pd.DataFrame([{"ticker": "AAPL", "event_timestamp": event_ts}])
    result_df = pd.DataFrame()

    # Empty is valid — Feast returned no rows (no data before cutoff)
    assert_no_future_leakage(result_df, entity_df)


def test_pit_missing_timestamp_column_raises_value_error():
    """ValueError raised when result_df lacks 'timestamp' column."""
    from feature_store.pit_validator import assert_no_future_leakage

    event_ts = pd.Timestamp("2024-01-15 21:00:00", tz="UTC")
    entity_df = pd.DataFrame([{"ticker": "AAPL", "event_timestamp": event_ts}])
    result_df = pd.DataFrame([{"ticker": "AAPL", "close": 185.0}])  # no timestamp column

    with pytest.raises(ValueError, match="timestamp"):
        assert_no_future_leakage(result_df, entity_df)


def test_response_includes_pit_flag():
    """BacktestResponse schema includes features_pit_correct: bool field (PIT-04)."""
    from app.models.schemas import BacktestResponse

    fields = BacktestResponse.model_fields
    assert "features_pit_correct" in fields, (
        "BacktestResponse must have features_pit_correct field"
    )
    # Verify default is False (existing predictions are not PIT-correct)
    response = BacktestResponse(
        ticker="AAPL",
        model_name="Ridge",
        horizon=7,
        start_date="2024-01-01",
        end_date="2024-06-01",
        metrics={"rmse": 1.0, "mae": 0.8, "mape": 0.5, "directional_accuracy": 55.0, "r2": 0.3, "total_points": 10},
        series=[],
    )
    assert response.features_pit_correct is False
