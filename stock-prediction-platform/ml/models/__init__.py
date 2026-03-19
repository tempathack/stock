"""Model registry and configuration."""

from __future__ import annotations

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

__all__ = [
    "BOOSTER_MODELS",
    "DISTANCE_NEURAL_MODELS",
    "LINEAR_MODELS",
    "TREE_MODELS",
    "ModelConfig",
    "TrainingResult",
    "get_all_model_configs",
    "get_model_configs",
    "register_model_family",
]
