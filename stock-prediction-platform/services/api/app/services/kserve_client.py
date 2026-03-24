"""Thin async HTTP client for KServe V2 inference protocol."""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """Lazy-initialise a module-level httpx.AsyncClient.

    Uses ``settings.KSERVE_INFERENCE_URL`` as default base URL.
    Reused across requests for connection pooling.
    """
    global _client  # noqa: PLW0603
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.KSERVE_INFERENCE_URL or "",
            timeout=httpx.Timeout(
                connect=5.0,
                read=settings.KSERVE_TIMEOUT_SECONDS,
                write=10.0,
                pool=5.0,
            ),
        )
    return _client


async def close_client() -> None:
    """Close the cached httpx client. Called from app lifespan shutdown."""
    global _client  # noqa: PLW0603
    if _client is not None:
        await _client.aclose()
        _client = None


async def infer_v2(
    model_name: str,
    input_data: list[list[float]],
    feature_names: list[str] | None = None,
    base_url: str | None = None,
) -> dict:
    """Call KServe V2 inference endpoint.

    POST ``{base_url}/v2/models/{model_name}/infer``

    Parameters
    ----------
    model_name:
        Model name registered with KServe.
    input_data:
        List of rows, e.g. ``[[feat1, feat2, ...]]``.
    feature_names:
        Optional column names (unused by V2 protocol but logged for debug).
    base_url:
        Override base URL for canary endpoint. When *None*, uses the
        default singleton client (``settings.KSERVE_INFERENCE_URL``).

    Returns
    -------
    dict
        Parsed JSON V2 InferResponse.

    Raises
    ------
    httpx.HTTPStatusError
        On 4xx/5xx from KServe.
    httpx.ConnectError, httpx.TimeoutException
        On network issues.
    """
    n_rows = len(input_data)
    n_features = len(input_data[0]) if input_data else 0

    # Flatten for V2 row-major layout
    flat_data = [v for row in input_data for v in row]

    payload = {
        "inputs": [
            {
                "name": "predict",
                "shape": [n_rows, n_features],
                "datatype": "FP64",
                "data": flat_data,
            },
        ],
    }

    url = f"/v2/models/{model_name}/infer"

    if base_url is not None:
        async with httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(
                connect=5.0,
                read=settings.KSERVE_TIMEOUT_SECONDS,
                write=10.0,
                pool=5.0,
            ),
        ) as tmp_client:
            resp = await tmp_client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

    client = await get_client()
    resp = await client.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()


def parse_v2_output(response: dict) -> float:
    """Extract predicted value from V2 InferResponse.

    Expected shape::

        {"outputs": [{"name": "predict", "shape": [1, 1],
                       "datatype": "FP64", "data": [123.45]}]}

    Returns the first scalar from ``outputs[0]["data"]``.
    """
    return float(response["outputs"][0]["data"][0])
