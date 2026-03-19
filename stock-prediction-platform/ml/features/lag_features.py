"""Lag feature generation — lagged close prices and rolling window statistics."""

from __future__ import annotations

import pandas as pd

# Default lag offsets for close price
DEFAULT_LAGS: list[int] = [1, 2, 3, 5, 7, 14, 21]

# Default rolling windows
DEFAULT_WINDOWS: list[int] = [5, 10, 21]


# ---------------------------------------------------------------------------
# FEAT-15: Lag Features
# ---------------------------------------------------------------------------


def compute_lag_features(
    df: pd.DataFrame, lags: list[int] | None = None
) -> pd.DataFrame:
    """Add lagged close-price columns (t-1, t-2, … t-21).

    Each lag column is named ``lag_close_{n}`` where *n* is the number of
    trading days shifted backward.  Uses :func:`pandas.Series.shift` so no
    future information can leak.
    """
    if lags is None:
        lags = DEFAULT_LAGS
    for n in lags:
        df[f"lag_close_{n}"] = df["close"].shift(n)
    return df


# ---------------------------------------------------------------------------
# FEAT-16: Rolling Window Stats
# ---------------------------------------------------------------------------


def compute_rolling_stats(
    df: pd.DataFrame, windows: list[int] | None = None
) -> pd.DataFrame:
    """Add rolling mean / std / min / max of close over multiple windows.

    Windows are trailing-only (``center=False``, the pandas default) to
    prevent look-ahead bias.
    """
    if windows is None:
        windows = DEFAULT_WINDOWS
    for w in windows:
        rolling = df["close"].rolling(w)
        df[f"rolling_mean_{w}"] = rolling.mean()
        df[f"rolling_std_{w}"] = rolling.std()
        df[f"rolling_min_{w}"] = rolling.min()
        df[f"rolling_max_{w}"] = rolling.max()
    return df


# ---------------------------------------------------------------------------
# FEAT-20: Target Label (percentage return)
# ---------------------------------------------------------------------------


def generate_target(df: pd.DataFrame, horizon: int = 7) -> pd.DataFrame:
    """Create a forward-looking percentage-return target column.

    ``target_{horizon}d = (close_{t+horizon} - close_t) / close_t``

    The last *horizon* rows will contain NaN because the future price is
    unknown.  The target is intentionally computed via a negative shift so
    that it can never leak into lag/rolling features (which use positive
    shifts only).
    """
    df[f"target_{horizon}d"] = df["close"].shift(-horizon) / df["close"] - 1
    return df


# ---------------------------------------------------------------------------
# FEAT-21: Drop Incomplete Rows
# ---------------------------------------------------------------------------


def drop_incomplete_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop every row that contains at least one NaN.

    This removes both the warm-up period at the start (from lags, rolling
    windows, and technical indicators) and the tail period (from the
    forward-shifted target).  Returns a copy so the caller's original
    DataFrame is unaffected.
    """
    return df.dropna().copy()
