"""Unit tests for OHLCV Normalizer pure Python logic.

Tests import normalizer_logic directly to avoid pyflink runtime dependency.
"""
import sys
import os
import unittest
from decimal import Decimal, ROUND_HALF_UP

# Add the ohlcv_normalizer package directory to sys.path so we can import
# normalizer_logic without triggering pyflink imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "services",
        "flink-jobs",
        "ohlcv_normalizer",
    ),
)

from normalizer_logic import should_include_record, normalize_vwap, round_decimal


class TestShouldIncludeRecord(unittest.TestCase):
    """Tests for the record inclusion filter logic."""

    def test_valid_intraday_record_passes(self):
        """Test 1: record with fetch_mode=intraday, valid ticker, close > 0 passes filter."""
        result = should_include_record(
            ticker="AAPL",
            close=Decimal("150.0000"),
            fetch_mode="intraday",
        )
        self.assertTrue(result)

    def test_historical_fetch_mode_filtered_out(self):
        """Test 2: record with fetch_mode=historical is filtered out."""
        result = should_include_record(
            ticker="AAPL",
            close=Decimal("150.0000"),
            fetch_mode="historical",
        )
        self.assertFalse(result)

    def test_close_zero_filtered_out(self):
        """Test 3: record with close = 0 is filtered out."""
        result = should_include_record(
            ticker="AAPL",
            close=Decimal("0"),
            fetch_mode="intraday",
        )
        self.assertFalse(result)

    def test_ticker_none_filtered_out(self):
        """Test 4: record with ticker = None is filtered out."""
        result = should_include_record(
            ticker=None,
            close=Decimal("150.0000"),
            fetch_mode="intraday",
        )
        self.assertFalse(result)

    def test_close_none_filtered_out(self):
        """Test 5: record with close = None is filtered out."""
        result = should_include_record(
            ticker="AAPL",
            close=None,
            fetch_mode="intraday",
        )
        self.assertFalse(result)

    def test_vwap_defaults_to_close_when_none(self):
        """Test 6: vwap defaults to close value when vwap is None."""
        result = normalize_vwap(
            vwap=None,
            close=Decimal("175.5000"),
        )
        self.assertEqual(result, Decimal("175.5000"))

    def test_decimal_precision_rounds_to_4dp(self):
        """Test 7: decimal precision — close = 1234.56789 rounds to 4dp -> 1234.5679."""
        result = round_decimal(Decimal("1234.56789"))
        self.assertEqual(result, Decimal("1234.5679"))


if __name__ == "__main__":
    unittest.main()
