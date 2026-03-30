"""Query Feast SQL registry for FeatureView freshness."""
from __future__ import annotations

import datetime
# Import concrete types so isinstance() still works when datetime module is mocked in tests
from datetime import datetime as _dt_type

from sqlalchemy import text

from app.config import settings
from app.models.database import get_async_session, get_engine
from app.models.schemas import FeastViewFreshness, FeastFreshnessResponse


def _feature_views() -> list[str]:
    return [v.strip() for v in settings.FEAST_FEATURE_VIEWS.split(",") if v.strip()]


async def get_feast_freshness() -> FeastFreshnessResponse:
    """Query feast_metadata table for last_updated_timestamp per FeatureView.
    Falls back to registry_available=False if DB is unavailable or table doesn't exist."""
    if get_engine() is None:
        return FeastFreshnessResponse(views=[], registry_available=False)

    views_to_check = _feature_views()
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    try:
        async with get_async_session() as session:
            # Feast 0.61.0 SQL registry: table feast_metadata,
            # columns: metadata_key, metadata_value, last_updated_timestamp, created_timestamp
            result = await session.execute(
                text("""
                    SELECT metadata_key, last_updated_timestamp
                    FROM feast_metadata
                    WHERE metadata_key = ANY(:views)
                """),
                {"views": views_to_check},
            )
            rows = {r["metadata_key"]: r["last_updated_timestamp"] for r in result.mappings()}
    except Exception:
        # Table may not exist if feast apply hasn't run
        return FeastFreshnessResponse(views=[], registry_available=False)

    result_views: list[FeastViewFreshness] = []
    for view_name in views_to_check:
        ts = rows.get(view_name)
        if ts is None:
            result_views.append(FeastViewFreshness(
                view_name=view_name,
                last_updated=None,
                staleness_seconds=None,
                status="unknown",
            ))
            continue

        # ts may be a datetime or unix int — normalize
        # Use _dt_type (bound at import time) so isinstance works even when datetime module is mocked
        if isinstance(ts, (int, float)):
            last_dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
        elif isinstance(ts, _dt_type):
            last_dt = ts.replace(tzinfo=datetime.timezone.utc) if ts.tzinfo is None else ts
        else:
            last_dt = None

        if last_dt is None:
            staleness_s = None
            status = "unknown"
        else:
            staleness_s = int((now - last_dt).total_seconds())
            # Thresholds from UI-SPEC: <15min fresh, <1h stale warning, >1h stale error
            if staleness_s < 15 * 60:
                status = "fresh"
            elif staleness_s < 60 * 60:
                status = "stale"
            else:
                status = "stale"

        result_views.append(FeastViewFreshness(
            view_name=view_name,
            last_updated=last_dt.isoformat() if last_dt else None,
            staleness_seconds=staleness_s,
            status=status,
        ))

    return FeastFreshnessResponse(views=result_views, registry_available=True)
