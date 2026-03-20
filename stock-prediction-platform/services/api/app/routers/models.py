"""Models router — /models/comparison and /models/drift endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import (
    DriftEventEntry,
    DriftStatusResponse,
    ModelComparisonEntry,
    ModelComparisonResponse,
)
from app.services.prediction_service import load_drift_events, load_model_comparison

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/comparison", response_model=ModelComparisonResponse)
async def models_comparison() -> ModelComparisonResponse:
    """Return model metrics comparison sorted by OOS RMSE."""
    raw_models = load_model_comparison(
        registry_dir=settings.MODEL_REGISTRY_DIR,
    )
    entries = [
        ModelComparisonEntry(
            model_name=m.get("model_name", "unknown"),
            scaler_variant=m.get("scaler_variant", "unknown"),
            version=m.get("version"),
            is_winner=m.get("is_winner", False),
            is_active=m.get("is_active", False),
            oos_metrics=m.get("oos_metrics", {}),
            fold_stability=m.get("fold_stability"),
            best_params=m.get("best_params", {}),
            saved_at=m.get("saved_at"),
        )
        for m in raw_models
    ]
    winner = next((e for e in entries if e.is_winner), None)
    return ModelComparisonResponse(
        models=entries,
        winner=winner,
        count=len(entries),
    )


@router.get("/drift", response_model=DriftStatusResponse)
async def models_drift() -> DriftStatusResponse:
    """Return recent drift detection events."""
    raw_events = load_drift_events(
        log_dir=settings.DRIFT_LOG_DIR,
    )
    events = [
        DriftEventEntry(
            drift_type=e.get("drift_type", "unknown"),
            is_drifted=e.get("is_drifted", False),
            severity=e.get("severity", "none"),
            details=e.get("details", {}),
            timestamp=e.get("timestamp"),
            features_affected=e.get("features_affected", []),
        )
        for e in raw_events
    ]
    any_recent = any(e.is_drifted for e in events)
    latest = events[0] if events else None
    return DriftStatusResponse(
        events=events,
        any_recent_drift=any_recent,
        latest_event=latest,
        count=len(events),
    )
