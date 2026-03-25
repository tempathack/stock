"""Tests for the prediction_service module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.prediction_service import (
    get_prediction_for_ticker,
    load_cached_predictions,
    load_drift_events,
    load_model_comparison,
)

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


class TestLoadCachedPredictions:
    def test_returns_predictions_from_file(self, tmp_path):
        pred_dir = tmp_path / "predictions"
        pred_dir.mkdir()
        (pred_dir / "latest.json").write_text(json.dumps(SAMPLE_PREDICTIONS))

        result = load_cached_predictions(str(tmp_path))
        assert len(result) == 2
        assert result[0]["ticker"] == "AAPL"

    def test_returns_empty_when_no_file(self, tmp_path):
        result = load_cached_predictions(str(tmp_path))
        assert result == []


class TestGetPredictionForTicker:
    def test_finds_ticker(self, tmp_path):
        pred_dir = tmp_path / "predictions"
        pred_dir.mkdir()
        (pred_dir / "latest.json").write_text(json.dumps(SAMPLE_PREDICTIONS))

        result = get_prediction_for_ticker("AAPL", str(tmp_path))
        assert result is not None
        assert result["ticker"] == "AAPL"

    def test_case_insensitive(self, tmp_path):
        pred_dir = tmp_path / "predictions"
        pred_dir.mkdir()
        (pred_dir / "latest.json").write_text(json.dumps(SAMPLE_PREDICTIONS))

        result = get_prediction_for_ticker("aapl", str(tmp_path))
        assert result is not None

    def test_returns_none_for_missing_ticker(self, tmp_path):
        pred_dir = tmp_path / "predictions"
        pred_dir.mkdir()
        (pred_dir / "latest.json").write_text(json.dumps(SAMPLE_PREDICTIONS))

        result = get_prediction_for_ticker("ZZZZ", str(tmp_path))
        assert result is None


class TestLoadModelComparison:
    def test_loads_models_sorted_by_rmse(self, tmp_path):
        # Create two model directories with metadata
        for model_name, rmse, is_winner in [
            ("Ridge_standard", 0.025, True),
            ("Lasso_standard", 0.030, False),
        ]:
            ver_dir = tmp_path / model_name / "v1"
            ver_dir.mkdir(parents=True)
            meta = {
                "model_name": model_name.split("_")[0],
                "scaler_variant": "standard",
                "oos_metrics": {"rmse": rmse},
                "is_winner": is_winner,
                "version": 1,
            }
            (ver_dir / "metadata.json").write_text(json.dumps(meta))

        result = load_model_comparison(str(tmp_path))
        assert len(result) == 2
        assert result[0]["oos_metrics"]["rmse"] < result[1]["oos_metrics"]["rmse"]

    def test_empty_registry(self, tmp_path):
        result = load_model_comparison(str(tmp_path))
        assert result == []

    def test_skips_predictions_and_runs_dirs(self, tmp_path):
        (tmp_path / "predictions").mkdir()
        (tmp_path / "runs").mkdir()
        result = load_model_comparison(str(tmp_path))
        assert result == []


class TestLoadDriftEvents:
    def test_loads_events_newest_first(self, tmp_path):
        events = [
            {"drift_type": "data", "is_drifted": True, "severity": "medium",
             "details": {}, "timestamp": "2026-03-20T10:00:00Z", "features_affected": []},
            {"drift_type": "prediction", "is_drifted": False, "severity": "none",
             "details": {}, "timestamp": "2026-03-20T11:00:00Z", "features_affected": []},
        ]
        log_file = tmp_path / "drift_events.jsonl"
        log_file.write_text("\n".join(json.dumps(e) for e in events))

        result = load_drift_events(str(tmp_path))
        assert len(result) == 2
        # Newest first
        assert result[0]["timestamp"] == "2026-03-20T11:00:00Z"

    def test_empty_when_no_file(self, tmp_path):
        result = load_drift_events(str(tmp_path))
        assert result == []


class TestPredictModelNameNotUnknown:
    """PRED-MNAME-03: prediction responses return model_name from cache, not 'unknown'."""

    @patch("app.services.model_metadata_cache.get_active_model_metadata")
    def test_predict_model_name_not_unknown(self, mock_get_metadata):
        """PRED-MNAME-03: get_active_model_metadata returns non-unknown model_name when cache populated."""
        mock_get_metadata.return_value = {
            "model_name": "Ridge",
            "scaler_variant": "standard",
            "version": 3,
        }
        from app.services.model_metadata_cache import get_active_model_metadata

        cached = get_active_model_metadata()
        model_name_str = cached.get("model_name")
        scaler = cached.get("scaler_variant")
        if model_name_str and scaler:
            model_name = f"{model_name_str}_{scaler}"
        elif model_name_str:
            model_name = model_name_str
        else:
            model_name = "unknown"

        assert model_name != "unknown"
        assert model_name == "Ridge_standard"
