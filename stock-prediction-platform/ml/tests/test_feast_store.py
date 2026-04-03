"""Tests for ml/features/feast_store.py — Feast wrapper module."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


class TestFeatureStoreConfig:
    """FEAST-01: feast_store.py can construct a FeatureStore with FEAST_REPO_PATH."""

    def test_get_store_returns_feast_store_instance(self):
        """get_store() returns a FeatureStore object."""
        with patch("ml.features.feast_store.FeatureStore") as mock_fs_cls:
            mock_fs_cls.return_value = MagicMock()
            from ml.features.feast_store import get_store
            store = get_store()
            mock_fs_cls.assert_called_once()
            assert store is not None

    def test_feast_repo_path_env_override(self, monkeypatch):
        """FEAST_REPO_PATH env var overrides the default repo path."""
        monkeypatch.setenv("FEAST_REPO_PATH", "/custom/path")
        import importlib
        import ml.features.feast_store as fmod
        importlib.reload(fmod)
        assert fmod.FEAST_REPO_PATH == "/custom/path"


class TestHistoricalFeatures:
    """FEAST-04: get_historical_features() calls store.get_historical_features() correctly."""

    @pytest.fixture
    def entity_df(self):
        return pd.DataFrame({
            "ticker": ["AAPL", "MSFT"],
            "event_timestamp": [
                datetime(2025, 1, 10, tzinfo=timezone.utc),
                datetime(2025, 1, 10, tzinfo=timezone.utc),
            ],
        })

    def test_calls_feast_get_historical_features(self, entity_df):
        """Delegates to FeatureStore.get_historical_features with correct features list."""
        mock_store = MagicMock()
        mock_store.get_historical_features.return_value.to_df.return_value = entity_df.copy()
        with patch("ml.features.feast_store.get_store", return_value=mock_store):
            from ml.features.feast_store import get_historical_features
            result = get_historical_features(entity_df)
            mock_store.get_historical_features.assert_called_once()
            call_kwargs = mock_store.get_historical_features.call_args
            assert call_kwargs is not None
            # features list must include ohlcv_stats_fv, technical_indicators_fv, lag_features_fv
            features_arg = call_kwargs.kwargs.get("features") or call_kwargs.args[1] if len(call_kwargs.args) > 1 else call_kwargs.kwargs["features"]
            feature_views = {f.split(":")[0] for f in features_arg}
            assert "ohlcv_stats_fv" in feature_views
            assert "technical_indicators_fv" in feature_views
            assert "lag_features_fv" in feature_views

    def test_returns_dataframe(self, entity_df):
        """Return type is pd.DataFrame."""
        mock_store = MagicMock()
        mock_store.get_historical_features.return_value.to_df.return_value = entity_df.copy()
        with patch("ml.features.feast_store.get_store", return_value=mock_store):
            from ml.features.feast_store import get_historical_features
            result = get_historical_features(entity_df)
            assert isinstance(result, pd.DataFrame)


class TestOnlineFeatures:
    """FEAST-05: get_online_features() calls store.get_online_features() with entity_rows."""

    def test_calls_feast_get_online_features(self):
        """Delegates to FeatureStore.get_online_features with ticker entity row."""
        mock_store = MagicMock()
        mock_store.get_online_features.return_value.to_dict.return_value = {
            "ticker": ["AAPL"],
            "ohlcv_stats_fv__close": [182.5],
        }
        with patch("ml.features.feast_store.get_store", return_value=mock_store):
            from ml.features.feast_store import get_online_features
            result = get_online_features("AAPL")
            mock_store.get_online_features.assert_called_once()
            call_kwargs = mock_store.get_online_features.call_args
            entity_rows = call_kwargs.kwargs.get("entity_rows") or call_kwargs.args[1]
            assert entity_rows == [{"ticker": "AAPL"}]

    def test_returns_dict(self):
        """Return type is dict."""
        mock_store = MagicMock()
        mock_store.get_online_features.return_value.to_dict.return_value = {"ticker": ["AAPL"]}
        with patch("ml.features.feast_store.get_store", return_value=mock_store):
            from ml.features.feast_store import get_online_features
            result = get_online_features("AAPL")
            assert isinstance(result, dict)

    def test_online_features_list_contains_required_views(self):
        """_ONLINE_FEATURES list spans ohlcv_stats_fv, technical_indicators_fv, lag_features_fv."""
        mock_store = MagicMock()
        mock_store.get_online_features.return_value.to_dict.return_value = {}
        with patch("ml.features.feast_store.get_store", return_value=mock_store):
            from ml.features import feast_store
            views = {f.split(":")[0] for f in feast_store._ONLINE_FEATURES}
            assert "ohlcv_stats_fv" in views
            assert "technical_indicators_fv" in views
            assert "lag_features_fv" in views


# ── Wave 0 additions — sentinel tests for Phase 92 feature coverage ──

def test_training_features_include_sentiment_columns():
    """_TRAINING_FEATURES must include all 4 reddit_sentiment_fv columns after Phase 92 extends it."""
    from ml.features.feast_store import _TRAINING_FEATURES
    assert "reddit_sentiment_fv:avg_sentiment" in _TRAINING_FEATURES
    assert "reddit_sentiment_fv:mention_count" in _TRAINING_FEATURES
    assert "reddit_sentiment_fv:positive_ratio" in _TRAINING_FEATURES
    assert "reddit_sentiment_fv:negative_ratio" in _TRAINING_FEATURES
    assert len(_TRAINING_FEATURES) == 34, (
        f"Expected 34 features (30 existing + 4 sentiment), got {len(_TRAINING_FEATURES)}"
    )


def test_online_feature_key_format_no_view_prefix():
    """All _TRAINING_FEATURES bare names (after ':') must not contain ':'.
    This confirms features.json will use unprefixed names matching to_dict() keys.
    """
    from ml.features.feast_store import _TRAINING_FEATURES
    for feature in _TRAINING_FEATURES:
        assert ":" in feature, f"Feature {feature!r} must be in 'view:col' format"
        bare = feature.split(":", 1)[1]
        assert ":" not in bare, f"Bare feature name {bare!r} must not contain ':'"
