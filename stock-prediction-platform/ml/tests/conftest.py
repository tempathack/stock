"""Shared fixtures for ml module tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """Return a deterministic synthetic OHLCV DataFrame with 250 rows.

    Simulates daily business-day data starting 2024-01-02 with a random-walk
    close price around 170 and realistic open/high/low/volume.
    """
    rng = np.random.default_rng(42)
    n = 250

    dates = pd.bdate_range(start="2024-01-02", periods=n, freq="B")

    # Random-walk close prices starting near 170
    returns = rng.normal(loc=0.0003, scale=0.015, size=n)
    close = 170.0 * np.cumprod(1 + returns)

    # Intraday spread around close
    spread = rng.uniform(0.002, 0.012, size=n)
    high = close * (1 + spread)
    low = close * (1 - spread)

    # Open near previous close with small gap
    open_ = np.empty(n)
    open_[0] = close[0] * (1 + rng.normal(0, 0.003))
    for i in range(1, n):
        open_[i] = close[i - 1] * (1 + rng.normal(0, 0.003))

    # Ensure high >= open and low <= open
    high = np.maximum(high, open_)
    low = np.minimum(low, open_)

    volume = rng.integers(1_000_000, 10_000_000, size=n)

    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=dates,
    )


# ---------------------------------------------------------------------------
# S3 / MinIO mock fixtures (moto)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_s3(monkeypatch):
    """Set up moto S3 mock with ``model-artifacts`` and ``drift-logs`` buckets.

    Sets the required environment variables so that
    :class:`~ml.models.storage_backends.S3StorageBackend` and
    :class:`~ml.models.s3_storage.S3Storage` can be constructed
    without real AWS / MinIO credentials.
    """
    import boto3
    from moto import mock_aws

    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("MINIO_ROOT_USER", "testing")
    monkeypatch.setenv("MINIO_ROOT_PASSWORD", "testing")
    monkeypatch.setenv("MINIO_BUCKET_MODELS", "model-artifacts")
    monkeypatch.setenv("MINIO_BUCKET_DRIFT", "drift-logs")
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)

    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="model-artifacts")
        client.create_bucket(Bucket="drift-logs")
        yield


@pytest.fixture
def s3_backend(mock_s3):
    """Return an :class:`S3StorageBackend` connected to the moto mock."""
    from ml.models.storage_backends import S3StorageBackend

    return S3StorageBackend(bucket="model-artifacts")


@pytest.fixture
def s3_registry(mock_s3):
    """Return a :class:`ModelRegistry` using the S3 backend against moto mock."""
    from ml.models.registry import ModelRegistry
    from ml.models.storage_backends import S3StorageBackend

    backend = S3StorageBackend(bucket="model-artifacts")
    return ModelRegistry(backend=backend)
