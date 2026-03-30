"""Integration tests for /analytics/* endpoints."""
from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    AnalyticsSummaryResponse,
    FeastFreshnessResponse,
    FeastViewFreshness,
    FlinkJobEntry,
    FlinkJobsResponse,
    KafkaLagResponse,
    KafkaPartitionLag,
)

client = TestClient(app)

SAMPLE_FLINK_JOBS = FlinkJobsResponse(
    jobs=[FlinkJobEntry(job_id="abc", name="ohlcv-normalizer", state="RUNNING",
                        start_time=0, duration_ms=1000, tasks_running=2)],
    total_running=1,
    total_failed=0,
)

SAMPLE_FEAST = FeastFreshnessResponse(
    views=[FeastViewFreshness(view_name="ohlcv_stats_fv",
                               last_updated="2026-03-30T12:00:00+00:00",
                               staleness_seconds=300, status="fresh")],
    registry_available=True,
)

SAMPLE_LAG = KafkaLagResponse(
    topic="processed-features",
    consumer_group="feast-writer-group",
    partitions=[KafkaPartitionLag(partition=0, current_offset=95, end_offset=100, lag=5)],
    total_lag=5,
    sampled_at=datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
)

SAMPLE_SUMMARY = AnalyticsSummaryResponse(
    argocd_sync_status="Synced",
    flink_running_jobs=1,
    flink_failed_jobs=0,
    feast_online_latency_ms=None,
    ca_last_refresh=None,
)


@pytest.fixture(autouse=True)
def bypass_cache():
    with patch("app.routers.analytics.cache_get", new_callable=AsyncMock, return_value=None), \
         patch("app.routers.analytics.cache_set", new_callable=AsyncMock):
        yield


def test_flink_jobs_endpoint_200():
    with patch("app.routers.analytics.get_flink_jobs", new_callable=AsyncMock, return_value=SAMPLE_FLINK_JOBS):
        resp = client.get("/analytics/flink/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert "jobs" in body
    assert "total_running" in body
    assert "total_failed" in body
    assert body["total_running"] == 1


def test_feast_freshness_endpoint_200():
    with patch("app.routers.analytics.get_feast_freshness", new_callable=AsyncMock, return_value=SAMPLE_FEAST):
        resp = client.get("/analytics/feast/freshness")
    assert resp.status_code == 200
    body = resp.json()
    assert "views" in body
    assert "registry_available" in body
    assert body["registry_available"] is True


def test_kafka_lag_endpoint_200():
    with patch("app.routers.analytics.get_kafka_lag", new_callable=AsyncMock, return_value=SAMPLE_LAG):
        resp = client.get("/analytics/kafka/lag")
    assert resp.status_code == 200
    body = resp.json()
    assert "partitions" in body
    assert "total_lag" in body
    assert "topic" in body
    assert body["total_lag"] == 5


def test_analytics_summary_endpoint_200():
    with patch("app.routers.analytics.get_analytics_summary", new_callable=AsyncMock, return_value=SAMPLE_SUMMARY):
        resp = client.get("/analytics/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert "flink_running_jobs" in body
    assert "flink_failed_jobs" in body
    assert "argocd_sync_status" in body
    assert body["flink_running_jobs"] == 1
