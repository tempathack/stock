"""Sentiment Stream — PyFlink Table API job.

Reads reddit-raw Kafka topic, UNNESTs ticker arrays to one row per (post, ticker),
applies VADER compound score per post via a ScalarFunction UDF, then aggregates
per-ticker sentiment in a 2-min TUMBLE window. Writes to two sinks:
  1. sentiment-aggregated Kafka topic (for Feast streaming features / WebSocket)
  2. sentiment_timeseries TimescaleDB table (for the 10h rolling chart API)

Window semantics: TUMBLE(2 min) — non-overlapping 2-minute windows. Every 2 minutes
a window closes and emits one sentiment row per active ticker.

VADER scoring: module-level SentimentIntensityAnalyzer singleton (thread-safe,
initialized once). compound score range: -1.0 (most negative) to +1.0 (most positive).
Thresholds: positive > 0.05, negative < -0.05, neutral otherwise.

Environment variables:
    KAFKA_BOOTSTRAP_SERVERS  - e.g. kafka-kafka-bootstrap.storage.svc.cluster.local:9092
"""
from __future__ import annotations

import os

from pyflink.table import DataTypes, EnvironmentSettings, TableEnvironment
from pyflink.table.udf import AggregateFunction, ScalarFunction, udaf, udf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ---------------------------------------------------------------------------
# VADER singleton — one analyzer instance for the entire job
# ---------------------------------------------------------------------------
_analyzer = SentimentIntensityAnalyzer()


# ---------------------------------------------------------------------------
# ScalarFunction UDF — VADER score per post
# ---------------------------------------------------------------------------
class VaderScoreUdf(ScalarFunction):
    """Score title+body text with VADER. Returns compound score in [-1, +1]."""

    def eval(self, text: str) -> float:
        if not text:
            return 0.0
        scores = _analyzer.polarity_scores(str(text))
        return float(scores["compound"])


# ---------------------------------------------------------------------------
# AggregateFunction UDAFs — per-window aggregation
# ---------------------------------------------------------------------------
class AvgSentimentUdaf(AggregateFunction):
    """Accumulates sum and count of compound scores; returns mean."""

    def create_accumulator(self):
        return [0.0, 0]

    def accumulate(self, acc, score):
        if score is not None:
            acc[0] += float(score)
            acc[1] += 1

    def get_value(self, acc):
        return acc[0] / acc[1] if acc[1] > 0 else 0.0

    def get_accumulator_type(self):
        return DataTypes.ARRAY(DataTypes.DOUBLE())

    def get_result_type(self):
        return DataTypes.DOUBLE()


class MentionCountUdaf(AggregateFunction):
    """Counts non-null records in window."""

    def create_accumulator(self):
        return [0]

    def accumulate(self, acc, val):
        if val is not None:
            acc[0] += 1

    def get_value(self, acc):
        return acc[0]

    def get_accumulator_type(self):
        return DataTypes.ARRAY(DataTypes.INT())

    def get_result_type(self):
        return DataTypes.INT()


class PositiveRatioUdaf(AggregateFunction):
    """Ratio of posts with compound score > 0.05 (VADER positive threshold)."""

    def create_accumulator(self):
        return [0, 0]  # [positive_count, total]

    def accumulate(self, acc, score):
        if score is not None:
            acc[1] += 1
            if float(score) > 0.05:
                acc[0] += 1

    def get_value(self, acc):
        return acc[0] / acc[1] if acc[1] > 0 else 0.0

    def get_accumulator_type(self):
        return DataTypes.ARRAY(DataTypes.DOUBLE())

    def get_result_type(self):
        return DataTypes.DOUBLE()


class NegativeRatioUdaf(AggregateFunction):
    """Ratio of posts with compound score < -0.05 (VADER negative threshold)."""

    def create_accumulator(self):
        return [0, 0]  # [negative_count, total]

    def accumulate(self, acc, score):
        if score is not None:
            acc[1] += 1
            if float(score) < -0.05:
                acc[0] += 1

    def get_value(self, acc):
        return acc[0] / acc[1] if acc[1] > 0 else 0.0

    def get_accumulator_type(self):
        return DataTypes.ARRAY(DataTypes.DOUBLE())

    def get_result_type(self):
        return DataTypes.DOUBLE()


# ---------------------------------------------------------------------------
# Main job entry point
# ---------------------------------------------------------------------------
def main() -> None:
    kafka_servers = os.environ["KAFKA_BOOTSTRAP_SERVERS"]

    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)
    t_env.get_config().set("parallelism.default", "1")
    t_env.get_config().set("python.fn-execution.memory.managed.fraction", "0.2")

    # Register UDFs
    t_env.create_temporary_function("vader_score",
        udf(VaderScoreUdf(), result_type=DataTypes.DOUBLE()))
    t_env.create_temporary_function("avg_sentiment_udaf",
        udaf(AvgSentimentUdaf(), result_type=DataTypes.DOUBLE(),
             accumulator_type=DataTypes.ARRAY(DataTypes.DOUBLE())))
    t_env.create_temporary_function("mention_count_udaf",
        udaf(MentionCountUdaf(), result_type=DataTypes.INT(),
             accumulator_type=DataTypes.ARRAY(DataTypes.INT())))
    t_env.create_temporary_function("positive_ratio_udaf",
        udaf(PositiveRatioUdaf(), result_type=DataTypes.DOUBLE(),
             accumulator_type=DataTypes.ARRAY(DataTypes.DOUBLE())))
    t_env.create_temporary_function("negative_ratio_udaf",
        udaf(NegativeRatioUdaf(), result_type=DataTypes.DOUBLE(),
             accumulator_type=DataTypes.ARRAY(DataTypes.DOUBLE())))

    # Source table: reddit-raw Kafka topic
    t_env.execute_sql(f"""
        CREATE TABLE reddit_raw_source (
            post_id      STRING,
            title        STRING,
            body         STRING,
            subreddit    STRING,
            created_utc  BIGINT,
            tickers      ARRAY<STRING>,
            event_time   AS TO_TIMESTAMP_LTZ(created_utc, 3),
            WATERMARK FOR event_time AS event_time - INTERVAL '30' SECOND
        ) WITH (
            'connector'                    = 'kafka',
            'topic'                        = 'reddit-raw',
            'properties.bootstrap.servers' = '{kafka_servers}',
            'properties.group.id'          = 'flink-sentiment-stream',
            'scan.startup.mode'            = 'latest-offset',
            'format'                       = 'json',
            'json.ignore-parse-errors'     = 'true'
        )
    """)

    # Sink table: sentiment-aggregated Kafka topic (upsert-kafka for keyed output).
    # event_timestamp aliases window_start so sentiment_writer can push a correctly
    # named column to the Feast online store without any rename step.
    t_env.execute_sql(f"""
        CREATE TABLE sentiment_aggregated_sink (
            ticker           STRING,
            window_start     TIMESTAMP(3),
            window_end       TIMESTAMP(3),
            event_timestamp  TIMESTAMP(3),
            avg_sentiment    DOUBLE,
            mention_count    INT,
            positive_ratio   DOUBLE,
            negative_ratio   DOUBLE,
            top_subreddit    STRING,
            PRIMARY KEY (ticker, window_start) NOT ENFORCED
        ) WITH (
            'connector'                    = 'upsert-kafka',
            'topic'                        = 'sentiment-aggregated',
            'properties.bootstrap.servers' = '{kafka_servers}',
            'key.format'                   = 'json',
            'value.format'                 = 'json'
        )
    """)

    # ── JDBC sink: write 2-min aggregates to TimescaleDB ──────────────────────
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgresql-service.database.svc.cluster.local")
    POSTGRES_DB = os.environ.get("POSTGRES_DB", "stockdb")
    POSTGRES_USER = os.environ.get("POSTGRES_USER", "stockuser")
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")

    t_env.execute_sql(f"""
        CREATE TABLE IF NOT EXISTS sentiment_timeseries_sink (
            ticker         STRING,
            window_start   TIMESTAMP(3),
            avg_sentiment  DOUBLE,
            mention_count  INT,
            positive_ratio DOUBLE,
            negative_ratio DOUBLE,
            PRIMARY KEY (ticker, window_start) NOT ENFORCED
        ) WITH (
            'connector'                   = 'jdbc',
            'url'                         = 'jdbc:postgresql://{POSTGRES_HOST}:5432/{POSTGRES_DB}',
            'table-name'                  = 'sentiment_timeseries',
            'username'                    = '{POSTGRES_USER}',
            'password'                    = '{POSTGRES_PASSWORD}',
            'sink.buffer-flush.interval'  = '0'
        )
    """)

    # UNNEST tickers array: one row per (post, ticker) with VADER score
    t_env.execute_sql("""
        CREATE VIEW reddit_unnested AS
        SELECT
            post_id,
            event_time,
            subreddit,
            ticker,
            vader_score(CONCAT(COALESCE(title, ''), ' ', COALESCE(body, ''))) AS compound_score
        FROM reddit_raw_source
        CROSS JOIN UNNEST(tickers) AS t(ticker)
        WHERE CARDINALITY(tickers) > 0
    """)

    # TUMBLE window aggregation: 2-min tumbling window (no overlap).
    # window_start is written to both window_start and event_timestamp columns so
    # downstream sentiment_writer can pass event_timestamp directly to Feast.
    # StatementSet runs both Kafka and JDBC sinks as a single Flink job.
    stmt_set = t_env.create_statement_set()
    stmt_set.add_insert_sql("""
        INSERT INTO sentiment_aggregated_sink
        SELECT
            ticker,
            window_start,
            window_end,
            window_start                        AS event_timestamp,
            avg_sentiment_udaf(compound_score)  AS avg_sentiment,
            mention_count_udaf(compound_score)  AS mention_count,
            positive_ratio_udaf(compound_score) AS positive_ratio,
            negative_ratio_udaf(compound_score) AS negative_ratio,
            FIRST_VALUE(subreddit)              AS top_subreddit
        FROM TABLE(
            TUMBLE(TABLE reddit_unnested, DESCRIPTOR(event_time),
                   INTERVAL '2' MINUTE)
        )
        GROUP BY ticker, window_start, window_end
    """)
    stmt_set.add_insert_sql("""
        INSERT INTO sentiment_timeseries_sink
        SELECT
            ticker,
            window_start,
            avg_sentiment_udaf(compound_score)  AS avg_sentiment,
            mention_count_udaf(compound_score)  AS mention_count,
            positive_ratio_udaf(compound_score) AS positive_ratio,
            negative_ratio_udaf(compound_score) AS negative_ratio
        FROM TABLE(
            TUMBLE(TABLE reddit_unnested, DESCRIPTOR(event_time),
                   INTERVAL '2' MINUTE)
        )
        GROUP BY ticker, window_start, window_end
    """)
    stmt_set.execute().wait()


if __name__ == "__main__":
    main()
