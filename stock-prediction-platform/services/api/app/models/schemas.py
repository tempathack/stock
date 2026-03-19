"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Optional request body for ingestion endpoints."""

    tickers: list[str] | None = Field(
        default=None,
        description="Ticker symbols to ingest. If omitted, uses the configured default list.",
    )


class IngestResponse(BaseModel):
    """Response model for ingestion endpoints."""

    status: str
    mode: str
    tickers_requested: int
    records_fetched: int
    records_produced: int


class ErrorResponse(BaseModel):
    """Structured error response."""

    status: str = "error"
    detail: str
