"""Tests for ingestion endpoints: POST /ingest/intraday and POST /ingest/historical."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _fake_records(n: int = 3, mode: str = "intraday") -> list[dict]:
    """Generate n fake OHLCV records."""
    return [
        {
            "ticker": "AAPL",
            "timestamp": f"2026-03-19T14:3{i}:00+00:00",
            "open": 170.0 + i,
            "high": 171.0 + i,
            "low": 169.5 + i,
            "close": 170.8 + i,
            "volume": 10000 + i * 1000,
            "fetch_mode": mode,
            "ingested_at": "2026-03-19T15:00:00+00:00",
        }
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# POST /ingest/intraday
# ---------------------------------------------------------------------------


@patch("app.routers.ingest.OHLCVProducer")
@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_intraday_success(mock_yf_cls, mock_prod_cls):
    """POST /ingest/intraday returns 200 accepted immediately (background task)."""
    mock_svc = MagicMock()
    mock_svc.tickers = ["AAPL", "MSFT"]
    mock_svc.fetch_intraday.return_value = _fake_records(3, "intraday")
    mock_yf_cls.return_value = mock_svc

    mock_prod = MagicMock()
    mock_prod.produce_records.return_value = 3
    mock_prod_cls.return_value = mock_prod

    response = client.post("/ingest/intraday")
    assert response.status_code == 200
    data = response.json()
    # Background-task pattern: immediate "accepted" response with 0 counts
    assert data["status"] == "accepted"
    assert data["mode"] == "intraday"
    assert data["tickers_requested"] == 2


@patch("app.routers.ingest.OHLCVProducer")
@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_intraday_with_custom_tickers(mock_yf_cls, mock_prod_cls):
    """POST /ingest/intraday with body tickers uses those tickers."""
    mock_svc = MagicMock()
    mock_svc.fetch_intraday.return_value = _fake_records(2, "intraday")
    mock_yf_cls.return_value = mock_svc

    mock_prod = MagicMock()
    mock_prod.produce_records.return_value = 2
    mock_prod_cls.return_value = mock_prod

    response = client.post("/ingest/intraday", json={"tickers": ["AAPL", "MSFT"]})
    assert response.status_code == 200
    data = response.json()
    assert data["tickers_requested"] == 2
    mock_svc.fetch_intraday.assert_called_once_with(tickers=["AAPL", "MSFT"])


@patch("app.routers.ingest.OHLCVProducer")
@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_intraday_zero_records(mock_yf_cls, mock_prod_cls):
    """When fetch returns 0 records, Kafka producer is not called."""
    mock_svc = MagicMock()
    mock_svc.tickers = ["AAPL"]
    mock_svc.fetch_intraday.return_value = []
    mock_yf_cls.return_value = mock_svc

    response = client.post("/ingest/intraday")
    assert response.status_code == 200
    data = response.json()
    assert data["records_fetched"] == 0
    assert data["records_produced"] == 0
    mock_prod_cls.assert_not_called()


# ---------------------------------------------------------------------------
# POST /ingest/historical
# ---------------------------------------------------------------------------


@patch("app.routers.ingest.OHLCVProducer")
@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_historical_success(mock_yf_cls, mock_prod_cls):
    """POST /ingest/historical returns 200 accepted immediately (background task)."""
    mock_svc = MagicMock()
    mock_svc.tickers = ["AAPL"]
    mock_svc.fetch_historical.return_value = _fake_records(5, "historical")
    mock_yf_cls.return_value = mock_svc

    mock_prod = MagicMock()
    mock_prod.produce_records.return_value = 5
    mock_prod_cls.return_value = mock_prod

    response = client.post("/ingest/historical")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["mode"] == "historical"


@patch("app.routers.ingest.OHLCVProducer")
@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_historical_with_custom_tickers(mock_yf_cls, mock_prod_cls):
    """POST /ingest/historical with body tickers uses those tickers."""
    mock_svc = MagicMock()
    mock_svc.fetch_historical.return_value = _fake_records(1, "historical")
    mock_yf_cls.return_value = mock_svc

    mock_prod = MagicMock()
    mock_prod.produce_records.return_value = 1
    mock_prod_cls.return_value = mock_prod

    response = client.post("/ingest/historical", json={"tickers": ["GOOGL"]})
    assert response.status_code == 200
    mock_svc.fetch_historical.assert_called_once_with(tickers=["GOOGL"])


# ---------------------------------------------------------------------------
# Error handling — Yahoo Finance failure
# ---------------------------------------------------------------------------


@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_intraday_yf_failure_accepted(mock_yf_cls):
    """Yahoo Finance fetch failure is handled in background task — endpoint still returns 200."""
    mock_svc = MagicMock()
    mock_svc.tickers = ["AAPL"]
    mock_svc.fetch_intraday.side_effect = ConnectionError("Yahoo Finance unreachable")
    mock_yf_cls.return_value = mock_svc

    response = client.post("/ingest/intraday")
    # Background task swallows the error; endpoint always returns "accepted"
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_historical_yf_failure_accepted(mock_yf_cls):
    """Yahoo Finance fetch failure in historical is handled in background task."""
    mock_svc = MagicMock()
    mock_svc.tickers = ["AAPL"]
    mock_svc.fetch_historical.side_effect = RuntimeError("API down")
    mock_yf_cls.return_value = mock_svc

    response = client.post("/ingest/historical")
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


# ---------------------------------------------------------------------------
# Error handling — Kafka failure
# ---------------------------------------------------------------------------


@patch("app.routers.ingest.OHLCVProducer")
@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_intraday_kafka_failure_accepted(mock_yf_cls, mock_prod_cls):
    """Kafka produce failure is handled in background task — endpoint still returns 200."""
    mock_svc = MagicMock()
    mock_svc.tickers = ["AAPL"]
    mock_svc.fetch_intraday.return_value = _fake_records(1, "intraday")
    mock_yf_cls.return_value = mock_svc

    mock_prod = MagicMock()
    mock_prod.produce_records.side_effect = RuntimeError("Broker unavailable")
    mock_prod_cls.return_value = mock_prod

    response = client.post("/ingest/intraday")
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@patch("app.routers.ingest.OHLCVProducer")
@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_historical_kafka_failure_accepted(mock_yf_cls, mock_prod_cls):
    """Kafka produce failure in historical is handled in background task."""
    mock_svc = MagicMock()
    mock_svc.tickers = ["AAPL"]
    mock_svc.fetch_historical.return_value = _fake_records(1, "historical")
    mock_yf_cls.return_value = mock_svc

    mock_prod = MagicMock()
    mock_prod.produce_records.side_effect = RuntimeError("Broker down")
    mock_prod_cls.return_value = mock_prod

    response = client.post("/ingest/historical")
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


# ---------------------------------------------------------------------------
# Response schema tests
# ---------------------------------------------------------------------------


@patch("app.routers.ingest.OHLCVProducer")
@patch("app.routers.ingest.YahooFinanceService")
def test_response_has_correct_keys(mock_yf_cls, mock_prod_cls):
    """Response JSON has exactly the expected keys."""
    mock_svc = MagicMock()
    mock_svc.tickers = ["AAPL"]
    mock_svc.fetch_intraday.return_value = _fake_records(1, "intraday")
    mock_yf_cls.return_value = mock_svc

    mock_prod = MagicMock()
    mock_prod.produce_records.return_value = 1
    mock_prod_cls.return_value = mock_prod

    response = client.post("/ingest/intraday")
    expected_keys = {"status", "mode", "tickers_requested", "records_fetched", "records_produced"}
    assert set(response.json().keys()) == expected_keys


# ---------------------------------------------------------------------------
# Empty body / no body tests
# ---------------------------------------------------------------------------


@patch("app.routers.ingest.OHLCVProducer")
@patch("app.routers.ingest.YahooFinanceService")
def test_ingest_intraday_no_body(mock_yf_cls, mock_prod_cls):
    """POST /ingest/intraday with no body uses default tickers."""
    mock_svc = MagicMock()
    mock_svc.tickers = ["AAPL", "MSFT", "GOOGL"]
    mock_svc.fetch_intraday.return_value = _fake_records(3, "intraday")
    mock_yf_cls.return_value = mock_svc

    mock_prod = MagicMock()
    mock_prod.produce_records.return_value = 3
    mock_prod_cls.return_value = mock_prod

    response = client.post("/ingest/intraday")
    assert response.status_code == 200
    assert response.json()["tickers_requested"] == 3
    mock_svc.fetch_intraday.assert_called_once_with(tickers=["AAPL", "MSFT", "GOOGL"])
