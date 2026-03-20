"""Drift detectors — data drift (KS-test, PSI), prediction drift, concept drift."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DriftResult dataclass
# ---------------------------------------------------------------------------


@dataclass
class DriftResult:
    """Result of a single drift detection check."""

    drift_type: str  # "data_drift" | "prediction_drift" | "concept_drift"
    is_drifted: bool
    severity: str  # "none" | "low" | "medium" | "high"
    details: dict
    timestamp: str
    features_affected: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Data Drift Detector (DRIFT-01)
# ---------------------------------------------------------------------------


class DataDriftDetector:
    """Detect data drift via KS-test and PSI on feature distributions."""

    def __init__(
        self,
        ks_threshold: float = 0.01,
        psi_threshold: float = 0.2,
        n_bins: int = 10,
    ) -> None:
        self.ks_threshold = ks_threshold
        self.psi_threshold = psi_threshold
        self.n_bins = n_bins

    def detect(
        self, reference: pd.DataFrame, current: pd.DataFrame,
    ) -> DriftResult:
        """Compare feature distributions between *reference* and *current*."""
        features_affected: list[str] = []
        per_feature: dict[str, dict] = {}

        common_cols = [c for c in reference.columns if c in current.columns]

        for col in common_cols:
            ref_vals = reference[col].dropna().values.astype(float)
            cur_vals = current[col].dropna().values.astype(float)

            if len(ref_vals) < 2 or len(cur_vals) < 2:
                continue

            ks_stat, ks_pval = self._ks_test(ref_vals, cur_vals)
            psi = self._compute_psi(ref_vals, cur_vals, self.n_bins)

            drifted = ks_pval < self.ks_threshold or psi > self.psi_threshold
            if drifted:
                features_affected.append(col)

            per_feature[col] = {
                "ks_statistic": float(ks_stat),
                "ks_pvalue": float(ks_pval),
                "psi": float(psi),
                "drifted": drifted,
            }

        is_drifted = len(features_affected) > 0
        severity = self._compute_severity(len(features_affected), len(common_cols))

        return DriftResult(
            drift_type="data_drift",
            is_drifted=is_drifted,
            severity=severity,
            details={
                "n_features_checked": len(common_cols),
                "n_features_drifted": len(features_affected),
                "per_feature": per_feature,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
            features_affected=features_affected,
        )

    @staticmethod
    def _ks_test(
        reference: np.ndarray, current: np.ndarray,
    ) -> tuple[float, float]:
        """Two-sample KS test. Returns (statistic, p-value)."""
        stat, pval = ks_2samp(reference, current)
        return float(stat), float(pval)

    @staticmethod
    def _compute_psi(
        reference: np.ndarray, current: np.ndarray, n_bins: int = 10,
    ) -> float:
        """Population Stability Index using quantile-based binning."""
        breakpoints = np.quantile(reference, np.linspace(0, 1, n_bins + 1))
        breakpoints[0] = -np.inf
        breakpoints[-1] = np.inf
        # Deduplicate breakpoints to handle constant features
        breakpoints = np.unique(breakpoints)
        if len(breakpoints) < 2:
            return 0.0

        ref_counts = np.histogram(reference, bins=breakpoints)[0]
        cur_counts = np.histogram(current, bins=breakpoints)[0]

        ref_pct = np.clip(ref_counts / max(ref_counts.sum(), 1), 1e-6, None)
        cur_pct = np.clip(cur_counts / max(cur_counts.sum(), 1), 1e-6, None)

        return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))

    @staticmethod
    def _compute_severity(n_drifted: int, n_total: int) -> str:
        if n_total == 0 or n_drifted == 0:
            return "none"
        ratio = n_drifted / n_total
        if ratio < 0.1:
            return "low"
        if ratio < 0.5:
            return "medium"
        return "high"


# ---------------------------------------------------------------------------
# Prediction Drift Detector (DRIFT-02)
# ---------------------------------------------------------------------------


class PredictionDriftDetector:
    """Detect prediction drift via rolling error comparison."""

    def __init__(self, error_multiplier: float = 1.5) -> None:
        self.error_multiplier = error_multiplier

    def detect(
        self,
        baseline_errors: np.ndarray,
        recent_errors: np.ndarray,
    ) -> DriftResult:
        """Compare recent prediction errors against historical baseline."""
        baseline_mae = float(np.mean(np.abs(baseline_errors)))
        recent_mae = float(np.mean(np.abs(recent_errors)))

        threshold = baseline_mae * self.error_multiplier
        is_drifted = recent_mae > threshold

        if baseline_mae > 0:
            ratio = recent_mae / baseline_mae
        else:
            ratio = 0.0 if recent_mae == 0 else float("inf")

        severity = self._compute_severity(ratio, self.error_multiplier)

        return DriftResult(
            drift_type="prediction_drift",
            is_drifted=is_drifted,
            severity=severity,
            details={
                "baseline_mae": baseline_mae,
                "recent_mae": recent_mae,
                "threshold": threshold,
                "error_ratio": ratio,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _compute_severity(ratio: float, multiplier: float) -> str:
        if ratio < multiplier:
            return "none"
        if ratio < 2 * multiplier:
            return "medium"
        return "high"


# ---------------------------------------------------------------------------
# Concept Drift Detector (DRIFT-03)
# ---------------------------------------------------------------------------


class ConceptDriftDetector:
    """Detect concept drift via model performance degradation."""

    def __init__(self, degradation_threshold: float = 1.3) -> None:
        self.degradation_threshold = degradation_threshold

    def detect(
        self, historical_rmse: float, recent_rmse: float,
    ) -> DriftResult:
        """Compare recent vs. historical model RMSE."""
        if historical_rmse > 0:
            ratio = recent_rmse / historical_rmse
        else:
            ratio = 0.0 if recent_rmse == 0 else float("inf")

        is_drifted = ratio > self.degradation_threshold
        severity = self._compute_severity(ratio, self.degradation_threshold)

        return DriftResult(
            drift_type="concept_drift",
            is_drifted=is_drifted,
            severity=severity,
            details={
                "historical_rmse": float(historical_rmse),
                "recent_rmse": float(recent_rmse),
                "degradation_ratio": float(ratio),
                "threshold": self.degradation_threshold,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _compute_severity(ratio: float, threshold: float) -> str:
        if ratio < threshold:
            return "none"
        if ratio < 2 * threshold:
            return "medium"
        return "high"
