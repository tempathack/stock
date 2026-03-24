"""Drift-triggered retraining pipeline definition."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from ml.pipelines.training_pipeline import (
    PIPELINE_VERSION,
    PipelineRunResult,
    run_training_pipeline,
)

if TYPE_CHECKING:
    from ml.pipelines.components.data_loader import DBSettings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Retraining trigger
# ---------------------------------------------------------------------------


def trigger_retraining(
    tickers: list[str] | None = None,
    db_settings: DBSettings | None = None,
    data_dict: dict[str, pd.DataFrame] | None = None,
    registry_dir: str = "model_registry",
    serving_dir: str = "/models/active",
    reason: str = "manual",
    skip_shap: bool = False,
) -> PipelineRunResult:
    """Trigger a full training pipeline run.

    This is the entry point for both manual and drift-triggered retraining.
    Phase 22 will wire drift detection output to this function.

    Parameters
    ----------
    reason:
        Why the pipeline was triggered. One of: ``"manual"``, ``"data_drift"``,
        ``"prediction_drift"``, ``"concept_drift"``, ``"scheduled"``.
    """
    logger.info("Triggering retraining — reason: %s", reason)

    result = run_training_pipeline(
        tickers=tickers,
        db_settings=db_settings,
        data_dict=data_dict,
        registry_dir=registry_dir,
        serving_dir=serving_dir,
        skip_shap=skip_shap,
    )

    _append_retraining_log(result, reason, registry_dir)

    logger.info(
        "Retraining %s — run_id=%s, reason=%s",
        result.status,
        result.run_id,
        reason,
    )
    return result


# ---------------------------------------------------------------------------
# Retraining log
# ---------------------------------------------------------------------------


def _append_retraining_log(
    result: PipelineRunResult,
    reason: str,
    registry_dir: str,
) -> None:
    """Append a JSON record to ``{registry_dir}/runs/retraining_log.jsonl``.

    Uses S3 when ``STORAGE_BACKEND=s3``, otherwise local filesystem.
    """
    winner_name = None
    if result.winner_info:
        winner_name = result.winner_info.get("winner_name")

    record = {
        "run_id": result.run_id,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": result.status,
        "pipeline_version": result.pipeline_version,
        "winner": winner_name,
    }
    line = json.dumps(record) + "\n"

    if os.environ.get("STORAGE_BACKEND", "local").lower() == "s3":
        from ml.models.s3_storage import S3Storage

        s3 = S3Storage.from_env()
        bucket = os.environ.get("MINIO_BUCKET_MODELS", "model-artifacts")
        key = f"{registry_dir}/runs/retraining_log.jsonl"

        existing = b""
        if s3.object_exists(bucket, key):
            existing = s3.download_bytes(bucket, key)
        s3.upload_bytes(existing + line.encode(), bucket, key)
        logger.info("Appended retraining log entry → s3://%s/%s", bucket, key)
        return

    runs_dir = Path(registry_dir) / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    log_path = runs_dir / "retraining_log.jsonl"

    with open(log_path, "a") as f:
        f.write(line)

    logger.info("Appended retraining log entry → %s", log_path)


# ---------------------------------------------------------------------------
# KFP compilation (gated on kfp availability)
# ---------------------------------------------------------------------------


def compile_kfp_pipeline(output_path: str = "training_pipeline.yaml") -> str:
    """Compile the training pipeline as a KFP v2 YAML.

    Requires the ``kfp`` SDK to be installed. Raises ``ImportError`` with
    install instructions if not available.
    """
    try:
        import kfp
        from kfp import dsl
        from kfp.compiler import Compiler
    except ImportError as exc:
        raise ImportError(
            "KFP SDK is required for pipeline compilation. "
            "Install with: pip install kfp>=2.0"
        ) from exc

    @dsl.pipeline(
        name="stock-training-pipeline",
        description="End-to-end stock prediction model training pipeline",
    )
    def stock_training_pipeline(
        tickers: str = "AAPL,MSFT,GOOGL",
        registry_dir: str = "model_registry",
        serving_dir: str = "/models/active",
        skip_shap: bool = True,
    ):
        """KFP v2 pipeline wrapper — each step is a lightweight component."""
        pass  # Full KFP component wiring deferred to Phase 21+

    Compiler().compile(
        pipeline_func=stock_training_pipeline,
        package_path=output_path,
    )
    logger.info("Compiled KFP pipeline → %s", output_path)
    return output_path


def submit_pipeline_run(
    pipeline_package_path: str,
    host: str = "http://ml-pipeline.ml.svc.cluster.local:8888",
    experiment_name: str = "stock-prediction",
    run_name: str | None = None,
) -> str:
    """Submit a compiled KFP pipeline to the Kubeflow Pipelines API.

    Requires ``kfp`` SDK and a running KFP deployment.
    """
    try:
        import kfp
    except ImportError as exc:
        raise ImportError(
            "KFP SDK is required for pipeline submission. "
            "Install with: pip install kfp>=2.0"
        ) from exc

    client = kfp.Client(host=host)
    experiment = client.create_experiment(name=experiment_name)

    if run_name is None:
        run_name = f"training-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    run = client.run_pipeline(
        experiment_id=experiment.experiment_id,
        job_name=run_name,
        pipeline_package_path=pipeline_package_path,
    )
    logger.info("Submitted pipeline run %s to %s", run.run_id, host)
    return run.run_id


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Trigger stock prediction retraining",
    )
    parser.add_argument("--tickers", type=str, help="Comma-separated ticker list")
    parser.add_argument(
        "--reason",
        default="manual",
        choices=["manual", "data_drift", "prediction_drift", "concept_drift", "scheduled"],
    )
    parser.add_argument("--registry-dir", default="model_registry")
    parser.add_argument("--serving-dir", default="/models/active")
    parser.add_argument("--compile-only", action="store_true", help="Compile KFP pipeline YAML only")
    parser.add_argument("--skip-shap", action="store_true")
    args = parser.parse_args()

    if args.compile_only:
        path = compile_kfp_pipeline()
        print(f"Compiled pipeline to {path}")
    else:
        tickers_list = args.tickers.split(",") if args.tickers else None
        run_result = trigger_retraining(
            tickers=tickers_list,
            reason=args.reason,
            registry_dir=args.registry_dir,
            serving_dir=args.serving_dir,
            skip_shap=args.skip_shap,
        )
        print(json.dumps(run_result.to_dict(), indent=2, default=str))
