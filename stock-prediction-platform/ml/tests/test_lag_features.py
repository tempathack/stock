"""Tests for ml.features.lag_features — lags, rolling stats, target & drop."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.features.lag_features import (
    DEFAULT_LAGS,
    DEFAULT_WINDOWS,
    compute_lag_features,
    compute_rolling_stats,
    drop_incomplete_rows,
    generate_target,
)


# ---------------------------------------------------------------------------
# FEAT-15: Lag Features
# ---------------------------------------------------------------------------


class TestLagFeatures:
    def test_adds_default_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_lag_features(sample_ohlcv_df.copy())
        for n in DEFAULT_LAGS:
            assert f"lag_close_{n}" in result.columns

    def test_shift_correctness(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        result = compute_lag_features(df)
        for n in DEFAULT_LAGS:
            expected = df["close"].shift(n)
            pd.testing.assert_series_equal(
                result[f"lag_close_{n}"], expected, check_names=False
            )

    def test_custom_lags(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_lag_features(sample_ohlcv_df.copy(), lags=[1, 10])
        assert "lag_close_1" in result.columns
        assert "lag_close_10" in result.columns
        assert "lag_close_21" not in result.columns

    def test_warm_up_nans(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_lag_features(sample_ohlcv_df.copy())
        # lag_close_21 should have first 21 rows NaN
        assert result["lag_close_21"].iloc[:21].isna().all()
        assert result["lag_close_21"].iloc[21:].notna().all()

    def test_preserves_ohlcv(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_lag_features(sample_ohlcv_df.copy())
        for col in ("open", "high", "low", "close", "volume"):
            assert col in result.columns

    def test_no_look_ahead(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Lag features at row i must only depend on rows < i."""
        df = sample_ohlcv_df.copy()
        result = compute_lag_features(df)
        # lag_close_1 at index 50 should equal close at index 49
        assert result["lag_close_1"].iloc[50] == df["close"].iloc[49]

    def test_returns_dataframe(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_lag_features(sample_ohlcv_df.copy())
        assert isinstance(result, pd.DataFrame)


# ---------------------------------------------------------------------------
# FEAT-16: Rolling Window Stats
# ---------------------------------------------------------------------------


class TestRollingStats:
    def test_adds_default_columns(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rolling_stats(sample_ohlcv_df.copy())
        for w in DEFAULT_WINDOWS:
            for stat in ("mean", "std", "min", "max"):
                assert f"rolling_{stat}_{w}" in result.columns

    def test_rolling_mean_matches_manual(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        result = compute_rolling_stats(df)
        expected = df["close"].rolling(5).mean()
        pd.testing.assert_series_equal(
            result["rolling_mean_5"], expected, check_names=False
        )

    def test_rolling_std_matches_manual(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        result = compute_rolling_stats(df)
        expected = df["close"].rolling(10).std()
        pd.testing.assert_series_equal(
            result["rolling_std_10"], expected, check_names=False
        )

    def test_rolling_min_max_bounds(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rolling_stats(sample_ohlcv_df.copy())
        valid = result.dropna()
        for w in DEFAULT_WINDOWS:
            assert (valid[f"rolling_min_{w}"] <= valid[f"rolling_mean_{w}"]).all()
            assert (valid[f"rolling_max_{w}"] >= valid[f"rolling_mean_{w}"]).all()

    def test_custom_windows(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rolling_stats(sample_ohlcv_df.copy(), windows=[3, 7])
        assert "rolling_mean_3" in result.columns
        assert "rolling_mean_7" in result.columns
        assert "rolling_mean_5" not in result.columns

    def test_warm_up_nans(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rolling_stats(sample_ohlcv_df.copy())
        # rolling_mean_21 needs 21 data points; first 20 rows are NaN
        assert result["rolling_mean_21"].iloc[:20].isna().all()
        assert result["rolling_mean_21"].iloc[20:].notna().all()

    def test_no_center_bias(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Trailing window only — value at row i must not use rows > i."""
        df = sample_ohlcv_df.copy()
        result = compute_rolling_stats(df)
        # rolling_mean_5 at row 10 should equal mean of rows 6..10
        expected = df["close"].iloc[6:11].mean()
        assert abs(result["rolling_mean_5"].iloc[10] - expected) < 1e-10

    def test_preserves_ohlcv(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = compute_rolling_stats(sample_ohlcv_df.copy())
        for col in ("open", "high", "low", "close", "volume"):
            assert col in result.columns


# ---------------------------------------------------------------------------
# FEAT-20: Target Label
# ---------------------------------------------------------------------------


class TestTarget:
    def test_adds_target_column(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = generate_target(sample_ohlcv_df.copy())
        assert "target_7d" in result.columns

    def test_percentage_return_correctness(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        result = generate_target(df)
        # At row 0, target = (close[7] - close[0]) / close[0]
        expected = (df["close"].iloc[7] - df["close"].iloc[0]) / df["close"].iloc[0]
        assert abs(result["target_7d"].iloc[0] - expected) < 1e-10

    def test_tail_nans(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = generate_target(sample_ohlcv_df.copy())
        # Last 7 rows must be NaN (no future data)
        assert result["target_7d"].iloc[-7:].isna().all()
        # Row before the tail should have a value
        assert result["target_7d"].iloc[-8:].notna().sum() >= 1

    def test_non_tail_has_values(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = generate_target(sample_ohlcv_df.copy())
        assert result["target_7d"].iloc[:-7].notna().all()

    def test_custom_horizon(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = generate_target(sample_ohlcv_df.copy(), horizon=14)
        assert "target_14d" in result.columns
        assert result["target_14d"].iloc[-14:].isna().all()

    def test_no_leakage_positive_shift_only_in_features(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """Target uses negative shift (future); features use positive shift (past).
        Verify that target at row i depends on close at row i+7, not i-7."""
        df = sample_ohlcv_df.copy()
        result = generate_target(df)
        idx = 100
        expected = (df["close"].iloc[idx + 7] - df["close"].iloc[idx]) / df["close"].iloc[idx]
        assert abs(result["target_7d"].iloc[idx] - expected) < 1e-10

    def test_preserves_ohlcv(self, sample_ohlcv_df: pd.DataFrame) -> None:
        result = generate_target(sample_ohlcv_df.copy())
        for col in ("open", "high", "low", "close", "volume"):
            assert col in result.columns


# ---------------------------------------------------------------------------
# FEAT-21: Drop Incomplete Rows
# ---------------------------------------------------------------------------


class TestDropIncomplete:
    def test_no_nans_remain(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        df = compute_lag_features(df)
        df = compute_rolling_stats(df)
        df = generate_target(df)
        result = drop_incomplete_rows(df)
        assert result.isna().sum().sum() == 0

    def test_row_count_reduced(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        original_len = len(df)
        df = compute_lag_features(df)
        df = compute_rolling_stats(df)
        df = generate_target(df)
        result = drop_incomplete_rows(df)
        # Must lose at least 21 (warm-up) + 7 (tail) rows
        assert len(result) < original_len
        assert len(result) <= original_len - 28

    def test_returns_copy(self, sample_ohlcv_df: pd.DataFrame) -> None:
        df = sample_ohlcv_df.copy()
        df = compute_lag_features(df)
        df = generate_target(df)
        result = drop_incomplete_rows(df)
        # Modifying result should not affect the original
        result.iloc[0, 0] = -999.0
        assert df.iloc[0, 0] != -999.0 or df.iloc[0, 0] == result.iloc[0, 0] is False

    def test_complete_rows_preserved(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Rows that have all values should survive the drop."""
        df = sample_ohlcv_df.copy()
        df = compute_lag_features(df)
        df = generate_target(df)
        result = drop_incomplete_rows(df)
        # The middle rows (after warm-up, before tail) should all be present
        assert len(result) > 0
        # All close values in result should be a subset of original
        assert set(result["close"].values).issubset(set(df["close"].values))

    def test_works_with_all_features(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Full pipeline: indicators + lag + rolling + target + drop."""
        from ml.features.indicators import compute_all_indicators

        df = sample_ohlcv_df.copy()
        df = compute_all_indicators(df)
        df = compute_lag_features(df)
        df = compute_rolling_stats(df)
        df = generate_target(df)
        result = drop_incomplete_rows(df)
        assert result.isna().sum().sum() == 0
        assert len(result) > 0
