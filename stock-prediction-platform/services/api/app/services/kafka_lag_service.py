"""Confluent-Kafka AdminClient wrapped in run_in_executor for async safety."""
from __future__ import annotations

import asyncio
import datetime

from confluent_kafka import Consumer, KafkaException, TopicPartition
from confluent_kafka.admin import AdminClient

from app.config import settings
from app.models.schemas import KafkaPartitionLag, KafkaLagResponse

PROCESSED_FEATURES_TOPIC = "processed-features"


def _sync_get_kafka_lag() -> KafkaLagResponse:
    """Synchronous kafka lag computation — must be called via run_in_executor."""
    now_iso = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    consumer_group = settings.KAFKA_CONSUMER_GROUP

    try:
        admin = AdminClient({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
        # Get cluster metadata to discover partition count
        meta = admin.list_topics(topic=PROCESSED_FEATURES_TOPIC, timeout=5)
        topic_meta = meta.topics.get(PROCESSED_FEATURES_TOPIC)
        if topic_meta is None or topic_meta.error:
            return KafkaLagResponse(
                topic=PROCESSED_FEATURES_TOPIC,
                consumer_group=consumer_group,
                partitions=[],
                total_lag=0,
                sampled_at=now_iso,
            )

        partition_ids = list(topic_meta.partitions.keys())
        tps = [TopicPartition(PROCESSED_FEATURES_TOPIC, pid) for pid in partition_ids]

        # Get committed offsets for consumer group
        consumer = Consumer({
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": consumer_group,
        })
        committed = consumer.committed(tps, timeout=5)
        consumer.close()

        # Get end (high watermark) offsets using Consumer.get_watermark_offsets
        result_partitions: list[KafkaPartitionLag] = []
        total_lag = 0
        for tp in committed:
            consumer2 = Consumer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS, "group.id": "_lag_probe"})
            low_off, high_off = consumer2.get_watermark_offsets(tp, timeout=5)
            consumer2.close()

            committed_off = tp.offset if tp.offset >= 0 else low_off
            lag = max(0, high_off - committed_off)
            total_lag += lag
            result_partitions.append(KafkaPartitionLag(
                partition=tp.partition,
                current_offset=committed_off,
                end_offset=high_off,
                lag=lag,
            ))

        return KafkaLagResponse(
            topic=PROCESSED_FEATURES_TOPIC,
            consumer_group=consumer_group,
            partitions=result_partitions,
            total_lag=total_lag,
            sampled_at=now_iso,
        )
    except Exception:
        return KafkaLagResponse(
            topic=PROCESSED_FEATURES_TOPIC,
            consumer_group=consumer_group,
            partitions=[],
            total_lag=0,
            sampled_at=now_iso,
        )


async def get_kafka_lag() -> KafkaLagResponse:
    """Async wrapper — runs synchronous AdminClient in thread executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_get_kafka_lag)
