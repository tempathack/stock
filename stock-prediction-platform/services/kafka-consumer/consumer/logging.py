"""Structured JSON logging utility for the Kafka consumer service."""

from __future__ import annotations

import logging
import os
from typing import Any

import structlog


def _add_service_name(
    logger: Any, method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Inject the service name into every log line."""
    event_dict["service"] = os.environ.get("SERVICE_NAME", "kafka-consumer")
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


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structlog for JSON logging."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_service_name,
            structlog.processors.add_log_level,
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
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger instance."""
    return structlog.get_logger(name)
