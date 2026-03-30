"""Pure Python helper functions for Indicator Stream UDAF logic.

These functions are imported by indicator_stream.py (PyFlink job) and by
unit tests. They have no pyflink dependency, so tests can run without a
Flink runtime installed.

All computations use Wilder's smoothing (EWM alpha=1/period) consistent
with ml/features/indicators.py from Phase 10.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd


def compute_rsi(prices: list[float]) -> Optional[float]:
    """Compute RSI-14 using Wilder's smoothing (EWM alpha=1/14).

    Mirrors the Phase 10 ml/features/indicators.py implementation.

    Args:
        prices: List of close prices. At least 14 required.

    Returns:
        RSI value in [0, 100], or None if insufficient data.
    """
    if len(prices) < 14:
        return None

    series = pd.Series(prices, dtype=float)
    delta = series.diff()

    gains = delta.clip(lower=0.0)
    losses = (-delta).clip(lower=0.0)

    # Wilder's smoothing: EWM with alpha = 1/14, adjust=False
    avg_gain = gains.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / 14, adjust=False).mean()

    last_gain = avg_gain.iloc[-1]
    last_loss = avg_loss.iloc[-1]

    if last_loss == 0.0:
        return 100.0

    rs = last_gain / last_loss
    return float(100.0 - 100.0 / (1.0 + rs))


def compute_ema(prices: list[float], span: int = 20) -> Optional[float]:
    """Compute EMA using pandas EWM with span parameter.

    Args:
        prices: List of close prices. At least `span` prices required.
        span: EMA span (default 20 for EMA-20).

    Returns:
        Last EMA value as float, or None if insufficient data.
    """
    if len(prices) < span:
        return None

    series = pd.Series(prices, dtype=float)
    ema_series = series.ewm(span=span, adjust=False).mean()
    return float(ema_series.iloc[-1])


def compute_macd_signal(prices: list[float]) -> Optional[float]:
    """Compute MACD signal line (EMA-9 of MACD line).

    MACD line = EMA-12 - EMA-26 (full series).
    Signal = EMA-9 of the MACD line series.

    Requires at least 35 prices (26 for EMA-26 + 9 for signal EMA).

    Args:
        prices: List of close prices.

    Returns:
        Last MACD signal value as float, or None if insufficient data.
    """
    if len(prices) < 35:
        return None

    series = pd.Series(prices, dtype=float)

    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()

    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()

    return float(signal.iloc[-1])
