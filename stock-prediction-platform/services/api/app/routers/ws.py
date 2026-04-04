"""WebSocket router — /ws/prices real-time price feed and /ws/sentiment/{ticker} sentiment feed."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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
    """ARCHIVED (Phase 93) — sentiment FeatureView removed from Feast registry.

    The sentiment WebSocket endpoint is disabled. Accepts the connection,
    sends a single available=False payload, then closes. This preserves
    backward compatibility for clients that connect to this endpoint.
    """
    await websocket.accept()
    await websocket.send_json({"available": False, "ticker": ticker.upper()})
    await websocket.close()
    logger.info("sentiment ws disabled (Phase 93): ticker=%s", ticker.upper())
