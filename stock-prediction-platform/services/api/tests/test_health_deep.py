"""Tests for rate limiting and deep health checks (Phase 48)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.rate_limit import reset_limiter

client = TestClient(app)


# ── Rate Limiting Tests ──────────────────────────────────────────────────


class TestRateLimiting:
    """Verify middleware rate limiting is wired correctly."""

    def setup_method(self) -> None:
        """Reset rate limiter state between tests."""
        reset_limiter()

    def test_health_exempt_from_rate_limit(self) -> None:
        """GET /health has no rate limit and always succeeds."""
        for _ in range(150):
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_rate_limit_returns_429_with_retry_after(self) -> None:
        """Exceeding the rate limit returns 429 with Retry-After header."""
        reset_limiter()
        responses = []
        for i in range(105):
            resp = client.get("/models/comparison")
            responses.append(resp.status_code)
            if resp.status_code == 429:
                assert "Retry-After" in resp.headers
                break

        assert 429 in responses, "Expected at least one 429 response"

    def test_rate_limit_response_body(self) -> None:
        """429 response body contains error, detail, retry_after fields."""
        reset_limiter()
        resp = None
        for _ in range(105):
            resp = client.get("/models/comparison")
            if resp.status_code == 429:
                break

        if resp and resp.status_code == 429:
            body = resp.json()
            assert body["error"] == "rate_limit_exceeded"
            assert "detail" in body
            assert "retry_after" in body

    def test_metrics_exempt_from_rate_limit(self) -> None:
        """GET /metrics is exempt from rate limiting."""
        for _ in range(110):
            resp = client.get("/metrics")
            assert resp.status_code == 200


# ── Health Check Tests ───────────────────────────────────────────────────


class TestHealthEndpoint:
    """Test the enhanced /health endpoint."""

    def test_health_returns_200(self) -> None:
        """GET /health returns HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_shape(self) -> None:
        """Response JSON has expected keys."""
        response = client.get("/health")
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data

    def test_health_service_values(self) -> None:
        """Response values match expected defaults."""
        response = client.get("/health")
        data = response.json()
        assert data["service"] == settings.SERVICE_NAME
        assert data["version"] == settings.APP_VERSION

    @patch("app.routers.health.check_db")
    def test_health_degraded_when_db_unreachable(self, mock_db: AsyncMock) -> None:
        """GET /health returns degraded status when DB check fails."""
        mock_db.return_value = {"status": "error", "message": "Connection refused"}

        response = client.get("/health")
        data = response.json()
        assert data["status"] == "degraded"

    @patch("app.routers.health.check_db")
    def test_health_ok_when_db_reachable(self, mock_db: AsyncMock) -> None:
        """GET /health returns ok when DB check passes."""
        mock_db.return_value = {"status": "ok"}

        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"


class TestDeepHealthEndpoint:
    """Test the /health/deep endpoint."""

    @patch("app.routers.health.run_deep_checks")
    def test_deep_health_returns_200(self, mock_checks: AsyncMock) -> None:
        """GET /health/deep returns HTTP 200."""
        mock_checks.return_value = {
            "status": "ok",
            "components": {
                "database": {"status": "ok"},
                "kafka": {"status": "ok", "brokers": 1},
                "model_freshness": {"status": "ok", "trained_at": "2026-03-20T00:00:00+00:00", "age_days": 4},
                "prediction_staleness": {"status": "ok", "last_prediction_at": "2026-03-24T00:00:00+00:00", "age_hours": 2.0},
            },
        }

        response = client.get("/health/deep")
        assert response.status_code == 200

    @patch("app.routers.health.run_deep_checks")
    def test_deep_health_response_shape(self, mock_checks: AsyncMock) -> None:
        """Response includes service, version, status, components."""
        mock_checks.return_value = {
            "status": "ok",
            "components": {
                "database": {"status": "ok"},
                "kafka": {"status": "ok", "brokers": 1},
                "model_freshness": {"status": "ok", "trained_at": "2026-03-20T00:00:00+00:00", "age_days": 4},
                "prediction_staleness": {"status": "ok", "last_prediction_at": "2026-03-24T00:00:00+00:00", "age_hours": 2.0},
            },
        }

        response = client.get("/health/deep")
        data = response.json()
        assert data["service"] == settings.SERVICE_NAME
        assert data["version"] == settings.APP_VERSION
        assert "components" in data
        assert set(data["components"].keys()) == {
            "database", "kafka", "model_freshness", "prediction_staleness"
        }

    @patch("app.routers.health.run_deep_checks")
    def test_deep_health_degraded_on_stale_model(self, mock_checks: AsyncMock) -> None:
        """Returns degraded when model freshness is warning."""
        mock_checks.return_value = {
            "status": "degraded",
            "components": {
                "database": {"status": "ok"},
                "kafka": {"status": "ok", "brokers": 1},
                "model_freshness": {"status": "warning", "message": "Model stale: trained 10d ago"},
                "prediction_staleness": {"status": "ok", "last_prediction_at": "2026-03-24T00:00:00+00:00", "age_hours": 2.0},
            },
        }

        response = client.get("/health/deep")
        data = response.json()
        assert data["status"] == "degraded"

    @patch("app.routers.health.run_deep_checks")
    def test_deep_health_unhealthy_on_db_error(self, mock_checks: AsyncMock) -> None:
        """Returns unhealthy when DB is down."""
        mock_checks.return_value = {
            "status": "unhealthy",
            "components": {
                "database": {"status": "error", "message": "Connection refused"},
                "kafka": {"status": "ok", "brokers": 1},
                "model_freshness": {"status": "warning", "message": "DB not available"},
                "prediction_staleness": {"status": "warning", "message": "DB not available"},
            },
        }

        response = client.get("/health/deep")
        data = response.json()
        assert data["status"] == "unhealthy"

    @patch("app.routers.health.run_deep_checks")
    def test_deep_health_all_components_ok(self, mock_checks: AsyncMock) -> None:
        """Returns ok when all components pass."""
        mock_checks.return_value = {
            "status": "ok",
            "components": {
                "database": {"status": "ok"},
                "kafka": {"status": "ok", "brokers": 3},
                "model_freshness": {"status": "ok", "trained_at": "2026-03-22T00:00:00+00:00", "age_days": 2},
                "prediction_staleness": {"status": "ok", "last_prediction_at": "2026-03-24T10:00:00+00:00", "age_hours": 1.0},
            },
        }

        response = client.get("/health/deep")
        data = response.json()
        assert data["status"] == "ok"


# ── Health Service Unit Tests ────────────────────────────────────────────


class TestHealthService:
    """Unit tests for the health_service module."""

    @pytest.mark.asyncio
    @patch("app.services.health_service.get_engine", return_value=None)
    async def test_check_db_no_engine(self, mock_engine: MagicMock) -> None:
        """check_db returns error when engine is not initialised."""
        from app.services.health_service import check_db
        result = await check_db()
        assert result["status"] == "error"

    @pytest.mark.asyncio
    @patch("app.services.health_service.get_engine", return_value=None)
    async def test_check_model_freshness_no_db(self, mock_engine: MagicMock) -> None:
        """check_model_freshness returns warning when DB unavailable."""
        from app.services.health_service import check_model_freshness
        result = await check_model_freshness()
        assert result["status"] == "warning"

    @pytest.mark.asyncio
    @patch("app.services.health_service.get_engine", return_value=None)
    async def test_check_prediction_staleness_no_db(self, mock_engine: MagicMock) -> None:
        """check_prediction_staleness returns warning when DB unavailable."""
        from app.services.health_service import check_prediction_staleness
        result = await check_prediction_staleness()
        assert result["status"] == "warning"


# ── Rate Limit Module Unit Tests ─────────────────────────────────────────


class TestRateLimitModule:
    """Unit tests for the rate_limit module internals."""

    def test_parse_rate_minute(self) -> None:
        from app.rate_limit import _parse_rate
        assert _parse_rate("100/minute") == (100, 60)

    def test_parse_rate_second(self) -> None:
        from app.rate_limit import _parse_rate
        assert _parse_rate("10/second") == (10, 1)

    def test_parse_rate_hour(self) -> None:
        from app.rate_limit import _parse_rate
        assert _parse_rate("1000/hour") == (1000, 3600)

    def test_parse_rate_day(self) -> None:
        from app.rate_limit import _parse_rate
        assert _parse_rate("10000/day") == (10000, 86400)

    def test_parse_rate_invalid(self) -> None:
        from app.rate_limit import _parse_rate
        with pytest.raises(ValueError):
            _parse_rate("not-a-rate")

    def test_sliding_window_allows_within_limit(self) -> None:
        from app.rate_limit import _SlidingWindow
        sw = _SlidingWindow()
        for _ in range(5):
            allowed, _ = sw.is_allowed("testkey", 10, 60)
            assert allowed

    def test_sliding_window_blocks_over_limit(self) -> None:
        from app.rate_limit import _SlidingWindow
        sw = _SlidingWindow()
        for _ in range(10):
            sw.is_allowed("testkey2", 10, 60)
        allowed, retry_after = sw.is_allowed("testkey2", 10, 60)
        assert not allowed
        assert retry_after > 0
