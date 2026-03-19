# Phase 10: Technical Indicators - Research

**Researched:** 2026-03-19
**Domain:** Technical analysis indicator computation with pandas
**Confidence:** HIGH

## Summary

Phase 10 implements 14 technical indicator families as pure pandas functions in `ml/features/indicators.py`. All indicators are well-known, standardized formulas computed on daily OHLCV data. Implementation uses only pandas and numpy — no external TA library dependencies.

The module provides individual `compute_*` functions plus a `compute_all_indicators()` orchestrator. Each function accepts and returns a `pd.DataFrame`, appending new columns. This pattern enables easy testing, composability, and integration with the Kubeflow pipeline.

**Primary recommendation:** Hand-rolled pandas implementation with clear separation by indicator category (momentum, trend, volatility, volume, price action). Each function is stateless and idempotent.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Library:** Hand-rolled pandas/numpy — no pandas-ta, no TA-Lib
- **Input format:** Single-ticker DataFrame with `open, high, low, close, volume` columns, DatetimeIndex
- **Output format:** Same DataFrame with indicator columns appended
- **NaN policy:** Do NOT drop NaN rows; warm-up period NaNs propagate naturally
- **Price column:** Use `close` (not `adj_close` which is NULL in DB)
- **Persistence:** None — compute on-the-fly, no feature store table
- **Column naming:** `rsi_14`, `macd_line`, `sma_20`, etc. (see CONTEXT.md for full list)

### Claude's Discretion
- Exact smoothing method for RSI (Wilder's recommended)
- Internal helpers for shared computations (true_range, etc.)
- Test data generation approach
- Input validation in `compute_all_indicators`

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Indicator | Category |
|----|-------------|-----------|----------|
| FEAT-01 | RSI (14-period) | RSI | Momentum |
| FEAT-02 | MACD (12/26/9) | MACD line, signal, histogram | Momentum |
| FEAT-03 | Stochastic Oscillator | %K, %D | Momentum |
| FEAT-04 | SMA (20, 50, 200) | Simple Moving Average | Trend |
| FEAT-05 | EMA (12, 26) | Exponential Moving Average | Trend |
| FEAT-06 | ADX | Average Directional Index | Trend |
| FEAT-07 | Bollinger Bands (20, 2σ) | Upper, lower, bandwidth | Volatility |
| FEAT-08 | ATR | Average True Range | Volatility |
| FEAT-09 | Rolling Volatility (21d) | Annualized rolling std | Volatility |
| FEAT-10 | OBV | On-Balance Volume | Volume |
| FEAT-11 | VWAP | Volume-Weighted Avg Price | Volume |
| FEAT-12 | Volume SMA | Moving avg of volume | Volume |
| FEAT-13 | Accumulation/Distribution | A/D Line | Volume |
| FEAT-14 | Returns (1d, 5d, 21d + log) | Pct change, log returns | Price Action |

</phase_requirements>

## Standard Stack

### Core (already in project)
| Library | Version | Purpose |
|---------|---------|---------|
| pandas | 2.x | DataFrame operations, rolling/ewm |
| numpy | 1.x | Math operations, log, sign |

### Test
| Library | Version | Purpose |
|---------|---------|---------|
| pytest | 8.x | Test framework (already installed) |

No new dependencies required.

## Architecture Patterns

### Pattern 1: Individual Indicator Function
```python
def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    df[f"rsi_{period}"] = 100 - (100 / (1 + rs))
    return df
```

### Pattern 2: Multi-Output Indicator
```python
def compute_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd_line"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd_line"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd_line"] - df["macd_signal"]
    return df
```

### Pattern 3: Shared Helper (True Range)
```python
def _true_range(df: pd.DataFrame) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift(1)).abs()
    low_close = (df["low"] - df["close"].shift(1)).abs()
    return pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
```
Used by both ATR (FEAT-08) and ADX (FEAT-06).

### Pattern 4: Orchestrator
```python
def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = compute_rsi(df)
    df = compute_macd(df)
    df = compute_stochastic(df)
    # ...all 14 categories...
    df = compute_returns(df)
    return df
```

## Indicator Formulas Reference

### Momentum
- **RSI**: Wilder's smoothing (EWM with α=1/period). RS = avg_gain / avg_loss. RSI = 100 - 100/(1+RS)
- **MACD**: MACD_line = EMA(close, 12) - EMA(close, 26). Signal = EMA(MACD_line, 9). Hist = line - signal
- **Stochastic**: %K = (close - lowest_low(K)) / (highest_high(K) - lowest_low(K)) × 100. %D = SMA(%K, D)

### Trend
- **SMA**: Simple rolling mean of close
- **EMA**: Exponential weighted mean of close (span=period)
- **ADX**: +DI = 100 × EWM(+DM) / ATR. -DI = 100 × EWM(-DM) / ATR. DX = |+DI - -DI| / (+DI + -DI) × 100. ADX = EWM(DX)

### Volatility
- **Bollinger**: Middle = SMA(close, 20). Upper = middle + 2σ. Lower = middle - 2σ. Bandwidth = (upper - lower) / middle
- **ATR**: EWM(true_range, period). True range = max(H-L, |H-prev_C|, |L-prev_C|)
- **Rolling Vol**: std(daily_returns, 21) × √252 for annualization

### Volume
- **OBV**: Cumulative sum of {+volume if close > prev_close, -volume if close < prev_close, 0 if equal}
- **VWAP**: cumsum(typical_price × volume) / cumsum(volume). Typical = (H + L + C) / 3
- **Volume SMA**: SMA(volume, 20)
- **A/D**: CLV = ((C-L) - (H-C)) / (H-L). A/D = cumsum(CLV × volume)

### Price Action
- **Returns**: pct_change(period) for 1d, 5d, 21d
- **Log returns**: log(close / close.shift(period)) for 1d, 5d, 21d
