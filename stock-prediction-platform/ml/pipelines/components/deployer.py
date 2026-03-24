"""Kubeflow component — deploy the winner model to the serving directory."""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ml.models.registry import ModelRegistry

logger = logging.getLogger(__name__)


def _get_storage_backend() -> str:
    return os.environ.get("STORAGE_BACKEND", "local").lower()


def deploy_winner_model(
    registry_dir: str = "model_registry",
    serving_dir: str = "/models/active",
) -> dict:
    """Deploy the winner model from the registry to the serving directory.

    Supports both local filesystem and S3 (MinIO) backends based on the
    ``STORAGE_BACKEND`` environment variable.

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
    winner_path = winner_entry["path"]

    logger.info(
        "Deploying winner %s_%s v%d from %s",
        model_name, scaler_variant, version, winner_path,
    )

    # 2. Deactivate previously active models
    registry.deactivate_all()

    deployed_at = datetime.now(timezone.utc).isoformat()
    backend = _get_storage_backend()

    if backend == "s3":
        return _deploy_winner_s3(
            registry, winner_entry, serving_dir, deployed_at,
        )

    return _deploy_winner_local(
        registry, winner_entry, serving_dir, deployed_at,
    )


def _deploy_winner_s3(
    registry: ModelRegistry,
    winner_entry: dict,
    serving_dir: str,
    deployed_at: str,
) -> dict:
    """Deploy winner artifacts to S3 serving path."""
    from ml.models.s3_storage import S3Storage

    model_name = winner_entry["model_name"]
    scaler_variant = winner_entry["scaler_variant"]
    version = winner_entry["version"]
    model_key = f"{model_name}_{scaler_variant}"

    s3 = S3Storage.from_env()
    bucket = os.environ.get("MINIO_BUCKET_MODELS", "model-artifacts")

    # Source prefix: {registry_dir}/{model_key}/v{version}/
    src_prefix = f"{registry._base_dir}/{model_key}/v{version}/"
    # Destination prefix: serving/active/ (or custom serving_dir)
    dst_prefix = serving_dir.strip("/") + "/"

    # Clear existing serving artifacts
    s3.delete_prefix(bucket, dst_prefix)

    # Copy all artifacts from registry to serving path
    copied = s3.copy_prefix(bucket, src_prefix, dst_prefix)

    # Load features and metrics from the copied artifacts
    features: list[str] = []
    feat_key = f"{dst_prefix}features.json"
    if s3.object_exists(bucket, feat_key):
        features = json.loads(s3.download_bytes(bucket, feat_key))

    oos_metrics: dict = {}
    meta_key = f"{dst_prefix}metadata.json"
    if s3.object_exists(bucket, meta_key):
        meta = json.loads(s3.download_bytes(bucket, meta_key))
        oos_metrics = meta.get("oos_metrics", {})

    serving_config = {
        "model_name": model_name,
        "scaler_variant": scaler_variant,
        "version": version,
        "features": features,
        "artifact_path": f"s3://{bucket}/{dst_prefix}",
        "deployed_at": deployed_at,
        "is_active": True,
        "oos_metrics": oos_metrics,
    }

    s3.upload_bytes(
        json.dumps(serving_config, indent=2).encode(),
        bucket,
        f"{dst_prefix}serving_config.json",
    )

    # Activate in registry
    registry.activate_model(model_name, scaler_variant, version)

    serving_path = f"s3://{bucket}/{dst_prefix}"
    logger.info(
        "Deployed %s_%s v%d → %s (%d objects)",
        model_name, scaler_variant, version, serving_path, copied,
    )

    return {
        "model_name": model_name,
        "scaler_variant": scaler_variant,
        "version": version,
        "serving_path": serving_path,
        "deployed_at": deployed_at,
    }


def _deploy_winner_local(
    registry: ModelRegistry,
    winner_entry: dict,
    serving_dir: str,
    deployed_at: str,
) -> dict:
    """Deploy winner artifacts to local filesystem serving directory."""
    model_name = winner_entry["model_name"]
    scaler_variant = winner_entry["scaler_variant"]
    version = winner_entry["version"]
    winner_path = Path(registry._base_dir) / winner_entry["path"]

    # Clear and recreate serving directory
    serving = Path(serving_dir)
    if serving.exists():
        shutil.rmtree(serving)
    serving.mkdir(parents=True, exist_ok=True)

    # Copy all artifacts from the winner version directory
    for src_file in winner_path.iterdir():
        if src_file.is_file():
            shutil.copy2(src_file, serving / src_file.name)

    # Load features and build serving config
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

    # Activate in registry
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


def deploy_multi_horizon_winners(
    registry_dir: str = "model_registry",
    serving_dir: str = "/models/active",
    horizons: list[int] | None = None,
) -> dict:
    """Deploy winner models for each horizon and write a top-level manifest.

    Calls :func:`deploy_winner_model` for each horizon with horizon-scoped
    registry and serving directories.  Writes ``{serving_dir}/horizons.json``
    listing available horizons.

    Returns dict mapping horizon → deploy_info.
    """
    if horizons is None:
        horizons = [1, 7, 30]

    results: dict[int, dict] = {}
    for h in horizons:
        h_registry = f"{registry_dir}/horizon_{h}d"
        h_serving = f"{serving_dir}/horizon_{h}d"
        try:
            info = deploy_winner_model(h_registry, h_serving)
            results[h] = info
        except FileNotFoundError:
            logger.warning("Horizon %dd: no winner found — skipping deploy.", h)
            continue

    manifest = {"horizons": sorted(results.keys()), "default": 7}
    backend = _get_storage_backend()

    if backend == "s3":
        from ml.models.s3_storage import S3Storage

        s3 = S3Storage.from_env()
        bucket = os.environ.get("MINIO_BUCKET_MODELS", "model-artifacts")
        manifest_key = serving_dir.strip("/") + "/horizons.json"
        s3.upload_bytes(
            json.dumps(manifest, indent=2).encode(), bucket, manifest_key,
        )
        logger.info("Wrote horizons manifest → s3://%s/%s", bucket, manifest_key)
    else:
        serving = Path(serving_dir)
        serving.mkdir(parents=True, exist_ok=True)
        with open(serving / "horizons.json", "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info("Wrote horizons manifest → %s/horizons.json", serving)

    return results
