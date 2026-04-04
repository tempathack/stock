"""Feast feature repository — Entity, DataSource, and FeatureView definitions.

This file is the Feast repository root scanned by ``feast apply``.
All objects must be defined at module top level so Feast discovers them.

Source tables (feast_ohlcv_stats, feast_technical_indicators, feast_lag_features,
feast_yfinance_macro) are created by Alembic migrations or the macro collector.
feast apply registers metadata only; it does NOT create these tables.

Phase 93: removed reddit_sentiment_fv and reddit_sentiment_push;
          added yfinance_macro_source and yfinance_macro_fv.
Phase 94: added fred_macro_source and fred_macro_fv (14 FRED economic series).
"""
from __future__ import annotations

from datetime import timedelta

from feast import Entity, FeatureView, Field, PushSource
from feast.types import Float64, Int64
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)

# ── Entity ───────────────────────────────────────────────────────────────────
ticker = Entity(
    name="ticker",
    join_keys=["ticker"],
    description="Stock ticker symbol (e.g. AAPL, MSFT)",
)

# ── DataSources ──────────────────────────────────────────────────────────────
# Each source maps to a wide-format PostgreSQL table populated by a
# materialization step (replaces the EAV feature_store table).
# TTL is set to 365 days to support historical training data retrieval.

ohlcv_source = PostgreSQLSource(
    name="ohlcv_stats_source",
    query=(
        "SELECT ticker, timestamp, open, high, low, close, volume, daily_return, vwap "
        "FROM feast_ohlcv_stats"
    ),
    timestamp_field="timestamp",
    created_timestamp_column="created_at",
)

indicators_source = PostgreSQLSource(
    name="technical_indicators_source",
    query=(
        "SELECT ticker, timestamp, "
        "rsi_14, macd_line, macd_signal, bb_upper, bb_lower, atr_14, adx_14, ema_20, obv "
        "FROM feast_technical_indicators"
    ),
    timestamp_field="timestamp",
    created_timestamp_column="created_at",
)

lag_source = PostgreSQLSource(
    name="lag_features_source",
    query=(
        "SELECT ticker, timestamp, "
        "lag_1, lag_2, lag_3, lag_5, lag_7, lag_10, lag_14, lag_21, "
        "rolling_mean_5, rolling_mean_10, rolling_mean_21, "
        "rolling_std_5, rolling_std_10, rolling_std_21 "
        "FROM feast_lag_features"
    ),
    timestamp_field="timestamp",
    created_timestamp_column="created_at",
)

# ── PushSource ───────────────────────────────────────────────────────────────
# Enables Flink feast_writer job to push real-time indicators to Redis via
# store.push(push_source_name="technical_indicators_push", ..., to=PushMode.ONLINE)
technical_indicators_push = PushSource(
    name="technical_indicators_push",
    batch_source=indicators_source,
)

# ── FeatureViews ──────────────────────────────────────────────────────────────
ohlcv_stats_fv = FeatureView(
    name="ohlcv_stats_fv",
    entities=[ticker],
    ttl=timedelta(days=365),
    schema=[
        Field(name="open",         dtype=Float64),
        Field(name="high",         dtype=Float64),
        Field(name="low",          dtype=Float64),
        Field(name="close",        dtype=Float64),
        Field(name="volume",       dtype=Int64),
        Field(name="daily_return", dtype=Float64),
        Field(name="vwap",         dtype=Float64),
    ],
    online=True,
    source=ohlcv_source,
)

technical_indicators_fv = FeatureView(
    name="technical_indicators_fv",
    entities=[ticker],
    ttl=timedelta(days=365),
    schema=[
        Field(name="rsi_14",      dtype=Float64),
        Field(name="macd_line",   dtype=Float64),
        Field(name="macd_signal", dtype=Float64),
        Field(name="bb_upper",    dtype=Float64),
        Field(name="bb_lower",    dtype=Float64),
        Field(name="atr_14",      dtype=Float64),
        Field(name="adx_14",      dtype=Float64),
        Field(name="ema_20",      dtype=Float64),
        Field(name="obv",         dtype=Float64),
    ],
    online=True,
    source=indicators_source,
    sink_source=technical_indicators_push,
)

lag_features_fv = FeatureView(
    name="lag_features_fv",
    entities=[ticker],
    ttl=timedelta(days=365),
    schema=[
        Field(name="lag_1",           dtype=Float64),
        Field(name="lag_2",           dtype=Float64),
        Field(name="lag_3",           dtype=Float64),
        Field(name="lag_5",           dtype=Float64),
        Field(name="lag_7",           dtype=Float64),
        Field(name="lag_10",          dtype=Float64),
        Field(name="lag_14",          dtype=Float64),
        Field(name="lag_21",          dtype=Float64),
        Field(name="rolling_mean_5",  dtype=Float64),
        Field(name="rolling_mean_10", dtype=Float64),
        Field(name="rolling_mean_21", dtype=Float64),
        Field(name="rolling_std_5",   dtype=Float64),
        Field(name="rolling_std_10",  dtype=Float64),
        Field(name="rolling_std_21",  dtype=Float64),
    ],
    online=True,
    source=lag_source,
)

# ── Phase 93: yfinance Macro FeatureView ─────────────────────────────────────

yfinance_macro_source = PostgreSQLSource(
    name="yfinance_macro_source",
    query=(
        "SELECT ticker, timestamp, vix, spy_return, sector_return, high52w_pct, low52w_pct "
        "FROM feast_yfinance_macro"
    ),
    timestamp_field="timestamp",
    created_timestamp_column="created_at",
)

yfinance_macro_fv = FeatureView(
    name="yfinance_macro_fv",
    entities=[ticker],
    ttl=timedelta(days=365),
    schema=[
        Field(name="vix",            dtype=Float64),
        Field(name="spy_return",     dtype=Float64),
        Field(name="sector_return",  dtype=Float64),
        Field(name="high52w_pct",    dtype=Float64),
        Field(name="low52w_pct",     dtype=Float64),
    ],
    source=yfinance_macro_source,
)

# ── Phase 94: FRED Macro FeatureView ─────────────────────────────────────────
# feast_fred_macro stores FRED data with ticker='MACRO' (same entity pattern as
# yfinance_macro_fv). Online serving: entity_rows=[{"ticker": "MACRO"}].

fred_macro_source = PostgreSQLSource(
    name="fred_macro_source",
    query=(
        "SELECT ticker, timestamp, "
        "dgs2, dgs10, t10y2y, t10y3m, "
        "bamlh0a0hym2, dbaa, t10yie, "
        "dcoilwtico, dtwexbgs, dexjpus, "
        "icsa, nfci, cpiaucsl, pcepilfe "
        "FROM feast_fred_macro"
    ),
    timestamp_field="timestamp",
    created_timestamp_column="created_at",
)

fred_macro_fv = FeatureView(
    name="fred_macro_fv",
    entities=[ticker],    # ticker='MACRO' — same online store pattern as stock features
    ttl=timedelta(days=365),
    schema=[
        Field(name="dgs2",         dtype=Float64),
        Field(name="dgs10",        dtype=Float64),
        Field(name="t10y2y",       dtype=Float64),
        Field(name="t10y3m",       dtype=Float64),
        Field(name="bamlh0a0hym2", dtype=Float64),
        Field(name="dbaa",         dtype=Float64),
        Field(name="t10yie",       dtype=Float64),
        Field(name="dcoilwtico",   dtype=Float64),
        Field(name="dtwexbgs",     dtype=Float64),
        Field(name="dexjpus",      dtype=Float64),
        Field(name="icsa",         dtype=Float64),
        Field(name="nfci",         dtype=Float64),
        Field(name="cpiaucsl",     dtype=Float64),
        Field(name="pcepilfe",     dtype=Float64),
    ],
    source=fred_macro_source,
)
