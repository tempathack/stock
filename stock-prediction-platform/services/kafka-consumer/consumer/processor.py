"""Message processor — micro-batch assembly and validation."""

from __future__ import annotations

import json
import time

from consumer.db_writer import BatchWriter
from consumer.logging import get_logger
from consumer.metrics import messages_consumed_total

logger = get_logger(__name__)


class MessageProcessor:
    """Accumulates Kafka messages into micro-batches and routes to BatchWriter."""

    def __init__(self, batch_size: int, batch_timeout_ms: int, writer: BatchWriter):
        self._buffer: list[dict] = []
        self._batch_size = batch_size
        self._batch_timeout_ms = batch_timeout_ms
        self._writer = writer
        self._batch_start: float = time.monotonic()

    def add_message(self, msg) -> None:
        """Deserialize a Kafka message and add to the batch buffer."""
        record = json.loads(msg.value().decode("utf-8"))
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
            count += self._writer.upsert_intraday_batch(intraday)
        if daily:
            count += self._writer.upsert_daily_batch(daily)

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
