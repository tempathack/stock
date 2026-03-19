"""Ingestion router — /ingest/intraday and /ingest/historical endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import IngestRequest, IngestResponse
from app.services.kafka_producer import OHLCVProducer
from app.services.yahoo_finance import YahooFinanceService
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])


def _run_ingestion(mode: str, tickers: list[str] | None) -> IngestResponse:
    """Shared logic for intraday and historical ingestion.

    Args:
        mode: Either ``"intraday"`` or ``"historical"``.
        tickers: Explicit ticker list, or None for defaults.

    Returns:
        IngestResponse with fetch and produce counts.

    Raises:
        HTTPException: On Yahoo Finance or Kafka failures.
    """
    yf_service = YahooFinanceService()
    resolved_tickers = tickers or yf_service.tickers

    try:
        if mode == "intraday":
            records = yf_service.fetch_intraday(tickers=resolved_tickers)
        else:
            records = yf_service.fetch_historical(tickers=resolved_tickers)
    except Exception as exc:
        logger.error("yahoo_finance_error", mode=mode, error=str(exc))
        raise HTTPException(
            status_code=502,
            detail=f"Yahoo Finance fetch failed: {exc}",
        ) from exc

    records_fetched = len(records)

    if records_fetched == 0:
        return IngestResponse(
            status="completed",
            mode=mode,
            tickers_requested=len(resolved_tickers),
            records_fetched=0,
            records_produced=0,
        )

    try:
        producer = OHLCVProducer()
        records_produced = producer.produce_records(records)
    except Exception as exc:
        logger.error("kafka_produce_error", mode=mode, error=str(exc))
        raise HTTPException(
            status_code=502,
            detail=f"Kafka produce failed: {exc}",
        ) from exc

    return IngestResponse(
        status="completed",
        mode=mode,
        tickers_requested=len(resolved_tickers),
        records_fetched=records_fetched,
        records_produced=records_produced,
    )


@router.post("/intraday", response_model=IngestResponse)
async def ingest_intraday(body: IngestRequest | None = None) -> IngestResponse:
    """Trigger intraday OHLCV fetch from Yahoo Finance and publish to Kafka."""
    tickers = body.tickers if body else None
    return _run_ingestion(mode="intraday", tickers=tickers)


@router.post("/historical", response_model=IngestResponse)
async def ingest_historical(body: IngestRequest | None = None) -> IngestResponse:
    """Trigger historical OHLCV fetch from Yahoo Finance and publish to Kafka."""
    tickers = body.tickers if body else None
    return _run_ingestion(mode="historical", tickers=tickers)
