"""Technical indicator computation — RSI, MACD, Bollinger, etc."""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _true_range(df: pd.DataFrame) -> pd.Series:
    """True Range: max(H-L, |H-prevC|, |L-prevC|)."""
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)


# ---------------------------------------------------------------------------
# FEAT-01: RSI  (Momentum)
# ---------------------------------------------------------------------------


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Relative Strength Index using Wilder's smoothing."""
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    df[f"rsi_{period}"] = 100 - (100 / (1 + rs))
    return df


# ---------------------------------------------------------------------------
# FEAT-02: MACD  (Momentum)
# ---------------------------------------------------------------------------


def compute_macd(
    df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
) -> pd.DataFrame:
    """MACD line, signal line, and histogram."""
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd_line"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd_line"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd_line"] - df["macd_signal"]
    return df


# ---------------------------------------------------------------------------
# FEAT-03: Stochastic Oscillator  (Momentum)
# ---------------------------------------------------------------------------


def compute_stochastic(
    df: pd.DataFrame, k_period: int = 14, d_period: int = 3
) -> pd.DataFrame:
    """%K and %D of the Stochastic Oscillator."""
    lowest_low = df["low"].rolling(k_period).min()
    highest_high = df["high"].rolling(k_period).max()
    df["stoch_k"] = (df["close"] - lowest_low) / (highest_high - lowest_low) * 100
    df["stoch_d"] = df["stoch_k"].rolling(d_period).mean()
    return df


# ---------------------------------------------------------------------------
# FEAT-04: SMA  (Trend)
# ---------------------------------------------------------------------------


def compute_sma(
    df: pd.DataFrame, periods: list[int] | None = None
) -> pd.DataFrame:
    """Simple Moving Averages of close."""
    if periods is None:
        periods = [20, 50, 200]
    for p in periods:
        df[f"sma_{p}"] = df["close"].rolling(p).mean()
    return df


# ---------------------------------------------------------------------------
# FEAT-05: EMA  (Trend)
# ---------------------------------------------------------------------------


def compute_ema(
    df: pd.DataFrame, periods: list[int] | None = None
) -> pd.DataFrame:
    """Exponential Moving Averages of close."""
    if periods is None:
        periods = [12, 26]
    for p in periods:
        df[f"ema_{p}"] = df["close"].ewm(span=p, adjust=False).mean()
    return df


# ---------------------------------------------------------------------------
# FEAT-06: ADX  (Trend)
# ---------------------------------------------------------------------------


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Average Directional Index."""
    up_move = df["high"].diff()
    down_move = -df["low"].diff()

    plus_dm = pd.Series(0.0, index=df.index)
    minus_dm = pd.Series(0.0, index=df.index)

    plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
    minus_dm[(down_move > up_move) & (down_move > 0)] = down_move

    tr = _true_range(df)

    atr_smooth = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    plus_dm_smooth = plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    minus_dm_smooth = minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    plus_di = 100 * plus_dm_smooth / atr_smooth
    minus_di = 100 * minus_dm_smooth / atr_smooth

    dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
    df["adx"] = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return df


# ---------------------------------------------------------------------------
# FEAT-07: Bollinger Bands  (Volatility)
# ---------------------------------------------------------------------------


def compute_bollinger(
    df: pd.DataFrame, period: int = 20, std_dev: float = 2.0
) -> pd.DataFrame:
    """Bollinger Bands: upper, lower, bandwidth."""
    middle = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    df["bb_upper"] = middle + std_dev * std
    df["bb_lower"] = middle - std_dev * std
    df["bb_bandwidth"] = (df["bb_upper"] - df["bb_lower"]) / middle
    return df


# ---------------------------------------------------------------------------
# FEAT-08: ATR  (Volatility)
# ---------------------------------------------------------------------------


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Average True Range using Wilder's smoothing."""
    tr = _true_range(df)
    df["atr"] = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return df


# ---------------------------------------------------------------------------
# FEAT-09: Rolling Volatility  (Volatility)
# ---------------------------------------------------------------------------


def compute_rolling_volatility(df: pd.DataFrame, window: int = 21) -> pd.DataFrame:
    """Annualized rolling volatility of daily returns."""
    daily_returns = df["close"].pct_change()
    df[f"rolling_vol_{window}"] = daily_returns.rolling(window).std() * np.sqrt(252)
    return df


# ---------------------------------------------------------------------------
# FEAT-10: OBV  (Volume)
# ---------------------------------------------------------------------------


def compute_obv(df: pd.DataFrame) -> pd.DataFrame:
    """On-Balance Volume."""
    sign = np.sign(df["close"].diff())
    df["obv"] = (sign * df["volume"]).cumsum()
    return df


# ---------------------------------------------------------------------------
# FEAT-11: VWAP  (Volume)
# ---------------------------------------------------------------------------


def compute_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """Volume-Weighted Average Price (cumulative)."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    df["vwap"] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
    return df


# ---------------------------------------------------------------------------
# FEAT-12: Volume SMA  (Volume)
# ---------------------------------------------------------------------------


def compute_volume_sma(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Simple Moving Average of volume."""
    df[f"volume_sma_{period}"] = df["volume"].rolling(period).mean()
    return df


# ---------------------------------------------------------------------------
# FEAT-13: Accumulation/Distribution  (Volume)
# ---------------------------------------------------------------------------


def compute_ad_line(df: pd.DataFrame) -> pd.DataFrame:
    """Accumulation/Distribution Line."""
    clv = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (
        df["high"] - df["low"]
    )
    df["ad_line"] = (clv * df["volume"]).cumsum()
    return df


# ---------------------------------------------------------------------------
# FEAT-14: Returns  (Price Action)
# ---------------------------------------------------------------------------


def compute_returns(
    df: pd.DataFrame, periods: list[int] | None = None
) -> pd.DataFrame:
    """Percentage returns and log returns."""
    if periods is None:
        periods = [1, 5, 21]
    for p in periods:
        df[f"return_{p}d"] = df["close"].pct_change(p)
        df[f"log_return_{p}d"] = np.log(df["close"] / df["close"].shift(p))
    return df


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all 14 technical indicator families on an OHLCV DataFrame."""
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = df[col].astype(float)
    df = compute_rsi(df)
    df = compute_macd(df)
    df = compute_stochastic(df)
    df = compute_sma(df)
    df = compute_ema(df)
    df = compute_adx(df)
    df = compute_bollinger(df)
    df = compute_atr(df)
    df = compute_rolling_volatility(df)
    df = compute_obv(df)
    df = compute_vwap(df)
    df = compute_volume_sma(df)
    df = compute_ad_line(df)
    df = compute_returns(df)
    return df
