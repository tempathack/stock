"""Shared fixtures for ml module tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """Return a deterministic synthetic OHLCV DataFrame with 250 rows.

    Simulates daily business-day data starting 2024-01-02 with a random-walk
    close price around 170 and realistic open/high/low/volume.
    """
    rng = np.random.default_rng(42)
    n = 250

    dates = pd.bdate_range(start="2024-01-02", periods=n, freq="B")

    # Random-walk close prices starting near 170
    returns = rng.normal(loc=0.0003, scale=0.015, size=n)
    close = 170.0 * np.cumprod(1 + returns)

    # Intraday spread around close
    spread = rng.uniform(0.002, 0.012, size=n)
    high = close * (1 + spread)
    low = close * (1 - spread)

    # Open near previous close with small gap
    open_ = np.empty(n)
    open_[0] = close[0] * (1 + rng.normal(0, 0.003))
    for i in range(1, n):
        open_[i] = close[i - 1] * (1 + rng.normal(0, 0.003))

    # Ensure high >= open and low <= open
    high = np.maximum(high, open_)
    low = np.minimum(low, open_)

    volume = rng.integers(1_000_000, 10_000_000, size=n)

    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=dates,
    )
