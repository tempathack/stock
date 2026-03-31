"""Prediction service — loads cached predictions, model metadata, drift events."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from ml.features.feast_store import get_online_features as _feast_get_online
    _FEAST_AVAILABLE = True
except ImportError:
    _FEAST_AVAILABLE = False
    _feast_get_online = None  # type: ignore[assignment]

# Expose at module level so tests can patch app.services.prediction_service.get_online_features
get_online_features = _feast_get_online


def load_cached_predictions(
    registry_dir: str = "model_registry",
    horizon: int | None = None,
) -> list[dict]:
    """Load predictions from ``{registry_dir}/predictions/latest.json``.

    When *horizon* is provided, loads from ``latest_{h}d.json`` instead.
    Returns an empty list if the file does not exist.
    """
    pred_dir = Path(registry_dir) / "predictions"
    if horizon is not None:
        path = pred_dir / f"latest_{horizon}d.json"
    else:
        path = pred_dir / "latest.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def get_prediction_for_ticker(
    ticker: str,
    registry_dir: str = "model_registry",
    horizon: int | None = None,
) -> dict | None:
    """Return the cached prediction for a single ticker, or ``None``."""
    predictions = load_cached_predictions(registry_dir, horizon=horizon)
    ticker_upper = ticker.upper()
    for pred in predictions:
        if pred.get("ticker", "").upper() == ticker_upper:
            return pred
    return None


def load_available_horizons(serving_dir: str = "/models/active") -> dict:
    """Read ``{serving_dir}/horizons.json`` if it exists.

    Returns ``{"horizons": [7], "default": 7}`` as fallback.
    """
    path = Path(serving_dir) / "horizons.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"horizons": [7], "default": 7}


def load_model_comparison(registry_dir: str = "model_registry") -> list[dict]:
    """Read all model metadata from the file-based registry.

    Scans ``{registry_dir}/{model_key}/v{N}/metadata.json``.
    Returns list sorted by OOS RMSE ascending.
    """
    base = Path(registry_dir)
    entries: list[dict] = []
    if not base.exists():
        return entries

    for model_dir in sorted(base.iterdir()):
        if not model_dir.is_dir() or model_dir.name in ("predictions", "runs"):
            continue
        for ver_dir in sorted(model_dir.iterdir()):
            meta_path = ver_dir / "metadata.json"
            if not meta_path.exists():
                continue
            with open(meta_path) as f:
                meta = json.load(f)
            entries.append(meta)

    entries.sort(
        key=lambda e: e.get("oos_metrics", {}).get("rmse") or float("inf"),
    )
    return entries


def load_drift_events(
    log_dir: str = "drift_logs",
    n: int = 100,
) -> list[dict]:
    """Read recent drift events from JSONL log.

    Returns list of dicts, newest first.
    """
    path = Path(log_dir) / "drift_events.jsonl"
    if not path.exists():
        return []
    with open(path) as f:
        lines = f.readlines()
    events = [json.loads(line) for line in lines]
    return list(reversed(events[-n:]))


# ── DB-first query functions (Phase 31 → async in Phase 40) ──────────────


async def load_model_comparison_from_db() -> list[dict] | None:
    """Query model_registry table for model comparison data.

    Returns list of dicts matching ModelComparisonEntry shape, sorted by OOS RMSE.
    Returns None if DB is unavailable (caller should fall back to file-based).
    """
    from sqlalchemy import text as sa_text

    from app.models.database import get_async_session, get_engine

    if get_engine() is None:
        return None

    query = sa_text("""
        SELECT model_name, version, metrics_json, trained_at, is_active
        FROM (
            SELECT DISTINCT ON (model_name, metrics_json->>'scaler_variant')
                model_name, version, metrics_json, trained_at, is_active
            FROM model_registry
            ORDER BY model_name, metrics_json->>'scaler_variant', trained_at DESC NULLS LAST
        ) deduped
        ORDER BY (metrics_json->>'oos_rmse')::numeric ASC NULLS LAST
    """)

    try:
        async with get_async_session() as session:
            result = await session.execute(query)
            rows = result.mappings().all()
    except Exception:
        logger.exception("Failed to query model_registry")
        return None

    entries = []
    for raw in rows:
        metrics = raw.get("metrics_json") or {}
        entries.append({
            "model_name": raw.get("model_name", "unknown"),
            "scaler_variant": metrics.get("scaler_variant", "unknown"),
            "version": raw.get("version"),
            "is_winner": metrics.get("is_winner", False),
            "is_active": raw.get("is_active", False),
            "oos_metrics": {
                k[4:]: v for k, v in metrics.items()
                if k.startswith("oos_")
            },
            "fold_stability": metrics.get("fold_stability"),
            "best_params": metrics.get("best_params", {}),
            "saved_at": raw["trained_at"].isoformat() if raw.get("trained_at") else None,
            "traffic_weight": 0.0,
        })
    return entries


async def load_db_predictions(horizon: int | None = None) -> list[dict] | None:
    """Read stored predictions from the DB predictions table.

    Used as a last-resort fallback when pipeline.pkl and cached files are absent.
    Returns the most recent prediction_date batch, optionally filtered to
    predictions whose horizon (predicted_date - prediction_date) matches.
    """
    from sqlalchemy import text as sa_text

    from app.models.database import get_async_session, get_engine

    if get_engine() is None:
        return None

    query = sa_text("""
        WITH latest AS (
            SELECT MAX(prediction_date) AS max_date FROM predictions
        ),
        active_model AS (
            SELECT model_id, model_name FROM model_registry
            WHERE is_active = true ORDER BY trained_at DESC LIMIT 1
        )
        SELECT
            p.ticker,
            p.prediction_date::text  AS prediction_date,
            p.predicted_date::text   AS predicted_date,
            p.predicted_price,
            p.confidence,
            COALESCE(a.model_name, 'unknown') AS model_name,
            p.model_id,
            (p.predicted_date - p.prediction_date) AS horizon_days
        FROM predictions p
        CROSS JOIN latest l
        LEFT JOIN active_model a ON TRUE
        WHERE p.prediction_date = l.max_date
        ORDER BY p.ticker, p.predicted_date
    """)

    try:
        async with get_async_session() as session:
            result = await session.execute(query)
            rows = result.mappings().all()
    except Exception:
        logger.exception("Failed to load DB predictions fallback")
        return None

    if not rows:
        return None

    entries = []
    for r in rows:
        h = int(r["horizon_days"]) if r.get("horizon_days") is not None else None
        if horizon is not None and h != horizon:
            continue
        entries.append({
            "ticker": r["ticker"],
            "prediction_date": r["prediction_date"],
            "predicted_date": r["predicted_date"],
            "predicted_price": float(r["predicted_price"]),
            "confidence": float(r["confidence"]) if r.get("confidence") is not None else None,
            "model_name": r["model_name"],
            "assigned_model_id": r["model_id"],
            "horizon_days": h,
        })

    # If horizon filter yielded nothing, return all (horizon mismatch — serve what exists)
    if not entries and horizon is not None:
        return await load_db_predictions(horizon=None)

    return entries if entries else None


async def load_drift_events_from_db(n: int = 100) -> list[dict] | None:
    """Query drift_logs table for recent drift events.

    Returns list of dicts matching DriftEventEntry shape, newest first.
    Returns None if DB is unavailable.
    """
    from sqlalchemy import text as sa_text

    from app.models.database import get_async_session, get_engine

    if get_engine() is None:
        return None

    query = sa_text("""
        SELECT drift_type, severity, details_json, detected_at
        FROM drift_logs
        ORDER BY detected_at DESC
        LIMIT :n
    """)

    try:
        async with get_async_session() as session:
            result = await session.execute(query, {"n": n})
            rows = result.mappings().all()
    except Exception:
        logger.exception("Failed to query drift_logs")
        return None

    events = []
    for raw in rows:
        details = raw.get("details_json") or {}
        events.append({
            "drift_type": raw.get("drift_type", "unknown"),
            "is_drifted": details.get("is_drifted", raw.get("severity", "none") != "none"),
            "severity": raw.get("severity", "none"),
            "details": details,
            "timestamp": raw["detected_at"].isoformat() if raw.get("detected_at") else None,
            "features_affected": [
                k for k, v in details.get("per_feature", {}).items()
                if v.get("drifted", False)
            ],
        })
    return events


async def get_live_prediction(
    ticker: str,
    serving_dir: str = "/models/active",
    horizon: int | None = None,
    ab_model: dict | None = None,
) -> dict | None:
    """Run live inference for a single ticker.

    When ``settings.KSERVE_ENABLED`` is True, inference is delegated to a
    KServe InferenceService via the V2 HTTP protocol.  When False, the
    legacy pipeline.pkl path is used.

    When *horizon* is provided, reads from ``{serving_dir}/horizon_{h}d/``.
    When *ab_model* is provided, overrides serving_dir / KServe URL.
    """
    from app.config import settings as _settings

    ticker = ticker.upper()

    if _settings.KSERVE_ENABLED:
        kserve_url = None
        kserve_model_name = None
        if ab_model is not None:
            kserve_url = ab_model.get("kserve_url")
            kserve_model_name = ab_model.get("kserve_model_name")
        return await _kserve_inference(
            ticker=ticker,
            serving_dir=serving_dir,
            horizon=horizon,
            ab_model=ab_model,
            kserve_url=kserve_url,
            kserve_model_name=kserve_model_name,
        )

    return await _legacy_inference(
        ticker=ticker,
        serving_dir=serving_dir,
        horizon=horizon,
        ab_model=ab_model,
    )


async def _kserve_inference(
    ticker: str,
    serving_dir: str = "/models/active",
    horizon: int | None = None,
    ab_model: dict | None = None,
    kserve_url: str | None = None,
    kserve_model_name: str | None = None,
) -> dict | None:
    """Run inference via KServe V2 protocol.

    Returns prediction dict (same schema as legacy path) or *None* on failure
    so that the caller can fall back to cached predictions.
    """
    from datetime import date, timedelta
    from pathlib import Path as _Path

    import numpy as np

    from app.config import settings as _settings
    from app.services import kserve_client

    model_name_for_kserve = kserve_model_name or _settings.KSERVE_MODEL_NAME

    # Resolve feature names from serving dir (features.json is lightweight)
    effective_serving_dir = serving_dir
    if ab_model is not None and "serving_path" in ab_model:
        effective_serving_dir = ab_model["serving_path"]
    if horizon is not None:
        base_srv = _Path(effective_serving_dir) / f"horizon_{horizon}d"
    else:
        base_srv = _Path(effective_serving_dir)
    features_path = base_srv / "features.json"
    # Fallback: if horizon-specific features.json missing, use root serving dir
    if not features_path.exists() and horizon is not None:
        features_path = _Path(effective_serving_dir) / "features.json"
    feature_names: list[str] | None = None
    if features_path.exists():
        with open(features_path) as f:
            feature_names = json.load(f)

    # Model name for response — use startup cache (MinIO/DB loaded at lifespan)
    from app.services.model_metadata_cache import get_active_model_metadata
    if ab_model is not None:
        model_display = ab_model["model_name"]
    else:
        cached = get_active_model_metadata()
        model_name_str = cached.get("model_name")
        scaler = cached.get("scaler_variant")
        if model_name_str and scaler:
            model_display = f"{model_name_str}_{scaler}"
        elif model_name_str:
            model_display = model_name_str
        else:
            model_display = "unknown"  # only if startup cache load failed

    # Load OHLCV data
    ohlcv_df = await _load_ohlcv_for_inference(ticker, lookback=250)
    if ohlcv_df is None or len(ohlcv_df) < 50:
        logger.warning(
            "Insufficient OHLCV data for %s (%d rows)",
            ticker,
            len(ohlcv_df) if ohlcv_df is not None else 0,
        )
        return None

    # Compute features
    try:
        from ml.features.indicators import compute_all_indicators
        from ml.features.lag_features import compute_lag_features, compute_rolling_stats

        enriched = compute_all_indicators(ohlcv_df.copy())
        enriched = compute_lag_features(enriched)
        enriched = compute_rolling_stats(enriched)
    except Exception:
        logger.exception("Failed to compute indicators for %s", ticker)
        return None

    # Align features
    try:
        if feature_names:
            available = [c for c in feature_names if c in enriched.columns]
            if len(available) < len(feature_names) * 0.8:
                logger.warning(
                    "Too many missing features for %s: %d/%d available",
                    ticker,
                    len(available),
                    len(feature_names),
                )
                return None
            X = enriched[available].iloc[[-1]]
            for col in feature_names:
                if col not in X.columns:
                    X[col] = 0.0
            X = X[feature_names]
        else:
            X = enriched.select_dtypes(include=[np.number]).iloc[[-1]]

        X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    except Exception:
        logger.exception("Feature alignment failed for %s", ticker)
        return None

    # Call KServe V2 inference
    try:
        response = await kserve_client.infer_v2(
            model_name=model_name_for_kserve,
            input_data=X.values.tolist(),
            feature_names=feature_names,
            base_url=kserve_url,
        )
        predicted_price = kserve_client.parse_v2_output(response)
    except Exception:
        logger.warning(
            "KServe inference failed for %s, falling back to cached",
            ticker,
            exc_info=True,
        )
        return None

    # Build response (same schema as legacy path)
    last_close = float(ohlcv_df["close"].iloc[-1])
    # Model predicts a percentage return (e.g. 0.05 means +5%).
    # Convert to absolute price: predicted_abs = last_close * (1 + predicted_return).
    if abs(predicted_price) < 10.0:
        # Raw output looks like a return (< 10x multiplier), convert to absolute
        predicted_price = last_close * (1.0 + predicted_price)
    confidence = max(0.0, min(1.0, 1.0 - abs(predicted_price - last_close) / last_close))
    h = horizon or 7
    predicted_date = date.today() + timedelta(days=h)

    result_dict: dict = {
        "ticker": ticker,
        "prediction_date": str(date.today()),
        "predicted_date": str(predicted_date),
        "predicted_price": round(predicted_price, 4),
        "model_name": model_display,
        "confidence": round(confidence, 4),
    }
    if horizon is not None:
        result_dict["horizon_days"] = horizon

    # Log A/B assignment
    if ab_model is not None:
        from app.services.ab_service import log_ab_assignment

        await log_ab_assignment(
            ticker=ticker,
            model_id=ab_model["model_id"],
            model_name=ab_model["model_name"],
            predicted_price=round(predicted_price, 4),
            horizon_days=horizon or 7,
        )

    return result_dict


async def _legacy_inference(
    ticker: str,
    serving_dir: str = "/models/active",
    horizon: int | None = None,
    ab_model: dict | None = None,
) -> dict | None:
    """Legacy pipeline.pkl-based inference (KSERVE_ENABLED=False)."""
    import pickle
    from datetime import date, timedelta
    from pathlib import Path as _Path

    import numpy as np

    ticker = ticker.upper()

    # Resolve serving dir — A/B model override takes priority
    effective_serving_dir = serving_dir
    if ab_model is not None:
        effective_serving_dir = ab_model["serving_path"]

    # Resolve horizon-specific serving dir
    if horizon is not None:
        base_srv = _Path(effective_serving_dir) / f"horizon_{horizon}d"
    else:
        base_srv = _Path(effective_serving_dir)

    pipeline_path = base_srv / "pipeline.pkl"
    features_path = base_srv / "features.json"
    metadata_path = base_srv / "metadata.json"

    # Step 1: Load the active model pipeline
    if not pipeline_path.exists():
        logger.warning("No active model pipeline at %s", pipeline_path)
        return None

    try:
        with open(pipeline_path, "rb") as f:
            pipeline = pickle.load(f)  # noqa: S301
    except Exception:
        logger.exception("Failed to load pipeline from %s", pipeline_path)
        return None

    # Load feature names (required to align columns)
    feature_names = None
    if features_path.exists():
        with open(features_path) as f:
            feature_names = json.load(f)

    # Load model metadata for response — use startup cache
    from app.services.model_metadata_cache import get_active_model_metadata
    if ab_model is not None:
        model_name = ab_model["model_name"]
    else:
        cached = get_active_model_metadata()
        model_name_str = cached.get("model_name")
        scaler = cached.get("scaler_variant")
        if model_name_str and scaler:
            model_name = f"{model_name_str}_{scaler}"
        elif model_name_str:
            model_name = model_name_str
        else:
            model_name = "unknown"  # only if startup cache load failed

    # Step 2: Fetch OHLCV data from DB
    ohlcv_df = await _load_ohlcv_for_inference(ticker, lookback=250)
    if ohlcv_df is None or len(ohlcv_df) < 50:
        logger.warning(
            "Insufficient OHLCV data for %s (%d rows)",
            ticker,
            len(ohlcv_df) if ohlcv_df is not None else 0,
        )
        return None

    # Step 3: Compute features
    try:
        from ml.features.indicators import compute_all_indicators

        enriched = compute_all_indicators(ohlcv_df.copy())
    except Exception:
        logger.exception("Failed to compute indicators for %s", ticker)
        return None

    # Step 4: Align features and predict
    try:
        if feature_names:
            available = [c for c in feature_names if c in enriched.columns]
            if len(available) < len(feature_names) * 0.8:
                logger.warning(
                    "Too many missing features for %s: %d/%d available",
                    ticker,
                    len(available),
                    len(feature_names),
                )
                return None
            X = enriched[available].iloc[[-1]]
            for col in feature_names:
                if col not in X.columns:
                    X[col] = 0.0
            X = X[feature_names]
        else:
            X = enriched.select_dtypes(include=[np.number]).iloc[[-1]]

        X = X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        predicted_price = float(pipeline.predict(X)[0])
    except Exception:
        logger.exception("pipeline.predict() failed for %s", ticker)
        return None

    # Step 5: Build response
    last_close = float(ohlcv_df["close"].iloc[-1])
    confidence = max(0.0, min(1.0, 1.0 - abs(predicted_price - last_close) / last_close))
    h = horizon or 7
    predicted_date = date.today() + timedelta(days=h)

    result_dict: dict = {
        "ticker": ticker,
        "prediction_date": str(date.today()),
        "predicted_date": str(predicted_date),
        "predicted_price": round(predicted_price, 4),
        "model_name": model_name,
        "confidence": round(confidence, 4),
    }
    if horizon is not None:
        result_dict["horizon_days"] = horizon

    # Log A/B assignment (fire-and-forget)
    if ab_model is not None:
        from app.services.ab_service import log_ab_assignment

        await log_ab_assignment(
            ticker=ticker,
            model_id=ab_model["model_id"],
            model_name=ab_model["model_name"],
            predicted_price=round(predicted_price, 4),
            horizon_days=horizon or 7,
        )

    return result_dict


async def _load_ohlcv_for_inference(
    ticker: str,
    lookback: int = 250,
) -> "pd.DataFrame | None":
    """Load recent OHLCV rows for a single ticker via async session."""
    from sqlalchemy import text as sa_text

    from app.models.database import get_async_session, get_engine

    if get_engine() is None:
        return None

    query = sa_text("""
        SELECT date, open, high, low, close, adj_close, volume, vwap
        FROM ohlcv_daily
        WHERE ticker = :ticker
        ORDER BY date DESC
        LIMIT :lookback
    """)

    try:
        import pandas as pd

        async with get_async_session() as session:
            result = await session.execute(
                query, {"ticker": ticker.upper(), "lookback": lookback},
            )
            rows = result.mappings().all()
        if not rows:
            return None
        df = pd.DataFrame([dict(r) for r in rows])
        df = df.sort_values("date").reset_index(drop=True)
        # Cast NUMERIC columns from decimal.Decimal to float64 for arithmetic ops
        numeric_cols = ["open", "high", "low", "close", "adj_close", "volume", "vwap"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(float)
        return df
    except Exception:
        logger.exception("Failed to load OHLCV for %s", ticker)
        return None


async def get_bulk_live_predictions(
    tickers: list[str],
    serving_dir: str = "/models/active",
    horizon: int | None = None,
    ab_model: dict | None = None,
) -> list[dict] | None:
    """Run live inference for all tickers.

    Returns list of prediction dicts, or None if live inference is
    completely unavailable (no pipeline, no DB).
    Skips individual ticker failures.
    """
    from pathlib import Path as _Path

    from app.config import settings as _settings
    from app.models.database import get_engine

    if get_engine() is None:
        return None

    # When KServe is enabled, skip the pipeline.pkl existence check
    if not _settings.KSERVE_ENABLED:
        effective_dir = ab_model["serving_path"] if ab_model is not None else serving_dir
        if horizon is not None:
            pipeline_path = _Path(effective_dir) / f"horizon_{horizon}d" / "pipeline.pkl"
        else:
            pipeline_path = _Path(effective_dir) / "pipeline.pkl"
        if not pipeline_path.exists():
            return None

    results = []
    for ticker in tickers:
        pred = await get_live_prediction(
            ticker=ticker,
            serving_dir=serving_dir,
            horizon=horizon,
            ab_model=ab_model,
        )
        if pred is not None:
            results.append(pred)

    return results if results else None


async def load_rolling_performance_from_db(days: int = 30) -> dict | None:
    """Query rolling prediction performance for the active model.

    Joins predictions -> ohlcv_daily to compare predicted_price vs actual close.
    Returns dict with 'entries' (per-date metrics) and 'model_name', or None if DB unavailable.
    """
    from sqlalchemy import text as sa_text

    from app.models.database import get_async_session, get_engine

    if get_engine() is None:
        return None

    query = sa_text("""
        WITH active AS (
            SELECT model_id, model_name
            FROM model_registry
            WHERE is_active = true
            LIMIT 1
        ),
        compared AS (
            SELECT
                p.predicted_date,
                p.predicted_price,
                o.close AS actual_price,
                a.model_name
            FROM predictions p
            JOIN active a ON p.model_id = a.model_id
            JOIN ohlcv_daily o ON p.ticker = o.ticker AND p.predicted_date = o.date
            WHERE p.predicted_date >= CURRENT_DATE - :days * INTERVAL '1 day'
        )
        SELECT
            predicted_date::text AS date,
            model_name,
            sqrt(avg(power(predicted_price - actual_price, 2))) AS rmse,
            avg(abs(predicted_price - actual_price)) AS mae,
            count(*) AS n_predictions
        FROM compared
        GROUP BY predicted_date, model_name
        ORDER BY predicted_date ASC
    """)

    try:
        async with get_async_session() as session:
            result = await session.execute(query, {"days": days})
            rows = result.mappings().all()
    except Exception:
        logger.exception("Failed to query rolling performance")
        return None

    if not rows:
        return {"entries": [], "model_name": None}

    entries = []
    model_name = None
    for raw in rows:
        model_name = raw.get("model_name")
        entries.append({
            "date": raw["date"],
            "rmse": round(float(raw["rmse"]), 6) if raw.get("rmse") else None,
            "mae": round(float(raw["mae"]), 6) if raw.get("mae") else None,
            "directional_accuracy": None,
            "n_predictions": raw.get("n_predictions", 0),
        })

    return {"entries": entries, "model_name": model_name}


async def get_retrain_status_from_db() -> dict | None:
    """Get the latest retrain status from model_registry.

    Returns current active model info plus previous model for comparison.
    Returns None if DB is unavailable.
    """
    from sqlalchemy import text as sa_text

    from app.models.database import get_async_session, get_engine

    if get_engine() is None:
        return None

    query = sa_text("""
        SELECT model_name, version, metrics_json, trained_at, is_active
        FROM model_registry
        ORDER BY trained_at DESC
        LIMIT 2
    """)

    try:
        async with get_async_session() as session:
            result = await session.execute(query)
            rows = result.mappings().all()
    except Exception:
        logger.exception("Failed to query retrain status")
        return None

    if not rows:
        return {
            "model_name": None,
            "version": None,
            "trained_at": None,
            "is_active": False,
            "oos_metrics": {},
            "previous_model": None,
            "previous_trained_at": None,
        }

    current = rows[0]
    metrics = current.get("metrics_json") or {}
    result_dict = {
        "model_name": current.get("model_name"),
        "version": current.get("version"),
        "trained_at": current["trained_at"].isoformat() if current.get("trained_at") else None,
        "is_active": current.get("is_active", False),
        "oos_metrics": {k: v for k, v in metrics.items() if k.startswith("oos_")},
        "previous_model": None,
        "previous_trained_at": None,
    }

    if len(rows) > 1:
        prev = rows[1]
        result_dict["previous_model"] = prev.get("model_name")
        result_dict["previous_trained_at"] = prev["trained_at"].isoformat() if prev.get("trained_at") else None

    return result_dict


def get_online_features_for_ticker(ticker: str) -> dict | None:
    """Retrieve online features from Feast/Redis for a single ticker.

    Returns a dict of feature name -> value list (Feast format) on success,
    or None when Feast is unavailable or Redis is unreachable.

    FEAST-07: Used by predict router before falling back to live KServe inference.
    """
    if not _FEAST_AVAILABLE or get_online_features is None:
        logger.debug("Feast not available — skipping online feature retrieval for %s", ticker)
        return None
    try:
        return get_online_features(ticker.upper())
    except Exception as exc:
        logger.warning(
            "Feast get_online_features failed for %s (%s) — returning None.", ticker.upper(), exc
        )
        return None


async def load_ab_results_from_db(days: int = 30) -> dict | None:
    """Query A/B test assignment results with actual price backfill.

    First backfills actual_price from ohlcv_daily for mature assignments,
    then aggregates per-model accuracy metrics.
    Returns None if DB is unavailable.
    """
    from sqlalchemy import text as sa_text

    from app.models.database import get_async_session, get_engine

    if get_engine() is None:
        return None

    # Step 1: Backfill actual_price for mature assignments
    backfill_query = sa_text("""
        UPDATE ab_test_assignments a
        SET actual_price = d.close, evaluated_at = NOW()
        FROM ohlcv_daily d
        WHERE a.ticker = d.ticker
          AND (a.assigned_at::date + a.horizon_days * INTERVAL '1 day') = d.date
          AND a.actual_price IS NULL
          AND a.evaluated_at IS NULL
    """)

    # Step 2: Aggregate per-model results
    aggregate_query = sa_text("""
        SELECT
            model_id,
            model_name,
            COUNT(*) AS n_assignments,
            COUNT(actual_price) AS n_evaluated,
            AVG(ABS(predicted_price - actual_price))
                FILTER (WHERE actual_price IS NOT NULL) AS mae,
            SQRT(AVG(POWER(predicted_price - actual_price, 2))
                FILTER (WHERE actual_price IS NOT NULL)) AS rmse,
            MIN(assigned_at) AS period_start,
            MAX(assigned_at) AS period_end
        FROM ab_test_assignments
        WHERE assigned_at >= CURRENT_DATE - :days * INTERVAL '1 day'
        GROUP BY model_id, model_name
        ORDER BY n_evaluated DESC
    """)

    try:
        async with get_async_session() as session:
            await session.execute(backfill_query)
            result = await session.execute(aggregate_query, {"days": days})
            rows = result.mappings().all()
    except Exception:
        logger.exception("Failed to query A/B results")
        return None

    models = []
    total_assignments = 0
    total_evaluated = 0
    period_start = None
    period_end = None

    for raw in rows:
        n_assign = raw.get("n_assignments", 0)
        n_eval = raw.get("n_evaluated", 0)
        total_assignments += n_assign
        total_evaluated += n_eval

        ps = raw.get("period_start")
        pe = raw.get("period_end")
        if ps:
            ps_str = ps.isoformat() if hasattr(ps, "isoformat") else str(ps)
            if period_start is None or ps_str < period_start:
                period_start = ps_str
        if pe:
            pe_str = pe.isoformat() if hasattr(pe, "isoformat") else str(pe)
            if period_end is None or pe_str > period_end:
                period_end = pe_str

        models.append({
            "model_id": raw["model_id"],
            "model_name": raw["model_name"],
            "n_assignments": n_assign,
            "n_evaluated": n_eval,
            "mae": round(float(raw["mae"]), 6) if raw.get("mae") is not None else None,
            "rmse": round(float(raw["rmse"]), 6) if raw.get("rmse") is not None else None,
            "directional_accuracy": None,
        })

    return {
        "models": models,
        "total_assignments": total_assignments,
        "total_evaluated": total_evaluated,
        "period_start": period_start,
        "period_end": period_end,
    }
