"""Tests for Parquet serialisation helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.pipelines.serialization import load_dataframes, save_dataframes


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def two_ticker_dict() -> dict[str, pd.DataFrame]:
    """Two-ticker dict with 50-row DataFrames."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-01", periods=50)
    data: dict[str, pd.DataFrame] = {}
    for ticker in ["AAPL", "MSFT"]:
        data[ticker] = pd.DataFrame(
            {
                "open": rng.normal(100, 5, 50),
                "high": rng.normal(105, 5, 50),
                "low": rng.normal(95, 5, 50),
                "close": rng.normal(100, 5, 50),
                "volume": rng.integers(1_000_000, 10_000_000, 50).astype(float),
            },
            index=dates,
        )
    return data


# ---------------------------------------------------------------------------
# TestSaveDataframes
# ---------------------------------------------------------------------------


class TestSaveDataframes:
    def test_creates_parquet_files(self, two_ticker_dict, tmp_path):
        save_dataframes(two_ticker_dict, tmp_path / "out")
        assert (tmp_path / "out" / "AAPL.parquet").exists()
        assert (tmp_path / "out" / "MSFT.parquet").exists()

    def test_empty_dict_creates_empty_dir(self, tmp_path):
        out = save_dataframes({}, tmp_path / "empty")
        assert out.exists()
        assert list(out.glob("*.parquet")) == []

    def test_overwrites_existing(self, two_ticker_dict, tmp_path):
        out_dir = tmp_path / "overwrite"
        save_dataframes(two_ticker_dict, out_dir)
        # Second save with different data
        modified = {k: v.head(10) for k, v in two_ticker_dict.items()}
        save_dataframes(modified, out_dir)
        loaded = load_dataframes(out_dir)
        for ticker in ["AAPL", "MSFT"]:
            assert len(loaded[ticker]) == 10

    def test_preserves_index(self, tmp_path):
        dates = pd.bdate_range("2020-01-01", periods=20)
        df = pd.DataFrame({"close": range(20)}, index=dates)
        save_dataframes({"TEST": df}, tmp_path / "idx")
        loaded = load_dataframes(tmp_path / "idx")
        pd.testing.assert_index_equal(loaded["TEST"].index, dates)


# ---------------------------------------------------------------------------
# TestLoadDataframes
# ---------------------------------------------------------------------------


class TestLoadDataframes:
    def test_round_trip(self, two_ticker_dict, tmp_path):
        save_dataframes(two_ticker_dict, tmp_path / "rt")
        loaded = load_dataframes(tmp_path / "rt")
        assert set(loaded.keys()) == {"AAPL", "MSFT"}
        for ticker in ["AAPL", "MSFT"]:
            pd.testing.assert_frame_equal(
                loaded[ticker], two_ticker_dict[ticker], check_freq=False,
            )

    def test_empty_dir_returns_empty_dict(self, tmp_path):
        empty = tmp_path / "empty_dir"
        empty.mkdir()
        assert load_dataframes(empty) == {}

    def test_nonexistent_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_dataframes(tmp_path / "missing")


# ---------------------------------------------------------------------------
# TestRoundTripIntegrity
# ---------------------------------------------------------------------------


class TestRoundTripIntegrity:
    def test_numeric_precision(self, tmp_path):
        rng = np.random.default_rng(99)
        df = pd.DataFrame({"val": rng.random(100)})
        save_dataframes({"PREC": df}, tmp_path / "prec")
        loaded = load_dataframes(tmp_path / "prec")
        np.testing.assert_allclose(
            loaded["PREC"]["val"].values, df["val"].values, atol=1e-15,
        )
