"""Model registry — persistence and retrieval of trained model artifacts."""

from __future__ import annotations

import logging
import pickle
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sklearn.pipeline import Pipeline

from ml.models.model_configs import TrainingResult
from ml.models.storage_backends import StorageBackend, create_storage_backend

if TYPE_CHECKING:
    from ml.evaluation.ranking import WinnerResult

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Model registry for artifact persistence and retrieval.

    Uses a pluggable :class:`StorageBackend` for I/O.  When no *backend* is
    provided, one is created automatically via :func:`create_storage_backend`
    based on the ``STORAGE_BACKEND`` environment variable (``local`` or ``s3``).

    Storage layout::

        {model_name}_{scaler_variant}/v{version}/
            pipeline.pkl
            metadata.json
            features.json
    """

    def __init__(
        self,
        base_dir: str = "model_registry",
        backend: StorageBackend | None = None,
    ) -> None:
        self._base_dir = base_dir
        if backend is not None:
            self._backend = backend
        else:
            self._backend = create_storage_backend(base_dir=base_dir)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_model(
        self,
        result: TrainingResult,
        pipeline: Pipeline,
        feature_names: list[str],
        rank: int | None = None,
        is_winner: bool = False,
        version: int | None = None,
    ) -> str:
        """Persist a trained pipeline, metadata, and feature list.

        Returns the logical version key (e.g. ``"ridge_standard/v1"``).
        """
        model_key = f"{result.model_name}_{result.scaler_variant}"

        if version is None:
            version = self._next_version(model_key)

        metadata = {
            "model_name": result.model_name,
            "scaler_variant": result.scaler_variant,
            "best_params": result.best_params,
            "oos_metrics": result.oos_metrics,
            "fold_metrics": result.fold_metrics,
            "fold_stability": result.fold_stability,
            "rank": rank,
            "is_winner": is_winner,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "version": version,
        }

        ver_key = f"{model_key}/v{version}"
        self._backend.write_bytes(
            f"{ver_key}/pipeline.pkl", pickle.dumps(pipeline),
        )
        self._backend.write_json(f"{ver_key}/metadata.json", metadata)
        self._backend.write_json(f"{ver_key}/features.json", feature_names)

        logger.info("Saved %s v%d → %s", model_key, version, ver_key)
        return ver_key

    def save_winner(
        self,
        winner_result: WinnerResult,
        pipeline: Pipeline,
        feature_names: list[str],
    ) -> str:
        """Convenience method to save the winning model."""
        return self.save_model(
            result=winner_result.winner.training_result,
            pipeline=pipeline,
            feature_names=feature_names,
            rank=winner_result.winner.rank,
            is_winner=True,
        )

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load_model(
        self,
        model_name: str,
        scaler_variant: str,
        version: int | None = None,
    ) -> dict:
        """Load a model artifact.  Loads latest version when *version* is ``None``.

        Raises ``FileNotFoundError`` if the model or version does not exist.
        """
        model_key = f"{model_name}_{scaler_variant}"

        if version is None:
            version = self._latest_version(model_key)

        ver_key = f"{model_key}/v{version}"

        if not self._backend.exists(f"{ver_key}/metadata.json"):
            raise FileNotFoundError(
                f"Model {model_key} v{version} not found in registry.",
            )

        pipeline = pickle.loads(  # noqa: S301
            self._backend.read_bytes(f"{ver_key}/pipeline.pkl"),
        )
        metadata = self._backend.read_json(f"{ver_key}/metadata.json")
        feature_names = self._backend.read_json(f"{ver_key}/features.json")

        return {
            "pipeline": pipeline,
            "metadata": metadata,
            "feature_names": feature_names,
            "version": version,
            "path": ver_key,
        }

    # ------------------------------------------------------------------
    # List / query
    # ------------------------------------------------------------------

    def list_models(self) -> list[dict]:
        """Return metadata summaries for every model version, sorted by OOS RMSE."""
        entries: list[dict] = []
        all_keys = self._backend.list_keys("")
        meta_keys = [k for k in all_keys if k.endswith("/metadata.json")]

        for mk in meta_keys:
            meta = self._backend.read_json(mk)
            ver_prefix = mk.rsplit("/metadata.json", 1)[0]
            entries.append(
                {
                    "model_name": meta.get("model_name"),
                    "scaler_variant": meta.get("scaler_variant"),
                    "version": meta.get("version"),
                    "is_winner": meta.get("is_winner", False),
                    "oos_rmse": meta.get("oos_metrics", {}).get("rmse"),
                    "path": ver_prefix,
                }
            )

        entries.sort(key=lambda e: e.get("oos_rmse") or float("inf"))
        return entries

    def get_winner(self) -> dict | None:
        """Return the latest model version flagged as winner, or ``None``."""
        winners = [e for e in self.list_models() if e.get("is_winner")]
        if not winners:
            return None
        # Return most recently saved winner (highest version for its model key)
        return winners[-1]

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------

    def activate_model(
        self,
        model_name: str,
        scaler_variant: str,
        version: int,
    ) -> None:
        """Mark a specific model version as active for serving.

        Raises ``FileNotFoundError`` if the model or version does not exist.
        """
        model_key = f"{model_name}_{scaler_variant}"
        meta_key = f"{model_key}/v{version}/metadata.json"

        if not self._backend.exists(meta_key):
            raise FileNotFoundError(
                f"Model {model_key} v{version} not found in registry.",
            )

        metadata = self._backend.read_json(meta_key)
        metadata["is_active"] = True
        self._backend.write_json(meta_key, metadata)
        logger.info("Activated %s v%d.", model_key, version)

    def deactivate_all(self) -> int:
        """Set ``is_active=False`` for all model versions. Returns count deactivated."""
        count = 0
        all_keys = self._backend.list_keys("")
        meta_keys = [k for k in all_keys if k.endswith("/metadata.json")]

        for mk in meta_keys:
            data = self._backend.read_json(mk)
            if data.get("is_active", False):
                data["is_active"] = False
                self._backend.write_json(mk, data)
                count += 1

        logger.info("Deactivated %d model version(s).", count)
        return count

    def get_active_model(self) -> dict | None:
        """Return metadata for the currently active model, or ``None``."""
        all_keys = self._backend.list_keys("")
        meta_keys = sorted(k for k in all_keys if k.endswith("/metadata.json"))

        for mk in meta_keys:
            data = self._backend.read_json(mk)
            if data.get("is_active", False):
                ver_prefix = mk.rsplit("/metadata.json", 1)[0]
                return {
                    "model_name": data.get("model_name"),
                    "scaler_variant": data.get("scaler_variant"),
                    "version": data.get("version"),
                    "is_active": True,
                    "is_winner": data.get("is_winner", False),
                    "oos_rmse": data.get("oos_metrics", {}).get("rmse"),
                    "path": ver_prefix,
                }

        return None

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_model(
        self,
        model_name: str,
        scaler_variant: str,
        version: int | None = None,
    ) -> bool:
        """Delete a specific version or all versions of a model."""
        model_key = f"{model_name}_{scaler_variant}"

        if version is not None:
            prefix = f"{model_key}/v{version}/"
        else:
            prefix = f"{model_key}/"

        keys = self._backend.list_keys(prefix)
        if not keys:
            return False

        for k in keys:
            self._backend.delete(k)
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _next_version(self, model_key: str) -> int:
        """Return the next auto-incremented version number."""
        keys = self._backend.list_keys(f"{model_key}/")
        versions: set[int] = set()
        for k in keys:
            for part in k.split("/"):
                if part.startswith("v") and part[1:].isdigit():
                    versions.add(int(part[1:]))
        return max(versions, default=0) + 1

    def _latest_version(self, model_key: str) -> int:
        """Return the highest existing version number."""
        keys = self._backend.list_keys(f"{model_key}/")
        versions: set[int] = set()
        for k in keys:
            for part in k.split("/"):
                if part.startswith("v") and part[1:].isdigit():
                    versions.add(int(part[1:]))
        if not versions:
            raise FileNotFoundError(f"No versions found for {model_key}.")
        return max(versions)
