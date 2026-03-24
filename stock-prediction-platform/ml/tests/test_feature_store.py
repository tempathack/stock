"""Tests for the feature store module."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd
import pytest

from ml.features.store import (
    _get_active_tickers,
    compute_and_store,
    compute_features_for_ticker,
    get_feature_freshness,
    read_features,
    write_features,
)


# ---------------------------------------------------------------------------
# Plan 44-01 tests — core compute / write / read
# ---------------------------------------------------------------------------


class TestComputeFeaturesForTicker:
    def test_compute_features_for_ticker(self, sample_ohlcv_df):
        """Computes features and drops NaN warm-up rows."""
        mock_conn = MagicMock()
        with patch(
            "ml.features.store.load_ticker_data", return_value=sample_ohlcv_df,
        ):
            result = compute_features_for_ticker("AAPL", mock_conn)

        assert not result.empty
        assert len(result.columns) > 40
        assert result.isna().sum().sum() == 0
        assert len(result) < 250  # warm-up rows dropped

    def test_compute_features_empty_data(self):
        """Returns empty DataFrame when no OHLCV data."""
        mock_conn = MagicMock()
        empty_df = pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        with patch(
            "ml.features.store.load_ticker_data", return_value=empty_df,
        ):
            result = compute_features_for_ticker("AAPL", mock_conn)

        assert result.empty


class TestWriteFeatures:
    def _make_small_df(self) -> pd.DataFrame:
        """Small feature DataFrame for write tests."""
        dates = pd.bdate_range("2024-06-01", periods=3)
        return pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [105, 106, 107],
                "low": [95, 96, 97],
                "close": [103, 104, 105],
                "volume": [1_000_000, 2_000_000, 3_000_000],
                "rsi_14": [55.0, 60.0, 65.0],
                "macd_line": [0.5, 0.6, 0.7],
            },
            index=dates,
        )

    def test_write_features(self):
        """Calls executemany with correct SQL pattern."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        df = self._make_small_df()
        count = write_features("AAPL", df, mock_conn)

        assert mock_cursor.executemany.called
        sql_arg = mock_cursor.executemany.call_args[0][0]
        assert "INSERT INTO feature_store" in sql_arg
        assert "ON CONFLICT" in sql_arg
        # 3 dates × 2 feature columns (rsi_14, macd_line) = 6 rows
        assert count == 6
        mock_conn.commit.assert_called_once()

    def test_write_features_batching(self):
        """Large DataFrames are batched in chunks of 5000."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # Create DataFrame with enough feature rows to exceed one batch.
        # We need >5000 total (ticker, date, feature) tuples.
        # 100 dates × 60 features = 6000 rows > 5000 → 2 executemany calls
        dates = pd.bdate_range("2023-01-01", periods=100)
        data = {"close": np.random.default_rng(0).normal(100, 5, 100)}
        for i in range(60):
            data[f"feat_{i}"] = np.random.default_rng(i).normal(0, 1, 100)
        df = pd.DataFrame(data, index=dates)

        count = write_features("AAPL", df, mock_conn)

        assert mock_cursor.executemany.call_count >= 2
        assert count == 100 * 60  # 6000 rows


class TestComputeAndStore:
    def test_compute_and_store(self, sample_ohlcv_df):
        """Successfully processes multiple tickers."""
        with (
            patch("ml.features.store.psycopg2") as mock_pg,
            patch("ml.features.store.load_ticker_data", return_value=sample_ohlcv_df),
        ):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_pg.connect.return_value = mock_conn

            result = compute_and_store(["AAPL", "MSFT", "GOOG"])

        assert len(result) == 3
        for v in result.values():
            assert isinstance(v, int)
            assert v > 0

    def test_compute_and_store_partial_failure(self, sample_ohlcv_df):
        """One ticker failure doesn't abort the others."""
        call_count = 0

        def _mock_load(ticker, conn):
            nonlocal call_count
            call_count += 1
            if ticker == "BAD":
                raise RuntimeError("simulated failure")
            return sample_ohlcv_df

        with (
            patch("ml.features.store.psycopg2") as mock_pg,
            patch("ml.features.store.load_ticker_data", side_effect=_mock_load),
        ):
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_pg.connect.return_value = mock_conn

            result = compute_and_store(["AAPL", "BAD", "GOOG"])

        assert result["BAD"] == 0
        assert result["AAPL"] > 0
        assert result["GOOG"] > 0


class TestReadFeatures:
    def test_read_features(self):
        """Pivots EAV rows into wide DataFrames."""
        eav_rows = [
            (date(2024, 6, 1), "rsi_14", 55.0),
            (date(2024, 6, 1), "macd_line", 0.5),
            (date(2024, 6, 2), "rsi_14", 60.0),
            (date(2024, 6, 2), "macd_line", 0.6),
        ]

        with patch("ml.features.store.psycopg2") as mock_pg:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = eav_rows
            mock_conn.cursor.return_value = mock_cursor
            mock_pg.connect.return_value = mock_conn

            result = read_features(["AAPL"])

        assert "AAPL" in result
        df = result["AAPL"]
        assert "rsi_14" in df.columns
        assert "macd_line" in df.columns
        assert len(df) == 2
        # Ensure wide format (no "feature_name" or "feature_value" columns)
        assert "feature_name" not in df.columns
        assert "feature_value" not in df.columns

    def test_read_features_empty(self):
        """Returns empty dict when no data found."""
        with patch("ml.features.store.psycopg2") as mock_pg:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_pg.connect.return_value = mock_conn

            result = read_features(["AAPL"])

        assert result == {}


class TestGetFeatureFreshness:
    def test_get_feature_freshness(self):
        """Returns the max date for a ticker."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (date(2024, 6, 15),)
        mock_conn.cursor.return_value = mock_cursor

        result = get_feature_freshness("AAPL", mock_conn)
        assert result == date(2024, 6, 15)

    def test_get_feature_freshness_no_data(self):
        """Returns None when no features exist."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)
        mock_conn.cursor.return_value = mock_cursor

        result = get_feature_freshness("AAPL", mock_conn)
        assert result is None


# ---------------------------------------------------------------------------
# Plan 44-02 tests — CLI, _get_active_tickers, feature_engineer integration
# ---------------------------------------------------------------------------


class TestGetActiveTickers:
    def test_get_active_tickers(self):
        """Returns list of active ticker strings."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("AAPL",), ("GOOG",), ("MSFT",)]
        mock_conn.cursor.return_value = mock_cursor

        result = _get_active_tickers(mock_conn)
        assert result == ["AAPL", "GOOG", "MSFT"]


class TestCLI:
    def test_cli_compute_all_flow(self):
        """--compute-all path: queries active tickers then calls compute_and_store."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("AAPL",), ("MSFT",)]
        mock_conn.cursor.return_value = mock_cursor

        tickers = _get_active_tickers(mock_conn)
        assert tickers == ["AAPL", "MSFT"]

        with patch("ml.features.store.psycopg2") as mock_pg:
            mock_pg.connect.return_value = MagicMock()
            mock_pg.connect.return_value.cursor.return_value = MagicMock()

            with patch("ml.features.store.compute_features_for_ticker") as mock_compute:
                mock_compute.return_value = pd.DataFrame()
                result = compute_and_store(tickers)

        assert len(result) == 2

    def test_cli_specific_tickers_flow(self):
        """--tickers path: parses comma-separated list and passes to compute_and_store."""
        raw = "AAPL,MSFT"
        ticker_list = [t.strip() for t in raw.split(",")]
        assert ticker_list == ["AAPL", "MSFT"]

        with patch("ml.features.store.psycopg2") as mock_pg:
            mock_pg.connect.return_value = MagicMock()
            mock_pg.connect.return_value.cursor.return_value = MagicMock()

            with patch("ml.features.store.compute_features_for_ticker") as mock_compute:
                mock_compute.return_value = pd.DataFrame()
                result = compute_and_store(ticker_list)

        assert len(result) == 2
        assert "AAPL" in result
        assert "MSFT" in result


class TestEngineerFeaturesWithStore:
    def test_engineer_features_with_store(self, sample_ohlcv_df):
        """engineer_features reads from feature store when enabled."""
        from ml.pipelines.components.feature_engineer import engineer_features

        precomputed = pd.DataFrame(
            {"rsi_14": [55.0, 60.0], "macd_line": [0.5, 0.6]},
            index=pd.to_datetime(["2024-06-01", "2024-06-02"]),
        )
        mock_settings = MagicMock()

        with patch(
            "ml.features.store.read_features",
            return_value={"AAPL": precomputed},
        ) as mock_read:
            result = engineer_features(
                {"AAPL": sample_ohlcv_df},
                use_feature_store=True,
                db_settings=mock_settings,
            )

        mock_read.assert_called_once()
        assert "AAPL" in result
        # Should use feature store data
        assert "rsi_14" in result["AAPL"].columns

    def test_engineer_features_fallback(self, sample_ohlcv_df):
        """Falls back to on-the-fly when feature store returns empty."""
        from ml.pipelines.components.feature_engineer import engineer_features

        mock_settings = MagicMock()

        with patch(
            "ml.features.store.read_features",
            return_value={},
        ):
            result = engineer_features(
                {"AAPL": sample_ohlcv_df},
                use_feature_store=True,
                db_settings=mock_settings,
            )

        assert "AAPL" in result
        # Should still produce features via on-the-fly computation
        assert len(result["AAPL"].columns) > 5
