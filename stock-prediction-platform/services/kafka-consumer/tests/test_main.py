"""Unit tests for consumer main.py: subscription, processing, shutdown, error handling."""
from __future__ import annotations

import signal
import threading
import os
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from tests.conftest import _make_kafka_message, _make_intraday_record


def _make_error_message(error_code):
    """Create a mock Kafka message with an error."""
    msg = MagicMock()
    error = MagicMock()
    error.code.return_value = error_code
    msg.error.return_value = error
    return msg


class TestConsumerSubscription:
    """Tests for consumer topic subscription and config (CONS-01)."""

    def test_consumer_subscribes_to_both_topics(self):
        from consumer.main import run_consumer
        import consumer.main as main_module

        mock_consumer = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_processor = MagicMock()
        mock_processor.buffer_size = 0
        mock_processor.should_flush.return_value = False

        # Return None once then stop the loop
        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                main_module._running = False
            return None

        mock_consumer.poll.side_effect = poll_side_effect

        run_consumer(consumer=mock_consumer, writer=mock_writer, processor=mock_processor)

        mock_consumer.subscribe.assert_called_once()
        topics = mock_consumer.subscribe.call_args[0][0]
        assert "intraday-data" in topics
        assert "historical-data" in topics

    def test_consumer_uses_correct_config(self):
        """When no consumer is injected, it should be created with correct config."""
        from consumer.main import run_consumer
        import consumer.main as main_module

        with patch("consumer.main.Consumer") as MockConsumer:
            mock_instance = MagicMock()
            MockConsumer.return_value = mock_instance
            mock_instance.poll.return_value = None

            mock_writer = MagicMock()
            mock_writer.close = MagicMock()
            mock_processor = MagicMock()
            mock_processor.buffer_size = 0
            mock_processor.should_flush.return_value = False

            call_count = 0

            def poll_side_effect(timeout=1.0):
                nonlocal call_count
                call_count += 1
                if call_count >= 2:
                    main_module._running = False
                return None

            mock_instance.poll.side_effect = poll_side_effect

            run_consumer(writer=mock_writer, processor=mock_processor)

            config = MockConsumer.call_args[0][0]
            assert config["group.id"] == "stock-consumer-group"
            assert config["enable.auto.commit"] is False
            assert config["auto.offset.reset"] == "earliest"


class TestConsumerProcessing:
    """Tests for message polling and processing (CONS-02)."""

    def test_consumer_polls_messages(self):
        from consumer.main import run_consumer
        import consumer.main as main_module

        mock_consumer = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_processor = MagicMock()
        mock_processor.buffer_size = 0
        mock_processor.should_flush.return_value = False

        msg = _make_kafka_message(_make_intraday_record())

        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return msg
            main_module._running = False
            return None

        mock_consumer.poll.side_effect = poll_side_effect

        run_consumer(consumer=mock_consumer, writer=mock_writer, processor=mock_processor)

        mock_processor.add_message.assert_called_once_with(msg)

    def test_consumer_commits_after_flush(self):
        from consumer.main import run_consumer
        import consumer.main as main_module

        mock_consumer = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_processor = MagicMock()
        mock_processor.buffer_size = 0

        msg = _make_kafka_message(_make_intraday_record())

        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return msg
            main_module._running = False
            return None

        mock_consumer.poll.side_effect = poll_side_effect
        mock_processor.should_flush.return_value = True
        mock_processor.flush.return_value = 1

        run_consumer(consumer=mock_consumer, writer=mock_writer, processor=mock_processor)

        mock_processor.flush.assert_called()
        mock_consumer.commit.assert_called_with(asynchronous=False)

    def test_consumer_handles_none_message(self):
        from consumer.main import run_consumer
        import consumer.main as main_module

        mock_consumer = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_processor = MagicMock()
        mock_processor.buffer_size = 0
        mock_processor.should_flush.return_value = False

        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                main_module._running = False
            return None

        mock_consumer.poll.side_effect = poll_side_effect

        run_consumer(consumer=mock_consumer, writer=mock_writer, processor=mock_processor)

        mock_processor.add_message.assert_not_called()


class TestConsumerErrorHandling:
    """Tests for error handling."""

    def test_consumer_handles_partition_eof(self):
        from consumer.main import run_consumer
        from confluent_kafka import KafkaError
        import consumer.main as main_module

        mock_consumer = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_processor = MagicMock()
        mock_processor.buffer_size = 0
        mock_processor.should_flush.return_value = False

        eof_msg = _make_error_message(KafkaError._PARTITION_EOF)

        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return eof_msg
            main_module._running = False
            return None

        mock_consumer.poll.side_effect = poll_side_effect

        # Should not raise
        run_consumer(consumer=mock_consumer, writer=mock_writer, processor=mock_processor)

        mock_processor.add_message.assert_not_called()

    def test_consumer_handles_broker_error(self):
        from consumer.main import run_consumer
        from confluent_kafka import KafkaError
        import consumer.main as main_module

        mock_consumer = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_processor = MagicMock()
        mock_processor.buffer_size = 0
        mock_processor.should_flush.return_value = False

        # Use a non-EOF error code
        error_msg = _make_error_message(KafkaError._ALL_BROKERS_DOWN)

        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return error_msg
            main_module._running = False
            return None

        mock_consumer.poll.side_effect = poll_side_effect

        # Should not raise — error is logged and loop continues
        run_consumer(consumer=mock_consumer, writer=mock_writer, processor=mock_processor)

        mock_processor.add_message.assert_not_called()


class TestGracefulShutdown:
    """Tests for SIGTERM/SIGINT graceful shutdown."""

    def test_graceful_shutdown_flushes_pending(self):
        from consumer.main import run_consumer
        import consumer.main as main_module

        mock_consumer = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_processor = MagicMock()
        mock_processor.should_flush.return_value = False
        # Simulate pending records in buffer
        type(mock_processor).buffer_size = PropertyMock(return_value=5)
        mock_processor.flush.return_value = 5

        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                main_module._running = False
            return None

        mock_consumer.poll.side_effect = poll_side_effect

        run_consumer(consumer=mock_consumer, writer=mock_writer, processor=mock_processor)

        # Flush should be called in the finally block due to pending records
        mock_processor.flush.assert_called()

    def test_graceful_shutdown_closes_consumer(self):
        from consumer.main import run_consumer
        import consumer.main as main_module

        mock_consumer = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_processor = MagicMock()
        mock_processor.buffer_size = 0
        mock_processor.should_flush.return_value = False

        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                main_module._running = False
            return None

        mock_consumer.poll.side_effect = poll_side_effect

        run_consumer(consumer=mock_consumer, writer=mock_writer, processor=mock_processor)

        mock_consumer.close.assert_called_once()

    def test_graceful_shutdown_closes_db_writer(self):
        from consumer.main import run_consumer
        import consumer.main as main_module

        mock_consumer = MagicMock()
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_processor = MagicMock()
        mock_processor.buffer_size = 0
        mock_processor.should_flush.return_value = False

        call_count = 0

        def poll_side_effect(timeout=1.0):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                main_module._running = False
            return None

        mock_consumer.poll.side_effect = poll_side_effect

        run_consumer(consumer=mock_consumer, writer=mock_writer, processor=mock_processor)

        mock_writer.close.assert_called_once()

    def test_shutdown_handler_sets_running_false(self):
        import consumer.main as main_module

        main_module._running = True
        main_module._shutdown_handler(signal.SIGTERM, None)
        assert main_module._running is False


class TestConsumerSettingsDefaults:
    """Tests for ConsumerSettings env var defaults (FIX-KAFKA)."""

    def test_default_kafka_broker_is_docker_compose_name(self, monkeypatch):
        """Default must be kafka:9092 — the docker-compose service name."""
        monkeypatch.delenv("KAFKA_BOOTSTRAP_SERVERS", raising=False)
        # Re-instantiate to pick up cleared env
        from consumer.config import ConsumerSettings
        s = ConsumerSettings()
        assert s.KAFKA_BOOTSTRAP_SERVERS == "kafka:9092"

    def test_kafka_broker_overridable_by_env(self, monkeypatch):
        """Env var takes priority over code default."""
        monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "broker-host:9092")
        from consumer.config import ConsumerSettings
        s = ConsumerSettings()
        assert s.KAFKA_BOOTSTRAP_SERVERS == "broker-host:9092"

    def test_database_url_default_is_empty(self, monkeypatch):
        """DATABASE_URL empty string default is unchanged."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        from consumer.config import ConsumerSettings
        s = ConsumerSettings()
        assert s.DATABASE_URL == ""
