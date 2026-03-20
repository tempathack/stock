"""Tests for prediction generation using the active deployed model."""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.pipelines.components.predictor import generate_predictions, save_predictions


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_ohlcv():
    """Generate minimal OHLCV data for 2 tickers — enough for feature engineering."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-01", periods=300)
    data = {}
    for ticker in ["AAPL", "MSFT"]:
        close = 100 + np.cumsum(rng.normal(0, 1, 300))
        close = np.maximum(close, 1.0)
        df = pd.DataFrame({
            "open": close + rng.normal(0, 0.5, 300),
            "high": close + abs(rng.normal(0, 1, 300)),
            "low": close - abs(rng.normal(0, 1, 300)),
            "close": close,
            "volume": rng.integers(1_000_000, 10_000_000, 300).astype(float),
        }, index=dates)
        data[ticker] = df
    return data


@pytest.fixture
def serving_dir(tmp_path, synthetic_ohlcv):
    """Create a serving directory with a trained pipeline."""
    from ml.pipelines.components.feature_engineer import engineer_features

    srv = tmp_path / "serving"
    srv.mkdir()

    # Engineer features to get feature names
    enriched = engineer_features(synthetic_ohlcv)
    sample_df = list(enriched.values())[0]
    # Use numeric columns only (exclude any non-numeric)
    feature_names = [c for c in sample_df.columns
                     if c not in ("open", "high", "low", "close", "volume")
                     and sample_df[c].dtype in (np.float64, np.float32, np.int64)]
    if not feature_names:
        feature_names = ["close", "volume"]

    # Train a simple pipeline on synthetic data (drop NaN from feature warm-up)
    clean = sample_df[feature_names].dropna()
    X = clean.values
    y = np.random.default_rng(99).normal(0, 1, len(X))
    pipe = Pipeline([("scaler", StandardScaler()), ("model", Ridge())])
    pipe.fit(X, y)

    # Save artifacts
    with open(srv / "pipeline.pkl", "wb") as f:
        pickle.dump(pipe, f)
    with open(srv / "features.json", "w") as f:
        json.dump(feature_names, f)
    with open(srv / "metadata.json", "w") as f:
        json.dump({"model_name": "ridge_standard", "version": 1}, f)

    return str(srv)


# ---------------------------------------------------------------------------
# TestGeneratePredictions
# ---------------------------------------------------------------------------


class TestGeneratePredictions:
    def test_generates_predictions_for_all_tickers(self, synthetic_ohlcv, serving_dir):
        preds = generate_predictions(synthetic_ohlcv, serving_dir=serving_dir)
        tickers_predicted = {p["ticker"] for p in preds}
        assert "AAPL" in tickers_predicted
        assert "MSFT" in tickers_predicted
        assert len(preds) == 2

    def test_prediction_has_required_fields(self, synthetic_ohlcv, serving_dir):
        preds = generate_predictions(synthetic_ohlcv, serving_dir=serving_dir)
        required = {"ticker", "prediction_date", "predicted_date",
                     "predicted_price", "model_name", "confidence"}
        for pred in preds:
            assert required.issubset(pred.keys())

    def test_prediction_values_are_numeric(self, synthetic_ohlcv, serving_dir):
        preds = generate_predictions(synthetic_ohlcv, serving_dir=serving_dir)
        for pred in preds:
            assert isinstance(pred["predicted_price"], float)

    def test_missing_serving_dir_raises(self, synthetic_ohlcv, tmp_path):
        with pytest.raises(FileNotFoundError):
            generate_predictions(synthetic_ohlcv, serving_dir=str(tmp_path / "nope"))

    def test_model_name_from_metadata(self, synthetic_ohlcv, serving_dir):
        preds = generate_predictions(synthetic_ohlcv, serving_dir=serving_dir)
        for pred in preds:
            assert pred["model_name"] == "ridge_standard"


# ---------------------------------------------------------------------------
# TestSavePredictions
# ---------------------------------------------------------------------------


class TestSavePredictions:
    def test_saves_to_file(self, tmp_path):
        preds = [{"ticker": "AAPL", "predicted_price": 150.0}]
        path = save_predictions(preds, registry_dir=str(tmp_path / "reg"))
        assert path.exists()
        with open(path) as f:
            loaded = json.load(f)
        assert len(loaded) == 1
        assert loaded[0]["ticker"] == "AAPL"

    def test_creates_directory(self, tmp_path):
        reg = str(tmp_path / "new_reg")
        save_predictions([], registry_dir=reg)
        assert (Path(reg) / "predictions" / "latest.json").exists()
