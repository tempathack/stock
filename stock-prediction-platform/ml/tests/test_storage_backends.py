"""Tests for ml.models.storage_backends — Local + S3 backends and factory."""

from __future__ import annotations

import os

import pytest

from ml.models.storage_backends import (
    LocalStorageBackend,
    S3StorageBackend,
    create_storage_backend,
)


# ---------------------------------------------------------------------------
# TestLocalStorageBackend
# ---------------------------------------------------------------------------


class TestLocalStorageBackend:
    def test_write_read_bytes(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        backend.write_bytes("test.bin", b"hello")
        assert backend.read_bytes("test.bin") == b"hello"

    def test_write_read_json(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        obj = {"key": "value", "num": 42}
        backend.write_json("data.json", obj)
        assert backend.read_json("data.json") == obj

    def test_read_nonexistent_raises(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        with pytest.raises(FileNotFoundError):
            backend.read_bytes("missing.bin")

    def test_list_keys(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        backend.write_bytes("a/f1.txt", b"1")
        backend.write_bytes("a/f2.txt", b"2")
        backend.write_bytes("a/f3.txt", b"3")
        keys = backend.list_keys("a/")
        assert len(keys) == 3
        assert "a/f1.txt" in keys
        assert "a/f2.txt" in keys
        assert "a/f3.txt" in keys

    def test_list_keys_empty(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        assert backend.list_keys("nonexistent/") == []

    def test_delete_file(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        backend.write_bytes("to_delete.txt", b"data")
        assert backend.delete("to_delete.txt") is True
        assert backend.exists("to_delete.txt") is False

    def test_delete_nonexistent(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        assert backend.delete("nope.txt") is False

    def test_exists_true(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        backend.write_bytes("exist.txt", b"yes")
        assert backend.exists("exist.txt") is True

    def test_exists_false(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        assert backend.exists("nope.txt") is False

    def test_nested_keys(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        backend.write_bytes("a/b/c/deep.txt", b"deep")
        assert backend.read_bytes("a/b/c/deep.txt") == b"deep"

    def test_delete_prunes_empty_parents(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        backend.write_bytes("model/v1/pipeline.pkl", b"pkl")
        backend.delete("model/v1/pipeline.pkl")
        # v1 dir and model dir should be pruned
        assert not (tmp_path / "store" / "model" / "v1").exists()
        assert not (tmp_path / "store" / "model").exists()

    def test_list_keys_all(self, tmp_path):
        backend = LocalStorageBackend(str(tmp_path / "store"))
        backend.write_bytes("m1/v1/meta.json", b"{}")
        backend.write_bytes("m2/v1/meta.json", b"{}")
        keys = backend.list_keys("")
        assert len(keys) == 2


# ---------------------------------------------------------------------------
# TestS3StorageBackend
# ---------------------------------------------------------------------------


class TestS3StorageBackend:
    def test_write_read_bytes(self, s3_backend):
        s3_backend.write_bytes("test.bin", b"hello-s3")
        assert s3_backend.read_bytes("test.bin") == b"hello-s3"

    def test_write_read_json(self, s3_backend):
        obj = {"key": "value", "num": 42}
        s3_backend.write_json("data.json", obj)
        assert s3_backend.read_json("data.json") == obj

    def test_read_nonexistent_raises(self, s3_backend):
        with pytest.raises(FileNotFoundError):
            s3_backend.read_bytes("missing.bin")

    def test_list_keys(self, s3_backend):
        s3_backend.write_bytes("a/f1.txt", b"1")
        s3_backend.write_bytes("a/f2.txt", b"2")
        s3_backend.write_bytes("a/f3.txt", b"3")
        keys = s3_backend.list_keys("a/")
        assert len(keys) == 3
        assert "a/f1.txt" in keys

    def test_list_keys_with_prefix(self, mock_s3):
        backend = S3StorageBackend(
            bucket="model-artifacts", prefix="models",
        )
        backend.write_bytes("inner/file.txt", b"data")
        keys = backend.list_keys("inner/")
        assert keys == ["inner/file.txt"]

    def test_list_keys_empty(self, s3_backend):
        assert s3_backend.list_keys("nonexistent/") == []

    def test_delete_object(self, s3_backend):
        s3_backend.write_bytes("del.txt", b"data")
        assert s3_backend.delete("del.txt") is True
        assert s3_backend.exists("del.txt") is False

    def test_exists_true(self, s3_backend):
        s3_backend.write_bytes("exist.txt", b"yes")
        assert s3_backend.exists("exist.txt") is True

    def test_exists_false(self, s3_backend):
        assert s3_backend.exists("nope.txt") is False

    def test_prefix_isolation(self, mock_s3):
        backend_a = S3StorageBackend(
            bucket="model-artifacts", prefix="ns-a",
        )
        backend_b = S3StorageBackend(
            bucket="model-artifacts", prefix="ns-b",
        )
        backend_a.write_bytes("file.txt", b"a-data")
        backend_b.write_bytes("file.txt", b"b-data")
        assert backend_a.read_bytes("file.txt") == b"a-data"
        assert backend_b.read_bytes("file.txt") == b"b-data"


# ---------------------------------------------------------------------------
# TestCreateStorageBackend
# ---------------------------------------------------------------------------


class TestCreateStorageBackend:
    def test_default_is_local(self, monkeypatch):
        monkeypatch.delenv("STORAGE_BACKEND", raising=False)
        backend = create_storage_backend()
        assert isinstance(backend, LocalStorageBackend)

    def test_env_var_local(self, monkeypatch):
        monkeypatch.setenv("STORAGE_BACKEND", "local")
        backend = create_storage_backend()
        assert isinstance(backend, LocalStorageBackend)

    def test_env_var_s3(self, mock_s3):
        # mock_s3 sets STORAGE_BACKEND=s3 and provides moto mock
        backend = create_storage_backend()
        assert isinstance(backend, S3StorageBackend)

    def test_explicit_override(self, monkeypatch):
        monkeypatch.setenv("STORAGE_BACKEND", "s3")
        backend = create_storage_backend("local")
        assert isinstance(backend, LocalStorageBackend)

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="redis"):
            create_storage_backend("redis")
