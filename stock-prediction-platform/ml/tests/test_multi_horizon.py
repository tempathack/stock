"""Tests for Phase 43 — multi-horizon prediction pipeline."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.features.lag_features import generate_target
from ml.pipelines.components.label_generator import (
    generate_labels,
    generate_multi_horizon_labels,
)


# ── Label generation tests ───────────────────────────────────────────────


def test_generate_multi_horizon_labels_basic(sample_ohlcv_df: pd.DataFrame):
    """All 3 target columns present with correct feature names."""
    data = {"AAPL": sample_ohlcv_df.copy()}
    result = generate_multi_horizon_labels(data, horizons=[1, 7, 30])

    assert "data" in result
    assert "feature_names" in result
    assert "target_cols" in result
    assert result["target_cols"] == ["target_1d", "target_7d", "target_30d"]

    df = result["data"]["AAPL"]
    for col in result["target_cols"]:
        assert col in df.columns

    # Feature names must exclude ALL target columns
    for col in result["target_cols"]:
        assert col not in result["feature_names"]
    assert len(result["feature_names"]) > 0


def test_generate_multi_horizon_labels_drops_nans(sample_ohlcv_df: pd.DataFrame):
    """30d horizon causes more row drops than 1d alone."""
    data = {"AAPL": sample_ohlcv_df.copy()}

    result_short = generate_multi_horizon_labels(data, horizons=[1])
    result_long = generate_multi_horizon_labels(data, horizons=[1, 30])

    # With 30d horizon we lose more trailing rows
    n_short = len(result_short["data"]["AAPL"])
    n_long = len(result_long["data"]["AAPL"])
    assert n_short > n_long


def test_generate_multi_horizon_labels_empty():
    """Empty input returns empty result."""
    result = generate_multi_horizon_labels({}, horizons=[1, 7, 30])
    assert result["data"] == {}
    assert result["feature_names"] == []
    assert result["target_cols"] == ["target_1d", "target_7d", "target_30d"]


def test_generate_multi_horizon_labels_single(sample_ohlcv_df: pd.DataFrame):
    """Single horizon [7] behaves consistently with generate_labels(horizon=7)."""
    data = {"AAPL": sample_ohlcv_df.copy()}

    multi = generate_multi_horizon_labels(data, horizons=[7])
    single, single_features = generate_labels(
        {"AAPL": sample_ohlcv_df.copy()}, horizon=7,
    )

    assert len(multi["data"]["AAPL"]) == len(single["AAPL"])
    assert "target_7d" in multi["target_cols"]


# ── Deployer tests ───────────────────────────────────────────────────────


def test_deploy_multi_horizon_winners(sample_ohlcv_df: pd.DataFrame):
    """deploy_multi_horizon_winners writes horizons.json."""
    from ml.pipelines.components.deployer import deploy_multi_horizon_winners

    tmp = tempfile.mkdtemp()
    try:
        registry_dir = Path(tmp) / "registry"
        serving_dir = Path(tmp) / "serving"

        # deploy_multi_horizon_winners with no winners should log warnings
        result = deploy_multi_horizon_winners(
            str(registry_dir), str(serving_dir), horizons=[1, 7],
        )
        # No winners exist, so result should be empty
        assert isinstance(result, dict)

        # horizons.json should still be written
        manifest_path = serving_dir / "horizons.json"
        assert manifest_path.exists()
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert "horizons" in manifest
        assert manifest["default"] == 7
    finally:
        shutil.rmtree(tmp)


# ── Predictor tests ──────────────────────────────────────────────────────


def test_predictor_backward_compat(sample_ohlcv_df: pd.DataFrame):
    """generate_predictions without horizons param works as before."""
    from ml.pipelines.components.predictor import generate_predictions

    # Without a real serving dir, this should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        generate_predictions(
            {"AAPL": sample_ohlcv_df},
            serving_dir="/nonexistent/path",
        )


def test_predictor_multi_horizon_no_models(sample_ohlcv_df: pd.DataFrame):
    """generate_predictions with horizons but no serving dirs returns empty."""
    from ml.pipelines.components.predictor import generate_predictions

    tmp = tempfile.mkdtemp()
    try:
        preds = generate_predictions(
            {"AAPL": sample_ohlcv_df},
            serving_dir=tmp,
            horizons=[1, 7],
        )
        assert preds == []
    finally:
        shutil.rmtree(tmp)


# ── Save predictions tests ──────────────────────────────────────────────


def test_save_predictions_multi_horizon():
    """save_predictions with horizons writes per-horizon files."""
    from ml.pipelines.components.predictor import save_predictions

    tmp = tempfile.mkdtemp()
    try:
        preds = [
            {"ticker": "AAPL", "horizon_days": 1, "predicted_price": 180.0},
            {"ticker": "AAPL", "horizon_days": 7, "predicted_price": 185.0},
            {"ticker": "MSFT", "horizon_days": 1, "predicted_price": 420.0},
        ]
        save_predictions(preds, registry_dir=tmp, horizons=[1, 7])

        pred_dir = Path(tmp) / "predictions"
        assert (pred_dir / "latest.json").exists()
        assert (pred_dir / "latest_1d.json").exists()
        assert (pred_dir / "latest_7d.json").exists()

        with open(pred_dir / "latest_1d.json") as f:
            h1 = json.load(f)
        assert len(h1) == 2  # AAPL + MSFT for 1d

        with open(pred_dir / "latest_7d.json") as f:
            h7 = json.load(f)
        assert len(h7) == 1  # AAPL only for 7d
    finally:
        shutil.rmtree(tmp)
