"""Tests for Phase 43 — horizon query parameter on /predict endpoints."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_PRED = {
    "ticker": "AAPL",
    "prediction_date": "2026-03-20",
    "predicted_date": "2026-03-27",
    "predicted_price": 0.0234,
    "model_name": "Ridge_standard",
    "confidence": None,
}

SAMPLE_PRED_HORIZON = {
    **SAMPLE_PRED,
    "horizon_days": 7,
}


class TestPredictTickerHorizon:
    """GET /predict/{ticker} with ?horizon param."""

    @patch("app.routers.predict.get_live_prediction", return_value=None)
    @patch("app.routers.predict.get_prediction_for_ticker")
    def test_predict_ticker_default_horizon(self, mock_get, mock_live):
        """Without horizon param → backward-compatible response."""
        mock_get.return_value = SAMPLE_PRED
        resp = client.get("/predict/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        # horizon_days should be None when not specified
        assert data.get("horizon_days") is None

    @patch("app.routers.predict.get_live_prediction", return_value=None)
    @patch("app.routers.predict.get_prediction_for_ticker")
    def test_predict_ticker_with_horizon(self, mock_get, mock_live):
        """With ?horizon=7 → horizon_days echoed in response."""
        mock_get.return_value = SAMPLE_PRED_HORIZON
        resp = client.get("/predict/AAPL?horizon=7")
        assert resp.status_code == 200
        data = resp.json()
        assert data["horizon_days"] == 7

    @patch("app.routers.predict.get_live_prediction", return_value=None)
    def test_predict_ticker_invalid_horizon(self, mock_live):
        """?horizon=999 → 400 error with descriptive message."""
        resp = client.get("/predict/AAPL?horizon=999")
        assert resp.status_code == 400
        assert "999" in resp.json()["detail"]


class TestPredictBulkHorizon:
    """GET /predict/bulk with ?horizon param."""

    @patch("app.routers.predict.get_bulk_live_predictions", return_value=None)
    @patch("app.routers.predict.load_cached_predictions")
    def test_predict_bulk_default(self, mock_load, mock_live):
        """Without horizon → backward-compatible."""
        mock_load.return_value = [SAMPLE_PRED, SAMPLE_PRED]
        resp = client.get("/predict/bulk")
        assert resp.status_code == 200
        data = resp.json()
        assert data["horizon_days"] is None

    @patch("app.routers.predict.get_bulk_live_predictions", return_value=None)
    @patch("app.routers.predict.load_cached_predictions")
    def test_predict_bulk_with_horizon(self, mock_load, mock_live):
        """With ?horizon=1 → horizon_days in response."""
        mock_load.return_value = [SAMPLE_PRED_HORIZON]
        resp = client.get("/predict/bulk?horizon=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["horizon_days"] == 1

    @patch("app.routers.predict.get_bulk_live_predictions", return_value=None)
    def test_predict_bulk_invalid_horizon(self, mock_live):
        """?horizon=99 → 400 error."""
        resp = client.get("/predict/bulk?horizon=99")
        assert resp.status_code == 400
        assert "99" in resp.json()["detail"]


class TestPredictHorizonsEndpoint:
    """GET /predict/horizons."""

    @patch("app.routers.predict.load_available_horizons")
    def test_predict_horizons_endpoint(self, mock_load):
        """Returns list of available horizons."""
        mock_load.return_value = {"horizons": [1, 7, 30], "default": 7}
        resp = client.get("/predict/horizons")
        assert resp.status_code == 200
        data = resp.json()
        assert data["horizons"] == [1, 7, 30]
        assert data["default"] == 7

    def test_predict_horizons_with_manifest(self):
        """Reads horizons.json from serving dir when it exists."""
        tmp = tempfile.mkdtemp()
        manifest = {"horizons": [1, 7, 30], "default": 7}
        with open(Path(tmp) / "horizons.json", "w") as f:
            json.dump(manifest, f)

        with patch("app.routers.predict.settings") as mock_settings:
            mock_settings.SERVING_DIR = tmp
            # Load fresh to pick up settings
            from app.services.prediction_service import load_available_horizons
            result = load_available_horizons(serving_dir=tmp)
            assert result["horizons"] == [1, 7, 30]


class TestLoadAvailableHorizons:
    """Unit tests for load_available_horizons."""

    def test_fallback_when_no_file(self):
        """Returns default [7] when no horizons.json."""
        from app.services.prediction_service import load_available_horizons
        result = load_available_horizons(serving_dir="/nonexistent/dir")
        assert result == {"horizons": [7], "default": 7}


class TestHorizon14Support:
    """Tests confirming that horizon=14 is accepted (76-03: add 14D horizon support)."""

    @patch("app.routers.predict.get_bulk_live_predictions", return_value=None)
    @patch("app.routers.predict.load_cached_predictions")
    @patch("app.routers.predict.load_db_predictions")
    def test_bulk_horizon_14_accepted(self, mock_db, mock_load, mock_live):
        """GET /predict/bulk?horizon=14 returns HTTP 200 when AVAILABLE_HORIZONS includes 14.

        This test exercises _validate_horizon against the real settings object.
        It will FAIL (RED) while AVAILABLE_HORIZONS='1,7,30' and PASS (GREEN)
        after config.py is updated to AVAILABLE_HORIZONS='1,7,14,30'.
        """
        sample_pred = {
            "ticker": "AAPL",
            "prediction_date": "2026-03-20",
            "predicted_date": "2026-04-03",
            "predicted_price": 0.0234,
            "model_name": "Ridge_standard",
            "confidence": None,
            "horizon_days": 14,
        }
        mock_load.return_value = [sample_pred]
        mock_db.return_value = None
        resp = client.get("/predict/bulk?horizon=14")
        assert resp.status_code == 200, (
            f"Expected 200 for horizon=14 but got {resp.status_code}. "
            "Update AVAILABLE_HORIZONS in config.py to '1,7,14,30'."
        )

    @patch("app.routers.predict.get_bulk_live_predictions", return_value=None)
    def test_bulk_horizon_99_rejected(self, mock_live):
        """GET /predict/bulk?horizon=99 returns HTTP 400 — confirms validation logic is active."""
        resp = client.get("/predict/bulk?horizon=99")
        assert resp.status_code == 400, (
            f"Expected 400 for horizon=99 but got {resp.status_code}."
        )
        assert "99" in resp.json()["detail"]


class TestCachedPredictionHorizon:
    """Unit tests for horizon-aware cached prediction loading."""

    def test_cached_prediction_horizon(self):
        """Loads from latest_{h}d.json when horizon specified."""
        tmp = tempfile.mkdtemp()
        pred_dir = Path(tmp) / "predictions"
        pred_dir.mkdir()

        preds_7d = [{"ticker": "AAPL", "predicted_price": 185.0, "horizon_days": 7}]
        with open(pred_dir / "latest_7d.json", "w") as f:
            json.dump(preds_7d, f)

        from app.services.prediction_service import load_cached_predictions
        result = load_cached_predictions(registry_dir=tmp, horizon=7)
        assert len(result) == 1
        assert result[0]["horizon_days"] == 7

    def test_cached_prediction_no_horizon(self):
        """Loads from latest.json when no horizon specified."""
        tmp = tempfile.mkdtemp()
        pred_dir = Path(tmp) / "predictions"
        pred_dir.mkdir()

        preds = [{"ticker": "AAPL", "predicted_price": 180.0}]
        with open(pred_dir / "latest.json", "w") as f:
            json.dump(preds, f)

        from app.services.prediction_service import load_cached_predictions
        result = load_cached_predictions(registry_dir=tmp)
        assert len(result) == 1
