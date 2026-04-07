"""Backtest router — /backtest/{ticker} historical prediction accuracy."""

from __future__ import annotations

import datetime
import logging

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import BacktestResponse
from app.services.backtest_service import get_backtest_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.get("/{ticker}", response_model=BacktestResponse, summary="Get backtest accuracy for a ticker")
async def backtest_ticker(
    ticker: str,
    start: str | None = Query(default=None, description="Start date (YYYY-MM-DD). Defaults to 1 year ago."),
    end: str | None = Query(default=None, description="End date (YYYY-MM-DD). Defaults to today."),
    horizon: int | None = Query(default=None, description="Prediction horizon in days."),
    model_id: int | None = Query(default=None, description="Specific model ID. Defaults to active model."),
) -> BacktestResponse:
    """Return actual vs predicted series with accuracy metrics for a ticker."""
    if not ticker or not ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker must be non-empty")

    today = datetime.date.today()
    start_date = start or (today - datetime.timedelta(days=365)).isoformat()
    end_date = end or today.isoformat()

    result = await get_backtest_data(
        ticker=ticker.upper().strip(),
        start_date=start_date,
        end_date=end_date,
        horizon=horizon,
        model_id=model_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No backtest data available for {ticker.upper()} in the given date range",
        )

    return BacktestResponse(**result)
