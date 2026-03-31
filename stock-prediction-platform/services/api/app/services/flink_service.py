"""Proxy the Flink REST API for analytics endpoints."""
from __future__ import annotations

import asyncio

import httpx
from kubernetes import client as k8s_client, config as k8s_config

from app.cache import build_key, cache_get, cache_set
from app.config import settings
from app.models.schemas import FlinkJobEntry, FlinkJobsResponse, AnalyticsSummaryResponse

FEAST_LATENCY_TTL = 60  # seconds — Feast latency measurement is cached to avoid timing on every request


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


async def _get_argocd_sync_status() -> str | None:
    """Read ArgoCD Application CRD sync status from K8s API.

    Uses kubernetes Python client with in-cluster config (falls back to kubeconfig for local dev).
    Returns 'Synced', 'OutOfSync', or None on any error (including RBAC denial).
    Does NOT use ARGOCD_TOKEN or httpx — reads directly from K8s API server.
    """
    try:
        def _sync() -> str:
            try:
                k8s_config.load_incluster_config()
            except k8s_config.ConfigException:
                k8s_config.load_kube_config()
            api = k8s_client.CustomObjectsApi()
            result = api.list_namespaced_custom_object(
                group="argoproj.io",
                version="v1alpha1",
                namespace="argocd",
                plural="applications",
            )
            statuses = [
                item.get("status", {}).get("sync", {}).get("status", "Unknown")
                for item in result.get("items", [])
            ]
            return "OutOfSync" if "OutOfSync" in statuses else "Synced"
        return await asyncio.to_thread(_sync)
    except Exception:
        return None


async def _get_feast_online_latency_cached() -> float | None:
    """Return cached Feast latency measurement (TTL=60s). Times a live get_online_features() call."""
    key = build_key("analytics", "feast", "latency")
    cached = await cache_get(key)
    if cached is not None:
        return cached.get("latency_ms")
    from app.services.feast_service import measure_feast_online_latency_ms
    latency_ms = await measure_feast_online_latency_ms()
    await cache_set(key, {"latency_ms": latency_ms}, FEAST_LATENCY_TTL)
    return latency_ms


async def get_analytics_summary() -> AnalyticsSummaryResponse:
    """Aggregate Flink cluster health + ArgoCD sync (K8s CRD) + Feast latency + CA last refresh."""
    import datetime

    # --- Flink summary ---
    flink = await get_flink_jobs()

    # --- ArgoCD sync status (K8s CRD — does NOT require ARGOCD_TOKEN) ---
    argocd_sync = await _get_argocd_sync_status()

    # --- Feast online latency (cached 60s) ---
    feast_latency = await _get_feast_online_latency_cached()

    # --- CA last refresh from TimescaleDB (query information schema) ---
    ca_last_refresh: str | None = None
    try:
        from app.models.database import get_async_session, get_engine
        from sqlalchemy import text
        if get_engine() is not None:
            async with get_async_session() as session:
                # Try primary column name first (TimescaleDB >= 2.x)
                # Fall back to 'last_run_started_at' if column name differs
                try:
                    result = await session.execute(text(
                        "SELECT last_updated_timestamp FROM timescaledb_information.continuous_aggregates "
                        "ORDER BY last_updated_timestamp DESC NULLS LAST LIMIT 1"
                    ))
                except Exception:
                    # Column may be named differently — try the information_schema lookup
                    result = await session.execute(text(
                        "SELECT last_run_started_at AS last_updated_timestamp "
                        "FROM timescaledb_information.continuous_aggregates "
                        "ORDER BY last_run_started_at DESC NULLS LAST LIMIT 1"
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
        feast_online_latency_ms=feast_latency,
        ca_last_refresh=ca_last_refresh,
    )
