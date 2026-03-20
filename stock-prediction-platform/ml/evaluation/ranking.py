"""Model ranking with composite scoring, variance penalty, and winner selection."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ml.models.model_configs import TrainingResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class RankedModel:
    """A TrainingResult augmented with ranking metadata."""

    rank: int
    training_result: TrainingResult
    composite_score: float
    raw_rmse: float
    directional_accuracy: float
    fold_stability: float
    variance_penalty: float


@dataclass
class WinnerResult:
    """The selected winner model with comparison context."""

    winner: RankedModel
    runner_up: RankedModel | None
    margin: float
    total_candidates: int


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def compute_composite_score(
    result: TrainingResult,
    stability_penalty_weight: float = 0.5,
    directional_accuracy_weight: float = 0.01,
) -> float:
    """Compute a single composite score for ranking (lower is better).

    Formula: ``oos_rmse + λ_stab × fold_stability - λ_da × directional_accuracy``
    """
    oos_rmse = result.oos_metrics.get("rmse", 0.0)
    da = result.oos_metrics.get("directional_accuracy", 0.0)
    penalty = stability_penalty_weight * result.fold_stability
    bonus = directional_accuracy_weight * da
    return oos_rmse + penalty - bonus


def rank_models(
    results: list[TrainingResult],
    stability_penalty_weight: float = 0.5,
    directional_accuracy_weight: float = 0.01,
) -> list[RankedModel]:
    """Rank models by composite score ascending (best first).

    Raises ``ValueError`` if *results* is empty.
    """
    if not results:
        raise ValueError("Cannot rank an empty list of results.")

    scored: list[tuple[float, TrainingResult]] = []
    for r in results:
        score = compute_composite_score(
            r,
            stability_penalty_weight=stability_penalty_weight,
            directional_accuracy_weight=directional_accuracy_weight,
        )
        scored.append((score, r))

    scored.sort(key=lambda t: t[0])

    ranked: list[RankedModel] = []
    for i, (score, r) in enumerate(scored, start=1):
        ranked.append(
            RankedModel(
                rank=i,
                training_result=r,
                composite_score=score,
                raw_rmse=r.oos_metrics.get("rmse", 0.0),
                directional_accuracy=r.oos_metrics.get("directional_accuracy", 0.0),
                fold_stability=r.fold_stability,
                variance_penalty=stability_penalty_weight * r.fold_stability,
            )
        )

    return ranked


def select_winner(
    results: list[TrainingResult],
    stability_penalty_weight: float = 0.5,
    directional_accuracy_weight: float = 0.01,
) -> WinnerResult:
    """Select the winning model from a list of training results.

    Raises ``ValueError`` if *results* is empty.
    """
    ranked = rank_models(
        results,
        stability_penalty_weight=stability_penalty_weight,
        directional_accuracy_weight=directional_accuracy_weight,
    )

    winner = ranked[0]
    runner_up = ranked[1] if len(ranked) > 1 else None
    margin = (runner_up.composite_score - winner.composite_score) if runner_up else 0.0

    logger.info(
        "Winner: %s_%s  score=%.6f  margin=%.6f",
        winner.training_result.model_name,
        winner.training_result.scaler_variant,
        winner.composite_score,
        margin,
    )

    return WinnerResult(
        winner=winner,
        runner_up=runner_up,
        margin=margin,
        total_candidates=len(ranked),
    )
