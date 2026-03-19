"""CronJob trigger for intraday ingestion.

Invoked by K8s CronJob via: ``python -m app.jobs.trigger_intraday``

Makes an HTTP POST to the running FastAPI service at /ingest/intraday
and exits with code 0 on success, 1 on failure.
"""

from __future__ import annotations

import os
import sys

import httpx

from app.utils.logging import get_logger

logger = get_logger(__name__)

API_BASE_URL = os.environ.get(
    "API_BASE_URL", "http://stock-api.ingestion.svc.cluster.local:8000"
)
REQUEST_TIMEOUT = int(os.environ.get("TRIGGER_TIMEOUT_SECONDS", "300"))


def main() -> int:
    """POST to /ingest/intraday and return exit code."""
    url = f"{API_BASE_URL}/ingest/intraday"
    logger.info("trigger_intraday_start", url=url, timeout=REQUEST_TIMEOUT)

    try:
        response = httpx.post(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "trigger_intraday_http_error",
            status_code=exc.response.status_code,
            detail=exc.response.text,
        )
        return 1
    except httpx.RequestError as exc:
        logger.error("trigger_intraday_request_error", error=str(exc))
        return 1

    data = response.json()
    logger.info(
        "trigger_intraday_complete",
        status=data.get("status"),
        records_fetched=data.get("records_fetched"),
        records_produced=data.get("records_produced"),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
