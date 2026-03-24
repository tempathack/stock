"""WebSocket router — /ws/prices real-time price feed."""

from __future__ import annotations

import asyncio
import logging

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
