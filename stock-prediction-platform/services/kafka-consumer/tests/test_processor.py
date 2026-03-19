"""Unit tests for MessageProcessor: batch accumulation, flush trigger, routing."""
from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import _make_intraday_record, _make_historical_record, _make_kafka_message


class TestAddMessage:
    """Tests for MessageProcessor.add_message."""

    def test_add_message_deserializes_json(self, mock_batch_writer, intraday_message):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=mock_batch_writer)
        processor.add_message(intraday_message)

        assert processor.buffer_size == 1

    def test_add_message_increments_buffer(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=mock_batch_writer)
        for i in range(3):
            msg = _make_kafka_message(_make_intraday_record(f"TICK{i}"))
            processor.add_message(msg)

        assert processor.buffer_size == 3


class TestShouldFlush:
    """Tests for MessageProcessor.should_flush."""

    def test_should_flush_false_when_empty(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=mock_batch_writer)
        assert processor.should_flush() is False

    def test_should_flush_true_at_batch_size(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=3, batch_timeout_ms=60000, writer=mock_batch_writer)
        for i in range(3):
            msg = _make_kafka_message(_make_intraday_record(f"TICK{i}"))
            processor.add_message(msg)

        assert processor.should_flush() is True

    def test_should_flush_false_below_batch_size(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=5, batch_timeout_ms=60000, writer=mock_batch_writer)
        for i in range(3):
            msg = _make_kafka_message(_make_intraday_record(f"TICK{i}"))
            processor.add_message(msg)

        assert processor.should_flush() is False

    def test_should_flush_true_at_timeout(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        # Start with monotonic returning 0.0, then advance past timeout
        with patch("consumer.processor.time") as mock_time:
            mock_time.monotonic.return_value = 0.0
            processor = MessageProcessor(batch_size=100, batch_timeout_ms=100, writer=mock_batch_writer)

            msg = _make_kafka_message(_make_intraday_record())
            processor.add_message(msg)

            # Advance time past timeout (100ms = 0.1s)
            mock_time.monotonic.return_value = 0.2
            assert processor.should_flush() is True


class TestFlush:
    """Tests for MessageProcessor.flush."""

    def test_flush_routes_intraday_to_writer(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=mock_batch_writer)
        for i in range(3):
            msg = _make_kafka_message(_make_intraday_record(f"TICK{i}"))
            processor.add_message(msg)

        processor.flush()

        mock_batch_writer.upsert_intraday_batch.assert_called_once()
        records = mock_batch_writer.upsert_intraday_batch.call_args[0][0]
        assert len(records) == 3
        assert all(r["fetch_mode"] == "intraday" for r in records)

    def test_flush_routes_historical_to_writer(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=mock_batch_writer)
        for i in range(3):
            msg = _make_kafka_message(_make_historical_record(f"TICK{i}"), topic="historical-data")
            processor.add_message(msg)

        processor.flush()

        mock_batch_writer.upsert_daily_batch.assert_called_once()
        records = mock_batch_writer.upsert_daily_batch.call_args[0][0]
        assert len(records) == 3
        assert all(r["fetch_mode"] == "historical" for r in records)

    def test_flush_routes_mixed_batch(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=mock_batch_writer)

        # Add 2 intraday + 2 historical
        for i in range(2):
            msg = _make_kafka_message(_make_intraday_record(f"INT{i}"))
            processor.add_message(msg)
        for i in range(2):
            msg = _make_kafka_message(_make_historical_record(f"HIST{i}"), topic="historical-data")
            processor.add_message(msg)

        processor.flush()

        mock_batch_writer.upsert_intraday_batch.assert_called_once()
        mock_batch_writer.upsert_daily_batch.assert_called_once()
        intraday_records = mock_batch_writer.upsert_intraday_batch.call_args[0][0]
        daily_records = mock_batch_writer.upsert_daily_batch.call_args[0][0]
        assert len(intraday_records) == 2
        assert len(daily_records) == 2

    def test_flush_clears_buffer(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=mock_batch_writer)
        msg = _make_kafka_message(_make_intraday_record())
        processor.add_message(msg)

        processor.flush()

        assert processor.buffer_size == 0

    def test_flush_resets_batch_timer(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        with patch("consumer.processor.time") as mock_time:
            mock_time.monotonic.return_value = 0.0
            processor = MessageProcessor(batch_size=100, batch_timeout_ms=100, writer=mock_batch_writer)

            msg = _make_kafka_message(_make_intraday_record())
            processor.add_message(msg)

            # Flush at time 0.2
            mock_time.monotonic.return_value = 0.2
            processor.flush()

            # Add new message after flush — timer should have been reset to 0.2
            msg2 = _make_kafka_message(_make_intraday_record("MSFT"))
            processor.add_message(msg2)

            # At time 0.25 (50ms after flush), should NOT flush yet (timeout=100ms)
            mock_time.monotonic.return_value = 0.25
            assert processor.should_flush() is False

    def test_flush_empty_buffer_returns_zero(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=mock_batch_writer)
        result = processor.flush()

        assert result == 0
        mock_batch_writer.upsert_intraday_batch.assert_not_called()
        mock_batch_writer.upsert_daily_batch.assert_not_called()

    def test_flush_returns_total_count(self, mock_batch_writer):
        from consumer.processor import MessageProcessor

        mock_batch_writer.upsert_intraday_batch.return_value = 3
        mock_batch_writer.upsert_daily_batch.return_value = 2

        processor = MessageProcessor(batch_size=100, batch_timeout_ms=5000, writer=mock_batch_writer)

        for i in range(3):
            msg = _make_kafka_message(_make_intraday_record(f"INT{i}"))
            processor.add_message(msg)
        for i in range(2):
            msg = _make_kafka_message(_make_historical_record(f"HIST{i}"), topic="historical-data")
            processor.add_message(msg)

        result = processor.flush()
        assert result == 5
