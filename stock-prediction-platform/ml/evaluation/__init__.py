"""Model evaluation and selection modules."""

from __future__ import annotations

from ml.evaluation.cross_validation import create_time_series_cv, walk_forward_evaluate
from ml.evaluation.metrics import (
    compute_all_metrics,
    compute_directional_accuracy,
    compute_fold_stability,
    compute_mae,
    compute_mape,
    compute_r2,
    compute_rmse,
)
from ml.evaluation.ranking import (
    RankedModel,
    WinnerResult,
    compute_composite_score,
    rank_models,
    select_winner,
)

try:
    from ml.evaluation.shap_analysis import (
        compute_feature_importance,
        compute_shap_values,
        get_explainer_type,
        get_shap_summary,
    )
except ImportError:  # shap / numba not available in this environment
    pass

__all__ = [
    "compute_r2",
    "compute_mae",
    "compute_rmse",
    "compute_mape",
    "compute_directional_accuracy",
    "compute_fold_stability",
    "compute_all_metrics",
    "create_time_series_cv",
    "walk_forward_evaluate",
    "RankedModel",
    "WinnerResult",
    "compute_composite_score",
    "rank_models",
    "select_winner",
    "compute_feature_importance",
    "compute_shap_values",
    "get_explainer_type",
    "get_shap_summary",
]
