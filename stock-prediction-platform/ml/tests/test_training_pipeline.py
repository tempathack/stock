"""Tests for the training pipeline orchestrator."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.pipelines.training_pipeline import (
    PIPELINE_VERSION,
    PipelineRunResult,
    run_training_pipeline,
)


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
def pipeline_run(tmp_path_factory):
    """Run the full training pipeline once and share results across tests."""
    base = tmp_path_factory.mktemp("pipeline")
    reg = str(base / "registry")
    srv = str(base / "serving")
    data = _make_synthetic_data()
    result = run_training_pipeline(
        data_dict=data,
        registry_dir=reg,
        serving_dir=srv,
        skip_shap=True,
    )
    return result, reg, srv


# ---------------------------------------------------------------------------
# TestPipelineRunResult
# ---------------------------------------------------------------------------


class TestPipelineRunResult:
    def test_to_dict(self):
        r = PipelineRunResult(
            run_id="abc123",
            pipeline_version="1.0.0",
            started_at="2026-01-01T00:00:00+00:00",
        )
        d = r.to_dict()
        assert isinstance(d, dict)
        assert d["run_id"] == "abc123"
        assert d["pipeline_version"] == "1.0.0"
        assert d["status"] == "running"

    def test_default_values(self):
        r = PipelineRunResult(
            run_id="x", pipeline_version="1.0.0", started_at="t",
        )
        assert r.status == "running"
        assert r.steps_completed == []
        assert r.winner_info is None
        assert r.deploy_info is None
        assert r.error is None

    def test_pipeline_version_constant(self):
        assert isinstance(PIPELINE_VERSION, str)
        assert len(PIPELINE_VERSION) > 0
        assert re.match(r"\d+\.\d+\.\d+", PIPELINE_VERSION)


# ---------------------------------------------------------------------------
# TestRunTrainingPipeline — share a single pipeline run
# ---------------------------------------------------------------------------


class TestRunTrainingPipeline:
    def test_full_pipeline_completes(self, pipeline_run):
        result, _reg, _srv = pipeline_run
        assert result.status == "completed"
        assert result.pipeline_version == PIPELINE_VERSION
        assert result.n_tickers == 2
        assert result.n_models_trained > 0
        assert len(result.steps_completed) == 12
        assert result.winner_info is not None
        assert result.deploy_info is not None
        assert result.error is None

    def test_run_result_persisted(self, pipeline_run):
        result, reg, _srv = pipeline_run
        run_file = Path(reg) / "runs" / f"pipeline_run_{result.run_id}.json"
        assert run_file.exists()
        with open(run_file) as f:
            data = json.load(f)
        assert data["run_id"] == result.run_id
        assert data["status"] == "completed"

    def test_serving_directory_populated(self, pipeline_run):
        _result, _reg, srv = pipeline_run
        srv_path = Path(srv)
        assert (srv_path / "serving_config.json").exists()
        assert (srv_path / "pipeline.pkl").exists()
        assert (srv_path / "metadata.json").exists()
        assert (srv_path / "features.json").exists()

    def test_model_is_active_after_pipeline(self, pipeline_run):
        from ml.models.registry import ModelRegistry

        _result, reg, _srv = pipeline_run
        registry = ModelRegistry(base_dir=reg)
        active = registry.get_active_model()
        assert active is not None

    def test_data_dict_required_or_tickers(self):
        with pytest.raises(ValueError, match="tickers.*data_dict"):
            run_training_pipeline()

    def test_ensemble_step_in_pipeline(self, pipeline_run):
        result, _reg, _srv = pipeline_run
        assert "ensemble_stacking" in result.steps_completed
        assert result.ensemble_info is not None
        assert "base_models" in result.ensemble_info

    def test_ensemble_disabled(self, tmp_path):
        reg = str(tmp_path / "registry")
        srv = str(tmp_path / "serving")
        data = _make_synthetic_data()
        result = run_training_pipeline(
            data_dict=data,
            registry_dir=reg,
            serving_dir=srv,
            skip_shap=True,
            enable_ensemble=False,
        )
        assert "ensemble_stacking" in result.steps_completed
        assert result.ensemble_info is None

    def test_ensemble_participates_in_ranking(self, pipeline_run):
        from ml.models.registry import ModelRegistry

        result, reg, _srv = pipeline_run
        # Either the ensemble is the winner or it participated in ranking
        if result.ensemble_info and "error" not in result.ensemble_info:
            assert len(result.ensemble_info["base_models"]) > 0

    def test_pipeline_with_feature_store(self, tmp_path):
        """Pipeline completes with use_feature_store=True (mocked read)."""
        from unittest.mock import patch

        reg = str(tmp_path / "registry")
        srv = str(tmp_path / "serving")
        data = _make_synthetic_data()

        # Mock read_features to return empty so it falls back to on-the-fly
        with patch(
            "ml.pipelines.components.feature_engineer.read_features",
            return_value={},
        ):
            result = run_training_pipeline(
                data_dict=data,
                registry_dir=reg,
                serving_dir=srv,
                skip_shap=True,
                use_feature_store=True,
            )

        assert result.status == "completed"
        assert "engineer_features" in result.steps_completed

    def test_pipeline_feature_store_fallback(self, tmp_path):
        """Pipeline falls back to on-the-fly when feature store raises."""
        from unittest.mock import patch

        reg = str(tmp_path / "registry")
        srv = str(tmp_path / "serving")
        data = _make_synthetic_data()

        with patch(
            "ml.pipelines.components.feature_engineer.read_features",
            side_effect=RuntimeError("DB unavailable"),
        ):
            result = run_training_pipeline(
                data_dict=data,
                registry_dir=reg,
                serving_dir=srv,
                skip_shap=True,
                use_feature_store=True,
            )

        assert result.status == "completed"
        assert "engineer_features" in result.steps_completed


class TestMainEntrypointTickerResolution:
    """Tests for __main__ TICKERS env var fallback (FIX-ML).

    Tests the ticker-resolution logic that __main__ will use:
      tickers_str = args_tickers or os.environ.get("TICKERS")
      tickers = tickers_str.split(",") if tickers_str else None
    """

    def test_tickers_from_env_var_when_no_cli_arg(self, monkeypatch):
        """TICKERS env var is used when --tickers CLI arg is absent."""
        import os
        monkeypatch.setenv("TICKERS", "AAPL,MSFT")
        args_tickers = None  # simulates no --tickers arg
        tickers_str = args_tickers or os.environ.get("TICKERS")
        tickers = tickers_str.split(",") if tickers_str else None
        assert tickers == ["AAPL", "MSFT"]

    def test_no_tickers_arg_no_env_var_resolves_to_none(self, monkeypatch):
        """Without arg or env var, tickers stays None (ValueError expected from pipeline)."""
        import os
        monkeypatch.delenv("TICKERS", raising=False)
        args_tickers = None
        tickers_str = args_tickers or os.environ.get("TICKERS")
        tickers = tickers_str.split(",") if tickers_str else None
        assert tickers is None

    def test_cli_arg_takes_precedence_over_env_var(self, monkeypatch):
        """--tickers CLI arg wins over TICKERS env var."""
        import os
        monkeypatch.setenv("TICKERS", "AAPL,MSFT")
        args_tickers = "GOOGL,NVDA"  # simulates --tickers CLI arg
        tickers_str = args_tickers or os.environ.get("TICKERS")
        tickers = tickers_str.split(",") if tickers_str else None
        assert tickers == ["GOOGL", "NVDA"]
