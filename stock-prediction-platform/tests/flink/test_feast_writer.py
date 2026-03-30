"""Unit tests for Feast Writer pure Python push logic.

Tests mock feast at sys.modules level to avoid requiring feast to be installed.
All five tests verify push_batch_to_feast behavior via mocked FeatureStore.
"""
import sys
import os
from unittest.mock import MagicMock, call, patch

# ---------------------------------------------------------------------------
# Mock feast modules BEFORE importing feast_writer so it never tries to import
# the real feast package (which may not be installed in the test environment).
# ---------------------------------------------------------------------------
feast_mock = MagicMock()
feast_push_source_mock = MagicMock()
pandas_mock = MagicMock()

# Set up PushMode enum-like mock
feast_push_source_mock.PushMode.ONLINE = "ONLINE"

sys.modules.setdefault("feast", feast_mock)
sys.modules.setdefault("feast.push_source", feast_push_source_mock)

# Add feast_writer directory to sys.path
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "services",
        "flink-jobs",
        "feast_writer",
    ),
)

# We need the actual pandas for DataFrame construction in the function
import pandas as pd

# Patch FeatureStore at import time of feast_writer
with patch.dict(sys.modules, {"feast": feast_mock, "feast.push_source": feast_push_source_mock}):
    import importlib
    import feast_writer as fw_module
    importlib.reload(fw_module)

from feast_writer import push_batch_to_feast


class TestPushBatchToFeast:
    """Unit tests for push_batch_to_feast function."""

    def setup_method(self):
        """Reset mock state before each test."""
        feast_mock.reset_mock()
        feast_push_source_mock.reset_mock()
        feast_push_source_mock.PushMode.ONLINE = "ONLINE"

    def test_single_record_calls_store_push_once(self):
        """Test 1: push_batch_to_feast with one record calls store.push exactly once."""
        records = [
            {
                "ticker": "AAPL",
                "timestamp": "2026-01-01T10:00:00Z",
                "ema_20": 150.5,
                "rsi_14": 55.0,
                "macd_signal": 0.3,
            }
        ]
        mock_store = MagicMock()
        with patch("feast_writer.FeatureStore", return_value=mock_store):
            push_batch_to_feast(records)
        mock_store.push.assert_called_once()
        call_kwargs = mock_store.push.call_args[1]
        assert call_kwargs["push_source_name"] == "technical_indicators_push"

    def test_empty_batch_does_not_call_store_push(self):
        """Test 2: push_batch_to_feast([]) does NOT call store.push."""
        mock_store = MagicMock()
        with patch("feast_writer.FeatureStore", return_value=mock_store):
            push_batch_to_feast([])
        mock_store.push.assert_not_called()

    def test_three_records_calls_store_push_with_3_rows(self):
        """Test 3: push_batch_to_feast with 3 records calls store.push with df of 3 rows."""
        records = [
            {"ticker": "AAPL", "timestamp": "2026-01-01T10:00:00Z", "ema_20": 150.0, "rsi_14": 55.0, "macd_signal": 0.1},
            {"ticker": "MSFT", "timestamp": "2026-01-01T10:05:00Z", "ema_20": 280.0, "rsi_14": 60.0, "macd_signal": 0.2},
            {"ticker": "GOOG", "timestamp": "2026-01-01T10:10:00Z", "ema_20": 2800.0, "rsi_14": 45.0, "macd_signal": -0.1},
        ]
        mock_store = MagicMock()
        with patch("feast_writer.FeatureStore", return_value=mock_store):
            push_batch_to_feast(records)
        mock_store.push.assert_called_once()
        df_arg = mock_store.push.call_args[1]["df"]
        assert len(df_arg) == 3

    def test_df_has_correct_columns(self):
        """Test 4: df passed to store.push has exactly the expected columns."""
        records = [
            {
                "ticker": "AAPL",
                "timestamp": "2026-01-01T10:00:00Z",
                "ema_20": 150.5,
                "rsi_14": 55.0,
                "macd_signal": 0.3,
                "extra_col": "should_not_appear",  # extra column should be dropped
            }
        ]
        mock_store = MagicMock()
        with patch("feast_writer.FeatureStore", return_value=mock_store):
            push_batch_to_feast(records)
        df_arg = mock_store.push.call_args[1]["df"]
        expected_columns = {"ticker", "event_timestamp", "ema_20", "rsi_14", "macd_signal"}
        assert set(df_arg.columns) == expected_columns

    def test_event_timestamp_is_timezone_aware(self):
        """Test 5: event_timestamp column in the pushed df is timezone-aware (UTC)."""
        records = [
            {
                "ticker": "AAPL",
                "timestamp": "2026-01-01T10:00:00Z",
                "ema_20": 150.5,
                "rsi_14": 55.0,
                "macd_signal": 0.3,
            }
        ]
        mock_store = MagicMock()
        with patch("feast_writer.FeatureStore", return_value=mock_store):
            push_batch_to_feast(records)
        df_arg = mock_store.push.call_args[1]["df"]
        # Timezone-aware datetime has tz attribute
        assert df_arg["event_timestamp"].dtype.tz is not None
        import pytz
        # Should be UTC
        assert str(df_arg["event_timestamp"].dtype.tz) in ("UTC", "utc")
