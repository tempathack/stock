"""Kafka producer service for publishing OHLCV data to topics."""
from __future__ import annotations

import json
from collections import defaultdict

from confluent_kafka import Producer

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class OHLCVProducer:
    """Publishes validated OHLCV records to Kafka topics based on fetch_mode.

    Args:
        producer: Optional confluent_kafka.Producer instance for dependency
            injection (testing). If None, a real producer is created using
            settings.KAFKA_BOOTSTRAP_SERVERS.
    """

    def __init__(self, producer: Producer | None = None) -> None:
        if producer is not None:
            self._producer = producer
        else:
            self._producer = Producer({
                "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                "acks": "all",
                "retries": 3,
                "retry.backoff.ms": 100,
                "linger.ms": 5,
                "batch.num.messages": 100,
            })
        self._intraday_topic = settings.INTRADAY_TOPIC
        self._historical_topic = settings.HISTORICAL_TOPIC

    def _delivery_report(self, err: object, msg: object) -> None:
        """Kafka delivery callback. Logs errors but never raises."""
        if err is not None:
            logger.error(
                "kafka_delivery_failed",
                error=str(err),
                topic=msg.topic(),
            )
        else:
            logger.debug(
                "kafka_delivery_ok",
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset(),
            )

    def _get_topic(self, fetch_mode: str) -> str:
        """Return the Kafka topic name for the given fetch_mode."""
        if fetch_mode == "intraday":
            return self._intraday_topic
        return self._historical_topic

    def produce_records(self, records: list[dict]) -> int:
        """Produce OHLCV records to Kafka, grouped by ticker.

        Args:
            records: List of OHLCV record dicts. Each must contain at minimum
                ``ticker`` and ``fetch_mode`` keys.

        Returns:
            Total number of records produced.
        """
        if not records:
            return 0

        # Group records by ticker for batched flush
        by_ticker: dict[str, list[dict]] = defaultdict(list)
        for record in records:
            by_ticker[record["ticker"]].append(record)

        total = 0
        for ticker, ticker_records in by_ticker.items():
            for record in ticker_records:
                topic = self._get_topic(record["fetch_mode"])
                key = record["ticker"].encode("utf-8")
                value = json.dumps(record).encode("utf-8")
                self._producer.produce(
                    topic=topic,
                    key=key,
                    value=value,
                    callback=self._delivery_report,
                )
                total += 1

            self._producer.flush(timeout=30)
            logger.info(
                "batch_produced",
                ticker=ticker,
                count=len(ticker_records),
            )

        return total

    def flush(self, timeout: float = 30) -> None:
        """Flush pending messages to Kafka.

        Args:
            timeout: Maximum time in seconds to wait for flush to complete.
        """
        self._producer.flush(timeout=timeout)
