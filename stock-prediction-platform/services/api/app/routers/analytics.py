"""FastAPI router for /analytics/* endpoints — stream health, feature freshness, Kafka lag."""
from __future__ import annotations

from fastapi import APIRouter

from app.cache import build_key, cache_get, cache_set
from app.models.schemas import (
    AnalyticsSummaryResponse,
    FeastFreshnessResponse,
    FlinkJobsResponse,
    KafkaLagResponse,
)
from app.services.flink_service import get_analytics_summary, get_flink_jobs
from app.services.feast_service import get_feast_freshness
from app.services.kafka_lag_service import get_kafka_lag

router = APIRouter(prefix="/analytics", tags=["analytics"])

# TTLs match frontend poll intervals exactly
ANALYTICS_FLINK_TTL = 10    # 10s — StreamHealthPanel polls every 10s
ANALYTICS_FEAST_TTL = 30    # 30s — FeatureFreshnessPanel polls every 30s
ANALYTICS_LAG_TTL = 15      # 15s — StreamLagMonitor polls every 15s
ANALYTICS_SUMMARY_TTL = 30  # 30s — SystemHealthSummary polls every 30s


@router.get("/flink/jobs", response_model=FlinkJobsResponse)
async def flink_jobs() -> FlinkJobsResponse:
    """List all Flink jobs across all configured FlinkDeployment REST endpoints."""
    key = build_key("analytics", "flink", "jobs")
    cached = await cache_get(key)
    if cached is not None:
        return FlinkJobsResponse(**cached)
    result = await get_flink_jobs()
    await cache_set(key, result.model_dump(), ANALYTICS_FLINK_TTL)
    return result


@router.get("/feast/freshness", response_model=FeastFreshnessResponse)
async def feast_freshness() -> FeastFreshnessResponse:
    """Return Feast FeatureView staleness from the SQL registry (feast_metadata table)."""
    key = build_key("analytics", "feast", "freshness")
    cached = await cache_get(key)
    if cached is not None:
        return FeastFreshnessResponse(**cached)
    result = await get_feast_freshness()
    await cache_set(key, result.model_dump(), ANALYTICS_FEAST_TTL)
    return result


@router.get("/kafka/lag", response_model=KafkaLagResponse)
async def kafka_lag() -> KafkaLagResponse:
    """Return per-partition consumer lag for processed-features topic."""
    key = build_key("analytics", "kafka", "lag")
    cached = await cache_get(key)
    if cached is not None:
        return KafkaLagResponse(**cached)
    result = await get_kafka_lag()
    await cache_set(key, result.model_dump(), ANALYTICS_LAG_TTL)
    return result


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary() -> AnalyticsSummaryResponse:
    """Aggregate Flink health + Argo CD sync + CA last refresh for SystemHealthSummary panel."""
    key = build_key("analytics", "summary")
    cached = await cache_get(key)
    if cached is not None:
        return AnalyticsSummaryResponse(**cached)
    result = await get_analytics_summary()
    await cache_set(key, result.model_dump(), ANALYTICS_SUMMARY_TTL)
    return result
