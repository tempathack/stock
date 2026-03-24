"""Tests for /predict/{ticker} and /predict/bulk endpoints."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_PREDICTIONS = [
    {
        "ticker": "AAPL",
        "prediction_date": "2026-03-20",
        "predicted_date": "2026-03-27",
        "predicted_price": 0.0234,
        "model_name": "Ridge_standard",
        "confidence": None,
    },
    {
        "ticker": "MSFT",
        "prediction_date": "2026-03-20",
        "predicted_date": "2026-03-27",
        "predicted_price": 0.0156,
        "model_name": "Ridge_standard",
        "confidence": None,
    },
]


class TestPredictTicker:
    """Tests for GET /predict/{ticker}."""

    @patch("app.routers.predict.get_prediction_for_ticker")
    def test_returns_prediction(self, mock_get):
        mock_get.return_value = SAMPLE_PREDICTIONS[0]
        resp = client.get("/predict/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["predicted_price"] == 0.0234
        assert data["model_name"] == "Ridge_standard"

    @patch("app.routers.predict.get_prediction_for_ticker")
    def test_case_insensitive_lookup(self, mock_get):
        mock_get.return_value = SAMPLE_PREDICTIONS[0]
        resp = client.get("/predict/aapl")
        assert resp.status_code == 200
        mock_get.assert_called_once()

    @patch("app.routers.predict.get_prediction_for_ticker")
    def test_ticker_not_found(self, mock_get):
        mock_get.return_value = None
        resp = client.get("/predict/ZZZZ")
        assert resp.status_code == 404
        assert "ZZZZ" in resp.json()["detail"]

    @patch("app.routers.predict.get_prediction_for_ticker")
    def test_response_schema_fields(self, mock_get):
        mock_get.return_value = SAMPLE_PREDICTIONS[0]
        resp = client.get("/predict/AAPL")
        data = resp.json()
        assert set(data.keys()) == {
            "ticker", "prediction_date", "predicted_date",
            "predicted_price", "model_name", "confidence", "horizon_days",
        }


class TestPredictBulk:
    """Tests for GET /predict/bulk."""

    @patch("app.routers.predict.load_cached_predictions")
    def test_returns_all_predictions(self, mock_load):
        mock_load.return_value = SAMPLE_PREDICTIONS
        resp = client.get("/predict/bulk")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["model_name"] == "Ridge_standard"
        assert len(data["predictions"]) == 2

    @patch("app.routers.predict.load_cached_predictions")
    def test_empty_predictions_returns_404(self, mock_load):
        mock_load.return_value = []
        resp = client.get("/predict/bulk")
        assert resp.status_code == 404

    @patch("app.routers.predict.load_cached_predictions")
    def test_bulk_response_schema(self, mock_load):
        mock_load.return_value = SAMPLE_PREDICTIONS
        resp = client.get("/predict/bulk")
        data = resp.json()
        assert set(data.keys()) == {
            "predictions", "model_name", "generated_at", "count", "horizon_days",
        }
        for pred in data["predictions"]:
            assert "ticker" in pred
            assert "predicted_price" in pred
