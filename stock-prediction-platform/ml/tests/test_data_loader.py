"""Tests for the data loading pipeline component."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_ohlcv_rows() -> list[tuple]:
    """Mimic psycopg2 cursor.fetchall() — 10 rows of (date, open, high, low, close, volume)."""
    base = date(2024, 1, 2)
    rows = []
    for i in range(10):
        d = date(2024, 1, 2 + i)
        rows.append((d, 170.0 + i, 172.0 + i, 168.0 + i, 171.0 + i, 5_000_000 + i * 100_000))
    return rows


@pytest.fixture
def mock_cursor(sample_ohlcv_rows):
    """Return a MagicMock cursor whose fetchall() returns sample_ohlcv_rows."""
    cursor = MagicMock()
    cursor.fetchall.return_value = sample_ohlcv_rows
    cursor.description = [
        ("date",), ("open",), ("high",), ("low",), ("close",), ("volume",),
    ]
    return cursor


@pytest.fixture
def mock_connection(mock_cursor):
    """Patch psycopg2.connect and wire up the mock cursor."""
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    return conn


# ---------------------------------------------------------------------------
# TestDBSettings
# ---------------------------------------------------------------------------


class TestDBSettings:
    """Tests for DBSettings dataclass."""

    def test_default_values(self):
        from ml.pipelines.components.data_loader import DBSettings

        settings = DBSettings()
        assert settings.host == "postgresql.storage.svc.cluster.local"
        assert settings.port == 5432
        assert settings.database == "stockdb"
        assert settings.user == "stockuser"

    def test_env_override(self, monkeypatch):
        from ml.pipelines.components.data_loader import DBSettings

        monkeypatch.setenv("POSTGRES_HOST", "custom-host")
        monkeypatch.setenv("POSTGRES_PORT", "9999")
        settings = DBSettings()
        assert settings.host == "custom-host"
        assert settings.port == 9999

    def test_connection_string(self):
        from ml.pipelines.components.data_loader import DBSettings

        settings = DBSettings(
            host="localhost", port=5432, database="testdb",
            user="user", password="pass",
        )
        assert settings.connection_string == "postgresql://user:pass@localhost:5432/testdb"

    def test_from_env_classmethod(self, monkeypatch):
        from ml.pipelines.components.data_loader import DBSettings

        monkeypatch.setenv("POSTGRES_HOST", "env-host")
        settings = DBSettings.from_env()
        assert settings.host == "env-host"


# ---------------------------------------------------------------------------
# TestLoadTickerData
# ---------------------------------------------------------------------------


class TestLoadTickerData:
    """Tests for load_ticker_data()."""

    def test_returns_dataframe(self, mock_connection):
        from ml.pipelines.components.data_loader import load_ticker_data

        result = load_ticker_data("AAPL", mock_connection)
        assert isinstance(result, pd.DataFrame)

    def test_dataframe_columns(self, mock_connection):
        from ml.pipelines.components.data_loader import load_ticker_data

        result = load_ticker_data("AAPL", mock_connection)
        assert list(result.columns) == ["open", "high", "low", "close", "volume"]

    def test_dataframe_index_is_datetime(self, mock_connection):
        from ml.pipelines.components.data_loader import load_ticker_data

        result = load_ticker_data("AAPL", mock_connection)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_dataframe_sorted_by_date(self, mock_connection):
        from ml.pipelines.components.data_loader import load_ticker_data

        result = load_ticker_data("AAPL", mock_connection)
        assert result.index.is_monotonic_increasing

    def test_empty_result_returns_empty_df(self, mock_connection):
        from ml.pipelines.components.data_loader import load_ticker_data

        mock_connection.cursor.return_value.fetchall.return_value = []
        result = load_ticker_data("AAPL", mock_connection)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ["open", "high", "low", "close", "volume"]


# ---------------------------------------------------------------------------
# TestLoadData
# ---------------------------------------------------------------------------


class TestLoadData:
    """Tests for load_data()."""

    @patch("ml.pipelines.components.data_loader.psycopg2")
    def test_returns_dict_of_dataframes(self, mock_psycopg2, mock_cursor):
        from ml.pipelines.components.data_loader import DBSettings, load_data

        mock_psycopg2.connect.return_value.__enter__ = MagicMock(return_value=MagicMock())
        conn = MagicMock()
        conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = conn

        result = load_data(["AAPL", "MSFT"], settings=DBSettings())
        assert isinstance(result, dict)
        for v in result.values():
            assert isinstance(v, pd.DataFrame)

    @patch("ml.pipelines.components.data_loader.psycopg2")
    def test_all_tickers_present(self, mock_psycopg2, mock_cursor):
        from ml.pipelines.components.data_loader import DBSettings, load_data

        conn = MagicMock()
        conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = conn

        result = load_data(["AAPL", "MSFT"], settings=DBSettings())
        assert set(result.keys()) == {"AAPL", "MSFT"}

    @patch("ml.pipelines.components.data_loader.psycopg2")
    def test_empty_ticker_skipped(self, mock_psycopg2):
        from ml.pipelines.components.data_loader import DBSettings, load_data

        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.description = [
            ("date",), ("open",), ("high",), ("low",), ("close",), ("volume",),
        ]
        conn = MagicMock()
        conn.cursor.return_value = cursor
        mock_psycopg2.connect.return_value = conn

        result = load_data(["EMPTY"], settings=DBSettings())
        assert "EMPTY" not in result

    @patch("ml.pipelines.components.data_loader.psycopg2")
    def test_date_range_filtering(self, mock_psycopg2, mock_cursor):
        from ml.pipelines.components.data_loader import DBSettings, load_data

        conn = MagicMock()
        conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = conn

        load_data(
            ["AAPL"],
            settings=DBSettings(),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
        )

        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "date >= %s" in executed_sql
        assert "date <= %s" in executed_sql

    @patch("ml.pipelines.components.data_loader.psycopg2")
    def test_sql_parameterized(self, mock_psycopg2, mock_cursor):
        from ml.pipelines.components.data_loader import DBSettings, load_data

        conn = MagicMock()
        conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = conn

        load_data(["AAPL"], settings=DBSettings())

        executed_sql = mock_cursor.execute.call_args[0][0]
        # Must use %s placeholder, not string interpolation
        assert "%s" in executed_sql
        assert "AAPL" not in executed_sql

    @patch("ml.pipelines.components.data_loader.psycopg2")
    def test_connection_closed_on_success(self, mock_psycopg2, mock_cursor):
        from ml.pipelines.components.data_loader import DBSettings, load_data

        conn = MagicMock()
        conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = conn

        load_data(["AAPL"], settings=DBSettings())
        conn.close.assert_called_once()


# ---------------------------------------------------------------------------
# TestLoadDataErrorHandling
# ---------------------------------------------------------------------------


class TestLoadDataErrorHandling:
    """Tests for load_data() error handling."""

    @patch("ml.pipelines.components.data_loader.psycopg2")
    def test_connection_failure_raises(self, mock_psycopg2):
        from ml.pipelines.components.data_loader import DBSettings, load_data

        mock_psycopg2.connect.side_effect = Exception("Connection refused")
        with pytest.raises(Exception, match="Connection refused"):
            load_data(["AAPL"], settings=DBSettings())

    @patch("ml.pipelines.components.data_loader.psycopg2")
    def test_connection_closed_on_error(self, mock_psycopg2):
        from ml.pipelines.components.data_loader import DBSettings, load_data

        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchall.side_effect = Exception("Query failed")
        cursor.description = [
            ("date",), ("open",), ("high",), ("low",), ("close",), ("volume",),
        ]
        conn.cursor.return_value = cursor
        mock_psycopg2.connect.return_value = conn

        with pytest.raises(Exception, match="Query failed"):
            load_data(["AAPL"], settings=DBSettings())

        conn.close.assert_called_once()

    def test_invalid_ticker_type_raises(self):
        from ml.pipelines.components.data_loader import load_data

        with pytest.raises(TypeError):
            load_data("AAPL")  # type: ignore[arg-type]
