"""FastAPI application entry point for the stock prediction API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import health, ingest
from app.utils.logging import get_logger

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
    yield
    logger.info("service shutting down")


app = FastAPI(
    title="Stock Prediction API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(ingest.router)
