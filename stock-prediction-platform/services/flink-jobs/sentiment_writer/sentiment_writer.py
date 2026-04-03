"""Sentiment Writer — PyFlink DataStream job.

Consumes the sentiment-aggregated Kafka topic (written by sentiment_stream) and
pushes avg_sentiment, mention_count, positive_ratio, negative_ratio, top_subreddit
values to the Feast Redis online store using store.push() with PushMode.ONLINE
via the reddit_sentiment_push PushSource.

The push function is defined at module level so that unit tests can import and
test it directly without a Flink or Feast runtime.

Environment variables:
    KAFKA_BOOTSTRAP_SERVERS  - e.g. kafka-kafka-bootstrap.storage.svc.cluster.local:9092
    FEAST_STORE_PATH         - path to feature_store.yaml directory (default /opt/feast)
                               # At runtime, mounted via ConfigMap volume or init container
                               # containing feature_store.yaml + registry.db

Feature store config (mounted at /opt/feast/):
    feature_store.yaml       - Feast registry/online-store config pointing to Redis
"""
import json
import os

import pandas as pd

from feast import FeatureStore
from feast.data_source import PushMode


def push_batch_to_feast(
    records: list[dict],
    store_path: str = "/opt/feast",
) -> None:
    """Push a batch of sentiment records to the Feast Redis online store.

    This function is importable by tests (no pyflink dependency at this level).

    Args:
        records: List of dicts with keys: ticker, event_timestamp, avg_sentiment,
                 mention_count, positive_ratio, negative_ratio, top_subreddit.
        store_path: Path to the Feast feature_store.yaml directory.
    """
    if not records:
        return

    store = FeatureStore(repo_path=store_path)
    df = pd.DataFrame(records)
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], utc=True)

    store.push(
        push_source_name="reddit_sentiment_push",
        df=df[["ticker", "event_timestamp", "avg_sentiment", "mention_count",
               "positive_ratio", "negative_ratio", "top_subreddit"]],
        to=PushMode.ONLINE,
    )


def main() -> None:
    """Entry point for the PyFlink DataStream job."""
    from pyflink.datastream import StreamExecutionEnvironment
    from pyflink.datastream.connectors.kafka import (
        KafkaSource,
        KafkaOffsetsInitializer,
    )
    from pyflink.common.serialization import SimpleStringSchema
    from pyflink.common import WatermarkStrategy
    from pyflink.datastream.functions import MapFunction

    KAFKA_BOOTSTRAP_SERVERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
    FEAST_STORE_PATH = os.environ.get("FEAST_STORE_PATH", "/opt/feast")

    env = StreamExecutionEnvironment.get_execution_environment()

    # ---------------------------------------------------------------------------
    # Source: sentiment-aggregated Kafka topic (output of sentiment_stream job)
    # ---------------------------------------------------------------------------
    kafka_source = (
        KafkaSource.builder()
        .set_bootstrap_servers(KAFKA_BOOTSTRAP_SERVERS)
        .set_topics("sentiment-aggregated")
        .set_group_id("flink-sentiment-writer")
        .set_starting_offsets(KafkaOffsetsInitializer.latest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    ds = env.from_source(
        kafka_source,
        WatermarkStrategy.no_watermarks(),
        "sentiment-aggregated-kafka",
    )

    # ---------------------------------------------------------------------------
    # Sink: push each record to Feast Redis online store.
    # MapFunction is used as a side-effecting sink — SinkFunction in PyFlink 1.19
    # wraps a Java interface and cannot be subclassed directly in Python.
    # ---------------------------------------------------------------------------
    class FeastPushMap(MapFunction):
        """MapFunction that pushes to Feast as a side effect and passes value through."""

        def __init__(self, feast_store_path: str):
            self._store_path = feast_store_path
            self._store = None  # Lazily initialized in open() — one instance per task

        def open(self, runtime_context) -> None:
            """Initialize the FeatureStore once per task instance (not per record)."""
            self._store = FeatureStore(repo_path=self._store_path)

        def map(self, value: str) -> str:
            try:
                record = json.loads(value)
                if not record:
                    return value
                df = pd.DataFrame([record])
                df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], utc=True)
                self._store.push(
                    push_source_name="reddit_sentiment_push",
                    df=df[["ticker", "event_timestamp", "avg_sentiment", "mention_count",
                            "positive_ratio", "negative_ratio", "top_subreddit"]],
                    to=PushMode.ONLINE,
                )
            except Exception as exc:
                # Log and continue — do not crash the job on a bad record
                print(f"[FeastPushMap] Failed to push record: {exc}", flush=True)
            return value

    ds.map(FeastPushMap(FEAST_STORE_PATH)).print()
    env.execute("sentiment-writer-job")


if __name__ == "__main__":
    main()
