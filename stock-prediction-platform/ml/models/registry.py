"""Model registry — persistence and retrieval of trained model artifacts."""

from __future__ import annotations

import json
import logging
import pickle
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from sklearn.pipeline import Pipeline

from ml.models.model_configs import TrainingResult

if TYPE_CHECKING:
    from ml.evaluation.ranking import WinnerResult

logger = logging.getLogger(__name__)


class ModelRegistry:
    """File-based model registry for artifact persistence and retrieval.

    Storage layout::

        {base_dir}/{model_name}_{scaler_variant}/v{version}/
            pipeline.pkl
            metadata.json
            features.json
    """

    def __init__(self, base_dir: str = "model_registry") -> None:
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

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

        Returns the path to the version directory.
        """
        model_key = f"{result.model_name}_{result.scaler_variant}"
        model_dir = self._base / model_key

        if version is None:
            version = self._next_version(model_dir)

        ver_dir = model_dir / f"v{version}"
        ver_dir.mkdir(parents=True, exist_ok=True)

        # pipeline
        with open(ver_dir / "pipeline.pkl", "wb") as f:
            pickle.dump(pipeline, f)

        # metadata
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
        with open(ver_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        # features
        with open(ver_dir / "features.json", "w") as f:
            json.dump(feature_names, f, indent=2)

        logger.info("Saved %s v%d → %s", model_key, version, ver_dir)
        return str(ver_dir)

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
        model_dir = self._base / model_key

        if not model_dir.exists():
            raise FileNotFoundError(f"Model {model_key} not found in registry.")

        if version is None:
            version = self._latest_version(model_dir)

        ver_dir = model_dir / f"v{version}"
        if not ver_dir.exists():
            raise FileNotFoundError(f"Version v{version} not found for {model_key}.")

        with open(ver_dir / "pipeline.pkl", "rb") as f:
            pipeline = pickle.load(f)  # noqa: S301

        with open(ver_dir / "metadata.json") as f:
            metadata = json.load(f)

        with open(ver_dir / "features.json") as f:
            feature_names = json.load(f)

        return {
            "pipeline": pipeline,
            "metadata": metadata,
            "feature_names": feature_names,
            "version": version,
            "path": str(ver_dir),
        }

    # ------------------------------------------------------------------
    # List / query
    # ------------------------------------------------------------------

    def list_models(self) -> list[dict]:
        """Return metadata summaries for every model version, sorted by OOS RMSE."""
        entries: list[dict] = []
        if not self._base.exists():
            return entries

        for model_dir in sorted(self._base.iterdir()):
            if not model_dir.is_dir():
                continue
            for ver_dir in sorted(model_dir.iterdir()):
                meta_path = ver_dir / "metadata.json"
                if not meta_path.exists():
                    continue
                with open(meta_path) as f:
                    meta = json.load(f)
                entries.append(
                    {
                        "model_name": meta.get("model_name"),
                        "scaler_variant": meta.get("scaler_variant"),
                        "version": meta.get("version"),
                        "is_winner": meta.get("is_winner", False),
                        "oos_rmse": meta.get("oos_metrics", {}).get("rmse"),
                        "path": str(ver_dir),
                    }
                )

        entries.sort(key=lambda e: e.get("oos_rmse") or float("inf"))
        return entries

    def get_winner(self) -> dict | None:
        """Return the latest model version flagged as winner, or ``None``."""
        winners: list[dict] = []
        for entry in self.list_models():
            if entry.get("is_winner"):
                winners.append(entry)
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
        ver_dir = self._base / model_key / f"v{version}"
        meta_path = ver_dir / "metadata.json"

        if not meta_path.exists():
            raise FileNotFoundError(
                f"Model {model_key} v{version} not found in registry."
            )

        with open(meta_path) as f:
            metadata = json.load(f)

        metadata["is_active"] = True

        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        logger.info("Activated %s v%d.", model_key, version)

    def deactivate_all(self) -> int:
        """Set ``is_active=False`` for all model versions. Returns count deactivated."""
        count = 0
        if not self._base.exists():
            return count

        for model_dir in self._base.iterdir():
            if not model_dir.is_dir():
                continue
            for ver_dir in model_dir.iterdir():
                meta_path = ver_dir / "metadata.json"
                if not meta_path.exists():
                    continue
                with open(meta_path) as f:
                    metadata = json.load(f)
                if metadata.get("is_active", False):
                    metadata["is_active"] = False
                    with open(meta_path, "w") as f:
                        json.dump(metadata, f, indent=2, default=str)
                    count += 1

        logger.info("Deactivated %d model version(s).", count)
        return count

    def get_active_model(self) -> dict | None:
        """Return metadata for the currently active model, or ``None``."""
        if not self._base.exists():
            return None

        for model_dir in sorted(self._base.iterdir()):
            if not model_dir.is_dir():
                continue
            for ver_dir in sorted(model_dir.iterdir()):
                meta_path = ver_dir / "metadata.json"
                if not meta_path.exists():
                    continue
                with open(meta_path) as f:
                    metadata = json.load(f)
                if metadata.get("is_active", False):
                    return {
                        "model_name": metadata.get("model_name"),
                        "scaler_variant": metadata.get("scaler_variant"),
                        "version": metadata.get("version"),
                        "is_active": True,
                        "is_winner": metadata.get("is_winner", False),
                        "oos_rmse": metadata.get("oos_metrics", {}).get("rmse"),
                        "path": str(ver_dir),
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
        model_dir = self._base / model_key

        if not model_dir.exists():
            return False

        if version is not None:
            ver_dir = model_dir / f"v{version}"
            if not ver_dir.exists():
                return False
            shutil.rmtree(ver_dir)
            # Clean up empty parent
            if not any(model_dir.iterdir()):
                model_dir.rmdir()
            return True

        shutil.rmtree(model_dir)
        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _next_version(model_dir: Path) -> int:
        """Return the next auto-incremented version number."""
        if not model_dir.exists():
            return 1
        existing = [
            int(d.name[1:])
            for d in model_dir.iterdir()
            if d.is_dir() and d.name.startswith("v") and d.name[1:].isdigit()
        ]
        return max(existing, default=0) + 1

    @staticmethod
    def _latest_version(model_dir: Path) -> int:
        """Return the highest existing version number."""
        existing = [
            int(d.name[1:])
            for d in model_dir.iterdir()
            if d.is_dir() and d.name.startswith("v") and d.name[1:].isdigit()
        ]
        if not existing:
            raise FileNotFoundError(f"No versions found in {model_dir}")
        return max(existing)
