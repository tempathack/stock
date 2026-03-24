"""Structured JSON logging utility using structlog.

Configures structlog for production JSON logging. Every log line is valid JSON
containing: timestamp, level, service, message, request_id, trace_id.

Usage:
    from app.utils.logging import get_logger

    logger = get_logger(__name__)
    logger.info("something happened", extra_key="value")

The ``service`` field is read from the ``SERVICE_NAME`` environment variable
(defaults to ``"unknown"``). ``request_id`` and ``trace_id`` are pulled from
structlog contextvars — bind them in FastAPI middleware per request.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import structlog


def _add_service_name(
    logger: Any, method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Inject the service name from the SERVICE_NAME environment variable."""
    event_dict["service"] = os.environ.get("SERVICE_NAME", "unknown")
    return event_dict


def _rename_event_to_message(
    logger: Any, method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Rename structlog's 'event' key to 'message' for consistent output."""
    event_dict["message"] = event_dict.pop("event")
    return event_dict


def _ensure_context_defaults(
    logger: Any, method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Ensure request_id and trace_id always appear, defaulting to empty string."""
    event_dict.setdefault("request_id", "")
    event_dict.setdefault("trace_id", "")
    return event_dict


# Configure stdlib logging level from LOG_LEVEL env var (structlog defers to it)
logging.basicConfig(
    format="%(message)s",
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO),
)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        _add_service_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        _ensure_context_defaults,
        _rename_event_to_message,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


def configure_uvicorn_logging() -> None:
    """Route uvicorn's access and error loggers through structlog JSON formatting.

    Call this once during application startup (lifespan) so that uvicorn startup
    messages and any residual access log lines are emitted as valid JSON matching
    the application log schema.
    """
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.add_log_level,
            _add_service_name,
            structlog.processors.TimeStamper(fmt="iso"),
            _ensure_context_defaults,
            _rename_event_to_message,
            structlog.processors.JSONRenderer(),
        ],
    )

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvi_logger = logging.getLogger(logger_name)
        uvi_logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        uvi_logger.addHandler(handler)
        uvi_logger.propagate = False


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger instance.

    Args:
        name: Logger name, typically ``__name__`` of the calling module.

    Returns:
        A bound structlog logger configured for JSON output.
    """
    return structlog.get_logger(name)
