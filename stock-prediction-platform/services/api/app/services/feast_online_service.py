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
    """Read reddit_sentiment_fv features from Feast Redis online store.

    Returns dict with available=True and feature values if data exists,
    or available=False if no data found (pipeline not yet running).

    This is a synchronous function — call via run_in_threadpool from async handlers.
    """
    import logging
    from datetime import datetime
    logger = logging.getLogger(__name__)
    try:
        from feast import FeatureStore
        from app.config import settings
        store = FeatureStore(repo_path=settings.FEAST_STORE_PATH)
        result = store.get_online_features(
            features=[
                "reddit_sentiment_fv:avg_sentiment",
                "reddit_sentiment_fv:mention_count",
                "reddit_sentiment_fv:positive_ratio",
                "reddit_sentiment_fv:negative_ratio",
                "reddit_sentiment_fv:top_subreddit",
            ],
            entity_rows=[{"ticker": ticker}],
        ).to_dict()
        avg_sentiment = (result.get("avg_sentiment") or [None])[0]
        return {
            "ticker": ticker,
            "avg_sentiment": avg_sentiment,
            "mention_count": (result.get("mention_count") or [None])[0],
            "positive_ratio": (result.get("positive_ratio") or [None])[0],
            "negative_ratio": (result.get("negative_ratio") or [None])[0],
            "top_subreddit": (result.get("top_subreddit") or [None])[0],
            "available": avg_sentiment is not None,
            "sampled_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        logger.warning("get_sentiment_features failed for ticker=%s: %s", ticker, exc)
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
