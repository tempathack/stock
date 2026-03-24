"""In-memory sliding-window rate limiter middleware.

No external dependencies — uses a per-IP counter with a sliding window.
Supports per-route overrides and returns 429 with ``Retry-After`` header.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict
from threading import Lock
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.utils.logging import get_logger

logger = get_logger(__name__)


def _parse_rate(rate_str: str) -> tuple[int, int]:
    """Parse a rate string like ``'100/minute'`` into (max_requests, window_seconds)."""
    match = re.match(r"(\d+)\s*/\s*(second|minute|hour|day)", rate_str.strip().lower())
    if not match:
        raise ValueError(f"Invalid rate format: {rate_str!r}. Use '<int>/<second|minute|hour|day>'")
    count = int(match.group(1))
    unit = match.group(2)
    windows = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}
    return count, windows[unit]


class _SlidingWindow:
    """Thread-safe sliding window counter per key."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, max_requests: int, window: int) -> tuple[bool, int]:
        """Check if the request is within the rate limit.

        Returns:
            (allowed, retry_after_seconds). retry_after is 0 when allowed.
        """
        now = time.monotonic()
        cutoff = now - window

        with self._lock:
            timestamps = self._hits[key]
            # Prune expired entries
            self._hits[key] = [t for t in timestamps if t > cutoff]
            timestamps = self._hits[key]

            if len(timestamps) >= max_requests:
                # Compute when the oldest entry in the window expires
                retry_after = int(timestamps[0] - cutoff) + 1
                return False, max(retry_after, 1)

            timestamps.append(now)
            return True, 0

    def reset(self) -> None:
        """Clear all counters (for testing)."""
        with self._lock:
            self._hits.clear()


# Module-level singleton
_window = _SlidingWindow()


def get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For behind a proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter middleware.

    Args:
        route_limits: Mapping of path prefixes to rate strings, applied
            in order of specificity (longest prefix first).
        default_limit: Fallback rate for unmatched routes.
        exempt_paths: Paths excluded from rate limiting.
    """

    def __init__(
        self,
        app: object,
        *,
        route_limits: dict[str, str] | None = None,
        default_limit: str = "100/minute",
        exempt_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._default_max, self._default_window = _parse_rate(default_limit)
        self._exempt = set(exempt_paths or [])

        # Pre-parse route limits, sorted by prefix length descending
        parsed: list[tuple[str, int, int]] = []
        for prefix, rate_str in (route_limits or {}).items():
            max_req, window_sec = _parse_rate(rate_str)
            parsed.append((prefix, max_req, window_sec))
        self._route_limits = sorted(parsed, key=lambda x: len(x[0]), reverse=True)

    def _match_limit(self, path: str) -> tuple[int, int]:
        """Return (max_requests, window) for the given path."""
        for prefix, max_req, window_sec in self._route_limits:
            if path.startswith(prefix):
                return max_req, window_sec
        return self._default_max, self._default_window

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        path = request.url.path

        # Skip exempt paths
        for exempt in self._exempt:
            if path.startswith(exempt):
                return await call_next(request)

        max_requests, window = self._match_limit(path)
        client_ip = get_client_ip(request)
        key = f"{client_ip}:{path}"

        allowed, retry_after = _window.is_allowed(key, max_requests, window)

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                client=client_ip,
                path=path,
                limit=f"{max_requests}/{window}s",
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": f"Rate limit exceeded: {max_requests} per {window}s",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


def reset_limiter() -> None:
    """Reset all rate limit counters (for testing)."""
    _window.reset()
