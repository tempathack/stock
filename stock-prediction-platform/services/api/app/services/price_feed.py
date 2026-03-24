"""Real-time price feed — fetch latest prices and broadcast to WebSocket subscribers."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import pytz
import yfinance as yf

logger = logging.getLogger(__name__)

_EASTERN = pytz.timezone("US/Eastern")


# ---------------------------------------------------------------------------
# Market hours helpers
# ---------------------------------------------------------------------------

def is_market_open() -> bool:
    """Return True if current US/Eastern time is Mon–Fri, 09:30–16:00."""
    now = datetime.now(_EASTERN)
    if now.weekday() >= 5:  # Sat=5, Sun=6
        return False
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close


def _next_market_open() -> str:
    """Return ISO-formatted next market open datetime (US/Eastern)."""
    now = datetime.now(_EASTERN)
    candidate = now.replace(hour=9, minute=30, second=0, microsecond=0)
    # If today's open is still in the future, use it (unless weekend)
    if candidate > now and now.weekday() < 5:
        return candidate.isoformat()
    # Otherwise advance to next weekday
    from datetime import timedelta
    day = now + timedelta(days=1)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day.replace(hour=9, minute=30, second=0, microsecond=0).isoformat()


# ---------------------------------------------------------------------------
# Price fetching
# ---------------------------------------------------------------------------

def fetch_live_prices(tickers: list[str]) -> list[dict[str, Any]]:
    """Fetch current price snapshot for *tickers* via yfinance.

    Returns a list of dicts with keys: ticker, price, change_pct, volume,
    timestamp.  Returns an empty list on complete failure (never raises).
    """
    results: list[dict[str, Any]] = []
    try:
        df = yf.download(tickers, period="1d", interval="1m", progress=False, group_by="ticker")
        if df.empty:
            raise ValueError("empty download")

        now_iso = datetime.now(_EASTERN).isoformat()
        for t in tickers:
            try:
                if len(tickers) == 1:
                    sub = df
                else:
                    sub = df[t]
                if sub.empty:
                    continue
                last = sub.iloc[-1]
                first = sub.iloc[0]
                price = float(last["Close"])
                open_price = float(first["Open"])
                change_pct = ((price - open_price) / open_price * 100) if open_price else 0.0
                results.append({
                    "ticker": t,
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 4),
                    "volume": int(last["Volume"]) if last["Volume"] == last["Volume"] else 0,
                    "timestamp": now_iso,
                })
            except Exception:
                logger.warning("partial fetch failure for %s", t)
    except Exception:
        # Fallback: per-ticker info lookup
        logger.warning("bulk download failed, falling back to per-ticker info")
        now_iso = datetime.now(_EASTERN).isoformat()
        for t in tickers:
            try:
                info = yf.Ticker(t).info
                price = info.get("regularMarketPrice")
                prev = info.get("regularMarketPreviousClose", price)
                if price is None:
                    continue
                change_pct = ((price - prev) / prev * 100) if prev else 0.0
                results.append({
                    "ticker": t,
                    "price": round(float(price), 2),
                    "change_pct": round(change_pct, 4),
                    "volume": int(info.get("regularMarketVolume", 0)),
                    "timestamp": now_iso,
                })
            except Exception:
                logger.warning("fallback fetch failure for %s", t)
    return results


# ---------------------------------------------------------------------------
# Broadcaster (pub/sub for connected WebSocket clients)
# ---------------------------------------------------------------------------

class PriceBroadcaster:
    """Fan-out broadcaster — one async queue per connected WebSocket client."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=32)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    def broadcast(self, message: dict[str, Any]) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                pass  # drop for slow consumers


broadcaster = PriceBroadcaster()


# ---------------------------------------------------------------------------
# Background feed loop
# ---------------------------------------------------------------------------

async def price_feed_loop(
    tickers: list[str],
    interval: float = 5.0,
    market_recheck: float = 60.0,
) -> None:
    """Run forever, broadcasting live prices while market is open."""
    loop = asyncio.get_running_loop()
    sent_closed_msg = False

    while True:
        try:
            if is_market_open():
                sent_closed_msg = False
                prices = await loop.run_in_executor(None, fetch_live_prices, tickers)
                if prices:
                    broadcaster.broadcast({"type": "price_update", "prices": prices})
                await asyncio.sleep(interval)
            else:
                if not sent_closed_msg:
                    broadcaster.broadcast({
                        "type": "market_closed",
                        "next_open": _next_market_open(),
                    })
                    sent_closed_msg = True
                await asyncio.sleep(market_recheck)
        except asyncio.CancelledError:
            logger.info("price feed loop cancelled")
            return
        except Exception:
            logger.exception("price feed loop error")
            await asyncio.sleep(interval)
