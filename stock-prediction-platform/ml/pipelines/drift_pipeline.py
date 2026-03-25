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

    Requires the ``kfp`` SDK to be installed (presence is checked).  The
    compiled YAML is a minimal pipeline spec stub — full Parquet I/O component
    wiring is deferred to Phase 21+ once cluster deployment is validated.

    Raises ``ImportError`` with install instructions if kfp is not available.
    """
    try:
        import kfp  # noqa: F401 — presence check
    except ImportError as exc:
        raise ImportError(
            "KFP SDK is required for pipeline compilation. "
            "Install with: pip install kfp>=2.0"
        ) from exc

    # KFP v2 lightweight component source inspection requires the component
    # function to exist in a real importable module (not an inline closure).
    # For this stub we write the canonical v2 IR spec directly instead of
    # using the @dsl.component decorator, which avoids the inspect.getsource
    # limitation for dynamically-defined functions.
    import yaml  # stdlib-backed; PyYAML is a kfp transitive dep

    pipeline_spec = {
        "components": {
            "comp-pipeline-entrypoint": {
                "executorLabel": "exec-pipeline-entrypoint",
                "inputDefinitions": {
                    "parameters": {
                        "registry_dir": {"parameterType": "STRING"},
                        "serving_dir": {"parameterType": "STRING"},
                        "tickers": {"parameterType": "STRING"},
                    },
                },
            },
        },
        "deploymentSpec": {
            "executors": {
                "exec-pipeline-entrypoint": {
                    "container": {
                        "args": [
                            "--executor_input",
                            "{{$}}",
                            "--function_to_execute",
                            "pipeline_entrypoint",
                        ],
                        "command": [
                            "sh",
                            "-c",
                            (
                                "\nif ! [ -x \"$(command -v pip)\" ]; then\n"
                                "    python3 -m ensurepip || python3 -m ensurepip "
                                "--upgrade || apt-get install python3-pip\nfi\n\n"
                                "pip3 install kfp==2.0.0 --quiet --no-warn-script-location "
                                "&& \"$0\" \"$@\"\n"
                            ),
                            "sh",
                            "-ec",
                            "program_path=$(mktemp -d)\npython3 -m kfp.dsl.executor_main",
                        ],
                        "image": "python:3.11",
                    },
                },
            },
        },
        "pipelineInfo": {
            "description": "End-to-end stock prediction model training pipeline (stub)",
            "displayName": "stock-training-pipeline",
            "name": "stock-training-pipeline",
        },
        "root": {
            "dag": {
                "tasks": {
                    "pipeline-entrypoint": {
                        "cachingOptions": {"enableCache": True},
                        "componentRef": {"name": "comp-pipeline-entrypoint"},
                        "inputs": {
                            "parameters": {
                                "registry_dir": {
                                    "componentInputParameter": "registry_dir",
                                },
                                "serving_dir": {
                                    "componentInputParameter": "serving_dir",
                                },
                                "tickers": {
                                    "componentInputParameter": "tickers",
                                },
                            },
                        },
                        "taskInfo": {"name": "pipeline-entrypoint"},
                    },
                },
            },
            "inputDefinitions": {
                "parameters": {
                    "registry_dir": {
                        "defaultValue": "model_registry",
                        "isOptional": True,
                        "parameterType": "STRING",
                    },
                    "serving_dir": {
                        "defaultValue": "/models/active",
                        "isOptional": True,
                        "parameterType": "STRING",
                    },
                    "tickers": {
                        "defaultValue": "AAPL,MSFT,GOOGL",
                        "isOptional": True,
                        "parameterType": "STRING",
                    },
                },
            },
        },
        "schemaVersion": "2.1.0",
        "sdkVersion": f"kfp-{kfp.__version__}",
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        yaml.dump(pipeline_spec, fh, default_flow_style=False, allow_unicode=True)

    logger.info("Compiled KFP pipeline → %s", out)
    return str(out)


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
