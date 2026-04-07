"""Kafka consumer entry point — connects to broker and dispatches messages."""

from __future__ import annotations

import signal

from confluent_kafka import Consumer, KafkaError, Producer

from consumer.config import settings
from consumer.db_writer import BatchWriter
from consumer.logging import get_logger, setup_logging
from consumer.metrics import consumer_lag, start_metrics_server
from consumer.processor import MessageProcessor

logger = get_logger(__name__)

_running = True


def _shutdown_handler(signum, frame):
    """Handle SIGTERM/SIGINT for graceful K8s pod shutdown."""
    global _running
    logger.info("shutdown_signal_received", signal=signum)
    _running = False


def run_consumer(consumer=None, writer=None, processor=None) -> None:
    """Run the Kafka consumer loop.

    Accepts optional DI parameters for testing. If not provided, creates real instances.
    """
    global _running
    _running = True

    setup_logging(settings.LOG_LEVEL)

    signal.signal(signal.SIGTERM, _shutdown_handler)
    signal.signal(signal.SIGINT, _shutdown_handler)

    # Start Prometheus metrics server
    start_metrics_server(9090)
    logger.info("metrics_server_started", port=9090)

    if consumer is None:
        consumer = Consumer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": settings.KAFKA_GROUP_ID,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })

    if writer is None:
        writer = BatchWriter()

    dlq_producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})

    if processor is None:
        processor = MessageProcessor(
            batch_size=settings.BATCH_SIZE,
            batch_timeout_ms=settings.BATCH_TIMEOUT_MS,
            writer=writer,
            dlq_producer=dlq_producer,
        )

    topics = [settings.INTRADAY_TOPIC, settings.HISTORICAL_TOPIC]
    consumer.subscribe(topics)
    logger.info("consumer_started", topics=topics, group_id=settings.KAFKA_GROUP_ID)

    try:
        while _running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                if processor.should_flush():
                    processor.flush()
                    consumer.commit(asynchronous=False)
                    _update_consumer_lag(consumer)
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("consumer_error", error=str(msg.error()))
                continue

            processor.add_message(msg)

            if processor.should_flush():
                processor.flush()
                consumer.commit(asynchronous=False)
                _update_consumer_lag(consumer)

    except Exception:
        logger.exception("consumer_fatal_error")
    finally:
        if processor.buffer_size > 0:
            logger.info("flushing_pending_records", count=processor.buffer_size)
            try:
                processor.flush()
                consumer.commit(asynchronous=False)
            except Exception:
                logger.exception("flush_on_shutdown_failed")

        consumer.close()
        writer.close()
        logger.info("consumer_stopped")


def _update_consumer_lag(kafka_consumer) -> None:
    """Update consumer_lag gauge from current partition assignments."""
    try:
        partitions = kafka_consumer.assignment()
        for tp in partitions:
            _, high = kafka_consumer.get_watermark_offsets(tp)
            committed_list = kafka_consumer.committed([tp])
            offset = (
                committed_list[0].offset
                if committed_list[0] and committed_list[0].offset >= 0
                else 0
            )
            lag = max(0, high - offset)
            consumer_lag.labels(topic=tp.topic, partition=str(tp.partition)).set(lag)
    except Exception:
        pass  # Partition not yet assigned or broker unavailable


if __name__ == "__main__":
    run_consumer()
