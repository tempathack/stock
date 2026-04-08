"""Ingestion router — /ingest/intraday and /ingest/historical endpoints."""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.config import settings
from app.models.schemas import IngestRequest, IngestResponse
from app.services.kafka_producer import OHLCVProducer
from app.services.yahoo_finance import (
    YahooFinanceService,
    create_fred_macro_table,
    fetch_fred_macro,
    write_fred_macro_to_db,
)
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])

# Global lock: yfinance uses a shared session/CrumbManager. Running two
# concurrent downloads in the same process corrupts per-ticker results
# (e.g., intraday and historical tasks return swapped data). Serialise all
# fetch work so only one background task touches yfinance at a time.
_yf_lock = threading.Lock()


def _run_ingestion_task(mode: str, tickers: list[str]) -> None:
    """Background task: fetch tickers in batches and produce to Kafka.

    Runs in a thread so the HTTP response returns immediately and the
    FastAPI event loop / liveness probe stay unblocked.
    """
    yf_service = YahooFinanceService()
    batch_size = 50
    total_fetched = 0
    total_produced = 0

    with _yf_lock:
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i : i + batch_size]
            logger.info("ingestion_batch_start", mode=mode, batch=i // batch_size + 1, size=len(batch))

            try:
                if mode == "intraday":
                    records = yf_service.fetch_intraday(tickers=batch)
                else:
                    records = yf_service.fetch_historical(tickers=batch)
            except Exception as exc:
                logger.error("yahoo_finance_batch_error", mode=mode, batch_start=i, error=str(exc))
                continue

            if not records:
                continue

            try:
                producer = OHLCVProducer()
                produced = producer.produce_records(records)
                total_fetched += len(records)
                total_produced += produced
            except Exception as exc:
                logger.error("kafka_produce_batch_error", mode=mode, batch_start=i, error=str(exc))
                continue

            logger.info(
                "ingestion_batch_complete",
                mode=mode,
                batch_start=i,
                fetched=len(records),
                produced=produced,
            )

    logger.info(
        "ingestion_complete",
        mode=mode,
        total_tickers=len(tickers),
        total_fetched=total_fetched,
        total_produced=total_produced,
    )

    # FRED macro — daily population of feast_fred_macro (historical mode only)
    if mode == "historical":
        try:
            end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            start_date = (datetime.now(timezone.utc) - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
            create_fred_macro_table()
            fred_df = fetch_fred_macro(start_date=start_date, end_date=end_date)
            write_fred_macro_to_db(fred_df)
            logger.info("fred_macro_complete", rows=len(fred_df))
        except Exception as exc:
            logger.error("fred_macro_error", error=str(exc))


@router.post("/intraday", response_model=IngestResponse)
async def ingest_intraday(
    body: IngestRequest | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> IngestResponse:
    """Trigger intraday OHLCV fetch — returns immediately, runs in background."""
    yf_service = YahooFinanceService()
    tickers = (body.tickers if body else None) or yf_service.tickers
    background_tasks.add_task(_run_ingestion_task, mode="intraday", tickers=tickers)
    return IngestResponse(
        status="accepted",
        mode="intraday",
        tickers_requested=len(tickers),
        records_fetched=0,
        records_produced=0,
    )


@router.post("/historical", response_model=IngestResponse)
async def ingest_historical(
    body: IngestRequest | None = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> IngestResponse:
    """Trigger historical OHLCV fetch — returns immediately, runs in background."""
    yf_service = YahooFinanceService()
    tickers = (body.tickers if body else None) or yf_service.tickers
    background_tasks.add_task(_run_ingestion_task, mode="historical", tickers=tickers)
    return IngestResponse(
        status="accepted",
        mode="historical",
        tickers_requested=len(tickers),
        records_fetched=0,
        records_produced=0,
    )
