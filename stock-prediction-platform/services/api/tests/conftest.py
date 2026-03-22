"""Shared pytest fixtures for Phase 6+ tests."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so `ml.*` imports work from services/api/
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock


@pytest.fixture
def mock_intraday_df():
    """Valid intraday DataFrame with tz-aware US/Eastern index (3 rows)."""
    idx = pd.DatetimeIndex([
        pd.Timestamp("2026-03-19 09:30:00", tz="US/Eastern"),
        pd.Timestamp("2026-03-19 09:31:00", tz="US/Eastern"),
        pd.Timestamp("2026-03-19 09:32:00", tz="US/Eastern"),
    ])
    return pd.DataFrame({
        "Open": [170.0, 170.5, 171.0],
        "High": [171.0, 171.5, 172.0],
        "Low": [169.5, 170.0, 170.5],
        "Close": [170.8, 171.2, 171.5],
        "Volume": [10000, 15000, 12000],
    }, index=idx)


@pytest.fixture
def mock_historical_df():
    """Valid historical DataFrame with tz-naive date index (3 rows)."""
    idx = pd.DatetimeIndex([
        pd.Timestamp("2026-03-17"),
        pd.Timestamp("2026-03-18"),
        pd.Timestamp("2026-03-19"),
    ])
    return pd.DataFrame({
        "Open": [168.0, 169.0, 170.0],
        "High": [169.5, 170.5, 171.0],
        "Low": [167.5, 168.5, 169.5],
        "Close": [169.0, 170.0, 170.8],
        "Volume": [5000000, 6000000, 5500000],
    }, index=idx)


@pytest.fixture
def mock_df_with_nan_ohlc():
    """DataFrame with NaN in Open column (should be rejected)."""
    idx = pd.DatetimeIndex([pd.Timestamp("2026-03-19")])
    return pd.DataFrame({
        "Open": [np.nan],
        "High": [171.0],
        "Low": [169.5],
        "Close": [170.8],
        "Volume": [10000],
    }, index=idx)


@pytest.fixture
def mock_df_with_negative_volume():
    """DataFrame with negative volume (should be rejected)."""
    idx = pd.DatetimeIndex([pd.Timestamp("2026-03-19")])
    return pd.DataFrame({
        "Open": [170.0],
        "High": [171.0],
        "Low": [169.5],
        "Close": [170.8],
        "Volume": [-100],
    }, index=idx)


@pytest.fixture
def mock_df_with_high_lt_low():
    """DataFrame where High < Low (should be rejected)."""
    idx = pd.DatetimeIndex([pd.Timestamp("2026-03-19")])
    return pd.DataFrame({
        "Open": [170.0],
        "High": [168.0],
        "Low": [169.5],
        "Close": [170.8],
        "Volume": [10000],
    }, index=idx)


@pytest.fixture
def mock_df_with_zero_volume():
    """DataFrame with Volume=0 (should PASS validation)."""
    idx = pd.DatetimeIndex([pd.Timestamp("2026-03-19")])
    return pd.DataFrame({
        "Open": [170.0],
        "High": [171.0],
        "Low": [169.5],
        "Close": [170.8],
        "Volume": [0],
    }, index=idx)


@pytest.fixture
def mock_df_with_nan_volume():
    """DataFrame with NaN volume (should be rejected)."""
    idx = pd.DatetimeIndex([pd.Timestamp("2026-03-19")])
    return pd.DataFrame({
        "Open": [170.0],
        "High": [171.0],
        "Low": [169.5],
        "Close": [170.8],
        "Volume": [np.nan],
    }, index=idx)


@pytest.fixture
def mock_empty_df():
    """Empty DataFrame (ticker not found or rate-limited)."""
    return pd.DataFrame()


@pytest.fixture
def mock_kafka_producer():
    """Mock confluent_kafka.Producer with produce() and flush()."""
    producer = MagicMock()
    producer.produce = MagicMock()
    producer.flush = MagicMock()
    return producer
