"""Tests for the label generation pipeline component."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml.features.indicators import compute_all_indicators
from ml.features.lag_features import compute_lag_features, compute_rolling_stats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def featured_data(sample_ohlcv_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Apply full feature engineering to the conftest fixture, return as dict."""
    df = sample_ohlcv_df.copy()
    df = compute_all_indicators(df)
    df = compute_lag_features(df)
    df = compute_rolling_stats(df)
    return {"AAPL": df}


# ---------------------------------------------------------------------------
# TestGenerateLabels
# ---------------------------------------------------------------------------


class TestGenerateLabels:
    """Tests for generate_labels()."""

    def test_returns_tuple(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        result = generate_labels(featured_data)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_data_dict_keys(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        data, _ = generate_labels(featured_data)
        assert set(data.keys()) == {"AAPL"}

    def test_target_column_present(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        data, _ = generate_labels(featured_data)
        assert "target_7d" in data["AAPL"].columns

    def test_no_nan_values(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        data, _ = generate_labels(featured_data)
        for df in data.values():
            assert not df.isna().any().any(), "Found NaN values in output"

    def test_feature_names_excludes_target(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        _, feature_names = generate_labels(featured_data)
        assert "target_7d" not in feature_names

    def test_feature_names_matches_columns(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        data, feature_names = generate_labels(featured_data)
        df = data["AAPL"]
        assert set(feature_names) | {"target_7d"} == set(df.columns)

    def test_row_count_reduced(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        original_rows = len(featured_data["AAPL"])
        data, _ = generate_labels(featured_data)
        assert len(data["AAPL"]) < original_rows

    def test_output_row_count_range(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        data, _ = generate_labels(featured_data)
        n = len(data["AAPL"])
        assert 20 <= n <= 60, f"Expected 20-60 rows, got {n}"


# ---------------------------------------------------------------------------
# TestLeakagePrevention
# ---------------------------------------------------------------------------


class TestLeakagePrevention:
    """Verify no future data leaks into features."""

    def test_target_equals_forward_return(self, sample_ohlcv_df, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        data, _ = generate_labels(featured_data)
        df_out = data["AAPL"]

        # Compute ground-truth from original close prices
        original_close = sample_ohlcv_df["close"]

        for idx in df_out.index:
            t_pos = original_close.index.get_loc(idx)
            if t_pos + 7 < len(original_close):
                expected = (original_close.iloc[t_pos + 7] - original_close.iloc[t_pos]) / original_close.iloc[t_pos]
                np.testing.assert_almost_equal(
                    df_out.loc[idx, "target_7d"], expected, decimal=10,
                    err_msg=f"Target mismatch at {idx}",
                )

    def test_no_future_features(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        data, feature_names = generate_labels(featured_data)
        forbidden = {"future", "forward"}
        for name in feature_names:
            assert not any(f in name.lower() for f in forbidden), f"Suspicious feature: {name}"

    def test_features_use_only_past_data(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        _, feature_names = generate_labels(featured_data)
        lag_features = [f for f in feature_names if f.startswith("lag_close_")]
        for f in lag_features:
            n = int(f.split("_")[-1])
            assert n > 0, f"Lag feature {f} references non-positive offset"


# ---------------------------------------------------------------------------
# TestGenerateLabelsEdgeCases
# ---------------------------------------------------------------------------


class TestGenerateLabelsEdgeCases:
    """Edge-case tests for generate_labels()."""

    def test_empty_dict_input(self):
        from ml.pipelines.components.label_generator import generate_labels

        data, feature_names = generate_labels({})
        assert data == {}
        assert feature_names == []

    def test_custom_horizon(self, featured_data):
        from ml.pipelines.components.label_generator import generate_labels

        data, _ = generate_labels(featured_data, horizon=14)
        assert "target_14d" in data["AAPL"].columns
        assert "target_7d" not in data["AAPL"].columns

    def test_ticker_with_insufficient_rows(self):
        from ml.pipelines.components.label_generator import generate_labels

        # Create a tiny DataFrame: only 10 rows — not enough after warm-up + target tail
        rng = np.random.default_rng(99)
        dates = pd.bdate_range("2024-01-02", periods=10)
        df = pd.DataFrame(
            {
                "open": rng.uniform(170, 175, 10),
                "high": rng.uniform(175, 180, 10),
                "low": rng.uniform(165, 170, 10),
                "close": rng.uniform(170, 175, 10),
                "volume": rng.integers(1_000_000, 5_000_000, 10),
            },
            index=dates,
        )
        # Apply indicators — many will produce NaN due to insufficient data
        df = compute_all_indicators(df)
        df = compute_lag_features(df)
        df = compute_rolling_stats(df)

        data, feature_names = generate_labels({"TINY": df})
        # Ticker should be omitted because all rows have NaN after drop
        assert "TINY" not in data
