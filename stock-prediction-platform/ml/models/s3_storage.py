"""S3-compatible storage client for MinIO integration."""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Storage:
    """Thin wrapper around boto3 S3 client for MinIO-compatible object storage.

    All methods target a single endpoint and handle common error patterns
    (missing keys, prefix listing, byte-level I/O).
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
    ) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        self._endpoint = endpoint_url

    @classmethod
    def from_env(cls) -> S3Storage:
        """Create an S3Storage instance from environment variables.

        Reads: MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_REGION.
        """
        return cls(
            endpoint_url=os.environ.get(
                "MINIO_ENDPOINT", "http://minio.storage.svc.cluster.local:9000",
            ),
            access_key=os.environ["MINIO_ROOT_USER"],
            secret_key=os.environ["MINIO_ROOT_PASSWORD"],
            region=os.environ.get("MINIO_REGION", "us-east-1"),
        )

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_file(self, local_path: str | Path, bucket: str, key: str) -> None:
        """Upload a local file to S3."""
        self._client.upload_file(str(local_path), bucket, key)
        logger.debug("Uploaded %s → s3://%s/%s", local_path, bucket, key)

    def upload_bytes(self, data: bytes, bucket: str, key: str) -> None:
        """Upload raw bytes to S3."""
        self._client.put_object(Bucket=bucket, Key=key, Body=data)
        logger.debug("Uploaded %d bytes → s3://%s/%s", len(data), bucket, key)

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download_file(self, bucket: str, key: str, local_path: str | Path) -> None:
        """Download an S3 object to a local file."""
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self._client.download_file(bucket, key, str(local_path))
        logger.debug("Downloaded s3://%s/%s → %s", bucket, key, local_path)

    def download_bytes(self, bucket: str, key: str) -> bytes:
        """Download an S3 object and return its contents as bytes."""
        resp = self._client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """List all object keys under *prefix* in *bucket*."""
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys

    def object_exists(self, bucket: str, key: str) -> bool:
        """Check whether an object exists in S3."""
        try:
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_object(self, bucket: str, key: str) -> None:
        """Delete a single object from S3."""
        self._client.delete_object(Bucket=bucket, Key=key)
        logger.debug("Deleted s3://%s/%s", bucket, key)

    def delete_prefix(self, bucket: str, prefix: str) -> int:
        """Delete all objects under *prefix*. Returns count deleted."""
        keys = self.list_objects(bucket, prefix)
        if not keys:
            return 0
        # S3 delete_objects accepts max 1000 keys per call
        deleted = 0
        for i in range(0, len(keys), 1000):
            batch = keys[i : i + 1000]
            self._client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": k} for k in batch]},
            )
            deleted += len(batch)
        logger.debug("Deleted %d objects under s3://%s/%s", deleted, bucket, prefix)
        return deleted

    # ------------------------------------------------------------------
    # Copy (S3 → S3)
    # ------------------------------------------------------------------

    def copy_object(self, bucket: str, src_key: str, dst_key: str) -> None:
        """Copy an object within the same bucket."""
        self._client.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": src_key},
            Key=dst_key,
        )
        logger.debug("Copied s3://%s/%s → s3://%s/%s", bucket, src_key, bucket, dst_key)

    def copy_prefix(
        self, bucket: str, src_prefix: str, dst_prefix: str,
    ) -> int:
        """Copy all objects under *src_prefix* to *dst_prefix*. Returns count."""
        keys = self.list_objects(bucket, src_prefix)
        for key in keys:
            relative = key[len(src_prefix):]
            self.copy_object(bucket, key, dst_prefix + relative)
        return len(keys)
