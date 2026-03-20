"""Kubeflow pipeline definition — full 11-step training pipeline."""

from __future__ import annotations

import json
import logging
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from ml.pipelines.components.deployer import deploy_winner_model
from ml.pipelines.components.evaluator import (
    evaluate_models,
    generate_comparison_report,
    generate_cv_report,
)
from ml.pipelines.components.feature_engineer import engineer_features
from ml.pipelines.components.label_generator import generate_labels
from ml.pipelines.components.model_trainer import (
    _build_pipeline,
    prepare_training_data,
    train_all_models,
)
from ml.pipelines.components.model_selector import select_and_persist_winner

if TYPE_CHECKING:
    from ml.pipelines.components.data_loader import DBSettings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PIPELINE_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Run result dataclass
# ---------------------------------------------------------------------------


@dataclass
class PipelineRunResult:
    """Full audit trail for a single pipeline execution."""

    run_id: str
    pipeline_version: str
    started_at: str
    completed_at: str = ""
    status: str = "running"
    steps_completed: list[str] = field(default_factory=list)
    n_tickers: int = 0
    n_models_trained: int = 0
    winner_info: dict | None = None
    deploy_info: dict | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _rebuild_pipelines(
    results: list,
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> dict[str, Pipeline]:
    """Reconstruct and refit pipelines from training results."""
    from ml.models.model_configs import (
        BOOSTER_MODELS,
        DISTANCE_NEURAL_MODELS,
        LINEAR_MODELS,
        TREE_MODELS,
        ModelConfig,
    )

    all_configs: dict[str, ModelConfig] = {
        **LINEAR_MODELS,
        **TREE_MODELS,
        **BOOSTER_MODELS,
        **DISTANCE_NEURAL_MODELS,
    }

    pipelines: dict[str, Pipeline] = {}
    for result in results:
        config = all_configs[result.model_name]
        pipeline = _build_pipeline(config, result.scaler_variant)
        if result.best_params:
            pipeline.set_params(
                **{f"model__{k}": v for k, v in result.best_params.items()}
            )
        pipeline.fit(X_train, y_train)
        key = f"{result.model_name}_{result.scaler_variant}"
        pipelines[key] = pipeline

    return pipelines


def _save_run_result(result: PipelineRunResult, registry_dir: str) -> Path:
    """Persist run result as JSON in ``{registry_dir}/runs/``."""
    runs_dir = Path(registry_dir) / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"pipeline_run_{result.run_id}.json"
    with open(path, "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)
    logger.info("Saved run result → %s", path)
    return path


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def run_training_pipeline(
    tickers: list[str] | None = None,
    db_settings: DBSettings | None = None,
    data_dict: dict[str, pd.DataFrame] | None = None,
    registry_dir: str = "model_registry",
    serving_dir: str = "/models/active",
    target_col: str = "target_7d",
    horizon: int = 7,
    test_ratio: float = 0.2,
    n_splits: int = 5,
    skip_shap: bool = False,
) -> PipelineRunResult:
    """Execute the full 11-step training pipeline.

    Accepts either ``tickers`` + ``db_settings`` (production) or ``data_dict``
    (test/pre-loaded).  All 11 steps are executed sequentially with step-level
    tracking and run result persistence.

    Raises ``ValueError`` if neither ``tickers`` nor ``data_dict`` is provided.
    """
    if data_dict is None and tickers is None:
        raise ValueError("Provide either 'tickers' or 'data_dict'.")

    run_id = uuid.uuid4().hex[:12]
    started_at = datetime.now(timezone.utc).isoformat()

    result = PipelineRunResult(
        run_id=run_id,
        pipeline_version=PIPELINE_VERSION,
        started_at=started_at,
    )

    try:
        # Step 1: Load data
        if data_dict is None:
            from ml.pipelines.components.data_loader import load_data

            data_dict = load_data(tickers=tickers, settings=db_settings)
        result.n_tickers = len(data_dict)
        result.steps_completed.append("load_data")
        logger.info("Step 1/11 load_data — %d tickers", result.n_tickers)

        # Step 2: Engineer features
        enriched = engineer_features(data_dict)
        result.steps_completed.append("engineer_features")
        logger.info("Step 2/11 engineer_features — done")

        # Step 3: Generate labels
        labelled, feature_names = generate_labels(enriched, horizon=horizon)
        result.steps_completed.append("generate_labels")
        logger.info("Step 3/11 generate_labels — %d features", len(feature_names))

        # Step 4: Prepare training data
        X_train, y_train, X_test, y_test = prepare_training_data(
            labelled, feature_names, target_col, test_ratio,
        )
        result.steps_completed.append("prepare_training_data")
        logger.info(
            "Step 4/11 prepare_training_data — train=%d test=%d",
            len(X_train), len(X_test),
        )

        # Step 5: Train all models
        results_list = train_all_models(X_train, y_train, X_test, y_test, n_splits)
        pipelines = _rebuild_pipelines(results_list, X_train, y_train)
        result.n_models_trained = len(results_list)
        result.steps_completed.append("train_models")
        logger.info("Step 5/11 train_models — %d models", len(results_list))

        # Step 6: Cross-validation report
        cv_report = generate_cv_report(results_list)
        result.steps_completed.append("cross_validation")
        logger.info("Step 6/11 cross_validation — done")

        # Step 7: Evaluate / rank models
        ranked = evaluate_models(results_list)
        result.steps_completed.append("evaluate_models")
        logger.info("Step 7/11 evaluate_models — %d ranked", len(ranked))

        # Step 8: Comparison report
        comparison = generate_comparison_report(ranked)
        result.steps_completed.append("model_comparison")
        logger.info("Step 8/11 model_comparison — done")

        # Step 9: Explainability (optional)
        if skip_shap:
            logger.info("Step 9/11 explainability — SKIPPED (skip_shap=True)")
        else:
            try:
                from ml.pipelines.components.explainer import explain_top_models

                explain_top_models(
                    results_list, pipelines, X_test, feature_names, registry_dir,
                )
                logger.info("Step 9/11 explainability — done")
            except (ImportError, Exception) as exc:
                logger.warning("Step 9/11 explainability — skipped (%s)", exc)
        result.steps_completed.append("explainability")

        # Step 10: Select and persist winner
        winner_info = select_and_persist_winner(
            results_list, pipelines, feature_names, registry_dir,
        )
        result.winner_info = winner_info
        result.steps_completed.append("select_winner")
        logger.info("Step 10/11 select_winner — %s", winner_info.get("winner_name"))

        # Step 11: Deploy winner
        deploy_info = deploy_winner_model(registry_dir, serving_dir)
        result.deploy_info = deploy_info
        result.steps_completed.append("deploy_model")
        logger.info("Step 11/11 deploy_model — done")

        # Finalise
        result.completed_at = datetime.now(timezone.utc).isoformat()
        result.status = "completed"
        _save_run_result(result, registry_dir)
        logger.info("Pipeline run %s completed successfully.", run_id)

    except Exception:
        result.completed_at = datetime.now(timezone.utc).isoformat()
        result.status = "failed"
        result.error = traceback.format_exc()
        _save_run_result(result, registry_dir)
        raise

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Run the stock prediction training pipeline",
    )
    parser.add_argument("--tickers", type=str, help="Comma-separated ticker list")
    parser.add_argument("--registry-dir", default="model_registry")
    parser.add_argument("--serving-dir", default="/models/active")
    parser.add_argument("--skip-shap", action="store_true")
    args = parser.parse_args()

    tickers = args.tickers.split(",") if args.tickers else None
    run_result = run_training_pipeline(
        tickers=tickers,
        registry_dir=args.registry_dir,
        serving_dir=args.serving_dir,
        skip_shap=args.skip_shap,
    )
    print(json.dumps(run_result.to_dict(), indent=2, default=str))
