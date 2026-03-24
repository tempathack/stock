"""Tests for the health check endpoint."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    """GET /health returns HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_shape() -> None:
    """Response JSON has expected keys: service, version, status, db_pool, redis_status."""
    response = client.get("/health")
    data = response.json()
    assert {"service", "version", "status", "db_pool", "redis_status"} == set(data.keys())


@patch("app.routers.health.check_db", return_value={"status": "ok"})
def test_health_response_values(mock_db) -> None:
    """Response values match expected defaults when DB is reachable."""
    response = client.get("/health")
    data = response.json()
    assert data["service"] == "stock-api"
    assert data["version"] == "1.0.0"
    assert data["status"] == "ok"


def test_health_service_name_from_settings() -> None:
    """Response service field matches settings.SERVICE_NAME."""
    response = client.get("/health")
    data = response.json()
    assert data["service"] == settings.SERVICE_NAME
