"""Unit tests for BatchWriter: upsert, idempotency, retry, dead-letter."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import psycopg2
import pytest

from tests.conftest import _make_intraday_record, _make_historical_record


@pytest.fixture
def batch_writer(mock_db_pool):
    """Create a BatchWriter with a mock connection pool."""
    from consumer.db_writer import BatchWriter

    return BatchWriter(pool=mock_db_pool)


@pytest.fixture
def mock_conn(mock_db_pool):
    """Get the mock connection from the pool."""
    return mock_db_pool.getconn()


class TestUpsertIntraday:
    """Tests for BatchWriter.upsert_intraday_batch (CONS-04)."""

    def test_upsert_intraday_batch_executes_sql(self, batch_writer, mock_db_pool):
        records = [_make_intraday_record()]

        with patch("consumer.db_writer.execute_values") as mock_exec:
            batch_writer.upsert_intraday_batch(records)

            # Check the SQL contains the expected fragments
            sql_arg = mock_exec.call_args_list[-1][0][1]
            assert "INSERT INTO ohlcv_intraday" in sql_arg
            assert "ON CONFLICT (ticker, timestamp) DO UPDATE" in sql_arg

    def test_upsert_intraday_extracts_correct_values(self, batch_writer, mock_db_pool):
        record = _make_intraday_record("AAPL")
        records = [record]

        with patch("consumer.db_writer.execute_values") as mock_exec:
            batch_writer.upsert_intraday_batch(records)

            # The OHLCV upsert call (last call to execute_values)
            values_arg = mock_exec.call_args_list[-1][0][2]
            row = values_arg[0]
            assert row[0] == "AAPL"  # ticker
            assert row[1] == record["timestamp"]  # timestamp
            assert row[2] == record["open"]
            assert row[3] == record["high"]
            assert row[4] == record["low"]
            assert row[5] == record["close"]
            assert row[6] == record["volume"]

    def test_upsert_commits_transaction(self, batch_writer, mock_db_pool):
        records = [_make_intraday_record()]

        with patch("consumer.db_writer.execute_values"):
            batch_writer.upsert_intraday_batch(records)

        conn = mock_db_pool.getconn()
        conn.commit.assert_called()

    def test_upsert_returns_connection_to_pool(self, batch_writer, mock_db_pool):
        records = [_make_intraday_record()]

        with patch("consumer.db_writer.execute_values"):
            batch_writer.upsert_intraday_batch(records)

        mock_db_pool.putconn.assert_called()

    def test_upsert_intraday_idempotent_with_duplicate(self, batch_writer, mock_db_pool):
        """Upserting the same record twice should not error (ON CONFLICT handles it)."""
        record = _make_intraday_record()

        with patch("consumer.db_writer.execute_values"):
            result1 = batch_writer.upsert_intraday_batch([record])
            result2 = batch_writer.upsert_intraday_batch([record])

        assert result1 == 1
        assert result2 == 1


class TestUpsertDaily:
    """Tests for BatchWriter.upsert_daily_batch (CONS-04)."""

    def test_upsert_daily_batch_executes_sql(self, batch_writer, mock_db_pool):
        records = [_make_historical_record()]

        with patch("consumer.db_writer.execute_values") as mock_exec:
            batch_writer.upsert_daily_batch(records)

            sql_arg = mock_exec.call_args_list[-1][0][1]
            assert "INSERT INTO ohlcv_daily" in sql_arg
            assert "ON CONFLICT (ticker, date) DO UPDATE" in sql_arg

    def test_upsert_daily_extracts_date_from_timestamp(self, batch_writer, mock_db_pool):
        record = _make_historical_record("AAPL")
        records = [record]

        with patch("consumer.db_writer.execute_values") as mock_exec:
            batch_writer.upsert_daily_batch(records)

            # Last execute_values call is the OHLCV upsert
            values_arg = mock_exec.call_args_list[-1][0][2]
            row = values_arg[0]
            assert row[0] == "AAPL"  # ticker
            # date should be extracted from timestamp
            from datetime import date
            assert isinstance(row[1], date)
            assert str(row[1]) == "2026-03-19"


class TestEnsureTickers:
    """Tests for BatchWriter._ensure_tickers (stocks FK handling)."""

    def test_ensure_tickers_called_before_upsert(self, batch_writer, mock_db_pool):
        records = [_make_intraday_record("AAPL"), _make_intraday_record("MSFT")]

        with patch("consumer.db_writer.execute_values") as mock_exec:
            batch_writer.upsert_intraday_batch(records)

            # First call should be stocks ensure, second should be OHLCV upsert
            assert mock_exec.call_count == 2
            first_sql = mock_exec.call_args_list[0][0][1]
            assert "INSERT INTO stocks" in first_sql

    def test_ensure_tickers_on_conflict_do_nothing(self, batch_writer, mock_db_pool):
        records = [_make_intraday_record()]

        with patch("consumer.db_writer.execute_values") as mock_exec:
            batch_writer.upsert_intraday_batch(records)

            first_sql = mock_exec.call_args_list[0][0][1]
            assert "ON CONFLICT (ticker) DO NOTHING" in first_sql


class TestRetry:
    """Tests for retry logic (CONS-05)."""

    def test_retry_on_operational_error(self, mock_db_pool):
        from consumer.db_writer import BatchWriter

        writer = BatchWriter(pool=mock_db_pool)
        records = [_make_intraday_record()]

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # call 1 = _ensure_tickers (succeed)
            # call 2 = first _execute_upsert attempt (fail)
            # call 3 = second _execute_upsert attempt (succeed)
            if call_count == 2:
                raise psycopg2.OperationalError("connection lost")

        with patch("consumer.db_writer.execute_values", side_effect=side_effect):
            result = writer.upsert_intraday_batch(records)

        assert result == 1
        assert call_count >= 3

    def test_retry_on_interface_error(self, mock_db_pool):
        from consumer.db_writer import BatchWriter

        writer = BatchWriter(pool=mock_db_pool)
        records = [_make_intraday_record()]

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # call 1 = _ensure_tickers (succeed)
            # call 2 = first _execute_upsert attempt (fail)
            # call 3 = second _execute_upsert attempt (succeed)
            if call_count == 2:
                raise psycopg2.InterfaceError("connection closed")

        with patch("consumer.db_writer.execute_values", side_effect=side_effect):
            result = writer.upsert_intraday_batch(records)

        assert result == 1
        assert call_count >= 3

    def test_retry_exhaustion_raises(self, mock_db_pool):
        from consumer.db_writer import BatchWriter

        writer = BatchWriter(pool=mock_db_pool)
        records = [_make_intraday_record()]

        with patch(
            "consumer.db_writer.execute_values",
            side_effect=psycopg2.OperationalError("always fails"),
        ):
            with pytest.raises(psycopg2.OperationalError):
                writer.upsert_intraday_batch(records)


class TestDeadLetter:
    """Tests for dead-letter logging (CONS-06)."""

    def test_dead_letter_logging_after_retry_exhaustion(self, mock_db_pool):
        from consumer.db_writer import BatchWriter

        writer = BatchWriter(pool=mock_db_pool)
        records = [_make_intraday_record()]

        with patch(
            "consumer.db_writer.execute_values",
            side_effect=psycopg2.OperationalError("always fails"),
        ), patch("consumer.db_writer.logger") as mock_logger:
            with pytest.raises(psycopg2.OperationalError):
                writer.upsert_intraday_batch(records)

            mock_logger.error.assert_called()
            # Check it was called with dead_letter_record event
            error_calls = mock_logger.error.call_args_list
            assert any(
                "dead_letter_record" in str(c) for c in error_calls
            )

    def test_dead_letter_includes_record_payload(self, mock_db_pool):
        from consumer.db_writer import BatchWriter

        writer = BatchWriter(pool=mock_db_pool)
        record = _make_intraday_record("AAPL")
        records = [record]

        with patch(
            "consumer.db_writer.execute_values",
            side_effect=psycopg2.OperationalError("always fails"),
        ), patch("consumer.db_writer.logger") as mock_logger:
            with pytest.raises(psycopg2.OperationalError):
                writer.upsert_intraday_batch(records)

            error_calls = mock_logger.error.call_args_list
            # Check that the ticker is in one of the error calls
            error_kwargs = [c.kwargs for c in error_calls if c.kwargs]
            assert any(
                kw.get("ticker") == "AAPL" for kw in error_kwargs
            )
