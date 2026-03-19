"""Tests for ml.features.indicators — all 14 technical indicator families."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.features.indicators import (
    compute_ad_line,
    compute_adx,
    compute_all_indicators,
    compute_atr,
    compute_bollinger,
    compute_ema,
    compute_macd,
    compute_obv,
    compute_returns,
    compute_rolling_volatility,
    compute_rsi,
    compute_sma,
    compute_stochastic,
    compute_volume_sma,
    compute_vwap,
)

# ---------------------------------------------------------------------------
# FEAT-01: RSI
# ---------------------------------------------------------------------------


class TestRSI:
    def test_rsi_adds_column(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rsi(sample_ohlcv_df.copy())
        assert "rsi_14" in result.columns

    def test_rsi_values_bounded(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rsi(sample_ohlcv_df.copy())
        valid = result["rsi_14"].dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_rsi_warm_up_nans(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rsi(sample_ohlcv_df.copy())
        # First 13 rows (index 0-12) should be NaN for period=14
        assert result["rsi_14"].iloc[:13].isna().all()

    def test_rsi_custom_period(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rsi(sample_ohlcv_df.copy(), period=7)
        assert "rsi_7" in result.columns
        assert result["rsi_7"].iloc[:6].isna().all()
        valid = result["rsi_7"].dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_rsi_returns_dataframe(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rsi(sample_ohlcv_df.copy())
        assert isinstance(result, pd.DataFrame)
        for col in ("open", "high", "low", "close", "volume"):
            assert col in result.columns


# ---------------------------------------------------------------------------
# FEAT-02: MACD
# ---------------------------------------------------------------------------


class TestMACD:
    def test_macd_adds_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_macd(sample_ohlcv_df.copy())
        for col in ("macd_line", "macd_signal", "macd_hist"):
            assert col in result.columns

    def test_macd_histogram_equals_diff(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_macd(sample_ohlcv_df.copy())
        valid_idx = result["macd_hist"].dropna().index
        diff = result.loc[valid_idx, "macd_line"] - result.loc[valid_idx, "macd_signal"]
        pd.testing.assert_series_equal(
            result.loc[valid_idx, "macd_hist"], diff, check_names=False, atol=1e-10
        )

    def test_macd_line_is_ema_diff(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        expected = ema12 - ema26
        result = compute_macd(df)
        pd.testing.assert_series_equal(
            result["macd_line"], expected, check_names=False, atol=1e-10
        )

    def test_macd_preserves_original_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_macd(sample_ohlcv_df.copy())
        for col in ("open", "high", "low", "close", "volume"):
            assert col in result.columns

    def test_macd_custom_params(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_macd(sample_ohlcv_df.copy(), fast=8, slow=21, signal=5)
        for col in ("macd_line", "macd_signal", "macd_hist"):
            assert col in result.columns


# ---------------------------------------------------------------------------
# FEAT-03: Stochastic Oscillator
# ---------------------------------------------------------------------------


class TestStochastic:
    def test_stochastic_adds_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_stochastic(sample_ohlcv_df.copy())
        assert "stoch_k" in result.columns
        assert "stoch_d" in result.columns

    def test_stochastic_k_bounded(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_stochastic(sample_ohlcv_df.copy())
        valid = result["stoch_k"].dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_stochastic_d_is_sma_of_k(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_stochastic(sample_ohlcv_df.copy())
        expected_d = result["stoch_k"].rolling(3).mean()
        valid_idx = result["stoch_d"].dropna().index
        pd.testing.assert_series_equal(
            result.loc[valid_idx, "stoch_d"],
            expected_d.loc[valid_idx],
            check_names=False,
            atol=1e-10,
        )

    def test_stochastic_custom_params(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_stochastic(sample_ohlcv_df.copy(), k_period=5, d_period=3)
        assert "stoch_k" in result.columns
        assert "stoch_d" in result.columns


# ---------------------------------------------------------------------------
# FEAT-04: SMA
# ---------------------------------------------------------------------------


class TestSMA:
    def test_sma_adds_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_sma(sample_ohlcv_df.copy())
        for p in (20, 50, 200):
            assert f"sma_{p}" in result.columns

    def test_sma_20_is_rolling_mean(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        expected = df["close"].rolling(20).mean()
        result = compute_sma(df)
        pd.testing.assert_series_equal(
            result["sma_20"], expected, check_names=False, atol=1e-10
        )

    def test_sma_warm_up_nans(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_sma(sample_ohlcv_df.copy())
        assert result["sma_200"].iloc[:199].isna().all()

    def test_sma_custom_periods(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_sma(sample_ohlcv_df.copy(), periods=[10, 30])
        assert "sma_10" in result.columns
        assert "sma_30" in result.columns


# ---------------------------------------------------------------------------
# FEAT-05: EMA
# ---------------------------------------------------------------------------


class TestEMA:
    def test_ema_adds_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_ema(sample_ohlcv_df.copy())
        assert "ema_12" in result.columns
        assert "ema_26" in result.columns

    def test_ema_responds_faster_than_sma(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        result = compute_ema(compute_sma(df, periods=[12]))
        ema_diff = (result["ema_12"] - result["close"]).abs()
        sma_diff = (result["sma_12"] - result["close"]).abs()
        # EMA should track close prices more closely on average
        assert ema_diff.dropna().mean() < sma_diff.dropna().mean()

    def test_ema_custom_periods(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_ema(sample_ohlcv_df.copy(), periods=[5, 10])
        assert "ema_5" in result.columns
        assert "ema_10" in result.columns


# ---------------------------------------------------------------------------
# FEAT-06: ADX
# ---------------------------------------------------------------------------


class TestADX:
    def test_adx_adds_column(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_adx(sample_ohlcv_df.copy())
        assert "adx" in result.columns

    def test_adx_values_non_negative(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_adx(sample_ohlcv_df.copy())
        valid = result["adx"].dropna()
        assert (valid >= 0).all()

    def test_adx_has_warm_up_nans(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_adx(sample_ohlcv_df.copy())
        # ADX needs warm-up: at least first row is NaN due to diff/shift
        assert result["adx"].iloc[0] != result["adx"].iloc[0]  # NaN check

    def test_adx_returns_dataframe(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_adx(sample_ohlcv_df.copy())
        assert isinstance(result, pd.DataFrame)
        for col in ("open", "high", "low", "close", "volume"):
            assert col in result.columns


# ---------------------------------------------------------------------------
# FEAT-07: Bollinger Bands
# ---------------------------------------------------------------------------


class TestBollinger:
    def test_bollinger_adds_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_bollinger(sample_ohlcv_df.copy())
        for col in ("bb_upper", "bb_lower", "bb_bandwidth"):
            assert col in result.columns

    def test_bollinger_upper_greater_than_lower(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_bollinger(sample_ohlcv_df.copy())
        valid_idx = result["bb_upper"].dropna().index
        assert (result.loc[valid_idx, "bb_upper"] > result.loc[valid_idx, "bb_lower"]).all()

    def test_bollinger_bandwidth_positive(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_bollinger(sample_ohlcv_df.copy())
        valid = result["bb_bandwidth"].dropna()
        assert (valid > 0).all()

    def test_bollinger_upper_equals_formula(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        middle = df["close"].rolling(20).mean()
        std = df["close"].rolling(20).std()
        expected_upper = middle + 2 * std
        result = compute_bollinger(df)
        valid_idx = result["bb_upper"].dropna().index
        pd.testing.assert_series_equal(
            result.loc[valid_idx, "bb_upper"],
            expected_upper.loc[valid_idx],
            check_names=False,
            atol=1e-10,
        )

    def test_bollinger_custom_params(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_bollinger(sample_ohlcv_df.copy(), period=10, std_dev=1.5)
        for col in ("bb_upper", "bb_lower", "bb_bandwidth"):
            assert col in result.columns


# ---------------------------------------------------------------------------
# FEAT-08: ATR
# ---------------------------------------------------------------------------


class TestATR:
    def test_atr_adds_column(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_atr(sample_ohlcv_df.copy())
        assert "atr" in result.columns

    def test_atr_values_non_negative(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_atr(sample_ohlcv_df.copy())
        valid = result["atr"].dropna()
        assert (valid >= 0).all()

    def test_atr_has_warm_up_nans(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_atr(sample_ohlcv_df.copy())
        # ATR with period=14 needs warm-up
        assert result["atr"].iloc[:1].isna().all()

    def test_atr_custom_period(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_atr(sample_ohlcv_df.copy(), period=7)
        assert "atr" in result.columns
        valid = result["atr"].dropna()
        assert (valid >= 0).all()


# ---------------------------------------------------------------------------
# FEAT-09: Rolling Volatility
# ---------------------------------------------------------------------------


class TestRollingVolatility:
    def test_rolling_vol_adds_column(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rolling_volatility(sample_ohlcv_df.copy())
        assert "rolling_vol_21" in result.columns

    def test_rolling_vol_positive(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rolling_volatility(sample_ohlcv_df.copy())
        valid = result["rolling_vol_21"].dropna()
        assert (valid > 0).all()

    def test_rolling_vol_custom_window(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rolling_volatility(sample_ohlcv_df.copy(), window=10)
        assert "rolling_vol_10" in result.columns

    def test_rolling_vol_annualized(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        daily_ret = df["close"].pct_change()
        raw_std = daily_ret.rolling(21).std()
        expected = raw_std * np.sqrt(252)
        result = compute_rolling_volatility(df)
        valid_idx = result["rolling_vol_21"].dropna().index
        pd.testing.assert_series_equal(
            result.loc[valid_idx, "rolling_vol_21"],
            expected.loc[valid_idx],
            check_names=False,
            atol=1e-10,
        )


# ---------------------------------------------------------------------------
# FEAT-10: OBV
# ---------------------------------------------------------------------------


class TestOBV:
    def test_obv_adds_column(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_obv(sample_ohlcv_df.copy())
        assert "obv" in result.columns

    def test_obv_increases_on_up_close(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_obv(sample_ohlcv_df.copy())
        close_diff = result["close"].diff()
        # Find an up-close row (guaranteed to exist in 250 rows)
        up_rows = close_diff > 0
        assert up_rows.any(), "Need at least one up-close row"
        first_up = up_rows.idxmax()
        prev_idx = result.index[result.index.get_loc(first_up) - 1]
        assert result.loc[first_up, "obv"] > result.loc[prev_idx, "obv"]

    def test_obv_decreases_on_down_close(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_obv(sample_ohlcv_df.copy())
        close_diff = result["close"].diff()
        # Skip first row (NaN from diff) and find a down-close with valid prior OBV
        down_rows = (close_diff < 0) & result["obv"].notna() & result["obv"].shift(1).notna()
        assert down_rows.any(), "Need at least one down-close row with valid OBV"
        first_down = down_rows.idxmax()
        prev_idx = result.index[result.index.get_loc(first_down) - 1]
        assert result.loc[first_down, "obv"] < result.loc[prev_idx, "obv"]


# ---------------------------------------------------------------------------
# FEAT-11: VWAP
# ---------------------------------------------------------------------------


class TestVWAP:
    def test_vwap_adds_column(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_vwap(sample_ohlcv_df.copy())
        assert "vwap" in result.columns

    def test_vwap_values_within_price_range(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_vwap(sample_ohlcv_df.copy())
        # VWAP (cumulative) should be within the overall price range
        valid = result["vwap"].dropna()
        assert valid.min() >= result["low"].min() * 0.9
        assert valid.max() <= result["high"].max() * 1.1


# ---------------------------------------------------------------------------
# FEAT-12: Volume SMA
# ---------------------------------------------------------------------------


class TestVolumeSMA:
    def test_volume_sma_adds_column(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_volume_sma(sample_ohlcv_df.copy())
        assert "volume_sma_20" in result.columns

    def test_volume_sma_custom_period(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_volume_sma(sample_ohlcv_df.copy(), period=10)
        assert "volume_sma_10" in result.columns

    def test_volume_sma_equals_rolling_mean(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        expected = df["volume"].rolling(20).mean()
        result = compute_volume_sma(df)
        valid_idx = result["volume_sma_20"].dropna().index
        pd.testing.assert_series_equal(
            result.loc[valid_idx, "volume_sma_20"],
            expected.loc[valid_idx],
            check_names=False,
            atol=1e-6,
        )


# ---------------------------------------------------------------------------
# FEAT-13: Accumulation/Distribution
# ---------------------------------------------------------------------------


class TestADLine:
    def test_ad_line_adds_column(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_ad_line(sample_ohlcv_df.copy())
        assert "ad_line" in result.columns

    def test_ad_line_is_cumulative(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_ad_line(sample_ohlcv_df.copy())
        # A/D line is cumulative; changes should track CLV * volume increments
        ad = result["ad_line"]
        clv = ((result["close"] - result["low"]) - (result["high"] - result["close"])) / (
            result["high"] - result["low"]
        )
        money_flow = clv * result["volume"]
        expected = money_flow.cumsum()
        pd.testing.assert_series_equal(ad, expected, check_names=False, atol=1e-6)


# ---------------------------------------------------------------------------
# FEAT-14: Returns
# ---------------------------------------------------------------------------


class TestReturns:
    def test_returns_adds_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_returns(sample_ohlcv_df.copy())
        for col in (
            "return_1d",
            "return_5d",
            "return_21d",
            "log_return_1d",
            "log_return_5d",
            "log_return_21d",
        ):
            assert col in result.columns

    def test_return_1d_equals_pct_change(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        expected = df["close"].pct_change(1)
        result = compute_returns(df)
        valid_idx = result["return_1d"].dropna().index
        pd.testing.assert_series_equal(
            result.loc[valid_idx, "return_1d"],
            expected.loc[valid_idx],
            check_names=False,
            atol=1e-10,
        )

    def test_log_return_1d_formula(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        expected = np.log(df["close"] / df["close"].shift(1))
        result = compute_returns(df)
        valid_idx = result["log_return_1d"].dropna().index
        pd.testing.assert_series_equal(
            result.loc[valid_idx, "log_return_1d"],
            expected.loc[valid_idx],
            check_names=False,
            atol=1e-10,
        )


# ---------------------------------------------------------------------------
# Orchestrator: compute_all_indicators
# ---------------------------------------------------------------------------


class TestAllIndicators:
    def test_all_indicators_adds_all_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        original_cols = set(df.columns)
        result = compute_all_indicators(df)
        new_cols = set(result.columns) - original_cols
        assert len(new_cols) >= 25

    def test_all_indicators_preserves_original(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_all_indicators(sample_ohlcv_df.copy())
        for col in ("open", "high", "low", "close", "volume"):
            assert col in result.columns

    def test_all_indicators_expected_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_all_indicators(sample_ohlcv_df.copy())
        expected = {
            "rsi_14",
            "macd_line",
            "macd_signal",
            "macd_hist",
            "stoch_k",
            "stoch_d",
            "sma_20",
            "sma_50",
            "sma_200",
            "ema_12",
            "ema_26",
            "adx",
            "bb_upper",
            "bb_lower",
            "bb_bandwidth",
            "atr",
            "rolling_vol_21",
            "obv",
            "vwap",
            "volume_sma_20",
            "ad_line",
            "return_1d",
            "return_5d",
            "return_21d",
            "log_return_1d",
            "log_return_5d",
            "log_return_21d",
        }
        assert expected.issubset(set(result.columns))
