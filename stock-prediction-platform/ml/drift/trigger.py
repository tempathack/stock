"""Drift trigger — event logging and bridge to retraining pipeline."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ml.drift.detector import DriftResult
from ml.drift.monitor import DriftCheckResult, DriftMonitor

logger = logging.getLogger(__name__)


def _get_storage_backend() -> str:
    return os.environ.get("STORAGE_BACKEND", "local").lower()


# ---------------------------------------------------------------------------
# DriftLogger
# ---------------------------------------------------------------------------


class DriftLogger:
    """Persist drift events to file (and optionally to database).

    Supports local filesystem and S3 (MinIO) backends via ``STORAGE_BACKEND``.
    """

    def __init__(self, log_dir: str = "drift_logs") -> None:
        self._log_dir_name = log_dir
        self._backend = _get_storage_backend()

        if self._backend == "s3":
            from ml.models.s3_storage import S3Storage

            self._s3 = S3Storage.from_env()
            self._bucket = os.environ.get("MINIO_BUCKET_DRIFT", "drift-logs")
            self._s3_key = f"{log_dir}/drift_events.jsonl"
        else:
            self._s3 = None  # type: ignore[assignment]
            self._bucket = ""
            self._s3_key = ""
            self._log_dir = Path(log_dir)
            self._log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def log_file(self) -> Path | str:
        if self._backend == "s3":
            return f"s3://{self._bucket}/{self._s3_key}"
        return self._log_dir / "drift_events.jsonl"

    def log_event(self, result: DriftResult) -> None:
        """Append a single drift event to the JSONL log file."""
        record = {
            "drift_type": result.drift_type,
            "is_drifted": result.is_drifted,
            "severity": result.severity,
            "details": result.details,
            "timestamp": result.timestamp,
            "features_affected": result.features_affected,
        }
        self._log_to_file(record)
        logger.info(
            "Logged drift event: type=%s drifted=%s severity=%s",
            result.drift_type, result.is_drifted, result.severity,
        )

    def log_check(self, check_result: DriftCheckResult) -> None:
        """Log events for all drifted detectors in a check result."""
        for result in (
            check_result.data_drift,
            check_result.prediction_drift,
            check_result.concept_drift,
        ):
            if result.is_drifted:
                self.log_event(result)

    def get_recent_events(self, n: int = 50) -> list[dict]:
        """Return the last *n* drift events from the log file."""
        if self._backend == "s3":
            if not self._s3.object_exists(self._bucket, self._s3_key):
                return []
            data = self._s3.download_bytes(self._bucket, self._s3_key)
            lines = data.decode().strip().splitlines()
            events = [json.loads(line) for line in lines]
            return events[-n:]

        if not self.log_file.exists():
            return []
        with open(self.log_file) as f:
            lines = f.readlines()
        events = [json.loads(line) for line in lines]
        return events[-n:]

    def _log_to_file(self, record: dict) -> None:
        line = json.dumps(record, default=str) + "\n"

        if self._backend == "s3":
            # Download existing, append, reupload (atomic for single-writer)
            existing = b""
            if self._s3.object_exists(self._bucket, self._s3_key):
                existing = self._s3.download_bytes(self._bucket, self._s3_key)
            self._s3.upload_bytes(
                existing + line.encode(), self._bucket, self._s3_key,
            )
            return

        with open(self.log_file, "a") as f:
            f.write(line)


# ---------------------------------------------------------------------------
# evaluate_and_trigger
# ---------------------------------------------------------------------------


def evaluate_and_trigger(
    reference_features: pd.DataFrame,
    current_features: pd.DataFrame,
    baseline_errors: np.ndarray,
    recent_errors: np.ndarray,
    historical_rmse: float,
    recent_rmse: float,
    tickers: list[str] | None = None,
    data_dict: dict[str, pd.DataFrame] | None = None,
    registry_dir: str = "model_registry",
    serving_dir: str = "/models/active",
    log_dir: str = "drift_logs",
    auto_retrain: bool = True,
    regenerate_predictions: bool = True,
    skip_shap: bool = False,
) -> DriftCheckResult:
    """Run drift check, log events, and optionally trigger retraining.

    Parameters
    ----------
    auto_retrain:
        If True and drift is detected, triggers ``trigger_retraining()``
        from the drift pipeline.
    regenerate_predictions:
        If True and retraining succeeds, regenerate predictions for all tickers.
    """
    monitor = DriftMonitor()
    check_result = monitor.check(
        reference_features=reference_features,
        current_features=current_features,
        baseline_errors=baseline_errors,
        recent_errors=recent_errors,
        historical_rmse=historical_rmse,
        recent_rmse=recent_rmse,
    )

    drift_logger = DriftLogger(log_dir=log_dir)
    drift_logger.log_check(check_result)

    if check_result.any_drift and auto_retrain:
        reason = _determine_reason(check_result)
        logger.info("Drift detected — triggering retraining (reason=%s)", reason)

        from ml.pipelines.drift_pipeline import trigger_retraining

        result = trigger_retraining(
            tickers=tickers,
            data_dict=data_dict,
            registry_dir=registry_dir,
            serving_dir=serving_dir,
            reason=reason,
            skip_shap=skip_shap,
        )

        if result.status == "completed" and regenerate_predictions and data_dict:
            logger.info("Regenerating predictions after retraining")
            from ml.pipelines.components.predictor import (
                generate_predictions,
                save_predictions,
            )

            predictions = generate_predictions(
                data_dict=data_dict, serving_dir=serving_dir,
            )
            save_predictions(predictions, registry_dir=registry_dir)

    return check_result


def _determine_reason(check_result: DriftCheckResult) -> str:
    """Pick the most specific drift reason from the check result."""
    if check_result.concept_drift.is_drifted:
        return "concept_drift"
    if check_result.prediction_drift.is_drifted:
        return "prediction_drift"
    return "data_drift"


# ---------------------------------------------------------------------------
# CLI — entry point for K8s CronJob execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import os
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Drift detection trigger — run drift check and optionally retrain",
    )
    parser.add_argument(
        "--auto-retrain",
        action="store_true",
        help="Run drift check and auto-trigger retraining if drift detected",
    )
    parser.add_argument(
        "--registry-dir",
        default=os.environ.get("MODEL_REGISTRY_DIR", "model_registry"),
    )
    parser.add_argument(
        "--serving-dir",
        default=os.environ.get("SERVING_DIR", "/models/active"),
    )
    parser.add_argument(
        "--drift-log-dir",
        default=os.environ.get("DRIFT_LOG_DIR", "drift_logs"),
    )
    parser.add_argument(
        "--tickers",
        type=str,
        help="Comma-separated ticker list",
    )
    parser.add_argument("--skip-shap", action="store_true")
    args = parser.parse_args()

    if not args.auto_retrain:
        parser.print_help()
        sys.exit(0)

    try:
        tickers = args.tickers.split(",") if args.tickers else None

        from ml.pipelines.components.data_loader import load_data
        from ml.pipelines.components.feature_engineer import engineer_features
        from ml.pipelines.components.label_generator import generate_labels

        logger.info("Loading data for drift check...")
        data_dict = load_data(tickers=tickers)

        logger.info("Engineering features for drift comparison...")
        enriched = engineer_features(data_dict)
        labelled, feature_names = generate_labels(enriched)

        # Split into reference (older 80%) vs current (recent 20%) for drift comparison
        combined = pd.concat(labelled.values(), ignore_index=True)
        split_idx = int(len(combined) * 0.8)
        reference_features = combined[feature_names].iloc[:split_idx]
        current_features = combined[feature_names].iloc[split_idx:]

        # Compute baseline vs recent errors (dummy zeros if no predictions exist yet)
        baseline_errors = np.zeros(min(100, split_idx))
        recent_errors = np.zeros(min(100, len(combined) - split_idx))
        historical_rmse = 0.0
        recent_rmse = 0.0

        logger.info(
            "Running drift check — reference=%d rows, current=%d rows",
            len(reference_features),
            len(current_features),
        )

        check_result = evaluate_and_trigger(
            reference_features=reference_features,
            current_features=current_features,
            baseline_errors=baseline_errors,
            recent_errors=recent_errors,
            historical_rmse=historical_rmse,
            recent_rmse=recent_rmse,
            tickers=tickers,
            data_dict=data_dict,
            registry_dir=args.registry_dir,
            serving_dir=args.serving_dir,
            log_dir=args.drift_log_dir,
            auto_retrain=True,
            regenerate_predictions=True,
            skip_shap=args.skip_shap,
        )

        logger.info(
            "Drift check complete — any_drift=%s, data=%s, prediction=%s, concept=%s",
            check_result.any_drift,
            check_result.data_drift.is_drifted,
            check_result.prediction_drift.is_drifted,
            check_result.concept_drift.is_drifted,
        )

    except Exception:
        logger.exception("Drift trigger failed")
        sys.exit(1)
