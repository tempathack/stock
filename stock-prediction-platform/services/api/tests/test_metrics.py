"""Tests for Prometheus metrics endpoint and custom prediction metrics."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_metrics_endpoint_returns_200(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]


def test_metrics_contains_default_http_metrics(client):
    # Trigger at least one request first
    client.get("/health")
    resp = client.get("/metrics")
    body = resp.text
    assert "http_request_duration_seconds" in body or "http_requests_total" in body


def test_metrics_contains_custom_prediction_metrics(client):
    # Make a prediction request (may 404 if no model — that's ok for metrics)
    client.get("/predict/AAPL")
    resp = client.get("/metrics")
    body = resp.text
    assert "prediction_requests_total" in body


def test_prediction_latency_histogram_exists(client):
    client.get("/predict/AAPL")
    resp = client.get("/metrics")
    body = resp.text
    assert "prediction_latency_seconds" in body
