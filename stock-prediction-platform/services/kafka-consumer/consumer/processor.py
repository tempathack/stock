"""Message processor — micro-batch assembly and validation."""

from __future__ import annotations

import json
import time
from typing import Any

from consumer.db_writer import BatchWriter
from consumer.logging import get_logger
from consumer.metrics import dlq_messages_total, messages_consumed_total

logger = get_logger(__name__)


class MessageProcessor:
    """Accumulates Kafka messages into micro-batches and routes to BatchWriter."""

    def __init__(
        self,
        batch_size: int,
        batch_timeout_ms: int,
        writer: BatchWriter,
        dlq_producer: Any = None,
    ):
        self._buffer: list[dict] = []
        self._batch_size = batch_size
        self._batch_timeout_ms = batch_timeout_ms
        self._writer = writer
        self._dlq_producer = dlq_producer
        self._batch_start: float = time.monotonic()

    def _send_to_dlq(self, msg, reason: str) -> None:
        """Produce the raw message bytes to the DLQ topic for the source topic."""
        if self._dlq_producer is None:
            return
        dlq_topic = f"{msg.topic()}-dlq"
        try:
            self._dlq_producer.produce(
                topic=dlq_topic,
                value=msg.value(),
                key=msg.key(),
            )
            self._dlq_producer.poll(0)
        except Exception:
            logger.exception("dlq_produce_failed", dlq_topic=dlq_topic)
        dlq_messages_total.labels(topic=msg.topic(), reason=reason).inc()
        logger.warning("message_routed_to_dlq", topic=msg.topic(), dlq_topic=dlq_topic, reason=reason)

    def add_message(self, msg) -> None:
        """Deserialize a Kafka message and add to the batch buffer.

        On deserialization error the raw message is routed to the DLQ topic
        (<source-topic>-dlq) via a separate producer instance.
        """
        try:
            record = json.loads(msg.value().decode("utf-8"))
        except Exception as exc:
            logger.error("deserialization_error", topic=msg.topic(), error=str(exc))
            self._send_to_dlq(msg, reason="deserialization_error")
            return
        messages_consumed_total.labels(topic=msg.topic()).inc()
        self._buffer.append(record)
        logger.debug(
            "message_added",
            ticker=record.get("ticker"),
            buffer_size=len(self._buffer),
        )

    def should_flush(self) -> bool:
        """Check whether the batch should be flushed."""
        if not self._buffer:
            return False
        if len(self._buffer) >= self._batch_size:
            return True
        elapsed_ms = (time.monotonic() - self._batch_start) * 1000
        return elapsed_ms >= self._batch_timeout_ms

    def flush(self) -> int:
        """Flush the buffer — route records to the appropriate upsert method."""
        if not self._buffer:
            return 0

        intraday = [r for r in self._buffer if r["fetch_mode"] == "intraday"]
        daily = [r for r in self._buffer if r["fetch_mode"] == "historical"]

        count = 0
        if intraday:
            try:
                count += self._writer.upsert_intraday_batch(intraday)
            except Exception as exc:
                logger.error("db_write_error", table="intraday", count=len(intraday), error=str(exc))
                dlq_messages_total.labels(topic="intraday-data", reason="db_write_error").inc(len(intraday))
        if daily:
            try:
                count += self._writer.upsert_daily_batch(daily)
            except Exception as exc:
                logger.error("db_write_error", table="daily", count=len(daily), error=str(exc))
                dlq_messages_total.labels(topic="historical-data", reason="db_write_error").inc(len(daily))

        logger.info(
            "batch_flushed",
            intraday_count=len(intraday),
            daily_count=len(daily),
            total=count,
        )

        self._buffer.clear()
        self._batch_start = time.monotonic()
        return count

    @property
    def buffer_size(self) -> int:
        """Current number of records in the buffer."""
        return len(self._buffer)
