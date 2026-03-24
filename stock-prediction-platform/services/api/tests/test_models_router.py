"""Tests for /models/comparison and /models/drift endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_MODELS = [
    {
        "model_name": "Ridge",
        "scaler_variant": "standard",
        "version": 1,
        "is_winner": True,
        "is_active": True,
        "oos_metrics": {"rmse": 0.025, "mae": 0.018, "r2": 0.92},
        "fold_stability": 0.003,
        "best_params": {"alpha": 1.0},
        "saved_at": "2026-03-20T10:00:00Z",
    },
    {
        "model_name": "Lasso",
        "scaler_variant": "standard",
        "version": 1,
        "is_winner": False,
        "is_active": False,
        "oos_metrics": {"rmse": 0.030, "mae": 0.022, "r2": 0.88},
        "fold_stability": 0.005,
        "best_params": {"alpha": 0.1},
        "saved_at": "2026-03-20T10:00:00Z",
    },
]

SAMPLE_DRIFT_EVENTS = [
    {
        "drift_type": "data",
        "is_drifted": True,
        "severity": "medium",
        "details": {"psi": 0.3, "features_drifted": 3},
        "timestamp": "2026-03-20T12:00:00Z",
        "features_affected": ["rsi_14", "macd_line", "sma_20"],
    },
    {
        "drift_type": "prediction",
        "is_drifted": False,
        "severity": "none",
        "details": {"error_ratio": 0.8},
        "timestamp": "2026-03-20T12:00:00Z",
        "features_affected": [],
    },
]


class TestModelsComparison:
    """Tests for GET /models/comparison."""

    @patch("app.routers.models.load_model_comparison")
    def test_returns_models(self, mock_load):
        mock_load.return_value = SAMPLE_MODELS
        resp = client.get("/models/comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["winner"]["model_name"] == "Ridge"

    @patch("app.routers.models.load_model_comparison")
    def test_empty_registry(self, mock_load):
        mock_load.return_value = []
        resp = client.get("/models/comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["winner"] is None

    @patch("app.routers.models.load_model_comparison")
    def test_response_schema(self, mock_load):
        mock_load.return_value = SAMPLE_MODELS
        resp = client.get("/models/comparison")
        data = resp.json()
        assert set(data.keys()) == {"models", "winner", "count"}
        model = data["models"][0]
        assert "model_name" in model
        assert "oos_metrics" in model
        assert "is_winner" in model

    @patch("app.routers.models.load_model_comparison")
    def test_no_winner_when_none_flagged(self, mock_load):
        models = [dict(m, is_winner=False) for m in SAMPLE_MODELS]
        mock_load.return_value = models
        resp = client.get("/models/comparison")
        data = resp.json()
        assert data["winner"] is None


class TestModelsDrift:
    """Tests for GET /models/drift."""

    @patch("app.routers.models.load_drift_events")
    def test_returns_events(self, mock_load):
        mock_load.return_value = SAMPLE_DRIFT_EVENTS
        resp = client.get("/models/drift")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["any_recent_drift"] is True
        assert data["latest_event"]["drift_type"] == "data"

    @patch("app.routers.models.load_drift_events")
    def test_no_events(self, mock_load):
        mock_load.return_value = []
        resp = client.get("/models/drift")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["any_recent_drift"] is False
        assert data["latest_event"] is None

    @patch("app.routers.models.load_drift_events")
    def test_no_drift_when_all_clean(self, mock_load):
        clean = [dict(e, is_drifted=False) for e in SAMPLE_DRIFT_EVENTS]
        mock_load.return_value = clean
        resp = client.get("/models/drift")
        data = resp.json()
        assert data["any_recent_drift"] is False

    @patch("app.routers.models.load_drift_events")
    def test_response_schema(self, mock_load):
        mock_load.return_value = SAMPLE_DRIFT_EVENTS
        resp = client.get("/models/drift")
        data = resp.json()
        assert set(data.keys()) == {
            "events", "any_recent_drift", "latest_event", "count",
        }
        event = data["events"][0]
        assert "drift_type" in event
        assert "severity" in event
        assert "is_drifted" in event
