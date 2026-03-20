"""Parquet I/O helpers for inter-component data transfer."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def save_dataframes(
    data_dict: dict[str, pd.DataFrame],
    output_dir: str | Path,
) -> Path:
    """Save per-ticker DataFrames as Parquet files in *output_dir*.

    Each ticker's DataFrame is written as ``{ticker}.parquet`` using the
    pyarrow engine.  The directory is created if it does not exist; existing
    Parquet files are overwritten.

    Returns the ``Path`` to *output_dir*.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for ticker, df in data_dict.items():
        path = out / f"{ticker}.parquet"
        df.to_parquet(path, engine="pyarrow")

    logger.info("Saved %d DataFrames to %s", len(data_dict), out)
    return out


def load_dataframes(input_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load per-ticker DataFrames from Parquet files in *input_dir*.

    Returns a dict keyed by ticker symbol (filename stem).

    Raises ``FileNotFoundError`` if *input_dir* does not exist.
    """
    src = Path(input_dir)
    if not src.exists():
        raise FileNotFoundError(f"Directory does not exist: {src}")

    result: dict[str, pd.DataFrame] = {}
    for path in sorted(src.glob("*.parquet")):
        ticker = path.stem
        result[ticker] = pd.read_parquet(path, engine="pyarrow")

    logger.info("Loaded %d DataFrames from %s", len(result), src)
    return result
