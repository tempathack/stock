"""Tests for ml/feature_store/feature_repo.py — Phase 94 FRED FeatureView definitions."""
from __future__ import annotations


class TestFredMacroFeatureView:
    """Phase 94: fred_macro_source and fred_macro_fv must be defined in feature_repo.py."""

    def test_fred_macro_source_defined(self):
        """fred_macro_source is exported from feature_repo."""
        from ml.feature_store.feature_repo import fred_macro_source  # noqa: F401
        assert fred_macro_source is not None

    def test_fred_macro_fv_defined(self):
        """fred_macro_fv is exported from feature_repo."""
        from ml.feature_store.feature_repo import fred_macro_fv  # noqa: F401
        assert fred_macro_fv is not None

    def test_fred_macro_fv_name(self):
        """fred_macro_fv.name == 'fred_macro_fv'."""
        from ml.feature_store.feature_repo import fred_macro_fv
        assert fred_macro_fv.name == "fred_macro_fv"

    def test_fred_macro_fv_has_14_schema_fields(self):
        """fred_macro_fv schema has exactly 14 fields."""
        from ml.feature_store.feature_repo import fred_macro_fv
        field_names = [f.name for f in fred_macro_fv.schema]
        assert len(field_names) == 14, f"Expected 14 fields, got {len(field_names)}"

    def test_fred_macro_fv_schema_contains_all_series(self):
        """fred_macro_fv schema includes all 14 FRED series as field names."""
        from ml.feature_store.feature_repo import fred_macro_fv
        expected = {
            "dgs2", "dgs10", "t10y2y", "t10y3m",
            "bamlh0a0hym2", "dbaa", "t10yie",
            "dcoilwtico", "dtwexbgs", "dexjpus",
            "icsa", "nfci", "cpiaucsl", "pcepilfe",
        }
        actual = {f.name for f in fred_macro_fv.schema}
        assert actual == expected, f"Schema mismatch. Missing: {expected - actual}"

    def test_fred_macro_fv_source_query_contains_table(self):
        """fred_macro_source query references feast_fred_macro table."""
        from ml.feature_store.feature_repo import fred_macro_source
        assert "feast_fred_macro" in fred_macro_source.query
