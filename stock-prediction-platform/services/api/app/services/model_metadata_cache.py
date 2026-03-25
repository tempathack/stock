"""Active model metadata cache — loaded once at API startup.

Fetches serving_config.json from MinIO (STORAGE_BACKEND=s3) at startup.
Falls back to model_registry DB query if MinIO is unavailable.
Leaves cache as None if both sources fail — predict endpoints fall back to 'unknown'.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

# Module-level cache — populated once in lifespan, read per-request
_active_metadata: dict | None = None

_SAFE_DEFAULT: dict = {"model_name": None, "scaler_variant": None, "version": None}


def get_active_model_metadata() -> dict:
    """Return cached active model metadata.

    Returns safe defaults (model_name=None) if startup load has not run or failed.
    """
    if _active_metadata is None:
        return _SAFE_DEFAULT.copy()
    return _active_metadata


async def load_active_model_metadata() -> None:
    """Fetch metadata from MinIO or DB at startup. Called from lifespan.

    Populates the module-level _active_metadata cache.
    Silently continues if both sources fail — metadata is cosmetic.
    """
    global _active_metadata
    try:
        result = await asyncio.to_thread(_sync_fetch_from_minio)
        if result is None:
            result = await _fetch_from_db()
        _active_metadata = result
        if _active_metadata is not None:
            logger.info(
                "active model metadata loaded: model_name=%s scaler=%s version=%s",
                _active_metadata.get("model_name"),
                _active_metadata.get("scaler_variant"),
                _active_metadata.get("version"),
            )
        else:
            logger.warning(
                "active model metadata unavailable — both MinIO and DB failed; "
                "predict responses will show model_name='unknown'"
            )
    except Exception:
        logger.warning("load_active_model_metadata: unexpected error", exc_info=True)


def _sync_fetch_from_minio() -> dict | None:
    """Synchronous boto3 fetch of serving_config.json from MinIO.

    Runs in a thread pool via asyncio.to_thread().
    Reads from s3://model-artifacts/serving/active/serving_config.json.
    Returns parsed dict or None on any failure.
    """
    endpoint = os.environ.get("MINIO_ENDPOINT")
    if not endpoint:
        return None

    try:
        import boto3

        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=os.environ.get("MINIO_ROOT_USER", ""),
            aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD", ""),
        )
        bucket = os.environ.get("MINIO_BUCKET_MODELS", "model-artifacts")
        # MINIO_SERVING_PREFIX: read from env to match ConfigMap/pydantic-settings value.
        # os.environ used here because this sync function runs in a thread pool and
        # cannot access FastAPI's dependency-injected settings; value is set by ConfigMap
        # via MINIO_SERVING_PREFIX and matches the Settings field default "serving/active".
        serving_prefix = os.environ.get("MINIO_SERVING_PREFIX", "serving/active")
        key = f"{serving_prefix.strip('/')}/serving_config.json"
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = json.loads(obj["Body"].read())
        return {
            "model_name": data.get("model_name"),
            "scaler_variant": data.get("scaler_variant"),
            "version": data.get("version"),
        }
    except Exception:
        logger.warning("MinIO serving_config.json fetch failed", exc_info=True)
        return None


async def _fetch_from_db() -> dict | None:
    """DB fallback — query model_registry WHERE is_active=true.

    Uses existing get_async_session() pattern from app.models.database.
    Returns None if DB is unavailable or query fails.
    """
    try:
        from sqlalchemy import text as sa_text
        from app.models.database import get_async_session, get_engine

        if get_engine() is None:
            return None

        query = sa_text("""
            SELECT model_name, version, metrics_json
            FROM model_registry
            WHERE is_active = true
            LIMIT 1
        """)
        async with get_async_session() as session:
            row = (await session.execute(query)).mappings().first()
        if not row:
            return None
        metrics = row.get("metrics_json") or {}
        return {
            "model_name": row.get("model_name"),
            "scaler_variant": metrics.get("scaler_variant"),
            "version": row.get("version"),
        }
    except Exception:
        logger.warning("DB model_registry fallback failed", exc_info=True)
        return None
