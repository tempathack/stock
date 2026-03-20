"""Drift monitoring — daily check job orchestrating all three drift detectors."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from ml.drift.detector import (
    ConceptDriftDetector,
    DataDriftDetector,
    DriftResult,
    PredictionDriftDetector,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DriftCheckResult
# ---------------------------------------------------------------------------


@dataclass
class DriftCheckResult:
    """Aggregated result from running all three drift detectors."""

    checked_at: str
    data_drift: DriftResult
    prediction_drift: DriftResult
    concept_drift: DriftResult
    any_drift: bool

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# DriftMonitor
# ---------------------------------------------------------------------------


class DriftMonitor:
    """Orchestrates all three drift detectors in a single check."""

    def __init__(
        self,
        ks_threshold: float = 0.01,
        psi_threshold: float = 0.2,
        error_multiplier: float = 1.5,
        degradation_threshold: float = 1.3,
    ) -> None:
        self._data_detector = DataDriftDetector(
            ks_threshold=ks_threshold, psi_threshold=psi_threshold,
        )
        self._pred_detector = PredictionDriftDetector(
            error_multiplier=error_multiplier,
        )
        self._concept_detector = ConceptDriftDetector(
            degradation_threshold=degradation_threshold,
        )

    def check(
        self,
        reference_features: pd.DataFrame,
        current_features: pd.DataFrame,
        baseline_errors: np.ndarray,
        recent_errors: np.ndarray,
        historical_rmse: float,
        recent_rmse: float,
    ) -> DriftCheckResult:
        """Run all three drift detectors and return aggregated result."""
        data_result = self._data_detector.detect(reference_features, current_features)
        pred_result = self._pred_detector.detect(baseline_errors, recent_errors)
        concept_result = self._concept_detector.detect(historical_rmse, recent_rmse)

        any_drift = (
            data_result.is_drifted
            or pred_result.is_drifted
            or concept_result.is_drifted
        )

        logger.info(
            "Drift check complete — data=%s pred=%s concept=%s any=%s",
            data_result.is_drifted,
            pred_result.is_drifted,
            concept_result.is_drifted,
            any_drift,
        )

        return DriftCheckResult(
            checked_at=datetime.now(timezone.utc).isoformat(),
            data_drift=data_result,
            prediction_drift=pred_result,
            concept_drift=concept_result,
            any_drift=any_drift,
        )
