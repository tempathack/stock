"""OHLCV Normalizer — PyFlink Table API job.

Reads intraday-data Kafka topic, validates and normalizes OHLCV records,
then upserts to the ohlcv_intraday TimescaleDB hypertable via JDBC connector.

The PRIMARY KEY (ticker, `timestamp`) NOT ENFORCED declaration on the sink
table triggers upsert mode in the JDBC connector, which translates to
INSERT ... ON CONFLICT DO UPDATE at the PostgreSQL level.

Environment variables (injected from flink-config ConfigMap + stock-platform-secrets):
    KAFKA_BOOTSTRAP_SERVERS  - e.g. kafka-kafka-bootstrap.storage.svc.cluster.local:9092
    POSTGRES_HOST            - e.g. postgresql.storage.svc.cluster.local
    POSTGRES_DB              - e.g. stockdb
    POSTGRES_USER            - e.g. stockuser
    POSTGRES_PASSWORD        - from stock-platform-secrets Secret

This module imports normalizer_logic for pure Python helpers so that unit
tests can exercise those helpers without requiring a Flink runtime.
"""
import os

from pyflink.table import EnvironmentSettings, TableEnvironment

from normalizer_logic import should_include_record  # noqa: F401  (re-exported for tests)


def main() -> None:
    KAFKA_BOOTSTRAP_SERVERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
    POSTGRES_HOST = os.environ["POSTGRES_HOST"]
    POSTGRES_DB = os.environ["POSTGRES_DB"]
    POSTGRES_USER = os.environ["POSTGRES_USER"]
    POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

    PG_URL = f"jdbc:postgresql://{POSTGRES_HOST}:5432/{POSTGRES_DB}"

    t_env = TableEnvironment.create(
        EnvironmentSettings.in_streaming_mode()
    )

    # ---------------------------------------------------------------------------
    # Source: Kafka intraday-data topic
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
        -- source keeps TIMESTAMP_LTZ for watermark; sink uses TIMESTAMP(3) for JDBC compat
        ) WITH (
            'connector'                     = 'kafka',
            'topic'                         = 'intraday-data',
            'properties.bootstrap.servers'  = '{KAFKA_BOOTSTRAP_SERVERS}',
            'properties.group.id'           = 'flink-ohlcv-normalizer',
            'scan.startup.mode'             = 'group-offsets',
            'properties.auto.offset.reset'  = 'latest',
            'format'                        = 'json',
            'json.ignore-parse-errors'      = 'true'
        )
    """)

    # ---------------------------------------------------------------------------
    # Sink: ohlcv_intraday JDBC upsert (PRIMARY KEY triggers upsert mode)
    # ---------------------------------------------------------------------------
    t_env.execute_sql(f"""
        CREATE TABLE ohlcv_intraday_sink (
            ticker        STRING,
            `timestamp`   TIMESTAMP(3),
            `open`        DECIMAL(12, 4),
            high          DECIMAL(12, 4),
            low           DECIMAL(12, 4),
            `close`       DECIMAL(12, 4),
            adj_close     DECIMAL(12, 4),
            volume        BIGINT,
            vwap          DECIMAL(12, 4),
            PRIMARY KEY (ticker, `timestamp`) NOT ENFORCED
        ) WITH (
            'connector'                       = 'jdbc',
            'url'                             = '{PG_URL}',
            'table-name'                      = 'ohlcv_intraday',
            'username'                        = '{POSTGRES_USER}',
            'password'                        = '{POSTGRES_PASSWORD}',
            'sink.buffer-flush.max-rows'      = '100',
            'sink.buffer-flush.interval'      = '2s'
        )
    """)

    # ---------------------------------------------------------------------------
    # Pipeline: filter + insert
    # vwap defaults to close when NULL (COALESCE in SQL)
    # ---------------------------------------------------------------------------
    t_env.execute_sql("""
        INSERT INTO ohlcv_intraday_sink
        SELECT
            ticker,
            CAST(`timestamp` AS TIMESTAMP(3)),
            `open`,
            high,
            low,
            `close`,
            adj_close,
            volume,
            COALESCE(vwap, `close`) AS vwap
        FROM intraday_source
        WHERE fetch_mode = 'intraday'
          AND ticker IS NOT NULL
          AND `close` IS NOT NULL
          AND `close` > 0
    """).wait()


if __name__ == "__main__":
    main()
