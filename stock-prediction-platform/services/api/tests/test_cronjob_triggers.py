"""Tests for CronJob trigger modules: trigger_intraday and trigger_historical."""
from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from app.jobs.trigger_intraday import main as trigger_intraday_main
from app.jobs.trigger_historical import main as trigger_historical_main


_SUCCESS_BODY = {
    "status": "completed",
    "mode": "intraday",
    "tickers_requested": 20,
    "records_fetched": 60,
    "records_produced": 60,
}

_HISTORICAL_SUCCESS_BODY = {
    "status": "completed",
    "mode": "historical",
    "tickers_requested": 20,
    "records_fetched": 5000,
    "records_produced": 5000,
}


# -----------------------------------------------------------------------
# trigger_intraday
# -----------------------------------------------------------------------


@patch("app.jobs.trigger_intraday.httpx.post")
def test_trigger_intraday_success(mock_post):
    """Returns exit code 0 on successful 200 response."""
    mock_resp = httpx.Response(
        200,
        json=_SUCCESS_BODY,
        request=httpx.Request("POST", "http://test/ingest/intraday"),
    )
    mock_post.return_value = mock_resp

    assert trigger_intraday_main() == 0
    mock_post.assert_called_once()
    call_url = mock_post.call_args[0][0]
    assert call_url.endswith("/ingest/intraday")


@patch("app.jobs.trigger_intraday.httpx.post")
def test_trigger_intraday_http_error(mock_post):
    """Returns exit code 1 on HTTP 502 response."""
    mock_resp = httpx.Response(502, json={"detail": "Yahoo Finance down"})
    mock_resp._request = httpx.Request("POST", "http://test/ingest/intraday")
    mock_post.return_value = mock_resp

    assert trigger_intraday_main() == 1


@patch("app.jobs.trigger_intraday.httpx.post")
def test_trigger_intraday_connection_error(mock_post):
    """Returns exit code 1 when API is unreachable."""
    mock_post.side_effect = httpx.ConnectError("Connection refused")

    assert trigger_intraday_main() == 1


@patch("app.jobs.trigger_intraday.httpx.post")
def test_trigger_intraday_timeout(mock_post):
    """Returns exit code 1 on request timeout."""
    mock_post.side_effect = httpx.ReadTimeout("Read timed out")

    assert trigger_intraday_main() == 1


@patch.dict("os.environ", {"API_BASE_URL": "http://custom:9090"})
@patch("app.jobs.trigger_intraday.API_BASE_URL", "http://custom:9090")
@patch("app.jobs.trigger_intraday.httpx.post")
def test_trigger_intraday_custom_base_url(mock_post):
    """Uses API_BASE_URL from environment override."""
    mock_resp = httpx.Response(
        200,
        json=_SUCCESS_BODY,
        request=httpx.Request("POST", "http://custom:9090/ingest/intraday"),
    )
    mock_post.return_value = mock_resp

    trigger_intraday_main()
    call_url = mock_post.call_args[0][0]
    assert call_url == "http://custom:9090/ingest/intraday"


# -----------------------------------------------------------------------
# trigger_historical
# -----------------------------------------------------------------------


@patch("app.jobs.trigger_historical.httpx.post")
def test_trigger_historical_success(mock_post):
    """Returns exit code 0 on successful 200 response."""
    mock_resp = httpx.Response(
        200,
        json=_HISTORICAL_SUCCESS_BODY,
        request=httpx.Request("POST", "http://test/ingest/historical"),
    )
    mock_post.return_value = mock_resp

    assert trigger_historical_main() == 0
    mock_post.assert_called_once()
    call_url = mock_post.call_args[0][0]
    assert call_url.endswith("/ingest/historical")


@patch("app.jobs.trigger_historical.httpx.post")
def test_trigger_historical_http_error(mock_post):
    """Returns exit code 1 on HTTP 502 response."""
    mock_resp = httpx.Response(502, json={"detail": "Yahoo Finance down"})
    mock_resp._request = httpx.Request("POST", "http://test/ingest/historical")
    mock_post.return_value = mock_resp

    assert trigger_historical_main() == 1


@patch("app.jobs.trigger_historical.httpx.post")
def test_trigger_historical_connection_error(mock_post):
    """Returns exit code 1 when API is unreachable."""
    mock_post.side_effect = httpx.ConnectError("Connection refused")

    assert trigger_historical_main() == 1


@patch("app.jobs.trigger_historical.httpx.post")
def test_trigger_historical_timeout(mock_post):
    """Returns exit code 1 on request timeout."""
    mock_post.side_effect = httpx.ReadTimeout("Read timed out")

    assert trigger_historical_main() == 1
