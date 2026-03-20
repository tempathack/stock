"""Drift trigger — event logging and bridge to retraining pipeline."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ml.drift.detector import DriftResult
from ml.drift.monitor import DriftCheckResult, DriftMonitor

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DriftLogger
# ---------------------------------------------------------------------------


class DriftLogger:
    """Persist drift events to file (and optionally to database)."""

    def __init__(self, log_dir: str = "drift_logs") -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def log_file(self) -> Path:
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
        if not self.log_file.exists():
            return []
        with open(self.log_file) as f:
            lines = f.readlines()
        events = [json.loads(line) for line in lines]
        return events[-n:]

    def _log_to_file(self, record: dict) -> None:
        with open(self.log_file, "a") as f:
            f.write(json.dumps(record, default=str) + "\n")


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
