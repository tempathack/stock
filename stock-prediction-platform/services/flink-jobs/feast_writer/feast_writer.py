"""Feast Writer — PyFlink DataStream job.

Consumes the processed-features Kafka topic (written by indicator_stream) and
pushes EMA-20, RSI-14, and MACD signal values to the Feast Redis online store
using store.push() with PushMode.ONLINE.

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
    """Push a batch of indicator records to the Feast Redis online store.

    This function is importable by tests (no pyflink dependency at this level).

    Args:
        records: List of dicts with keys: ticker, timestamp, ema_20, rsi_14, macd_signal.
        store_path: Path to the Feast feature_store.yaml directory.
    """
    if not records:
        return

    store = FeatureStore(repo_path=store_path)
    df = pd.DataFrame(records)
    df["event_timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    store.push(
        push_source_name="technical_indicators_push",
        df=df[["ticker", "event_timestamp", "ema_20", "rsi_14", "macd_signal"]],
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
    # Source: processed-features Kafka topic (output of indicator_stream job)
    # ---------------------------------------------------------------------------
    kafka_source = (
        KafkaSource.builder()
        .set_bootstrap_servers(KAFKA_BOOTSTRAP_SERVERS)
        .set_topics("processed-features")
        .set_group_id("flink-feast-writer")
        .set_starting_offsets(KafkaOffsetsInitializer.latest())
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    ds = env.from_source(
        kafka_source,
        WatermarkStrategy.no_watermarks(),
        "processed-features-kafka",
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

        def map(self, value: str) -> str:
            try:
                record = json.loads(value)
                push_batch_to_feast([record], store_path=self._store_path)
            except Exception as exc:
                # Log and continue — do not crash the job on a bad record
                print(f"[FeastPushMap] Failed to push record: {exc}", flush=True)
            return value

    ds.map(FeastPushMap(FEAST_STORE_PATH)).print()
    env.execute("feast-writer-job")


if __name__ == "__main__":
    main()
