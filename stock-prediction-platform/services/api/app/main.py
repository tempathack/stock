"""FastAPI application entry point for the stock prediction API."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from prometheus_fastapi_instrumentator import Instrumentator

from app.cache import close_redis, init_redis
from app.config import settings
from app.middleware import RequestContextMiddleware
from app.models.database import dispose_engine, init_engine
from app.rate_limit import RateLimitMiddleware
from app.routers import backtest, health, ingest, market, models, predict, ws
from app.services.price_feed import price_feed_loop
from app.utils.logging import configure_uvicorn_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle events."""
    logger.info(
        "service starting",
        service=settings.SERVICE_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )
    configure_uvicorn_logging()

    # Initialise async DB engine with connection pooling
    if settings.DATABASE_URL:
        init_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
        )
        logger.info(
            "database pool ready",
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
        )

    # Initialise Redis cache (if configured)
    if settings.REDIS_URL:
        init_redis(settings.REDIS_URL)
        logger.info("redis cache enabled")

    # Start WebSocket price feed background task
    tickers = [t.strip() for t in settings.TICKER_SYMBOLS.split(",") if t.strip()]
    app.state.price_feed_task = asyncio.create_task(
        price_feed_loop(
            tickers,
            interval=settings.WS_PRICE_INTERVAL,
            market_recheck=settings.WS_MARKET_RECHECK_INTERVAL,
        )
    )
    logger.info("price feed started", tickers=len(tickers), interval=settings.WS_PRICE_INTERVAL)

    yield

    # Cancel price feed task
    app.state.price_feed_task.cancel()
    try:
        await app.state.price_feed_task
    except asyncio.CancelledError:
        pass

    # Close KServe HTTP client
    from app.services.kserve_client import close_client as close_kserve
    await close_kserve()

    # Close Redis
    await close_redis()

    # Dispose engine on shutdown
    await dispose_engine()
    logger.info("service shutting down")


app = FastAPI(
    title="Stock Prediction API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    RateLimitMiddleware,
    route_limits={
        "/predict": settings.RATE_LIMIT_PREDICT,
        "/ingest": settings.RATE_LIMIT_INGEST,
    },
    default_limit=settings.RATE_LIMIT_GLOBAL,
    exempt_paths=["/health", "/metrics", "/ws"],
)
app.add_middleware(RequestContextMiddleware)

app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(predict.router)
app.include_router(models.router)
app.include_router(market.router)
app.include_router(ws.router)
app.include_router(backtest.router)

Instrumentator().instrument(app).expose(app)
