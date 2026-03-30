"""Proxy the Flink REST API for analytics endpoints."""
from __future__ import annotations

import httpx
from app.config import settings
from app.models.schemas import FlinkJobEntry, FlinkJobsResponse, AnalyticsSummaryResponse


def _flink_rest_urls() -> list[str]:
    return [u.strip() for u in settings.FLINK_REST_URLS.split(",") if u.strip()]


async def get_flink_jobs() -> FlinkJobsResponse:
    """Proxy GET /v1/jobs/overview from ALL configured Flink REST endpoints.
    Each FlinkDeployment (application mode) has its own REST service.
    Aggregate jobs from all three into one response. On failure returns empty list."""
    all_jobs: list[FlinkJobEntry] = []
    for base_url in _flink_rest_urls():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{base_url}/v1/jobs/overview")
                resp.raise_for_status()
                data = resp.json()
            jobs = [
                FlinkJobEntry(
                    job_id=j.get("jid", ""),
                    name=j.get("name", ""),
                    state=j.get("state", "UNKNOWN"),
                    start_time=j.get("start-time", 0),
                    duration_ms=j.get("duration", 0),
                    tasks_running=j.get("tasks", {}).get("running", 0),
                )
                for j in data.get("jobs", [])
            ]
            all_jobs.extend(jobs)
        except Exception:
            # Flink may be unreachable in local dev — return empty, not 500
            continue

    running = sum(1 for j in all_jobs if j.state == "RUNNING")
    failed = sum(1 for j in all_jobs if j.state in ("FAILED", "FAILING"))
    return FlinkJobsResponse(jobs=all_jobs, total_running=running, total_failed=failed)


async def get_analytics_summary() -> AnalyticsSummaryResponse:
    """Aggregate Flink cluster health + Argo CD sync + CA last refresh for SystemHealthSummary."""
    import datetime

    # --- Flink summary ---
    flink = await get_flink_jobs()

    # --- Argo CD sync status (optional — requires ARGOCD_TOKEN) ---
    argocd_sync: str | None = None
    if settings.ARGOCD_TOKEN:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{settings.ARGOCD_URL}/api/v1/applications",
                    headers={"Authorization": f"Bearer {settings.ARGOCD_TOKEN}"},
                )
                resp.raise_for_status()
                apps = resp.json().get("items", [])
                # Report OutOfSync if ANY application is out of sync
                statuses = [
                    a.get("status", {}).get("sync", {}).get("status", "Unknown")
                    for a in apps
                ]
                argocd_sync = "OutOfSync" if "OutOfSync" in statuses else "Synced"
        except Exception:
            argocd_sync = None

    # --- CA last refresh from TimescaleDB (query information schema) ---
    ca_last_refresh: str | None = None
    try:
        from app.models.database import get_async_session, get_engine
        from sqlalchemy import text
        if get_engine() is not None:
            async with get_async_session() as session:
                result = await session.execute(text(
                    "SELECT last_updated_timestamp FROM timescaledb_information.continuous_aggregates "
                    "ORDER BY last_updated_timestamp DESC LIMIT 1"
                ))
                row = result.fetchone()
                if row and row[0]:
                    ca_last_refresh = row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
    except Exception:
        ca_last_refresh = None

    return AnalyticsSummaryResponse(
        argocd_sync_status=argocd_sync,
        flink_running_jobs=flink.total_running,
        flink_failed_jobs=flink.total_failed,
        feast_online_latency_ms=None,  # Phase 69: not measured yet
        ca_last_refresh=ca_last_refresh,
    )
