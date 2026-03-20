"""Kubeflow pipeline component definitions."""

from __future__ import annotations

try:
    from ml.pipelines.components.data_loader import DBSettings, load_data, load_ticker_data
except ImportError:  # psycopg2 not installed — DB components unavailable
    pass
from ml.pipelines.components.deployer import deploy_winner_model
from ml.pipelines.components.evaluator import (
    evaluate_models,
    generate_comparison_report,
    generate_cv_report,
)
from ml.pipelines.components.explainer import explain_top_models
from ml.pipelines.components.feature_engineer import engineer_features
from ml.pipelines.components.label_generator import generate_labels
from ml.pipelines.components.model_selector import select_and_persist_winner
from ml.pipelines.components.model_trainer import (
    prepare_training_data,
    train_all_models_pipeline,
)
from ml.pipelines.components.predictor import generate_predictions, save_predictions

__all__ = [
    "DBSettings",
    "load_data",
    "load_ticker_data",
    "deploy_winner_model",
    "engineer_features",
    "generate_labels",
    "evaluate_models",
    "generate_comparison_report",
    "generate_cv_report",
    "explain_top_models",
    "generate_predictions",
    "prepare_training_data",
    "save_predictions",
    "select_and_persist_winner",
    "train_all_models_pipeline",
]
