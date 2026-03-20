"""Tests for the feature engineering pipeline component."""

from __future__ import annotations

import pandas as pd
import pytest

from ml.features.indicators import compute_all_indicators
from ml.features.lag_features import compute_lag_features, compute_rolling_stats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def single_ticker_data(sample_ohlcv_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Wrap the conftest fixture as a single-ticker dict."""
    return {"AAPL": sample_ohlcv_df.copy()}


@pytest.fixture
def multi_ticker_data(sample_ohlcv_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Two-ticker data dict."""
    return {"AAPL": sample_ohlcv_df.copy(), "MSFT": sample_ohlcv_df.copy()}


# ---------------------------------------------------------------------------
# TestEngineerFeatures
# ---------------------------------------------------------------------------


class TestEngineerFeatures:
    """Tests for engineer_features()."""

    def test_returns_dict(self, single_ticker_data):
        from ml.pipelines.components.feature_engineer import engineer_features

        result = engineer_features(single_ticker_data)
        assert isinstance(result, dict)

    def test_all_tickers_present(self, multi_ticker_data):
        from ml.pipelines.components.feature_engineer import engineer_features

        result = engineer_features(multi_ticker_data)
        assert set(result.keys()) == {"AAPL", "MSFT"}

    def test_dataframe_type(self, single_ticker_data):
        from ml.pipelines.components.feature_engineer import engineer_features

        result = engineer_features(single_ticker_data)
        for v in result.values():
            assert isinstance(v, pd.DataFrame)

    def test_original_columns_preserved(self, single_ticker_data):
        from ml.pipelines.components.feature_engineer import engineer_features

        result = engineer_features(single_ticker_data)
        for col in ["open", "high", "low", "close", "volume"]:
            assert col in result["AAPL"].columns

    def test_indicator_columns_added(self, single_ticker_data):
        from ml.pipelines.components.feature_engineer import engineer_features

        result = engineer_features(single_ticker_data)
        expected = ["rsi_14", "macd_line", "macd_signal", "sma_20", "ema_12", "bb_upper", "atr", "obv"]
        for col in expected:
            assert col in result["AAPL"].columns, f"Missing indicator column: {col}"

    def test_lag_columns_added(self, single_ticker_data):
        from ml.pipelines.components.feature_engineer import engineer_features

        result = engineer_features(single_ticker_data)
        expected = ["lag_close_1", "lag_close_7", "lag_close_21"]
        for col in expected:
            assert col in result["AAPL"].columns, f"Missing lag column: {col}"

    def test_rolling_columns_added(self, single_ticker_data):
        from ml.pipelines.components.feature_engineer import engineer_features

        result = engineer_features(single_ticker_data)
        expected = ["rolling_mean_5", "rolling_std_21", "rolling_max_10"]
        for col in expected:
            assert col in result["AAPL"].columns, f"Missing rolling column: {col}"

    def test_column_count_matches_direct_computation(self, sample_ohlcv_df):
        from ml.pipelines.components.feature_engineer import engineer_features

        # Direct computation
        df = sample_ohlcv_df.copy()
        df = compute_all_indicators(df)
        df = compute_lag_features(df)
        df = compute_rolling_stats(df)
        expected_cols = len(df.columns)

        # Via component
        result = engineer_features({"AAPL": sample_ohlcv_df.copy()})
        assert len(result["AAPL"].columns) == expected_cols


# ---------------------------------------------------------------------------
# TestEngineerFeaturesEdgeCases
# ---------------------------------------------------------------------------


class TestEngineerFeaturesEdgeCases:
    """Edge-case tests for engineer_features()."""

    def test_empty_dict_returns_empty(self):
        from ml.pipelines.components.feature_engineer import engineer_features

        result = engineer_features({})
        assert result == {}

    def test_single_ticker(self, single_ticker_data):
        from ml.pipelines.components.feature_engineer import engineer_features

        result = engineer_features(single_ticker_data)
        assert len(result) == 1

    def test_index_preserved(self, single_ticker_data):
        from ml.pipelines.components.feature_engineer import engineer_features

        original_index = single_ticker_data["AAPL"].index.copy()
        result = engineer_features(single_ticker_data)
        pd.testing.assert_index_equal(result["AAPL"].index, original_index)
