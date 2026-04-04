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


# ---------------------------------------------------------------------------
# TestFeastDataLoader
# ── Wave 0 stub — tests will be RED until Plan 02 implements load_feast_data() ──
# ---------------------------------------------------------------------------


class TestFeastDataLoader:
    """Tests for load_feast_data() — Feast offline training data loader.
    RED state until 92-02-PLAN.md implements load_feast_data() in data_loader.py.
    """

    _FEAST_COLS = [
        "ticker", "event_timestamp",
        "open", "high", "low", "close", "volume", "daily_return", "vwap",
        "rsi_14", "macd_line", "macd_signal", "bb_upper", "bb_lower",
        "atr_14", "adx_14", "ema_20", "obv",
        "lag_1", "lag_2", "lag_3", "lag_5", "lag_7", "lag_10", "lag_14", "lag_21",
        "rolling_mean_5", "rolling_mean_10", "rolling_mean_21",
        "rolling_std_5", "rolling_std_10", "rolling_std_21",
        "avg_sentiment", "mention_count", "positive_ratio", "negative_ratio",
    ]

    def _make_mock_feast_df(self, tickers=None, null_sentiment=False):
        tickers = tickers or ["AAPL"]
        rows = []
        for t in tickers:
            for i in range(3):
                row = {c: 1.0 for c in self._FEAST_COLS if c not in ("ticker", "event_timestamp")}
                row["ticker"] = t
                row["event_timestamp"] = pd.Timestamp("2024-01-01", tz="UTC") + pd.Timedelta(days=i)
                if null_sentiment:
                    for col in ("avg_sentiment", "mention_count", "positive_ratio", "negative_ratio"):
                        row[col] = None
                rows.append(row)
        return pd.DataFrame(rows)

    def test_load_feast_data_returns_dataframe(self):
        from ml.pipelines.components.data_loader import load_feast_data
        mock_store = MagicMock()
        mock_store.get_historical_features.return_value.to_df.return_value = self._make_mock_feast_df()
        with patch("ml.pipelines.components.data_loader.get_store", return_value=mock_store):
            result = load_feast_data(tickers=["AAPL"], start_date="2024-01-01", end_date="2024-03-31")
        assert isinstance(result, pd.DataFrame)
        assert "avg_sentiment" in result.columns

    def test_load_feast_data_fills_null_sentiment(self):
        from ml.pipelines.components.data_loader import load_feast_data
        mock_store = MagicMock()
        mock_store.get_historical_features.return_value.to_df.return_value = self._make_mock_feast_df(null_sentiment=True)
        with patch("ml.pipelines.components.data_loader.get_store", return_value=mock_store):
            result = load_feast_data(tickers=["AAPL"], start_date="2024-01-01", end_date="2024-03-31")
        for col in ("avg_sentiment", "mention_count", "positive_ratio", "negative_ratio"):
            assert result[col].isna().sum() == 0, f"{col} must have no NaN after fill"
            assert (result[col] == 0.0).all(), f"{col} nulls must be filled with 0.0"

    def test_load_feast_data_drops_entity_cols(self):
        from ml.pipelines.components.data_loader import load_feast_data
        mock_store = MagicMock()
        mock_store.get_historical_features.return_value.to_df.return_value = self._make_mock_feast_df()
        with patch("ml.pipelines.components.data_loader.get_store", return_value=mock_store):
            result = load_feast_data(tickers=["AAPL"], start_date="2024-01-01", end_date="2024-03-31")
        assert "event_timestamp" not in result.columns, "event_timestamp must be stripped"

    def test_load_feast_data_entity_df_structure(self):
        from ml.pipelines.components.data_loader import load_feast_data
        mock_store = MagicMock()
        mock_store.get_historical_features.return_value.to_df.return_value = self._make_mock_feast_df()
        with patch("ml.pipelines.components.data_loader.get_store", return_value=mock_store):
            load_feast_data(tickers=["AAPL", "MSFT"], start_date="2024-01-01", end_date="2024-01-31")
        call_args = mock_store.get_historical_features.call_args
        _edf = call_args.kwargs.get("entity_df")
        if _edf is None:
            _edf = call_args[1].get("entity_df") if call_args[1] else call_args[0][0]
        entity_df = _edf
        assert "ticker" in entity_df.columns
        assert "event_timestamp" in entity_df.columns
        assert entity_df["event_timestamp"].dt.tz is not None, "event_timestamp must be UTC"
        assert set(entity_df["ticker"].unique()) == {"AAPL", "MSFT"}


# ---------------------------------------------------------------------------
# TestYfinanceMacroLoader
# ── Wave 0 stub — tests will be RED until Plan 93-02 implements load_yfinance_macro() ──
# ---------------------------------------------------------------------------


class TestYfinanceMacroLoader:
    """Tests for load_yfinance_macro() — yfinance macro feature loader.
    RED state until 93-02-PLAN.md implements load_yfinance_macro() in data_loader.py.
    """

    _EXPECTED_MACRO_COLS = [
        "vix",
        "spy_return",
        "sector_return",
        "high52w_pct",
        "low52w_pct",
    ]

    def test_load_yfinance_macro_returns_dataframe(self):
        """load_yfinance_macro() returns a DataFrame with DatetimeIndex and required macro columns."""
        from ml.pipelines.components.data_loader import load_yfinance_macro  # noqa: F401 — fails RED until 93-02

        result = load_yfinance_macro(
            tickers=["AAPL"],
            start_date="2024-01-01",
            end_date="2024-03-31",
        )
        assert isinstance(result, pd.DataFrame), "load_yfinance_macro() must return a pd.DataFrame"
        assert isinstance(result.index, pd.DatetimeIndex), "Result must have a DatetimeIndex"
        for col in self._EXPECTED_MACRO_COLS:
            assert col in result.columns, (
                f"Expected macro column {col!r} not found in result. "
                f"Got: {list(result.columns)}"
            )
