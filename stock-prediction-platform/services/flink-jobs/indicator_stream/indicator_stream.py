"""Indicator Stream — PyFlink Table API job.

Reads intraday-data Kafka topic, computes 5-minute sliding technical
indicators (EMA-20, RSI-14, MACD signal) using HOP windows and registered
Python UDAFs, then writes results to the processed-features Kafka topic.

Window semantics: HOP(5 min slide, 20 min size) so every 5 minutes a new
20-minute window closes and emits one indicator row per ticker.

Environment variables (injected from flink-config ConfigMap + secrets):
    KAFKA_BOOTSTRAP_SERVERS  - e.g. kafka-kafka-bootstrap.storage.svc.cluster.local:9092

This module imports indicator_udaf_logic for pure Python UDAF helpers so
that unit tests can exercise those helpers without a Flink runtime.
"""
import os
import sys

# Allow running from /opt/flink/usrlib/ where both files are deployed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pyflink.table import EnvironmentSettings, TableEnvironment, DataTypes
from pyflink.table.udf import AggregateFunction, udaf

import indicator_udaf_logic  # noqa: F401  (imported for re-export to tests)
from indicator_udaf_logic import compute_rsi, compute_ema, compute_macd_signal


# ---------------------------------------------------------------------------
# UDAF definitions — accumulate close prices over the HOP window
# ---------------------------------------------------------------------------

class RsiUdaf(AggregateFunction):
    """RSI-14 UDAF: accumulates close prices, computes Wilder's RSI on flush.

    No retract() — HOP windows produce append-only output (each window is
    a distinct time range), so retraction semantics are not required.
    """

    def create_accumulator(self):
        return []

    def accumulate(self, acc, value):
        if value is not None:
            acc.append(float(value))

    def get_value(self, acc):
        return compute_rsi(acc)

    def get_accumulator_type(self):
        return DataTypes.ARRAY(DataTypes.DOUBLE())

    def get_result_type(self):
        return DataTypes.DOUBLE()


class EmaUdaf(AggregateFunction):
    """EMA-20 UDAF: accumulates close prices, computes EWM EMA on flush."""

    def create_accumulator(self):
        return []

    def accumulate(self, acc, value):
        if value is not None:
            acc.append(float(value))

    def get_value(self, acc):
        return compute_ema(acc, span=20)

    def get_accumulator_type(self):
        return DataTypes.ARRAY(DataTypes.DOUBLE())

    def get_result_type(self):
        return DataTypes.DOUBLE()


class MacdSignalUdaf(AggregateFunction):
    """MACD Signal UDAF: accumulates close prices, computes MACD signal line on flush."""

    def create_accumulator(self):
        return []

    def accumulate(self, acc, value):
        if value is not None:
            acc.append(float(value))

    def get_value(self, acc):
        return compute_macd_signal(acc)

    def get_accumulator_type(self):
        return DataTypes.ARRAY(DataTypes.DOUBLE())

    def get_result_type(self):
        return DataTypes.DOUBLE()


def main() -> None:
    KAFKA_BOOTSTRAP_SERVERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]

    t_env = TableEnvironment.create(
        EnvironmentSettings.in_streaming_mode()
    )

    # Register Python UDAFs
    t_env.create_temporary_function(
        "rsi_udaf",
        udaf(RsiUdaf(), result_type=DataTypes.DOUBLE()),
    )
    t_env.create_temporary_function(
        "ema_udaf",
        udaf(EmaUdaf(), result_type=DataTypes.DOUBLE()),
    )
    t_env.create_temporary_function(
        "macd_signal_udaf",
        udaf(MacdSignalUdaf(), result_type=DataTypes.DOUBLE()),
    )

    # ---------------------------------------------------------------------------
    # Source: intraday-data Kafka topic (same schema as OHLCV Normalizer)
    # group.id = flink-indicator-stream (separate from ohlcv-normalizer consumer)
    # ---------------------------------------------------------------------------
    t_env.execute_sql(f"""
        CREATE TABLE intraday_source (
            ticker        STRING,
            `timestamp`   TIMESTAMP_LTZ(3),
            `open`        DECIMAL(12, 4),
            high          DECIMAL(12, 4),
            low           DECIMAL(12, 4),
            `close`       DECIMAL(12, 4),
            adj_close     DECIMAL(12, 4),
            volume        BIGINT,
            vwap          DECIMAL(12, 4),
            fetch_mode    STRING,
            WATERMARK FOR `timestamp` AS `timestamp` - INTERVAL '10' SECONDS
        ) WITH (
            'connector'                     = 'kafka',
            'topic'                         = 'intraday-data',
            'properties.bootstrap.servers'  = '{KAFKA_BOOTSTRAP_SERVERS}',
            'properties.group.id'           = 'flink-indicator-stream',
            'scan.startup.mode'             = 'group-offsets',
            'properties.auto.offset.reset'  = 'latest',
            'format'                        = 'json',
            'json.ignore-parse-errors'      = 'true'
        )
    """)

    # ---------------------------------------------------------------------------
    # Sink: processed-features Kafka topic
    # ---------------------------------------------------------------------------
    # upsert-kafka is used because Python UDAFs with GROUP BY produce an
    # update changelog that append-mode kafka does not accept.
    # upsert-kafka requires a PRIMARY KEY and emits the latest value per key.
    t_env.execute_sql(f"""
        CREATE TABLE processed_features_sink (
            ticker        STRING,
            `timestamp`   TIMESTAMP(3),
            ema_20        DOUBLE,
            rsi_14        DOUBLE,
            macd_signal   DOUBLE,
            PRIMARY KEY (ticker, `timestamp`) NOT ENFORCED
        ) WITH (
            'connector'                     = 'upsert-kafka',
            'topic'                         = 'processed-features',
            'properties.bootstrap.servers'  = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                    = 'json',
            'value.format'                  = 'json'
        )
    """)

    # ---------------------------------------------------------------------------
    # Pipeline: HOP window (5-min slide, 20-min size) + UDAF aggregations
    # Flink 1.19 HOP window TVF syntax
    # ---------------------------------------------------------------------------
    t_env.execute_sql("""
        INSERT INTO processed_features_sink
        SELECT
            ticker,
            window_start AS `timestamp`,
            ema_udaf(`close`)         AS ema_20,
            rsi_udaf(`close`)         AS rsi_14,
            macd_signal_udaf(`close`) AS macd_signal
        FROM TABLE(
            HOP(TABLE intraday_source, DESCRIPTOR(`timestamp`),
                INTERVAL '5' MINUTE, INTERVAL '20' MINUTE)
        )
        WHERE fetch_mode = 'intraday'
          AND `close` IS NOT NULL
          AND `close` > 0
        GROUP BY ticker, window_start, window_end
    """).wait()


if __name__ == "__main__":
    main()
