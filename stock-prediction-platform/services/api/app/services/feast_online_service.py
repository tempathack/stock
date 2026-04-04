"""Feast online store reader — synchronous helpers for WebSocket and HTTP handlers."""
from __future__ import annotations

import datetime
import logging

from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.models.schemas import StreamingFeaturesResponse

logger = logging.getLogger(__name__)


def _fetch_from_feast(ticker: str) -> StreamingFeaturesResponse:
    """Synchronous Feast online store read. Must be called via run_in_threadpool.

    Feast 0.61.0 uses a synchronous Redis client internally — calling this
    directly in an async handler would block the event loop.
    """
    import feast  # lazy import — avoids slow package-level registry init at startup

    sampled_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        store = feast.FeatureStore(repo_path=settings.FEAST_STORE_PATH)
        result = store.get_online_features(
            features=[
                "technical_indicators_fv:ema_20",
                "technical_indicators_fv:rsi_14",
                "technical_indicators_fv:macd_signal",
            ],
            entity_rows=[{"ticker": ticker.upper()}],
        ).to_dict()

        ema_20 = result.get("ema_20", [None])[0]
        rsi_14 = result.get("rsi_14", [None])[0]
        macd_signal = result.get("macd_signal", [None])[0]

        # available=True only when at least one feature has a real value
        available = any(v is not None for v in (ema_20, rsi_14, macd_signal))

        return StreamingFeaturesResponse(
            ticker=ticker.upper(),
            ema_20=ema_20,
            rsi_14=rsi_14,
            macd_signal=macd_signal,
            available=available,
            source="flink-indicator-stream",
            sampled_at=sampled_at,
        )
    except Exception:
        logger.warning(
            "feast online store unavailable",
            extra={"ticker": ticker},
            exc_info=True,
        )
        return StreamingFeaturesResponse(
            ticker=ticker.upper(),
            ema_20=None,
            rsi_14=None,
            macd_signal=None,
            available=False,
            source="flink-indicator-stream",
            sampled_at=sampled_at,
        )


async def get_streaming_features(ticker: str) -> StreamingFeaturesResponse:
    """Async wrapper — runs the synchronous Feast call in a thread pool."""
    return await run_in_threadpool(_fetch_from_feast, ticker)


def get_sentiment_features(ticker: str) -> dict:
    """ARCHIVED (Phase 93) — reddit_sentiment FeatureView removed from Feast registry.

    Returns a static available=False payload so callers (ws.py) continue
    to receive a well-formed dict without raising or hitting Feast.
    No Feast call is made.
    """
    return {
        "ticker": ticker,
        "avg_sentiment": None,
        "mention_count": None,
        "positive_ratio": None,
        "negative_ratio": None,
        "top_subreddit": None,
        "available": False,
        "sampled_at": None,
    }
