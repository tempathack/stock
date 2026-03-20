"""Kubeflow pipeline definitions."""

from __future__ import annotations

from ml.pipelines.drift_pipeline import trigger_retraining
from ml.pipelines.serialization import load_dataframes, save_dataframes
from ml.pipelines.training_pipeline import (
    PIPELINE_VERSION,
    PipelineRunResult,
    run_training_pipeline,
)

__all__ = [
    "PIPELINE_VERSION",
    "PipelineRunResult",
    "load_dataframes",
    "run_training_pipeline",
    "save_dataframes",
    "trigger_retraining",
]
