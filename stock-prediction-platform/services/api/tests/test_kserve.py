"""Tests for KServe V2 inference client and prediction service integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# ─── kserve_client.infer_v2 payload tests ─────────────────────────────────


@pytest.mark.asyncio
async def test_infer_v2_builds_correct_payload():
    """infer_v2() sends a well-formed V2 InferRequest."""
    from app.services.kserve_client import infer_v2

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "outputs": [{"name": "predict", "shape": [1, 1], "datatype": "FP64", "data": [150.0]}],
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_response

    with patch("app.services.kserve_client.get_client", return_value=mock_client):
        result = await infer_v2(
            model_name="stock-model-serving",
            input_data=[[1.0, 2.0, 3.0]],
            feature_names=["f1", "f2", "f3"],
        )

    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    url = call_args[0][0]
    payload = call_args[1]["json"]

    assert url == "/v2/models/stock-model-serving/infer"
    assert len(payload["inputs"]) == 1
    inp = payload["inputs"][0]
    assert inp["name"] == "predict"
    assert inp["shape"] == [1, 3]
    assert inp["datatype"] == "FP64"
    assert inp["data"] == [1.0, 2.0, 3.0]
    assert result == mock_response.json.return_value


# ─── kserve_client.parse_v2_output tests ──────────────────────────────────


def test_parse_v2_output_extracts_float():
    """parse_v2_output() returns scalar from V2 response."""
    from app.services.kserve_client import parse_v2_output

    response = {
        "outputs": [
            {"name": "predict", "shape": [1, 1], "datatype": "FP64", "data": [123.45]},
        ],
    }
    assert parse_v2_output(response) == 123.45


def test_parse_v2_output_handles_int():
    """parse_v2_output() casts int-typed data to float."""
    from app.services.kserve_client import parse_v2_output

    response = {
        "outputs": [
            {"name": "predict", "shape": [1, 1], "datatype": "FP64", "data": [42]},
        ],
    }
    assert parse_v2_output(response) == 42.0
    assert isinstance(parse_v2_output(response), float)


# ─── infer_v2 with base_url override (canary) ───────────────────────────

@pytest.mark.asyncio
async def test_infer_v2_with_base_url_creates_temporary_client():
    """When base_url is provided, infer_v2 creates a temp client."""
    from app.services.kserve_client import infer_v2

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "outputs": [{"name": "predict", "shape": [1, 1], "datatype": "FP64", "data": [99.0]}],
    }
    mock_response.raise_for_status = MagicMock()

    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.kserve_client.httpx.AsyncClient", return_value=mock_client_instance) as mock_cls:
        result = await infer_v2(
            model_name="stock-model-serving-canary",
            input_data=[[1.0, 2.0]],
            base_url="http://canary-url:80",
        )

    mock_cls.assert_called_once()
    call_kwargs = mock_cls.call_args[1]
    assert call_kwargs["base_url"] == "http://canary-url:80"
    assert result["outputs"][0]["data"][0] == 99.0


# ─── get_live_prediction with KSERVE_ENABLED=True ─────────────────────────

@pytest.mark.asyncio
async def test_get_live_prediction_kserve_calls_client():
    """get_live_prediction with KSERVE_ENABLED delegates to kserve_client."""
    import numpy as np
    import pandas as pd

    from app.services.prediction_service import get_live_prediction

    # Mock OHLCV data
    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    ohlcv_df = pd.DataFrame({
        "date": dates,
        "open": np.random.default_rng(42).uniform(100, 200, 60),
        "high": np.random.default_rng(42).uniform(100, 200, 60),
        "low": np.random.default_rng(42).uniform(100, 200, 60),
        "close": np.random.default_rng(42).uniform(100, 200, 60),
        "adj_close": np.random.default_rng(42).uniform(100, 200, 60),
        "volume": np.random.default_rng(42).integers(1_000_000, 10_000_000, 60),
        "vwap": np.random.default_rng(42).uniform(100, 200, 60),
    })

    mock_kserve_response = {
        "outputs": [{"name": "predict", "shape": [1, 1], "datatype": "FP64", "data": [155.42]}],
    }

    with (
        patch("app.services.prediction_service._load_ohlcv_for_inference", return_value=ohlcv_df),
        patch("app.services.prediction_service.json") as mock_json,
        patch("app.services.kserve_client.infer_v2", new_callable=AsyncMock, return_value=mock_kserve_response),
        patch("app.config.settings") as mock_settings,
        patch("ml.features.indicators.compute_all_indicators", return_value=ohlcv_df),
    ):
        mock_settings.KSERVE_ENABLED = True
        mock_settings.KSERVE_MODEL_NAME = "stock-model-serving"
        mock_settings.KSERVE_INFERENCE_URL = "http://localhost:8080"
        mock_settings.KSERVE_TIMEOUT_SECONDS = 30.0
        mock_settings.SERVING_DIR = "/models/active"
        mock_json.load.return_value = None  # no features.json

        result = await get_live_prediction(ticker="AAPL", serving_dir="/tmp/fake")

    assert result is not None
    assert result["ticker"] == "AAPL"
    assert result["predicted_price"] == 155.42


# ─── get_live_prediction KServe fallback on ConnectError ──────────────────

@pytest.mark.asyncio
async def test_get_live_prediction_kserve_fallback_on_error():
    """get_live_prediction returns None when KServe is unreachable."""
    import numpy as np
    import pandas as pd

    from app.services.prediction_service import get_live_prediction

    dates = pd.date_range("2026-01-01", periods=60, freq="B")
    ohlcv_df = pd.DataFrame({
        "date": dates,
        "open": np.random.default_rng(42).uniform(100, 200, 60),
        "high": np.random.default_rng(42).uniform(100, 200, 60),
        "low": np.random.default_rng(42).uniform(100, 200, 60),
        "close": np.random.default_rng(42).uniform(100, 200, 60),
        "adj_close": np.random.default_rng(42).uniform(100, 200, 60),
        "volume": np.random.default_rng(42).integers(1_000_000, 10_000_000, 60),
        "vwap": np.random.default_rng(42).uniform(100, 200, 60),
    })

    with (
        patch("app.services.prediction_service._load_ohlcv_for_inference", return_value=ohlcv_df),
        patch("app.services.kserve_client.infer_v2", new_callable=AsyncMock, side_effect=httpx.ConnectError("refused")),
        patch("app.config.settings") as mock_settings,
        patch("ml.features.indicators.compute_all_indicators", return_value=ohlcv_df),
    ):
        mock_settings.KSERVE_ENABLED = True
        mock_settings.KSERVE_MODEL_NAME = "stock-model-serving"
        mock_settings.KSERVE_INFERENCE_URL = "http://localhost:8080"
        mock_settings.KSERVE_TIMEOUT_SECONDS = 30.0
        mock_settings.SERVING_DIR = "/models/active"

        result = await get_live_prediction(ticker="AAPL", serving_dir="/tmp/fake")

    assert result is None


# ─── ab_service select_model_for_request with KServe ──────────────────────

@pytest.mark.asyncio
async def test_select_model_returns_kserve_url_when_enabled():
    """select_model_for_request adds kserve_url when KSERVE_ENABLED=True."""
    from unittest.mock import PropertyMock

    from app.services.ab_service import select_model_for_request

    # Create mock row objects
    row1 = MagicMock()
    row1.model_id = 1
    row1.model_name = "Ridge"
    row1.version = "v3"
    row1.traffic_weight = 0.8

    row2 = MagicMock()
    row2.model_id = 2
    row2.model_name = "XGBoost"
    row2.version = "v1"
    row2.traffic_weight = 0.2

    mock_result = MagicMock()
    mock_result.all.return_value = [row1, row2]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.services.ab_service.get_engine", return_value=MagicMock()),
        patch("app.services.ab_service.get_async_session", return_value=mock_session),
        patch("app.services.ab_service.settings") as mock_settings,
        patch("app.services.ab_service.random.choices", return_value=[row1]),
    ):
        mock_settings.KSERVE_ENABLED = True
        mock_settings.KSERVE_INFERENCE_URL = "http://primary:80"
        mock_settings.KSERVE_MODEL_NAME = "stock-model-serving"
        mock_settings.KSERVE_CANARY_URL = "http://canary:80"

        result = await select_model_for_request()

    assert result is not None
    assert "kserve_url" in result
    assert result["kserve_url"] == "http://primary:80"
    assert result["kserve_model_name"] == "stock-model-serving"


@pytest.mark.asyncio
async def test_select_model_canary_returns_canary_url():
    """Canary model selection returns KSERVE_CANARY_URL."""
    from app.services.ab_service import select_model_for_request

    row1 = MagicMock()
    row1.model_id = 1
    row1.model_name = "Ridge"
    row1.version = "v3"
    row1.traffic_weight = 0.8

    row2 = MagicMock()
    row2.model_id = 2
    row2.model_name = "XGBoost"
    row2.version = "v1"
    row2.traffic_weight = 0.2

    mock_result = MagicMock()
    mock_result.all.return_value = [row1, row2]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.services.ab_service.get_engine", return_value=MagicMock()),
        patch("app.services.ab_service.get_async_session", return_value=mock_session),
        patch("app.services.ab_service.settings") as mock_settings,
        patch("app.services.ab_service.random.choices", return_value=[row2]),
    ):
        mock_settings.KSERVE_ENABLED = True
        mock_settings.KSERVE_INFERENCE_URL = "http://primary:80"
        mock_settings.KSERVE_MODEL_NAME = "stock-model-serving"
        mock_settings.KSERVE_CANARY_URL = "http://canary:80"

        result = await select_model_for_request()

    assert result is not None
    assert result["kserve_url"] == "http://canary:80"
    assert result["kserve_model_name"] == "stock-model-serving-canary"


@pytest.mark.asyncio
async def test_select_model_no_kserve_url_when_disabled():
    """select_model_for_request omits kserve_url when KSERVE_ENABLED=False."""
    from app.services.ab_service import select_model_for_request

    row1 = MagicMock()
    row1.model_id = 1
    row1.model_name = "Ridge"
    row1.version = "v3"
    row1.traffic_weight = 1.0

    mock_result = MagicMock()
    mock_result.all.return_value = [row1]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.services.ab_service.get_engine", return_value=MagicMock()),
        patch("app.services.ab_service.get_async_session", return_value=mock_session),
        patch("app.services.ab_service.settings") as mock_settings,
    ):
        mock_settings.KSERVE_ENABLED = False

        result = await select_model_for_request()

    assert result is not None
    assert "kserve_url" not in result
