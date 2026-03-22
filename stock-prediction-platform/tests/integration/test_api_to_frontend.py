"""TEST-03: API → Frontend contract integration tests.

Validates all FastAPI endpoints return correctly shaped responses
matching the frontend TypeScript interface contracts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_snake_case(key: str) -> bool:
    """Return True if key follows snake_case convention."""
    return bool(re.match(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$", key))


def _assert_all_keys_snake_case(data, path: str = "") -> None:
    """Recursively assert all dict keys are snake_case."""
    if isinstance(data, dict):
        for key in data:
            full = f"{path}.{key}" if path else key
            assert _is_snake_case(key), f"Non-snake_case key: {full}"
            _assert_all_keys_snake_case(data[key], full)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            _assert_all_keys_snake_case(item, f"{path}[{i}]")


# ---------------------------------------------------------------------------
# Fixtures — seed file-based data
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_settings(tmp_path, monkeypatch):
    """Seed temporary model_registry and drift_logs then patch settings."""
    # Model registry — two models
    for model_info in [
        {
            "model_name": "CatBoost",
            "scaler_variant": "standard",
            "version": 1,
            "is_winner": True,
            "is_active": True,
            "oos_metrics": {"rmse": 0.023, "mae": 0.018, "r2": 0.85},
            "fold_stability": 0.009,
            "best_params": {"depth": 6},
            "saved_at": "2026-03-18T12:00:00Z",
        },
        {
            "model_name": "Ridge",
            "scaler_variant": "quantile",
            "version": 1,
            "is_winner": False,
            "is_active": False,
            "oos_metrics": {"rmse": 0.041, "mae": 0.033, "r2": 0.72},
            "fold_stability": 0.012,
            "best_params": {"alpha": 1.5},
            "saved_at": "2026-03-18T12:00:00Z",
        },
    ]:
        name = f"{model_info['model_name']}_{model_info['scaler_variant']}"
        ver_dir = tmp_path / "registry" / name / f"v{model_info['version']}"
        ver_dir.mkdir(parents=True)
        with open(ver_dir / "metadata.json", "w") as f:
            json.dump(model_info, f)

    # Predictions
    pred_dir = tmp_path / "registry" / "predictions"
    pred_dir.mkdir(parents=True)
    predictions = []
    for ticker in ["AAPL", "MSFT", "GOOGL"]:
        for day in range(1, 8):
            predictions.append(
                {
                    "ticker": ticker,
                    "prediction_date": "2026-03-20",
                    "predicted_date": f"2026-03-{20 + day}",
                    "predicted_price": 180.0 + day * 0.5,
                    "model_name": "CatBoost_standard",
                    "confidence": None,
                }
            )
    with open(pred_dir / "latest.json", "w") as f:
        json.dump(predictions, f)

    # Drift logs
    drift_dir = tmp_path / "drift_logs"
    drift_dir.mkdir(parents=True)
    events = [
        {
            "drift_type": "data_drift",
            "is_drifted": True,
            "severity": "medium",
            "details": {"n_features_drifted": 3},
            "timestamp": "2026-03-19T12:00:00Z",
            "features_affected": ["rsi_14", "macd_line"],
        },
        {
            "drift_type": "prediction_drift",
            "is_drifted": False,
            "severity": "low",
            "details": {"error_ratio": 1.1},
            "timestamp": "2026-03-18T12:00:00Z",
            "features_affected": [],
        },
        {
            "drift_type": "concept_drift",
            "is_drifted": True,
            "severity": "high",
            "details": {"degradation_ratio": 1.8},
            "timestamp": "2026-03-17T12:00:00Z",
            "features_affected": [],
        },
    ]
    with open(drift_dir / "drift_events.jsonl", "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    monkeypatch.setattr("app.config.settings.MODEL_REGISTRY_DIR", str(tmp_path / "registry"))
    monkeypatch.setattr("app.config.settings.DRIFT_LOG_DIR", str(drift_dir))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAPIFrontendContract:
    """TEST-03: Every endpoint returns shapes matching TypeScript interfaces."""

    # ── Test 1: /health ───────────────────────────────────────────────

    def test_health_response_shape(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "service" in data and isinstance(data["service"], str)
        assert "version" in data and isinstance(data["version"], str)
        assert "status" in data and data["status"] == "ok"

    # ── Test 2: /predict/{ticker} ─────────────────────────────────────

    def test_predict_ticker_response_shape(self):
        resp = client.get("/predict/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert isinstance(data["predicted_price"], (int, float))
        for key in ("prediction_date", "predicted_date", "model_name"):
            assert key in data

    # ── Test 3: /predict/bulk ─────────────────────────────────────────

    def test_predict_bulk_response_shape(self):
        resp = client.get("/predict/bulk")
        assert resp.status_code == 200
        data = resp.json()
        assert "predictions" in data and isinstance(data["predictions"], list)
        assert "model_name" in data
        assert "generated_at" in data
        assert data["count"] == len(data["predictions"])
        for item in data["predictions"]:
            assert "ticker" in item
            assert "predicted_price" in item

    # ── Test 4: /predict unknown ticker → 404 ─────────────────────────

    def test_predict_unknown_ticker_404(self):
        resp = client.get("/predict/ZZZZ")
        assert resp.status_code == 404

    # ── Test 5: /models/comparison ────────────────────────────────────

    def test_models_comparison_response_shape(self):
        resp = client.get("/models/comparison")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data and isinstance(data["models"], list)
        assert "winner" in data
        assert "count" in data
        assert data["count"] == len(data["models"])

        # Each model entry should have the required fields
        for m in data["models"]:
            for key in (
                "model_name",
                "scaler_variant",
                "is_winner",
                "is_active",
                "oos_metrics",
                "best_params",
            ):
                assert key in m, f"Missing key '{key}' in model entry"

        winners = [m for m in data["models"] if m["is_winner"]]
        assert len(winners) == 1

    # ── Test 6: /models/drift ─────────────────────────────────────────

    def test_models_drift_response_shape(self):
        resp = client.get("/models/drift")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data and isinstance(data["events"], list)
        assert "any_recent_drift" in data and isinstance(data["any_recent_drift"], bool)
        assert "latest_event" in data
        assert "count" in data

        for ev in data["events"]:
            for key in (
                "drift_type",
                "is_drifted",
                "severity",
                "details",
                "timestamp",
                "features_affected",
            ):
                assert key in ev, f"Missing key '{key}' in drift event"
            assert ev["drift_type"] in ("data_drift", "prediction_drift", "concept_drift")

    # ── Test 7: /market/overview ──────────────────────────────────────

    @patch("app.routers.market.get_market_overview")
    def test_market_overview_response_shape(self, mock_overview):
        mock_overview.return_value = [
            {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "sector": "Technology",
                "market_cap": 3_400_000_000_000,
                "last_close": 178.50,
                "daily_change_pct": 1.23,
            },
            {
                "ticker": "MSFT",
                "company_name": "Microsoft Corp.",
                "sector": "Technology",
                "market_cap": 3_100_000_000_000,
                "last_close": 425.30,
                "daily_change_pct": -0.45,
            },
        ]
        resp = client.get("/market/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "stocks" in data and isinstance(data["stocks"], list)
        assert "count" in data and data["count"] == 2

        for stock in data["stocks"]:
            for key in (
                "ticker",
                "company_name",
                "sector",
                "market_cap",
                "last_close",
                "daily_change_pct",
            ):
                assert key in stock

    # ── Test 8: /market/indicators/{ticker} ───────────────────────────

    @patch("app.routers.market.get_ticker_indicators")
    def test_market_indicators_response_shape(self, mock_indicators):
        mock_indicators.return_value = {
            "ticker": "AAPL",
            "latest": {
                "date": "2026-03-19",
                "close": 178.50,
                "rsi_14": 55.3,
                "macd_line": 1.23,
                "macd_signal": 1.10,
                "macd_histogram": 0.13,
                "stoch_k": None,
                "stoch_d": None,
                "sma_20": 175.0,
                "sma_50": 172.0,
                "sma_200": 168.0,
                "ema_12": None,
                "ema_26": None,
                "adx": None,
                "bb_upper": 182.0,
                "bb_middle": 175.0,
                "bb_lower": 168.0,
                "atr": 3.5,
                "rolling_volatility_21": None,
                "obv": None,
                "vwap": None,
                "volume_sma_20": None,
                "ad_line": None,
                "return_1d": None,
                "return_5d": None,
                "return_21d": None,
                "log_return": None,
            },
            "series": [
                {
                    "date": "2026-03-19",
                    "close": 178.50,
                    "rsi_14": 55.3,
                    "macd_line": 1.23,
                    "macd_signal": None,
                    "macd_histogram": None,
                    "stoch_k": None,
                    "stoch_d": None,
                    "sma_20": 175.0,
                    "sma_50": None,
                    "sma_200": None,
                    "ema_12": None,
                    "ema_26": None,
                    "adx": None,
                    "bb_upper": 182.0,
                    "bb_middle": None,
                    "bb_lower": None,
                    "atr": 3.5,
                    "rolling_volatility_21": None,
                    "obv": None,
                    "vwap": None,
                    "volume_sma_20": None,
                    "ad_line": None,
                    "return_1d": None,
                    "return_5d": None,
                    "return_21d": None,
                    "log_return": None,
                },
            ],
            "count": 1,
        }
        resp = client.get("/market/indicators/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert "latest" in data
        assert "series" in data and isinstance(data["series"], list)
        assert "count" in data

        latest = data["latest"]
        for key in ("date", "close", "rsi_14", "macd_line", "sma_20", "bb_upper", "atr"):
            assert key in latest

    # ── Test 9: /market/indicators unknown ticker → 404 ───────────────

    @patch("app.routers.market.get_ticker_indicators")
    def test_market_indicators_unknown_ticker_404(self, mock_indicators):
        mock_indicators.return_value = None
        resp = client.get("/market/indicators/ZZZZ")
        assert resp.status_code == 404

    # ── Test 10: /ingest/intraday ─────────────────────────────────────

    @patch("app.routers.ingest.OHLCVProducer")
    @patch("app.routers.ingest.YahooFinanceService")
    def test_ingest_intraday_response_shape(self, mock_yf_cls, mock_prod_cls):
        mock_svc = MagicMock()
        mock_svc.tickers = ["AAPL"]
        mock_svc.fetch_intraday.return_value = [
            {"ticker": "AAPL", "fetch_mode": "intraday"},
        ]
        mock_yf_cls.return_value = mock_svc

        mock_prod = MagicMock()
        mock_prod.produce_records.return_value = 1
        mock_prod_cls.return_value = mock_prod

        resp = client.post("/ingest/intraday")
        assert resp.status_code == 200
        data = resp.json()
        for key in ("status", "mode", "tickers_requested", "records_fetched", "records_produced"):
            assert key in data, f"Missing key '{key}' in ingest response"

    # ── Test 11: /ingest/historical ───────────────────────────────────

    @patch("app.routers.ingest.OHLCVProducer")
    @patch("app.routers.ingest.YahooFinanceService")
    def test_ingest_historical_response_shape(self, mock_yf_cls, mock_prod_cls):
        mock_svc = MagicMock()
        mock_svc.tickers = ["AAPL"]
        mock_svc.fetch_historical.return_value = [
            {"ticker": "AAPL", "fetch_mode": "historical"},
        ]
        mock_yf_cls.return_value = mock_svc

        mock_prod = MagicMock()
        mock_prod.produce_records.return_value = 1
        mock_prod_cls.return_value = mock_prod

        resp = client.post("/ingest/historical")
        assert resp.status_code == 200
        data = resp.json()
        for key in ("status", "mode", "tickers_requested", "records_fetched", "records_produced"):
            assert key in data

    # ── Test 12: all response keys are snake_case ─────────────────────

    @patch("app.routers.market.get_market_overview")
    def test_all_response_keys_are_snake_case(self, mock_overview):
        mock_overview.return_value = [
            {
                "ticker": "AAPL",
                "company_name": "Apple",
                "sector": "Tech",
                "market_cap": 3_000_000_000_000,
                "last_close": 178.0,
                "daily_change_pct": 0.5,
            },
        ]

        endpoints = [
            ("GET", "/health"),
            ("GET", "/predict/AAPL"),
            ("GET", "/predict/bulk"),
            ("GET", "/models/comparison"),
            ("GET", "/models/drift"),
            ("GET", "/market/overview"),
        ]

        for method, path in endpoints:
            resp = client.request(method, path)
            if resp.status_code == 200:
                _assert_all_keys_snake_case(resp.json())
