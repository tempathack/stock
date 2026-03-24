"""Redis caching layer — async client, TTL constants, get/set/invalidate helpers."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

# --- TTL constants (seconds) ---
MARKET_OVERVIEW_TTL = 30
MARKET_INDICATORS_TTL = 30
BULK_PREDICTIONS_TTL = 60
SINGLE_PREDICTION_TTL = 60
MODEL_COMPARISON_TTL = 300
DRIFT_STATUS_TTL = 300
BACKTEST_TTL = 120
HORIZONS_TTL = 600

# --- Module-level singleton ---
_redis_client: aioredis.Redis | None = None


def init_redis(redis_url: str) -> None:
    """Create the async Redis client from a URL.

    Must be called once during application startup (e.g. in the lifespan handler).
    """
    global _redis_client  # noqa: PLW0603
    _redis_client = aioredis.from_url(redis_url, decode_responses=True)
    # Log host only — never log credentials
    safe_host = redis_url.split("@")[-1] if "@" in redis_url else redis_url
    logger.info("redis client initialised", extra={"redis_host": safe_host})


async def close_redis() -> None:
    """Close the Redis connection on shutdown."""
    global _redis_client  # noqa: PLW0603
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("redis client closed")


def get_redis() -> aioredis.Redis | None:
    """Return the current Redis client (or ``None`` if not initialised)."""
    return _redis_client


async def cache_get(key: str) -> dict | list | None:
    """Fetch a cached value by key. Returns ``None`` on miss or if Redis is unavailable."""
    if _redis_client is None:
        return None
    try:
        value = await _redis_client.get(key)
        if value is not None:
            return json.loads(value)
        return None
    except aioredis.RedisError:
        logger.warning("redis cache_get failed", extra={"key": key}, exc_info=True)
        return None


async def cache_set(key: str, value: Any, ttl: int) -> None:
    """Store a value in Redis with a TTL (seconds). No-op if Redis is unavailable."""
    if _redis_client is None:
        return
    try:
        await _redis_client.setex(key, ttl, json.dumps(value, default=str))
    except aioredis.RedisError:
        logger.warning("redis cache_set failed", extra={"key": key}, exc_info=True)


async def cache_delete(pattern: str) -> int:
    """Delete all keys matching a glob pattern. Returns count of deleted keys."""
    if _redis_client is None:
        return 0
    try:
        count = 0
        async for key in _redis_client.scan_iter(match=pattern):
            await _redis_client.delete(key)
            count += 1
        return count
    except aioredis.RedisError:
        logger.warning("redis cache_delete failed", extra={"pattern": pattern}, exc_info=True)
        return 0


async def invalidate_predictions() -> int:
    """Clear all prediction caches (predict:*)."""
    return await cache_delete("predict:*")


async def invalidate_models() -> int:
    """Clear all model comparison/drift caches (models:*)."""
    return await cache_delete("models:*")


async def invalidate_all() -> int:
    """Flush the entire application cache."""
    return await cache_delete("*")


def build_key(*parts: str) -> str:
    """Build a colon-separated cache key — e.g. ``build_key("predict", "AAPL", "7")`` → ``"predict:AAPL:7"``."""
    return ":".join(parts)
