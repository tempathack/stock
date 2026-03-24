"""Model registry and configuration."""

from __future__ import annotations

from ml.models.ensemble import StackingEnsemble
from ml.models.model_configs import (
    BOOSTER_MODELS,
    DISTANCE_NEURAL_MODELS,
    LINEAR_MODELS,
    TREE_MODELS,
    ModelConfig,
    TrainingResult,
    get_all_model_configs,
    get_model_configs,
    register_model_family,
)
from ml.models.registry import ModelRegistry
from ml.models.storage_backends import (
    LocalStorageBackend,
    S3StorageBackend,
    StorageBackend,
    create_storage_backend,
)

__all__ = [
    "BOOSTER_MODELS",
    "DISTANCE_NEURAL_MODELS",
    "LINEAR_MODELS",
    "LocalStorageBackend",
    "ModelConfig",
    "ModelRegistry",
    "S3StorageBackend",
    "StackingEnsemble",
    "StorageBackend",
    "TREE_MODELS",
    "TrainingResult",
    "create_storage_backend",
    "get_all_model_configs",
    "get_model_configs",
    "register_model_family",
]
