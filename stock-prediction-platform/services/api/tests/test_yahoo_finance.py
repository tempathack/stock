"""Unit tests for YahooFinanceService: fetch, validation, ticker list, edge cases."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from app.services.yahoo_finance import YahooFinanceService


# ---------------------------------------------------------------------------
# Ticker list tests (INGEST-01)
# ---------------------------------------------------------------------------

def test_default_ticker_list():
    """YahooFinanceService uses 20 default tickers matching the hardcoded list."""
    svc = YahooFinanceService()
    expected = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
        "META", "TSLA", "BRK-B", "JPM", "JNJ",
        "V", "PG", "UNH", "HD", "MA",
        "BAC", "XOM", "PFE", "ABBV", "CVX",
    ]
    assert svc.tickers == expected
    assert len(svc.tickers) == 20


def test_ticker_list_from_config(monkeypatch):
    """Monkeypatched TICKER_SYMBOLS='AAPL,MSFT' yields exactly those two."""
    from app.config import settings
    monkeypatch.setattr(settings, "TICKER_SYMBOLS", "AAPL,MSFT")
    svc = YahooFinanceService()
    assert svc.tickers == ["AAPL", "MSFT"]


# ---------------------------------------------------------------------------
# Fetch tests (INGEST-02)
# ---------------------------------------------------------------------------

@patch("app.services.yahoo_finance._fetch_ticker_data")
def test_fetch_intraday_calls_yf_download(mock_fetch, mock_intraday_df):
    """fetch_intraday calls _fetch_ticker_data with period='1d', interval='1m'."""
    mock_fetch.return_value = mock_intraday_df
    svc = YahooFinanceService()
    svc.fetch_intraday(tickers=["AAPL"])
    mock_fetch.assert_called_once_with("AAPL", period="1d", interval="1m")


@patch("app.services.yahoo_finance._fetch_ticker_data")
def test_fetch_historical_calls_yf_download(mock_fetch, mock_historical_df):
    """fetch_historical calls _fetch_ticker_data with period='5y', interval='1d'."""
    mock_fetch.return_value = mock_historical_df
    svc = YahooFinanceService()
    svc.fetch_historical(tickers=["AAPL"])
    mock_fetch.assert_called_once_with("AAPL", period="5y", interval="1d")


@patch("app.services.yahoo_finance._fetch_ticker_data")
def test_fetch_returns_valid_records(mock_fetch, mock_intraday_df):
    """Fetch returns 3 records with correct keys."""
    mock_fetch.return_value = mock_intraday_df
    svc = YahooFinanceService()
    records = svc.fetch_intraday(tickers=["AAPL"])
    assert len(records) == 3
    expected_keys = {
        "ticker", "timestamp", "open", "high", "low",
        "close", "volume", "fetch_mode", "ingested_at",
    }
    for rec in records:
        assert set(rec.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Validation tests (INGEST-06)
# ---------------------------------------------------------------------------

def test_validate_rejects_nan_ohlc(mock_df_with_nan_ohlc):
    """NaN in OHLC column -> 0 valid, 1 skipped."""
    svc = YahooFinanceService()
    valid, skipped = svc.validate_ohlcv(mock_df_with_nan_ohlc, "TEST")
    assert len(valid) == 0
    assert skipped == 1


def test_validate_rejects_negative_volume(mock_df_with_negative_volume):
    """Negative volume -> 0 valid, 1 skipped."""
    svc = YahooFinanceService()
    valid, skipped = svc.validate_ohlcv(mock_df_with_negative_volume, "TEST")
    assert len(valid) == 0
    assert skipped == 1


def test_validate_rejects_nan_volume(mock_df_with_nan_volume):
    """NaN volume -> 0 valid, 1 skipped."""
    svc = YahooFinanceService()
    valid, skipped = svc.validate_ohlcv(mock_df_with_nan_volume, "TEST")
    assert len(valid) == 0
    assert skipped == 1


def test_validate_rejects_high_lt_low(mock_df_with_high_lt_low):
    """High < Low -> 0 valid, 1 skipped."""
    svc = YahooFinanceService()
    valid, skipped = svc.validate_ohlcv(mock_df_with_high_lt_low, "TEST")
    assert len(valid) == 0
    assert skipped == 1


def test_validate_passes_zero_volume(mock_df_with_zero_volume):
    """Volume=0 is valid (pre-market/after-hours bar)."""
    svc = YahooFinanceService()
    valid, skipped = svc.validate_ohlcv(mock_df_with_zero_volume, "TEST")
    assert len(valid) == 1
    assert skipped == 0


# ---------------------------------------------------------------------------
# Edge case / empty tests
# ---------------------------------------------------------------------------

@patch("app.services.yahoo_finance._fetch_ticker_data")
def test_fetch_empty_df_skips_ticker(mock_fetch, mock_empty_df):
    """Empty DataFrame -> 0 records, no exception."""
    mock_fetch.return_value = mock_empty_df
    svc = YahooFinanceService()
    records = svc.fetch_intraday(tickers=["FAKE"])
    assert len(records) == 0


# ---------------------------------------------------------------------------
# Timestamp normalization tests
# ---------------------------------------------------------------------------

@patch("app.services.yahoo_finance._fetch_ticker_data")
def test_timestamp_normalized_to_utc(mock_fetch, mock_intraday_df):
    """US/Eastern timestamps are converted to UTC (+00:00)."""
    mock_fetch.return_value = mock_intraday_df
    svc = YahooFinanceService()
    records = svc.fetch_intraday(tickers=["AAPL"])
    for rec in records:
        assert "+00:00" in rec["timestamp"]


@patch("app.services.yahoo_finance._fetch_ticker_data")
def test_historical_timestamp_normalized_to_utc(mock_fetch, mock_historical_df):
    """Tz-naive historical timestamps are localized to UTC (+00:00)."""
    mock_fetch.return_value = mock_historical_df
    svc = YahooFinanceService()
    records = svc.fetch_historical(tickers=["AAPL"])
    for rec in records:
        assert "+00:00" in rec["timestamp"]


# ---------------------------------------------------------------------------
# fetch_mode field tests
# ---------------------------------------------------------------------------

@patch("app.services.yahoo_finance._fetch_ticker_data")
def test_fetch_mode_intraday(mock_fetch, mock_intraday_df):
    """Intraday fetch sets fetch_mode='intraday' on all records."""
    mock_fetch.return_value = mock_intraday_df
    svc = YahooFinanceService()
    records = svc.fetch_intraday(tickers=["AAPL"])
    for rec in records:
        assert rec["fetch_mode"] == "intraday"


@patch("app.services.yahoo_finance._fetch_ticker_data")
def test_fetch_mode_historical(mock_fetch, mock_historical_df):
    """Historical fetch sets fetch_mode='historical' on all records."""
    mock_fetch.return_value = mock_historical_df
    svc = YahooFinanceService()
    records = svc.fetch_historical(tickers=["AAPL"])
    for rec in records:
        assert rec["fetch_mode"] == "historical"
