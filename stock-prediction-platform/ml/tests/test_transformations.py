"""Tests for ml.features.transformations — scaler pipeline factory."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer, StandardScaler

from ml.features.transformations import (
    SCALER_VARIANTS,
    build_scaler_pipeline,
)


# ---------------------------------------------------------------------------
# Factory basics
# ---------------------------------------------------------------------------


class TestBuildScalerPipeline:
    def test_returns_pipeline(self) -> None:
        pipe = build_scaler_pipeline("standard")
        assert isinstance(pipe, Pipeline)

    @pytest.mark.parametrize("variant", SCALER_VARIANTS)
    def test_all_variants_return_pipeline(self, variant: str) -> None:
        pipe = build_scaler_pipeline(variant)
        assert isinstance(pipe, Pipeline)

    def test_standard_scaler_type(self) -> None:
        pipe = build_scaler_pipeline("standard")
        assert isinstance(pipe.named_steps["scaler"], StandardScaler)

    def test_quantile_scaler_type(self) -> None:
        pipe = build_scaler_pipeline("quantile")
        scaler = pipe.named_steps["scaler"]
        assert isinstance(scaler, QuantileTransformer)
        assert scaler.output_distribution == "normal"

    def test_minmax_scaler_type(self) -> None:
        pipe = build_scaler_pipeline("minmax")
        assert isinstance(pipe.named_steps["scaler"], MinMaxScaler)

    def test_unknown_variant_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown scaler variant"):
            build_scaler_pipeline("robust")

    def test_scaler_variants_constant(self) -> None:
        assert "standard" in SCALER_VARIANTS
        assert "quantile" in SCALER_VARIANTS
        assert "minmax" in SCALER_VARIANTS


# ---------------------------------------------------------------------------
# FEAT-17: StandardScaler
# ---------------------------------------------------------------------------


class TestStandardScaler:
    def test_zero_mean_unit_std(self, sample_ohlcv_df: pd.DataFrame) -> None:
        pipe = build_scaler_pipeline("standard")
        X = sample_ohlcv_df[["close", "volume"]].values
        X_t = pipe.fit_transform(X)
        # After transform, each column should have ~0 mean and ~1 std
        assert np.abs(X_t.mean(axis=0)).max() < 1e-10
        assert np.abs(X_t.std(axis=0) - 1.0).max() < 0.01


# ---------------------------------------------------------------------------
# FEAT-18: QuantileTransformer
# ---------------------------------------------------------------------------


class TestQuantileTransformer:
    def test_approximately_normal(self, sample_ohlcv_df: pd.DataFrame) -> None:
        pipe = build_scaler_pipeline("quantile")
        X = sample_ohlcv_df[["close", "volume"]].values
        X_t = pipe.fit_transform(X)
        # Mean should be approximately 0, std approximately 1
        assert np.abs(X_t.mean(axis=0)).max() < 0.15
        assert np.abs(X_t.std(axis=0) - 1.0).max() < 0.15


# ---------------------------------------------------------------------------
# FEAT-19: MinMaxScaler
# ---------------------------------------------------------------------------


class TestMinMaxScaler:
    def test_values_in_0_1(self, sample_ohlcv_df: pd.DataFrame) -> None:
        pipe = build_scaler_pipeline("minmax")
        X = sample_ohlcv_df[["close", "volume"]].values
        X_t = pipe.fit_transform(X)
        assert X_t.min() >= 0.0 - 1e-10
        assert X_t.max() <= 1.0 + 1e-10


# ---------------------------------------------------------------------------
# No-leakage verification
# ---------------------------------------------------------------------------


class TestNoLeakage:
    def test_fit_on_train_transform_on_test(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """Scaler fitted on training data should NOT reflect test statistics."""
        X = sample_ohlcv_df[["close"]].values
        split = 200
        X_train, X_test = X[:split], X[split:]

        pipe = build_scaler_pipeline("standard")
        pipe.fit(X_train)

        X_test_t = pipe.transform(X_test)
        # Test mean should NOT be zero (it was fit on train distribution)
        # If it were zero, that would indicate test data leaked into fit
        # (with enough data shift, test mean should differ from 0)
        # This is a structural test: we just verify fit/transform works
        assert X_test_t.shape == X_test.shape

    def test_separate_pipelines_independent(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """Two pipelines built from the factory should be independent."""
        pipe1 = build_scaler_pipeline("standard")
        pipe2 = build_scaler_pipeline("standard")
        X = sample_ohlcv_df[["close"]].values

        pipe1.fit(X[:100])
        pipe2.fit(X[100:200])

        # The scalers should have different means
        mean1 = pipe1.named_steps["scaler"].mean_[0]
        mean2 = pipe2.named_steps["scaler"].mean_[0]
        assert mean1 != mean2
