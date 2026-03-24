"""Pluggable storage backends for model artifact persistence.

Provides a :class:`StorageBackend` protocol and two concrete implementations:

* :class:`LocalStorageBackend` — file-system based (default for local dev).
* :class:`S3StorageBackend` — S3-compatible (MinIO) object storage.

Use :func:`create_storage_backend` to instantiate the correct backend based on
the ``STORAGE_BACKEND`` environment variable (``local`` or ``s3``).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class StorageBackend(Protocol):
    """Protocol defining the interface for model artifact storage."""

    def write_bytes(self, key: str, data: bytes) -> None: ...
    def read_bytes(self, key: str) -> bytes: ...
    def write_json(self, key: str, obj: Any) -> None: ...
    def read_json(self, key: str) -> Any: ...
    def list_keys(self, prefix: str) -> list[str]: ...
    def delete(self, key: str) -> bool: ...
    def exists(self, key: str) -> bool: ...


# ---------------------------------------------------------------------------
# Local filesystem backend
# ---------------------------------------------------------------------------


class LocalStorageBackend:
    """File-system based storage backend."""

    def __init__(self, base_dir: str) -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def write_bytes(self, key: str, data: bytes) -> None:
        path = self._base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def read_bytes(self, key: str) -> bytes:
        path = self._base / key
        if not path.exists():
            raise FileNotFoundError(f"Key not found: {key}")
        return path.read_bytes()

    def write_json(self, key: str, obj: Any) -> None:
        self.write_bytes(key, json.dumps(obj, indent=2, default=str).encode())

    def read_json(self, key: str) -> Any:
        return json.loads(self.read_bytes(key).decode())

    def list_keys(self, prefix: str) -> list[str]:
        search_dir = self._base / prefix if prefix else self._base
        if not search_dir.exists():
            return []
        return sorted(
            str(p.relative_to(self._base)).replace("\\", "/")
            for p in search_dir.rglob("*")
            if p.is_file()
        )

    def delete(self, key: str) -> bool:
        path = self._base / key
        if path.is_file():
            path.unlink()
            # Prune empty parent directories up to base_dir
            parent = path.parent
            while parent != self._base:
                if not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
                else:
                    break
            return True
        if path.is_dir():
            shutil.rmtree(path)
            return True
        return False

    def exists(self, key: str) -> bool:
        return (self._base / key).exists()


# ---------------------------------------------------------------------------
# S3-compatible (MinIO) backend
# ---------------------------------------------------------------------------


class S3StorageBackend:
    """S3-compatible (MinIO) object storage backend."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        endpoint_url: str | None = None,
        region_name: str = "us-east-1",
    ) -> None:
        import boto3

        self._bucket = bucket
        self._prefix = prefix.strip("/") if prefix else ""

        resolved_endpoint = endpoint_url or os.environ.get("MINIO_ENDPOINT")
        access_key = os.environ.get("MINIO_ROOT_USER") or os.environ.get(
            "AWS_ACCESS_KEY_ID",
        )
        secret_key = os.environ.get("MINIO_ROOT_PASSWORD") or os.environ.get(
            "AWS_SECRET_ACCESS_KEY",
        )

        client_kwargs: dict[str, Any] = {"region_name": region_name}
        if resolved_endpoint:
            client_kwargs["endpoint_url"] = resolved_endpoint
        if access_key:
            client_kwargs["aws_access_key_id"] = access_key
        if secret_key:
            client_kwargs["aws_secret_access_key"] = secret_key

        self._client = boto3.client("s3", **client_kwargs)

    def _full_key(self, key: str) -> str:
        """Prepend the backend prefix to *key*."""
        key = key.strip("/")
        if self._prefix:
            return f"{self._prefix}/{key}"
        return key

    def write_bytes(self, key: str, data: bytes) -> None:
        self._client.put_object(
            Bucket=self._bucket, Key=self._full_key(key), Body=data,
        )

    def read_bytes(self, key: str) -> bytes:
        from botocore.exceptions import ClientError

        try:
            resp = self._client.get_object(
                Bucket=self._bucket, Key=self._full_key(key),
            )
            return resp["Body"].read()
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"Key not found: {key}") from exc
            raise

    def write_json(self, key: str, obj: Any) -> None:
        self.write_bytes(key, json.dumps(obj, indent=2, default=str).encode())

    def read_json(self, key: str) -> Any:
        return json.loads(self.read_bytes(key).decode())

    def list_keys(self, prefix: str) -> list[str]:
        if prefix:
            clean = prefix.lstrip("/")
            full_prefix = f"{self._prefix}/{clean}" if self._prefix else clean
        elif self._prefix:
            full_prefix = f"{self._prefix}/"
        else:
            full_prefix = ""

        strip_len = len(self._prefix) + 1 if self._prefix else 0
        paginator = self._client.get_paginator("list_objects_v2")
        keys: list[str] = []
        for page in paginator.paginate(Bucket=self._bucket, Prefix=full_prefix):
            for obj in page.get("Contents", []):
                raw_key = obj["Key"]
                keys.append(raw_key[strip_len:] if strip_len else raw_key)
        return sorted(keys)

    def delete(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.delete_object(
                Bucket=self._bucket, Key=self._full_key(key),
            )
            return True
        except ClientError:
            return False

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(
                Bucket=self._bucket, Key=self._full_key(key),
            )
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_storage_backend(
    backend_type: str | None = None, **kwargs: Any,
) -> StorageBackend:
    """Create a storage backend instance.

    Parameters
    ----------
    backend_type:
        ``"local"`` or ``"s3"``.  Falls back to the ``STORAGE_BACKEND``
        environment variable, then ``"local"``.
    **kwargs:
        Forwarded to the backend constructor.  Recognised keys:

        * *local*: ``base_dir`` (default ``"model_registry"``).
        * *s3*: ``bucket``, ``prefix``, ``endpoint_url``, ``region_name``.
    """
    if backend_type is None:
        backend_type = os.environ.get("STORAGE_BACKEND", "local").lower()

    if backend_type == "local":
        return LocalStorageBackend(
            base_dir=kwargs.get("base_dir", "model_registry"),
        )

    if backend_type == "s3":
        return S3StorageBackend(
            bucket=kwargs.get(
                "bucket",
                os.environ.get("MINIO_BUCKET_MODELS", "model-artifacts"),
            ),
            prefix=kwargs.get("prefix", kwargs.get("base_dir", "")),
            endpoint_url=kwargs.get("endpoint_url"),
            region_name=kwargs.get("region_name", "us-east-1"),
        )

    raise ValueError(f"Unknown storage backend type: {backend_type!r}")
