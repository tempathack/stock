"""WebSocket router — /ws/prices real-time price feed and /ws/sentiment/{ticker} sentiment feed."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

from app.services.price_feed import broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/prices")
async def ws_prices(websocket: WebSocket) -> None:
    """Stream live price updates to a connected client."""
    await websocket.accept()
    client = websocket.client
    logger.info("ws client connected: %s", client)

    queue = broadcaster.subscribe()
    try:
        # Task that listens for client messages (ping / close)
        async def _recv() -> None:
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                pass

        recv_task = asyncio.create_task(_recv())
        try:
            while True:
                message = await queue.get()
                await websocket.send_json(message)
        except WebSocketDisconnect:
            pass
        finally:
            recv_task.cancel()
    finally:
        broadcaster.unsubscribe(queue)
        logger.info("ws client disconnected: %s", client)


@router.websocket("/ws/sentiment/{ticker}")
async def ws_sentiment(websocket: WebSocket, ticker: str) -> None:
    """Push live Reddit sentiment data for a single ticker every 60 seconds.

    Reads from Feast Redis online store (reddit_sentiment_fv) on each push cycle.
    Returns {available: false} if no sentiment data exists yet (pipeline starting up).
    Exponential backoff reconnect is handled client-side.
    """
    await websocket.accept()
    ticker_upper = ticker.upper()
    logger.info("sentiment ws connected: ticker=%s client=%s", ticker_upper, websocket.client)

    async def _recv_loop() -> None:
        """Drain incoming messages — detect close/ping from client."""
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    recv_task = asyncio.create_task(_recv_loop())
    try:
        while True:
            features = await run_in_threadpool(_get_sentiment_sync, ticker_upper)
            await websocket.send_json(features)
            await asyncio.sleep(60)  # aligns with 1-min HOP output rate
    except WebSocketDisconnect:
        pass
    finally:
        recv_task.cancel()
        logger.info("sentiment ws disconnected: ticker=%s", ticker_upper)


def _get_sentiment_sync(ticker: str) -> dict:
    """Synchronous Feast read — called via run_in_threadpool from ws_sentiment."""
    from app.services.feast_online_service import get_sentiment_features  # local import avoids circular
    return get_sentiment_features(ticker)
