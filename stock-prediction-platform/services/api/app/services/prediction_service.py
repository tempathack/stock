"""Prediction service — loads cached predictions, model metadata, drift events."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_cached_predictions(registry_dir: str = "model_registry") -> list[dict]:
    """Load predictions from ``{registry_dir}/predictions/latest.json``.

    Returns an empty list if the file does not exist.
    """
    path = Path(registry_dir) / "predictions" / "latest.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def get_prediction_for_ticker(
    ticker: str,
    registry_dir: str = "model_registry",
) -> dict | None:
    """Return the cached prediction for a single ticker, or ``None``."""
    predictions = load_cached_predictions(registry_dir)
    ticker_upper = ticker.upper()
    for pred in predictions:
        if pred.get("ticker", "").upper() == ticker_upper:
            return pred
    return None


def load_model_comparison(registry_dir: str = "model_registry") -> list[dict]:
    """Read all model metadata from the file-based registry.

    Scans ``{registry_dir}/{model_key}/v{N}/metadata.json``.
    Returns list sorted by OOS RMSE ascending.
    """
    base = Path(registry_dir)
    entries: list[dict] = []
    if not base.exists():
        return entries

    for model_dir in sorted(base.iterdir()):
        if not model_dir.is_dir() or model_dir.name in ("predictions", "runs"):
            continue
        for ver_dir in sorted(model_dir.iterdir()):
            meta_path = ver_dir / "metadata.json"
            if not meta_path.exists():
                continue
            with open(meta_path) as f:
                meta = json.load(f)
            entries.append(meta)

    entries.sort(
        key=lambda e: e.get("oos_metrics", {}).get("rmse") or float("inf"),
    )
    return entries


def load_drift_events(
    log_dir: str = "drift_logs",
    n: int = 100,
) -> list[dict]:
    """Read recent drift events from JSONL log.

    Returns list of dicts, newest first.
    """
    path = Path(log_dir) / "drift_events.jsonl"
    if not path.exists():
        return []
    with open(path) as f:
        lines = f.readlines()
    events = [json.loads(line) for line in lines]
    return list(reversed(events[-n:]))
