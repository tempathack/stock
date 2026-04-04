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
    sampled_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        import feast  # lazy import inside try — avoids 500 when feast not installed
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

        # Phase 94: second Feast call for FRED macro features — entity ticker='MACRO'
        fred_macro: dict | None = None
        try:
            fred_result = store.get_online_features(
                features=[
                    "fred_macro_fv:dgs2",
                    "fred_macro_fv:dgs10",
                    "fred_macro_fv:t10y2y",
                    "fred_macro_fv:t10y3m",
                    "fred_macro_fv:bamlh0a0hym2",
                    "fred_macro_fv:dbaa",
                    "fred_macro_fv:t10yie",
                    "fred_macro_fv:dcoilwtico",
                    "fred_macro_fv:dtwexbgs",
                    "fred_macro_fv:dexjpus",
                    "fred_macro_fv:icsa",
                    "fred_macro_fv:nfci",
                    "fred_macro_fv:cpiaucsl",
                    "fred_macro_fv:pcepilfe",
                ],
                entity_rows=[{"ticker": "MACRO"}],
            ).to_dict()
            # Extract scalar values from list-wrapped Feast results
            fred_cols = [
                "dgs2", "dgs10", "t10y2y", "t10y3m",
                "bamlh0a0hym2", "dbaa", "t10yie",
                "dcoilwtico", "dtwexbgs", "dexjpus",
                "icsa", "nfci", "cpiaucsl", "pcepilfe",
            ]
            fred_macro = {col: fred_result.get(col, [None])[0] for col in fred_cols}
            if all(v is None for v in fred_macro.values()):
                # FRED not yet materialized — degrade gracefully
                logger.warning("fred_macro_fv not materialized (all None)")
                fred_macro = None
        except Exception:
            logger.warning("fred_macro_fv online fetch failed — degrading gracefully", exc_info=True)
            fred_macro = None

        return StreamingFeaturesResponse(
            ticker=ticker.upper(),
            ema_20=ema_20,
            rsi_14=rsi_14,
            macd_signal=macd_signal,
            available=available,
            source="flink-indicator-stream",
            sampled_at=sampled_at,
            fred_macro=fred_macro,
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
            fred_macro=None,
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
