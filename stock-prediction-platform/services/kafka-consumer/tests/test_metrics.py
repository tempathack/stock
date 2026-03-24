"""Tests for Kafka consumer Prometheus metrics."""

from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import REGISTRY

from consumer.metrics import (
    batch_write_duration_seconds,
    consumer_lag,
    messages_consumed_total,
    start_metrics_server,
)


class TestMessagesConsumedCounter:
    """Verify messages_consumed_total increments on add_message."""

    def test_counter_increments_on_add_message(self):
        from consumer.processor import MessageProcessor

        writer = MagicMock()
        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=writer)

        msg = MagicMock()
        msg.value.return_value = b'{"ticker": "AAPL", "fetch_mode": "intraday", "timestamp": "2025-01-01T10:00:00", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100}'
        msg.topic.return_value = "stock-intraday"

        before = REGISTRY.get_sample_value(
            "messages_consumed_total", {"topic": "stock-intraday"}
        ) or 0.0

        processor.add_message(msg)

        after = REGISTRY.get_sample_value(
            "messages_consumed_total", {"topic": "stock-intraday"}
        ) or 0.0
        assert after - before == 1.0


class TestBatchWriteDuration:
    """Verify batch_write_duration_seconds observes values."""

    def test_histogram_observes_value(self):
        before = REGISTRY.get_sample_value(
            "batch_write_duration_seconds_count", {"table": "ohlcv_test"}
        ) or 0.0

        batch_write_duration_seconds.labels(table="ohlcv_test").observe(0.05)

        after = REGISTRY.get_sample_value(
            "batch_write_duration_seconds_count", {"table": "ohlcv_test"}
        ) or 0.0
        assert after - before == 1.0


class TestConsumerLag:
    """Verify consumer_lag gauge can be set."""

    def test_gauge_sets_value(self):
        consumer_lag.labels(topic="stock-intraday", partition="0").set(42)
        val = REGISTRY.get_sample_value(
            "consumer_lag", {"topic": "stock-intraday", "partition": "0"}
        )
        assert val == 42.0


class TestMetricsServer:
    """Verify start_metrics_server calls prometheus_client.start_http_server."""

    @patch("consumer.metrics.start_http_server")
    def test_starts_on_specified_port(self, mock_start):
        start_metrics_server(9191)
        mock_start.assert_called_once_with(9191)
