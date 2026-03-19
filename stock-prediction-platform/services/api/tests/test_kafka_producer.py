"""Tests for the Kafka producer service (INGEST-03)."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from app.services.kafka_producer import OHLCVProducer


def _make_record(ticker="AAPL", fetch_mode="intraday"):
    """Factory helper for OHLCV record dicts."""
    return {
        "ticker": ticker,
        "timestamp": "2026-03-19T14:30:00+00:00",
        "open": 172.50,
        "high": 173.20,
        "low": 172.10,
        "close": 172.80,
        "volume": 1234567,
        "fetch_mode": fetch_mode,
        "ingested_at": "2026-03-19T15:01:00+00:00",
    }


# ---------------------------------------------------------------------------
# Topic routing tests
# ---------------------------------------------------------------------------


def test_produce_intraday_routes_to_intraday_topic(mock_kafka_producer):
    """Intraday records are produced to the intraday-data topic."""
    producer = OHLCVProducer(producer=mock_kafka_producer)
    records = [_make_record(fetch_mode="intraday")]
    producer.produce_records(records)

    call_kwargs = mock_kafka_producer.produce.call_args
    assert call_kwargs.kwargs.get("topic") or call_kwargs[1].get("topic") == "intraday-data"
    # More robust check
    mock_kafka_producer.produce.assert_called_once()
    args, kwargs = mock_kafka_producer.produce.call_args
    assert kwargs["topic"] == "intraday-data"


def test_produce_historical_routes_to_historical_topic(mock_kafka_producer):
    """Historical records are produced to the historical-data topic."""
    producer = OHLCVProducer(producer=mock_kafka_producer)
    records = [_make_record(fetch_mode="historical")]
    producer.produce_records(records)

    mock_kafka_producer.produce.assert_called_once()
    _, kwargs = mock_kafka_producer.produce.call_args
    assert kwargs["topic"] == "historical-data"


# ---------------------------------------------------------------------------
# Message schema tests
# ---------------------------------------------------------------------------


def test_message_key_is_ticker_bytes(mock_kafka_producer):
    """Message key is the ticker string encoded as UTF-8 bytes."""
    producer = OHLCVProducer(producer=mock_kafka_producer)
    records = [_make_record(ticker="AAPL")]
    producer.produce_records(records)

    _, kwargs = mock_kafka_producer.produce.call_args
    assert kwargs["key"] == b"AAPL"


def test_message_value_is_json_bytes(mock_kafka_producer):
    """Message value is JSON-serialized record with all expected keys."""
    producer = OHLCVProducer(producer=mock_kafka_producer)
    records = [_make_record()]
    producer.produce_records(records)

    _, kwargs = mock_kafka_producer.produce.call_args
    value = json.loads(kwargs["value"])
    expected_keys = {
        "ticker", "timestamp", "open", "high", "low",
        "close", "volume", "fetch_mode", "ingested_at",
    }
    assert set(value.keys()) == expected_keys


def test_message_value_has_correct_types(mock_kafka_producer):
    """Deserialized value has correct Python types for each field."""
    producer = OHLCVProducer(producer=mock_kafka_producer)
    records = [_make_record()]
    producer.produce_records(records)

    _, kwargs = mock_kafka_producer.produce.call_args
    value = json.loads(kwargs["value"])
    assert isinstance(value["ticker"], str)
    assert isinstance(value["open"], float)
    assert isinstance(value["high"], float)
    assert isinstance(value["low"], float)
    assert isinstance(value["close"], float)
    assert isinstance(value["volume"], int)
    assert isinstance(value["fetch_mode"], str)


# ---------------------------------------------------------------------------
# Flush behavior tests
# ---------------------------------------------------------------------------


def test_flush_called_after_produce(mock_kafka_producer):
    """flush(timeout=30) is called after producing records."""
    producer = OHLCVProducer(producer=mock_kafka_producer)
    records = [_make_record()]
    producer.produce_records(records)

    mock_kafka_producer.flush.assert_called()
    _, kwargs = mock_kafka_producer.flush.call_args
    assert kwargs.get("timeout") == 30 or (mock_kafka_producer.flush.call_args[0] and mock_kafka_producer.flush.call_args[0][0] == 30)


# ---------------------------------------------------------------------------
# Delivery callback tests
# ---------------------------------------------------------------------------


def test_delivery_callback_logs_error_on_failure(mock_kafka_producer):
    """Delivery callback handles error without raising exception."""
    producer = OHLCVProducer(producer=mock_kafka_producer)

    mock_err = MagicMock()
    mock_err.__str__ = lambda self: "Broker unavailable"
    mock_msg = MagicMock()
    mock_msg.topic.return_value = "intraday-data"

    # Should not raise
    producer._delivery_report(mock_err, mock_msg)


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------


def test_produce_empty_records_no_error(mock_kafka_producer):
    """Empty record list produces nothing and raises no error."""
    producer = OHLCVProducer(producer=mock_kafka_producer)
    result = producer.produce_records([])

    mock_kafka_producer.produce.assert_not_called()
    assert result == 0


def test_produce_mixed_modes_routes_correctly(mock_kafka_producer):
    """Mixed intraday and historical records route to correct topics."""
    producer = OHLCVProducer(producer=mock_kafka_producer)
    records = [
        _make_record(ticker="AAPL", fetch_mode="intraday"),
        _make_record(ticker="AAPL", fetch_mode="historical"),
    ]
    producer.produce_records(records)

    assert mock_kafka_producer.produce.call_count == 2
    calls = mock_kafka_producer.produce.call_args_list
    topics = [c.kwargs["topic"] for c in calls]
    assert "intraday-data" in topics
    assert "historical-data" in topics


# ---------------------------------------------------------------------------
# Constructor test
# ---------------------------------------------------------------------------


@patch("app.services.kafka_producer.Producer")
def test_producer_uses_settings_bootstrap_servers(mock_producer_cls):
    """Default constructor creates Producer with bootstrap.servers from settings."""
    from app.config import settings

    OHLCVProducer()
    mock_producer_cls.assert_called_once()
    config = mock_producer_cls.call_args[0][0]
    assert config["bootstrap.servers"] == settings.KAFKA_BOOTSTRAP_SERVERS
