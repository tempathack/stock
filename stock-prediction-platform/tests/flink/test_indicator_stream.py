"""Unit tests for Indicator Stream UDAF pure Python logic.

Tests import indicator_udaf_logic directly to avoid pyflink runtime dependency.
All seven test cases exercise compute_rsi, compute_ema, and compute_macd_signal.
"""
import sys
import os

# Add the indicator_stream package directory to sys.path so we can import
# indicator_udaf_logic without triggering pyflink imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "services",
        "flink-jobs",
        "indicator_stream",
    ),
)

from indicator_udaf_logic import compute_rsi, compute_ema, compute_macd_signal


class TestComputeRsi:
    """Tests for Wilder's RSI computation."""

    def test_rsi_mixed_prices_in_range(self):
        """Test 1: compute_rsi with mixed gains/losses returns float between 0 and 100."""
        # 20 prices with mixed movement
        prices = [
            100.0, 102.0, 101.0, 103.5, 102.0,
            104.0, 106.0, 105.0, 107.0, 106.5,
            108.0, 107.0, 109.0, 110.0, 108.5,
            109.5, 111.0, 110.0, 112.0, 113.0,
        ]
        result = compute_rsi(prices)
        assert result is not None
        assert isinstance(result, float)
        assert 0.0 <= result <= 100.0

    def test_rsi_all_gains_overbought(self):
        """Test 2: compute_rsi with all ascending prices returns RSI > 70 (overbought)."""
        # Strictly ascending prices — all gains, no losses
        prices = [100.0 + i * 2.0 for i in range(20)]
        result = compute_rsi(prices)
        assert result is not None
        assert result > 70.0

    def test_rsi_all_losses_oversold(self):
        """Test 3: compute_rsi with all descending prices returns RSI < 30 (oversold)."""
        # Strictly descending prices — all losses, no gains
        prices = [120.0 - i * 2.0 for i in range(20)]
        result = compute_rsi(prices)
        assert result is not None
        assert result < 30.0

    def test_rsi_insufficient_data_returns_none(self):
        """Test 6: compute_rsi with fewer than 14 prices returns None."""
        prices = [100.0, 101.0, 102.0, 101.5, 103.0]  # only 5 prices
        result = compute_rsi(prices)
        assert result is None

    def test_rsi_exactly_13_prices_returns_none(self):
        """Additional: 13 prices (< 14) also returns None."""
        prices = [100.0 + i for i in range(13)]
        result = compute_rsi(prices)
        assert result is None


class TestComputeEma:
    """Tests for EMA computation."""

    def test_ema_returns_float_close_to_mean(self):
        """Test 4: compute_ema with 25 prices returns float (EMA-20)."""
        prices = [100.0 + i * 0.5 for i in range(25)]
        result = compute_ema(prices, span=20)
        assert result is not None
        assert isinstance(result, float)
        # EMA should be in a reasonable range for the given prices
        assert 100.0 <= result <= 115.0

    def test_ema_insufficient_data_returns_none(self):
        """Additional boundary: fewer than span prices returns None."""
        prices = [100.0 + i for i in range(15)]  # 15 < span=20
        result = compute_ema(prices, span=20)
        assert result is None


class TestComputeMacdSignal:
    """Tests for MACD signal line computation."""

    def test_macd_signal_returns_float(self):
        """Test 5: compute_macd_signal with 35 prices returns float (MACD signal)."""
        prices = [100.0 + i * 0.3 for i in range(35)]
        result = compute_macd_signal(prices)
        assert result is not None
        assert isinstance(result, float)

    def test_macd_signal_insufficient_data_returns_none(self):
        """Test 7: compute_macd_signal with fewer than 35 prices returns None."""
        prices = [100.0 + i for i in range(30)]  # only 30, need 35
        result = compute_macd_signal(prices)
        assert result is None

    def test_macd_signal_exactly_34_prices_returns_none(self):
        """Additional: exactly 34 prices (< 35) returns None."""
        prices = [100.0 + i * 0.5 for i in range(34)]
        result = compute_macd_signal(prices)
        assert result is None
