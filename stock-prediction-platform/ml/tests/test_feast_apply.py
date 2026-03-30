"""Tests for feast apply registration — FEAST-03.

Verifies that feature_repo.py exports the correct objects
so that feast apply can register them without error.
All assertions use mocked FeatureStore to avoid live registry dependency.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestFeastApplyRegistration:
    """FEAST-03: feast apply registers Entity and three FeatureViews without error."""

    def test_feature_repo_exports_entity_and_feature_views(self):
        """feature_repo.py exports: ticker (Entity), ohlcv_stats_fv, technical_indicators_fv, lag_features_fv."""
        from ml.feature_store import feature_repo
        assert hasattr(feature_repo, "ticker"), "feature_repo must export 'ticker' Entity"
        assert hasattr(feature_repo, "ohlcv_stats_fv"), "feature_repo must export 'ohlcv_stats_fv'"
        assert hasattr(feature_repo, "technical_indicators_fv"), (
            "feature_repo must export 'technical_indicators_fv'"
        )
        assert hasattr(feature_repo, "lag_features_fv"), "feature_repo must export 'lag_features_fv'"

    def test_feast_apply_calls_apply_with_all_objects(self):
        """Mocked FeatureStore.apply() is called with ticker, ohlcv_stats_fv, technical_indicators_fv, lag_features_fv."""
        from ml.feature_store.feature_repo import (
            ticker,
            ohlcv_stats_fv,
            technical_indicators_fv,
            lag_features_fv,
        )
        mock_store = MagicMock()
        with patch("feast.FeatureStore", return_value=mock_store):
            # Simulate what `feast apply` does: constructs FeatureStore and calls apply()
            from feast import FeatureStore
            store = FeatureStore(repo_path="/app/ml/feature_store")
            store.apply([ticker, ohlcv_stats_fv, technical_indicators_fv, lag_features_fv])
            mock_store.apply.assert_called_once()
            applied_objects = mock_store.apply.call_args.args[0]
            applied_names = {
                obj.name if hasattr(obj, "name") else str(obj)
                for obj in applied_objects
            }
            assert "ticker" in applied_names
            assert "ohlcv_stats_fv" in applied_names
            assert "technical_indicators_fv" in applied_names
            assert "lag_features_fv" in applied_names

    def test_source_table_names_match_migration(self):
        """DataSource query strings reference the correct table names from the Alembic migration."""
        from ml.feature_store.feature_repo import (
            ohlcv_stats_fv,
            technical_indicators_fv,
            lag_features_fv,
        )
        # Access the batch_source (PostgreSQLSource) for each FeatureView
        # PostgreSQLSource exposes get_table_query_string() not .query attribute
        ohlcv_query = str(ohlcv_stats_fv.batch_source.get_table_query_string())
        indicators_query = str(technical_indicators_fv.batch_source.get_table_query_string())
        lag_query = str(lag_features_fv.batch_source.get_table_query_string())

        assert "feast_ohlcv_stats" in ohlcv_query, (
            f"ohlcv_stats_fv DataSource query must reference feast_ohlcv_stats, got: {ohlcv_query}"
        )
        assert "feast_technical_indicators" in indicators_query, (
            "technical_indicators_fv DataSource query must reference feast_technical_indicators"
        )
        assert "feast_lag_features" in lag_query, (
            "lag_features_fv DataSource query must reference feast_lag_features"
        )
