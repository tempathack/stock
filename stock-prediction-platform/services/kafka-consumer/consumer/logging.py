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
