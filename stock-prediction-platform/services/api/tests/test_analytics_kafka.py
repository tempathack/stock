"""Unit tests for kafka_lag_service."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from app.services.kafka_lag_service import _sync_get_kafka_lag

def test_sync_get_kafka_lag_success():
    mock_partition = MagicMock()
    mock_partition.partition = 0

    mock_topic_meta = MagicMock()
    mock_topic_meta.error = None
    mock_topic_meta.partitions = {0: mock_partition}

    mock_meta = MagicMock()
    mock_meta.topics = {"processed-features": mock_topic_meta}

    mock_admin = MagicMock()
    mock_admin.list_topics.return_value = mock_meta

    mock_tp = MagicMock()
    mock_tp.partition = 0
    mock_tp.offset = 95

    mock_consumer = MagicMock()
    mock_consumer.committed.return_value = [mock_tp]
    mock_consumer.get_watermark_offsets.return_value = (0, 100)

    with patch("app.services.kafka_lag_service.AdminClient", return_value=mock_admin), \
         patch("app.services.kafka_lag_service.Consumer", return_value=mock_consumer):
        result = _sync_get_kafka_lag()

    assert result.total_lag == 5
    assert len(result.partitions) == 1
    assert result.partitions[0].lag == 5

def test_sync_get_kafka_lag_unreachable():
    from confluent_kafka import KafkaException
    with patch("app.services.kafka_lag_service.AdminClient", side_effect=KafkaException("fail")):
        result = _sync_get_kafka_lag()
    assert result.total_lag == 0
    assert result.partitions == []
