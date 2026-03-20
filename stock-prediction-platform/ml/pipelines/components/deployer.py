"""Kubeflow component — deploy the winner model to the serving directory."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ml.models.registry import ModelRegistry

logger = logging.getLogger(__name__)


def deploy_winner_model(
    registry_dir: str = "model_registry",
    serving_dir: str = "/models/active",
) -> dict:
    """Deploy the winner model from the registry to the serving directory.

    Steps:
        1. Find the current winner in the registry.
        2. Deactivate any previously active models.
        3. Clear and recreate the serving directory.
        4. Copy winner artifacts (pipeline.pkl, metadata.json, features.json,
           and any SHAP files).
        5. Write ``serving_config.json``.
        6. Activate the winner in the registry.
        7. Return deployment summary.

    Raises ``FileNotFoundError`` if no winner exists in the registry.
    """
    registry = ModelRegistry(base_dir=registry_dir)

    # 1. Find winner
    winner_entry = registry.get_winner()
    if winner_entry is None:
        raise FileNotFoundError("No winner found in the registry.")

    model_name = winner_entry["model_name"]
    scaler_variant = winner_entry["scaler_variant"]
    version = winner_entry["version"]
    winner_path = Path(winner_entry["path"])

    logger.info(
        "Deploying winner %s_%s v%d from %s",
        model_name, scaler_variant, version, winner_path,
    )

    # 2. Deactivate previously active models
    registry.deactivate_all()

    # 3. Clear and recreate serving directory
    serving = Path(serving_dir)
    if serving.exists():
        shutil.rmtree(serving)
    serving.mkdir(parents=True, exist_ok=True)

    # 4. Copy all artifacts from the winner version directory
    for src_file in winner_path.iterdir():
        if src_file.is_file():
            shutil.copy2(src_file, serving / src_file.name)

    # 5. Load features and build serving config
    features: list[str] = []
    features_path = serving / "features.json"
    if features_path.exists():
        with open(features_path) as f:
            features = json.load(f)

    oos_metrics: dict = {}
    meta_path = serving / "metadata.json"
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
        oos_metrics = meta.get("oos_metrics", {})

    deployed_at = datetime.now(timezone.utc).isoformat()

    serving_config = {
        "model_name": model_name,
        "scaler_variant": scaler_variant,
        "version": version,
        "features": features,
        "artifact_path": str(serving),
        "deployed_at": deployed_at,
        "is_active": True,
        "oos_metrics": oos_metrics,
    }

    with open(serving / "serving_config.json", "w") as f:
        json.dump(serving_config, f, indent=2)

    # 6. Activate in registry
    registry.activate_model(model_name, scaler_variant, version)

    logger.info(
        "Deployed %s_%s v%d → %s", model_name, scaler_variant, version, serving,
    )

    return {
        "model_name": model_name,
        "scaler_variant": scaler_variant,
        "version": version,
        "serving_path": str(serving),
        "deployed_at": deployed_at,
    }
