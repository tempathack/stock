"""Tests for the drift-triggered retraining pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.pipelines.drift_pipeline import trigger_retraining
from ml.pipelines.training_pipeline import PIPELINE_VERSION


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_synthetic_data() -> dict[str, pd.DataFrame]:
    """Generate realistic OHLCV data for 2 tickers."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-01", periods=300)
    data: dict[str, pd.DataFrame] = {}
    for ticker in ["AAPL", "MSFT"]:
        base_price = 100 + rng.uniform(0, 50)
        close = base_price + np.cumsum(rng.normal(0, 1, 300))
        close = np.maximum(close, 1.0)
        df = pd.DataFrame(
            {
                "open": close + rng.normal(0, 0.5, 300),
                "high": close + abs(rng.normal(0, 1, 300)),
                "low": close - abs(rng.normal(0, 1, 300)),
                "close": close,
                "volume": rng.integers(1_000_000, 10_000_000, 300).astype(float),
            },
            index=dates,
        )
        data[ticker] = df
    return data


@pytest.fixture(scope="module")
def drift_run(tmp_path_factory):
    """Run trigger_retraining once for the module."""
    base = tmp_path_factory.mktemp("drift")
    reg = str(base / "registry")
    srv = str(base / "serving")
    data = _make_synthetic_data()
    result = trigger_retraining(
        data_dict=data,
        registry_dir=reg,
        serving_dir=srv,
        reason="data_drift",
        skip_shap=True,
    )
    return result, reg, srv


# ---------------------------------------------------------------------------
# TestTriggerRetraining
# ---------------------------------------------------------------------------


class TestTriggerRetraining:
    def test_trigger_completes(self, drift_run):
        result, _reg, _srv = drift_run
        assert result.status == "completed"
        assert result.winner_info is not None

    def test_reason_recorded(self, drift_run):
        _result, reg, _srv = drift_run
        log_path = Path(reg) / "runs" / "retraining_log.jsonl"
        assert log_path.exists()
        with open(log_path) as f:
            lines = f.readlines()
        record = json.loads(lines[0])
        assert record["reason"] == "data_drift"

    def test_retraining_log_created(self, drift_run):
        _result, reg, _srv = drift_run
        log_path = Path(reg) / "runs" / "retraining_log.jsonl"
        assert log_path.exists()

    def test_retraining_log_content(self, drift_run):
        _result, reg, _srv = drift_run
        log_path = Path(reg) / "runs" / "retraining_log.jsonl"
        with open(log_path) as f:
            record = json.loads(f.readline())
        assert "run_id" in record
        assert "reason" in record
        assert "timestamp" in record
        assert "status" in record
        assert "pipeline_version" in record
        assert record["pipeline_version"] == PIPELINE_VERSION

    def test_multiple_triggers_append_log(self, tmp_path):
        """Two triggers append separate entries to the log."""
        reg = str(tmp_path / "registry")
        srv = str(tmp_path / "serving")
        data = _make_synthetic_data()

        trigger_retraining(
            data_dict=data,
            registry_dir=reg,
            serving_dir=srv,
            reason="manual",
            skip_shap=True,
        )
        trigger_retraining(
            data_dict=data,
            registry_dir=reg,
            serving_dir=srv,
            reason="data_drift",
            skip_shap=True,
        )

        log_path = Path(reg) / "runs" / "retraining_log.jsonl"
        with open(log_path) as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["reason"] == "manual"
        assert json.loads(lines[1])["reason"] == "data_drift"


# ---------------------------------------------------------------------------
# TestCompileKfpPipeline
# ---------------------------------------------------------------------------


class TestCompileKfpPipeline:
    def test_compile_creates_yaml(self, tmp_path):
        kfp = pytest.importorskip("kfp")
        from ml.pipelines.drift_pipeline import compile_kfp_pipeline

        output = str(tmp_path / "pipeline.yaml")
        result = compile_kfp_pipeline(output_path=output)
        assert Path(result).exists()
        assert result.endswith(".yaml")
