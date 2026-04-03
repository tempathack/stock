"""Unit tests for sentiment timeseries endpoint and schema.

Phase 89 — Wave 0 scaffold. Tests start RED (schema + service not yet implemented)
and turn GREEN after Task 2.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest


# ── Migration file existence ─────────────────────────────────────────────────

def test_migration_006_file_exists():
    """Migration 006 file must exist in alembic/versions/."""
    migration_dir = Path(__file__).parent.parent / "alembic" / "versions"
    files = list(migration_dir.glob("006*.py"))
    assert files, (
        "006_sentiment_timeseries.py not found in alembic/versions/. "
        "Create the Alembic migration for the sentiment_timeseries hypertable."
    )


def test_migration_006_contains_create_table():
    """Migration 006 must contain CREATE TABLE sentiment_timeseries."""
    migration_dir = Path(__file__).parent.parent / "alembic" / "versions"
    files = list(migration_dir.glob("006*.py"))
    assert files, "Migration 006 file not found"
    content = files[0].read_text()
    assert "sentiment_timeseries" in content, (
        "Migration 006 must create the sentiment_timeseries table"
    )
    assert "create_hypertable" in content, (
        "Migration 006 must convert sentiment_timeseries to a TimescaleDB hypertable"
    )


def test_migration_006_down_revision():
    """Migration 006 must chain from 005timescaleolap."""
    migration_dir = Path(__file__).parent.parent / "alembic" / "versions"
    files = list(migration_dir.glob("006*.py"))
    assert files, "Migration 006 file not found"
    content = files[0].read_text()
    assert "005timescaleolap" in content, (
        "Migration 006 down_revision must be '005timescaleolap' to chain from migration 005"
    )


# ── Schema tests ─────────────────────────────────────────────────────────────

def test_sentiment_data_point_schema():
    """SentimentDataPoint must have timestamp, avg_sentiment, mention_count, positive_ratio, negative_ratio."""
    from app.models.schemas import SentimentDataPoint

    point = SentimentDataPoint(
        timestamp="2026-04-03T10:00:00+00:00",
        avg_sentiment=0.25,
        mention_count=42,
        positive_ratio=0.6,
        negative_ratio=0.1,
    )
    assert point.timestamp == "2026-04-03T10:00:00+00:00"
    assert point.avg_sentiment == 0.25
    assert point.mention_count == 42
    assert point.positive_ratio == 0.6
    assert point.negative_ratio == 0.1


def test_sentiment_data_point_nullable_fields():
    """SentimentDataPoint fields other than timestamp must be nullable."""
    from app.models.schemas import SentimentDataPoint

    point = SentimentDataPoint(timestamp="2026-04-03T10:00:00+00:00")
    assert point.avg_sentiment is None
    assert point.mention_count is None
    assert point.positive_ratio is None
    assert point.negative_ratio is None


def test_sentiment_timeseries_response_schema():
    """SentimentTimeseriesResponse must have ticker, points, count, window_hours."""
    from app.models.schemas import SentimentDataPoint, SentimentTimeseriesResponse

    pts = [
        SentimentDataPoint(
            timestamp="2026-04-03T10:00:00+00:00",
            avg_sentiment=0.1,
            mention_count=5,
            positive_ratio=0.4,
            negative_ratio=0.2,
        )
    ]
    resp = SentimentTimeseriesResponse(
        ticker="AAPL",
        points=pts,
        count=1,
        window_hours=10,
    )
    assert resp.ticker == "AAPL"
    assert len(resp.points) == 1
    assert resp.count == 1
    assert resp.window_hours == 10


# ── Service function tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_sentiment_timeseries_returns_list():
    """get_sentiment_timeseries must return a list of dicts with required keys."""
    from app.services.market_service import get_sentiment_timeseries

    mock_rows = [
        {
            "timestamp": "2026-04-03T10:00:00+00:00",
            "avg_sentiment": 0.3,
            "mention_count": 10,
            "positive_ratio": 0.5,
            "negative_ratio": 0.15,
        }
    ]

    with patch(
        "app.services.market_service.get_async_session"
    ) as mock_session_ctx:
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = [
            type("Row", (), {"_mapping": row})() for row in mock_rows
        ]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await get_sentiment_timeseries("AAPL", hours=10)

    assert isinstance(result, list)
    assert len(result) == 1
    row = result[0]
    assert "timestamp" in row
    assert "avg_sentiment" in row
    assert "mention_count" in row
    assert "positive_ratio" in row
    assert "negative_ratio" in row


# ── Endpoint smoke tests ──────────────────────────────────────────────────────

def test_sentiment_timeseries_endpoint_registered():
    """GET /market/sentiment/{ticker}/timeseries must be registered in the router."""
    from app.routers.market import router

    routes = [r.path for r in router.routes]
    assert any("sentiment" in p and "timeseries" in p for p in routes), (
        f"No /market/sentiment/{{ticker}}/timeseries route found. Routes: {routes}"
    )
