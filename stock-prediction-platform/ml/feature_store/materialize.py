"""Feast incremental materialization script.

Called by the feast-materialize K8s CronJob as:
    python -m ml.feature_store.materialize

Reads FEAST_REPO_PATH from environment (default: /app/ml/feature_store),
constructs a FeatureStore, and runs materialize_incremental up to now (UTC).
"""
from __future__ import annotations

import datetime
import logging
import os

from feast import FeatureStore

logger = logging.getLogger(__name__)


def run_materialization() -> None:
    """Run incremental materialization to now (UTC)."""
    repo_path = os.environ.get("FEAST_REPO_PATH", "/app/ml/feature_store")
    store = FeatureStore(repo_path=repo_path)
    end = datetime.datetime.now(tz=datetime.timezone.utc)
    logger.info("Starting incremental materialization up to %s", end.isoformat())
    store.materialize_incremental(end_date=end)
    logger.info("Materialization complete up to %s", end.isoformat())
    print(f"Materialization complete up to {end.isoformat()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_materialization()
