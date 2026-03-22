"""TEST-01: Integration tests for ingest → Kafka → PostgreSQL flow.

Validates the full ingestion pipeline from Yahoo Finance fetch through
Kafka produce/consume to database writer, with external boundaries mocked.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_yfinance_df(tickers: list[str], days: int = 5) -> dict[str, pd.DataFrame]:
    """Build per-ticker DataFrames mimicking yfinance.download output."""
    frames = {}
    base_prices = {"AAPL": 178.0, "MSFT": 425.0, "GOOGL": 175.0}
    for ticker in tickers:
        bp = base_prices.get(ticker, 100.0)
        idx = pd.bdate_range(end="2026-03-19", periods=days)
        frames[ticker] = pd.DataFrame(
            {
                "Open": [bp + i * 0.5 for i in range(days)],
                "High": [bp + i * 0.5 + 1.0 for i in range(days)],
                "Low": [bp + i * 0.5 - 0.5 for i in range(days)],
                "Close": [bp + i * 0.5 + 0.3 for i in range(days)],
                "Volume": [5_000_000 + i * 100_000 for i in range(days)],
            },
            index=idx,
        )
    return frames


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestIngestToDBFlow:
    """TEST-01: End-to-end flow validation — ingest → Kafka → PostgreSQL."""

    # ── Test 1: yahoo → kafka record count ────────────────────────────

    @patch("app.services.yahoo_finance._fetch_ticker_data")
    def test_yahoo_to_kafka_record_count(self, mock_fetch):
        """Records fetched from Yahoo Finance are all produced to Kafka."""
        from app.services.kafka_producer import OHLCVProducer
        from app.services.yahoo_finance import YahooFinanceService

        tickers = ["AAPL", "MSFT", "GOOGL"]
        frames = _make_yfinance_df(tickers)
        mock_fetch.side_effect = lambda ticker, **kw: frames[ticker]

        svc = YahooFinanceService()
        records = svc.fetch_historical(tickers=tickers)
        assert len(records) == 15  # 3 tickers × 5 days

        mock_producer = MagicMock()
        producer = OHLCVProducer(producer=mock_producer)
        count = producer.produce_records(records)

        assert count == 15
        assert mock_producer.produce.call_count == 15

        produced_tickers = set()
        for call in mock_producer.produce.call_args_list:
            value = json.loads(call.kwargs["value"].decode("utf-8"))
            produced_tickers.add(value["ticker"])
        assert produced_tickers == set(tickers)

    # ── Test 2: kafka messages → processor batch ──────────────────────

    def test_kafka_message_to_processor_batch(
        self, sample_ohlcv_records, mock_kafka_message_factory,
    ):
        """MessageProcessor batches all 15 messages and passes them to writer."""
        from consumer.processor import MessageProcessor

        mock_writer = MagicMock()
        proc = MessageProcessor(
            batch_size=100, batch_timeout_ms=60_000, writer=mock_writer,
        )

        topic = "historical-data"
        for rec in sample_ohlcv_records:
            msg = mock_kafka_message_factory(rec, topic=topic)
            proc.add_message(msg)

        assert proc.buffer_size == 15
        count = proc.flush()

        # All records have fetch_mode=historical → upsert_daily_batch
        assert mock_writer.upsert_daily_batch.called
        total_records = sum(
            len(call.args[0])
            for call in mock_writer.upsert_daily_batch.call_args_list
        )
        assert total_records == 15

    # ── Test 3: OHLC invariants preserved ─────────────────────────────

    def test_ohlc_invariants_preserved(
        self, sample_ohlcv_records, mock_kafka_message_factory,
    ):
        """Low ≤ open/close ≤ high and volume > 0 survive the pipeline."""
        from consumer.processor import MessageProcessor

        captured: list[dict] = []
        mock_writer = MagicMock()
        mock_writer.upsert_daily_batch.side_effect = lambda recs: (
            captured.extend(recs) or len(recs)
        )

        proc = MessageProcessor(
            batch_size=100, batch_timeout_ms=60_000, writer=mock_writer,
        )
        for rec in sample_ohlcv_records:
            proc.add_message(mock_kafka_message_factory(rec, "historical-data"))
        proc.flush()

        assert len(captured) == 15
        for rec in captured:
            assert rec["low"] <= rec["open"], f"low > open for {rec['ticker']}"
            assert rec["low"] <= rec["close"], f"low > close for {rec['ticker']}"
            assert rec["high"] >= rec["open"], f"high < open for {rec['ticker']}"
            assert rec["high"] >= rec["close"], f"high < close for {rec['ticker']}"
            assert rec["volume"] > 0

    # ── Test 4: ticker/date round-trip ────────────────────────────────

    @patch("app.services.yahoo_finance._fetch_ticker_data")
    def test_ticker_date_roundtrip(self, mock_fetch, mock_kafka_message_factory):
        """(ticker, date) tuples survive Yahoo → serialize → deserialize."""
        from app.services.kafka_producer import OHLCVProducer
        from app.services.yahoo_finance import YahooFinanceService
        from consumer.processor import MessageProcessor

        tickers = ["AAPL", "MSFT", "GOOGL"]
        frames = _make_yfinance_df(tickers)
        mock_fetch.side_effect = lambda ticker, **kw: frames[ticker]

        svc = YahooFinanceService()
        records = svc.fetch_historical(tickers=tickers)

        input_pairs = {(r["ticker"], r["timestamp"][:10]) for r in records}

        # Serialize (mock produce) → deserialize via MessageProcessor
        captured: list[dict] = []
        mock_writer = MagicMock()
        mock_writer.upsert_daily_batch.side_effect = lambda recs: (
            captured.extend(recs) or len(recs)
        )

        proc = MessageProcessor(
            batch_size=100, batch_timeout_ms=60_000, writer=mock_writer,
        )
        for rec in records:
            msg = mock_kafka_message_factory(rec, "historical-data")
            proc.add_message(msg)
        proc.flush()

        output_pairs = {(r["ticker"], r["timestamp"][:10]) for r in captured}
        assert input_pairs == output_pairs

    # ── Test 5: topic routing ─────────────────────────────────────────

    def test_topic_routing(
        self,
        sample_ohlcv_records,
        sample_intraday_records,
        mock_kafka_message_factory,
    ):
        """Records from both topics are batched and routed correctly."""
        from consumer.processor import MessageProcessor

        mock_writer = MagicMock()
        mock_writer.upsert_daily_batch.return_value = 0
        mock_writer.upsert_intraday_batch.return_value = 0

        proc = MessageProcessor(
            batch_size=200, batch_timeout_ms=60_000, writer=mock_writer,
        )

        for rec in sample_ohlcv_records:
            proc.add_message(
                mock_kafka_message_factory(rec, "historical-data"),
            )
        for rec in sample_intraday_records:
            proc.add_message(
                mock_kafka_message_factory(rec, "intraday-data"),
            )

        proc.flush()

        assert mock_writer.upsert_daily_batch.called
        assert mock_writer.upsert_intraday_batch.called

    # ── Test 6: empty fetch produces nothing ──────────────────────────

    @patch("app.services.yahoo_finance._fetch_ticker_data")
    def test_empty_fetch_produces_nothing(self, mock_fetch):
        """Empty Yahoo Finance response means zero records produced."""
        from app.services.yahoo_finance import YahooFinanceService

        mock_fetch.return_value = pd.DataFrame()

        svc = YahooFinanceService()
        records = svc.fetch_historical(tickers=["AAPL"])

        assert records == []
