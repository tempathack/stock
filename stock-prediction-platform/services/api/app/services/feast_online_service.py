"""Feast online store reader — synchronous helpers for WebSocket and HTTP handlers."""
from __future__ import annotations


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
