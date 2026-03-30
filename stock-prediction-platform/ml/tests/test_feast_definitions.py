"""Tests for ml/feature_store/feature_repo.py — Entity and FeatureView definitions."""
from __future__ import annotations

import pytest


class TestFeatureViewDefinitions:
    """FEAST-02, FEAST-03: FeatureView objects have correct names, entities, fields, TTL."""

    def test_ticker_entity_join_key(self):
        """ticker Entity has join_keys=['ticker']."""
        from ml.feature_store.feature_repo import ticker
        assert ticker.name == "ticker"
        assert "ticker" in ticker.join_keys

    def test_ohlcv_stats_fv_exists(self):
        """ohlcv_stats_fv FeatureView is importable and named correctly."""
        from ml.feature_store.feature_repo import ohlcv_stats_fv
        assert ohlcv_stats_fv.name == "ohlcv_stats_fv"

    def test_ohlcv_stats_fv_has_required_fields(self):
        """ohlcv_stats_fv schema contains: open, high, low, close, volume, daily_return, vwap."""
        from ml.feature_store.feature_repo import ohlcv_stats_fv
        field_names = {f.name for f in ohlcv_stats_fv.schema}
        required = {"open", "high", "low", "close", "volume", "daily_return", "vwap"}
        assert required.issubset(field_names), f"Missing fields: {required - field_names}"

    def test_technical_indicators_fv_exists(self):
        """technical_indicators_fv FeatureView is importable."""
        from ml.feature_store.feature_repo import technical_indicators_fv
        assert technical_indicators_fv.name == "technical_indicators_fv"

    def test_technical_indicators_fv_has_required_fields(self):
        """technical_indicators_fv schema contains: rsi_14, macd_line, macd_signal, bb_upper, bb_lower, atr_14, adx_14, ema_20, obv."""
        from ml.feature_store.feature_repo import technical_indicators_fv
        field_names = {f.name for f in technical_indicators_fv.schema}
        required = {"rsi_14", "macd_line", "macd_signal", "bb_upper", "bb_lower", "atr_14", "adx_14", "ema_20", "obv"}
        assert required.issubset(field_names), f"Missing fields: {required - field_names}"

    def test_lag_features_fv_exists(self):
        """lag_features_fv FeatureView is importable."""
        from ml.feature_store.feature_repo import lag_features_fv
        assert lag_features_fv.name == "lag_features_fv"

    def test_lag_features_fv_has_required_lag_fields(self):
        """lag_features_fv schema contains lag_1 through lag_21 and rolling stats."""
        from ml.feature_store.feature_repo import lag_features_fv
        field_names = {f.name for f in lag_features_fv.schema}
        required = {
            "lag_1", "lag_2", "lag_3", "lag_5", "lag_7", "lag_10", "lag_14", "lag_21",
            "rolling_mean_5", "rolling_mean_10", "rolling_mean_21",
            "rolling_std_5", "rolling_std_10", "rolling_std_21",
        }
        assert required.issubset(field_names), f"Missing fields: {required - field_names}"

    def test_all_feature_views_online_enabled(self):
        """All three FeatureViews have online=True for Redis materialization."""
        from ml.feature_store.feature_repo import (
            lag_features_fv, ohlcv_stats_fv, technical_indicators_fv,
        )
        assert ohlcv_stats_fv.online is True
        assert technical_indicators_fv.online is True
        assert lag_features_fv.online is True

    def test_all_feature_views_have_ticker_entity(self):
        """All three FeatureViews reference the ticker entity."""
        from ml.feature_store.feature_repo import (
            lag_features_fv, ohlcv_stats_fv, technical_indicators_fv,
        )
        for fv in [ohlcv_stats_fv, technical_indicators_fv, lag_features_fv]:
            entity_names = [e if isinstance(e, str) else e.name for e in fv.entities]
            assert "ticker" in entity_names, f"{fv.name} missing ticker entity"

    def test_feature_views_ttl_at_least_365_days(self):
        """All FeatureViews have TTL >= 365 days (required for historical training retrieval)."""
        from datetime import timedelta
        from ml.feature_store.feature_repo import (
            lag_features_fv, ohlcv_stats_fv, technical_indicators_fv,
        )
        for fv in [ohlcv_stats_fv, technical_indicators_fv, lag_features_fv]:
            assert fv.ttl is None or fv.ttl >= timedelta(days=365), (
                f"{fv.name} TTL {fv.ttl} is too short for training data retrieval"
            )
