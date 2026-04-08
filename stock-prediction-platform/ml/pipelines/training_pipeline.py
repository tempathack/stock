"""Kubeflow pipeline definition — full 11-step training pipeline."""

from __future__ import annotations

import json
import logging
import os
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from ml.pipelines.components.deployer import deploy_multi_horizon_winners, deploy_winner_model
from ml.pipelines.components.evaluator import (
    evaluate_models,
    generate_comparison_report,
    generate_cv_report,
)
from ml.pipelines.components.feature_engineer import engineer_features
from ml.pipelines.components.label_generator import generate_labels, generate_multi_horizon_labels
from ml.pipelines.components.model_trainer import (
    _build_pipeline,
    prepare_training_data,
    train_all_models,
    train_linear_models,
)
from ml.models.ensemble import StackingEnsemble
from ml.pipelines.components.model_selector import select_and_persist_winner

if TYPE_CHECKING:
    from ml.pipelines.components.data_loader import DBSettings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PIPELINE_VERSION = "1.2.0"
DEFAULT_HORIZONS = [1, 7, 30]

# ---------------------------------------------------------------------------
# Run result dataclass
# ---------------------------------------------------------------------------


@dataclass
class PipelineRunResult:
    """Full audit trail for a single pipeline execution."""

    run_id: str
    pipeline_version: str
    started_at: str
    completed_at: str = ""
    status: str = "running"
    steps_completed: list[str] = field(default_factory=list)
    n_tickers: int = 0
    n_models_trained: int = 0
    winner_info: dict | None = None
    deploy_info: dict | None = None
    ensemble_info: dict | None = None
    horizon_results: dict[int, dict] | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _rebuild_pipelines(
    results: list,
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> dict[str, Pipeline]:
    """Reconstruct and refit pipelines from training results."""
    from ml.models.model_configs import (
        BOOSTER_MODELS,
        DISTANCE_NEURAL_MODELS,
        LINEAR_MODELS,
        SKTIME_MODELS,
        TREE_MODELS,
        ModelConfig,
    )

    all_configs: dict[str, ModelConfig] = {
        **LINEAR_MODELS,
        **TREE_MODELS,
        **BOOSTER_MODELS,
        **DISTANCE_NEURAL_MODELS,
        **{cfg.name: cfg for cfg in SKTIME_MODELS},
    }

    pipelines: dict[str, Pipeline] = {}
    for result in results:
        if result.model_name == "stacking_ensemble":
            continue
        config = all_configs.get(result.model_name)
        if config is None:
            logger.warning("No config found for model %s — skipping rebuild", result.model_name)
            continue
        pipeline = _build_pipeline(config, result.scaler_variant)
        if result.best_params:
            pipeline.set_params(
                **{f"model__{k}": v for k, v in result.best_params.items()}
            )
        pipeline.fit(X_train, y_train)
        key = f"{result.model_name}_{result.scaler_variant}"
        pipelines[key] = pipeline

    return pipelines


def _save_run_result(result: PipelineRunResult, registry_dir: str) -> Path | str:
    """Persist run result as JSON in ``{registry_dir}/runs/``.

    Uses S3 when ``STORAGE_BACKEND=s3``, otherwise local filesystem.
    """
    payload = json.dumps(result.to_dict(), indent=2, default=str)
    filename = f"pipeline_run_{result.run_id}.json"

    if os.environ.get("STORAGE_BACKEND", "local").lower() == "s3":
        from ml.models.s3_storage import S3Storage

        s3 = S3Storage.from_env()
        bucket = os.environ.get("MINIO_BUCKET_MODELS", "model-artifacts")
        key = f"{registry_dir}/runs/{filename}"
        s3.upload_bytes(payload.encode(), bucket, key)
        uri = f"s3://{bucket}/{key}"
        logger.info("Saved run result → %s", uri)
        return uri

    runs_dir = Path(registry_dir) / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / filename
    with open(path, "w") as f:
        f.write(payload)
    logger.info("Saved run result → %s", path)
    return path


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def run_training_pipeline(
    tickers: list[str] | None = None,
    db_settings: DBSettings | None = None,
    data_dict: dict[str, pd.DataFrame] | None = None,
    registry_dir: str = "model_registry",
    serving_dir: str = "/models/active",
    target_col: str = "target_7d",
    horizon: int = 7,
    test_ratio: float = 0.2,
    n_splits: int = 5,
    skip_shap: bool = False,
    enable_ensemble: bool = True,
    use_feature_store: bool = False,
    horizons: list[int] | None = None,
    linear_only: bool = False,
    use_feast_data: bool = False,
    include_sktime: bool = True,
    include_sktime_regression: bool = True,
    use_fred: bool = False,
) -> PipelineRunResult:
    """Execute the full 12-step training pipeline.

    Accepts either ``tickers`` + ``db_settings`` (production) or ``data_dict``
    (test/pre-loaded).  All 12 steps are executed sequentially with step-level
    tracking and run result persistence.

    When *horizons* is provided (e.g. ``[1, 7, 30]``), the pipeline enters
    multi-horizon mode: steps 4–12 are run once per horizon with separate
    registry and serving directories.  When *horizons* is ``None``, the
    legacy single-horizon mode is used for full backward compatibility.

    Raises ``ValueError`` if neither ``tickers`` nor ``data_dict`` is provided.
    """
    if data_dict is None and tickers is None:
        raise ValueError("Provide either 'tickers' or 'data_dict'.")

    run_id = uuid.uuid4().hex[:12]
    started_at = datetime.now(timezone.utc).isoformat()

    result = PipelineRunResult(
        run_id=run_id,
        pipeline_version=PIPELINE_VERSION,
        started_at=started_at,
    )
    logger.info(json.dumps({"event": "training_start", "run_id": run_id, "tickers": tickers, "horizons": horizons}))

    try:
        # Step 1: Load data
        _feast_mode = False
        if data_dict is None:
            if use_feast_data:
                from ml.pipelines.components.data_loader import load_feast_data
                import pandas as _pd
                feast_df = load_feast_data(
                    tickers=tickers,
                    start_date="2020-01-01",
                    end_date=_pd.Timestamp.now().strftime("%Y-%m-%d"),
                )
                # Convert flat DataFrame to per-ticker dict expected by downstream steps
                data_dict = {
                    t: feast_df[feast_df["ticker"] == t].drop(columns=["ticker"], errors="ignore")
                    for t in feast_df["ticker"].unique()
                }
                _feast_mode = True
                result.steps_completed.append("load_feast_data")
                logger.info("Step 1/12 load_feast_data (Feast offline) — %d tickers", len(data_dict))
            else:
                from ml.pipelines.components.data_loader import load_data, load_yfinance_macro
                data_dict = load_data(tickers=tickers, settings=db_settings)
                result.steps_completed.append("load_data")
                logger.info("Step 1/12 load_data — %d tickers", len(data_dict))

                # Step 1b: Fetch and join yfinance macro features per ticker
                try:
                    import pandas as _pd
                    _start = "2019-01-01"
                    _end = _pd.Timestamp.now().strftime("%Y-%m-%d")
                    macro_df = load_yfinance_macro(list(data_dict.keys()), _start, _end)
                    _macro_cols = ["vix", "spy_return", "sector_return", "high52w_pct", "low52w_pct"]
                    for _ticker, _df in data_dict.items():
                        _macro_ticker = macro_df[macro_df["ticker"] == _ticker][_macro_cols]
                        joined = _df.join(_macro_ticker, how="left")
                        # Fill NaN macro columns with 0 when fetch returned no rows
                        # (prevents drop_incomplete_rows from removing all training rows)
                        for _col in _macro_cols:
                            if _col in joined.columns and joined[_col].isna().all():
                                joined[_col] = 0.0
                        data_dict[_ticker] = joined
                    logger.info("Step 1b/12 load_yfinance_macro — macro features joined for %d tickers", len(data_dict))
                except Exception as _exc:
                    logger.warning("Step 1b/12 load_yfinance_macro — failed (%s); continuing without macro features", _exc)

                # Step 1c: FRED macro — create table and upsert latest data (gated on use_fred)
                if use_fred:
                    try:
                        from ml.pipelines.components.data_loader import (
                            create_fred_macro_table,
                            fetch_fred_macro,
                            write_fred_macro_to_db,
                        )
                        create_fred_macro_table()
                        fred_df = fetch_fred_macro(start_date=_start, end_date=_end)
                        write_fred_macro_to_db(fred_df)
                        logger.info("Step 1c/12 FRED macro: wrote %d rows to feast_fred_macro.", len(fred_df))
                    except Exception as _exc:
                        logger.warning("Step 1c/12 FRED macro — failed (%s); continuing without FRED features", _exc)
                else:
                    logger.info("Step 1c/12 FRED macro — skipped (use_fred=False)")

                # Step 1d: join FRED macro features from DB into each ticker's DataFrame (gated on use_fred)
                if use_fred:
                    try:
                        from ml.pipelines.components.data_loader import (
                            _FRED_COLS as _FRED_COLS_LIST,
                            load_fred_macro_from_db,
                        )
                        fred_wide = load_fred_macro_from_db(start_date=_start, end_date=_end, settings=db_settings)
                        if not fred_wide.empty:
                            for _ticker, _df in data_dict.items():
                                _df_copy = _df.copy()
                                if not isinstance(_df_copy.index, pd.DatetimeIndex):
                                    _df_copy.index = pd.to_datetime(_df_copy.index)
                                joined = _df_copy.join(fred_wide, how="left")
                                for _col in _FRED_COLS_LIST:
                                    if _col in joined.columns:
                                        joined[_col] = joined[_col].ffill().fillna(0.0)
                                data_dict[_ticker] = joined
                            logger.info(
                                "Step 1d/12 FRED DB join — joined %d FRED columns for %d tickers",
                                len(fred_wide.columns), len(data_dict),
                            )
                        else:
                            logger.warning("Step 1d/12 FRED DB join — feast_fred_macro empty; skipping join")
                    except Exception as _exc:
                        logger.warning("Step 1d/12 FRED DB join — failed (%s); continuing without FRED columns", _exc)
                else:
                    logger.info("Step 1d/12 FRED DB join — skipped (use_fred=False)")
        else:
            # Pre-loaded data_dict provided — track step for consistent step count
            result.steps_completed.append("load_data")
            logger.info("Step 1/12 load_data (pre-loaded) — %d tickers", len(data_dict))
        result.n_tickers = len(data_dict)

        # Step 2: Engineer features
        if _feast_mode:
            # Feast path: features already pre-computed (all 34 columns present)
            enriched = data_dict
            result.steps_completed.append("engineer_features")
            logger.info("Step 2/12 engineer_features (Feast mode — passthrough) — done")
            logger.info(json.dumps({"event": "feature_engineering_complete", "run_id": run_id, "source": "feast"}))
        else:
            fs_settings = db_settings
            if use_feature_store and fs_settings is None:
                from ml.pipelines.components.data_loader import DBSettings as _DBS
                fs_settings = _DBS.from_env()
            try:
                enriched = engineer_features(
                    data_dict,
                    use_feature_store=use_feature_store,
                    db_settings=fs_settings,
                )
            except Exception as exc:
                logger.warning("Feature store failed (%s) — falling back to on-the-fly.", exc)
                enriched = engineer_features(data_dict)
            source = "feature_store" if use_feature_store else "on-the-fly"
            result.steps_completed.append("engineer_features")
            logger.info("Step 2/12 engineer_features (source: %s) — done", source)
            logger.info(json.dumps({"event": "feature_engineering_complete", "run_id": run_id, "source": source}))

        # Step 3: Generate labels
        if horizons is not None:
            # ── Multi-horizon mode ──
            multi = generate_multi_horizon_labels(enriched, horizons=horizons)
            labelled = multi["data"]
            feature_names = multi["feature_names"]
            target_cols = multi["target_cols"]
            result.steps_completed.append("generate_labels")
            logger.info(
                "Step 3/12 generate_labels (multi-horizon) — %d features, horizons=%s",
                len(feature_names), horizons,
            )

            horizon_results: dict[int, dict] = {}
            total_models = 0

            for h in horizons:
                h_target_col = f"target_{h}d"
                h_registry_dir = f"{registry_dir}/horizon_{h}d"
                h_serving_dir = f"{serving_dir}/horizon_{h}d"
                logger.info("══ Horizon %dd ══ Training models...", h)

                try:
                    # Step 4: Prepare training data
                    X_train, y_train, X_test, y_test = prepare_training_data(
                        labelled, feature_names, h_target_col, test_ratio,
                    )

                    # Step 5: Train all models
                    if linear_only:
                        logger.info("LINEAR_ONLY mode — skipping tree/booster models for speed")
                        results_list = train_linear_models(X_train, y_train, X_test, y_test, n_splits)
                    else:
                        results_list = train_all_models(X_train, y_train, X_test, y_test, n_splits, include_sktime=include_sktime, include_sktime_regression=include_sktime_regression)
                    pipelines = _rebuild_pipelines(results_list, X_train, y_train)
                    total_models += len(results_list)

                    # Step 6: Cross-validation report
                    cv_report = generate_cv_report(results_list)

                    # Step 7: Evaluate / rank models
                    ranked = evaluate_models(results_list)

                    # Step 8: Ensemble stacking
                    if enable_ensemble:
                        try:
                            ensemble = StackingEnsemble(
                                top_n=5, meta_learner_alpha=1.0, cv=n_splits,
                            )
                            ensemble.build(results_list, pipelines)
                            ensemble.fit(X_train, y_train)
                            ensemble_result = ensemble.evaluate(X_test, y_test)
                            results_list.append(ensemble_result)
                            pipelines["stacking_ensemble_meta_ridge"] = (
                                ensemble.get_stacking_model()
                            )
                        except Exception as exc:
                            logger.warning(
                                "Horizon %dd ensemble_stacking — failed (%s)", h, exc,
                            )

                    # Step 9: Comparison report
                    comparison = generate_comparison_report(ranked)

                    # Step 10: Explainability
                    if not skip_shap:
                        try:
                            from ml.pipelines.components.explainer import explain_top_models
                            explain_top_models(
                                results_list, pipelines, X_test, feature_names, h_registry_dir,
                            )
                        except (ImportError, Exception) as exc:
                            logger.warning("Horizon %dd explainability — skipped (%s)", h, exc)

                    # Step 11: Select and persist winner
                    winner_info_h = select_and_persist_winner(
                        results_list, pipelines, feature_names, h_registry_dir,
                    )

                    # Step 12: Deploy winner
                    deploy_info_h = deploy_winner_model(h_registry_dir, h_serving_dir)

                    horizon_results[h] = {
                        "winner_name": winner_info_h.get("winner_name"),
                        "winner_rmse": winner_info_h.get("winner_rmse"),
                        "n_models": len(results_list),
                    }
                    result.steps_completed.append(f"horizon_{h}d_complete")
                    logger.info("══ Horizon %dd ══ Complete — winner: %s", h, winner_info_h.get("winner_name"))
                    logger.info(json.dumps({"event": "model_fit_complete", "run_id": run_id, "horizon_days": h, "model_name": winner_info_h.get("winner_name"), "rmse": winner_info_h.get("winner_rmse")}))
                    logger.info(json.dumps({"event": "model_saved", "run_id": run_id, "horizon_days": h, "registry_dir": h_registry_dir, "serving_dir": h_serving_dir}))

                except Exception as exc:
                    logger.error("══ Horizon %dd ══ FAILED: %s", h, exc)
                    horizon_results[h] = {"error": str(exc)}
                    continue

            result.horizon_results = horizon_results
            result.n_models_trained = total_models

            # Deploy multi-horizon manifest
            try:
                deploy_info = deploy_multi_horizon_winners(registry_dir, serving_dir, horizons)
                result.deploy_info = deploy_info
            except Exception as exc:
                logger.warning("Multi-horizon deploy manifest failed: %s", exc)

        else:
            # ── Legacy single-horizon mode ──
            labelled, feature_names = generate_labels(enriched, horizon=horizon)
            result.steps_completed.append("generate_labels")
            logger.info("Step 3/12 generate_labels — %d features", len(feature_names))

            # Step 4: Prepare training data
            X_train, y_train, X_test, y_test = prepare_training_data(
                labelled, feature_names, target_col, test_ratio,
            )
            result.steps_completed.append("prepare_training_data")
            logger.info(
                "Step 4/12 prepare_training_data — train=%d test=%d",
                len(X_train), len(X_test),
            )

            # Step 5: Train all models
            if linear_only:
                logger.info("LINEAR_ONLY mode — skipping tree/booster models for speed")
                results_list = train_linear_models(X_train, y_train, X_test, y_test, n_splits)
            else:
                results_list = train_all_models(X_train, y_train, X_test, y_test, n_splits, include_sktime=include_sktime, include_sktime_regression=include_sktime_regression)
            pipelines = _rebuild_pipelines(results_list, X_train, y_train)
            result.n_models_trained = len(results_list)
            result.steps_completed.append("train_models")
            logger.info("Step 5/12 train_models — %d models", len(results_list))

            # Step 6: Cross-validation report
            cv_report = generate_cv_report(results_list)
            result.steps_completed.append("cross_validation")
            logger.info("Step 6/12 cross_validation — done")

            # Step 7: Evaluate / rank models
            ranked = evaluate_models(results_list)
            result.steps_completed.append("evaluate_models")
            logger.info("Step 7/12 evaluate_models — %d ranked", len(ranked))

            # Step 8: Ensemble stacking
            if enable_ensemble:
                try:
                    ensemble = StackingEnsemble(
                        top_n=5, meta_learner_alpha=1.0, cv=n_splits,
                    )
                    ensemble.build(results_list, pipelines)
                    ensemble.fit(X_train, y_train)
                    ensemble_result = ensemble.evaluate(X_test, y_test)
                    results_list.append(ensemble_result)
                    pipelines["stacking_ensemble_meta_ridge"] = (
                        ensemble.get_stacking_model()
                    )
                    result.ensemble_info = {
                        "base_models": ensemble.base_model_names,
                        "ensemble_rmse": ensemble_result.oos_metrics["rmse"],
                        "top_n": 5,
                    }
                    logger.info(
                        "Step 8/12 ensemble_stacking — RMSE=%.6f",
                        ensemble_result.oos_metrics["rmse"],
                    )
                except Exception as exc:
                    logger.warning(
                        "Step 8/12 ensemble_stacking — failed (%s)", exc,
                    )
                    result.ensemble_info = {"error": str(exc)}
            else:
                logger.info("Step 8/12 ensemble_stacking — SKIPPED")
            result.steps_completed.append("ensemble_stacking")

            # Step 9: Comparison report
            comparison = generate_comparison_report(ranked)
            result.steps_completed.append("model_comparison")
            logger.info("Step 9/12 model_comparison — done")

            # Step 10: Explainability (optional)
            if skip_shap:
                logger.info("Step 10/12 explainability — SKIPPED (skip_shap=True)")
            else:
                try:
                    from ml.pipelines.components.explainer import explain_top_models

                    explain_top_models(
                        results_list, pipelines, X_test, feature_names, registry_dir,
                    )
                    logger.info("Step 10/12 explainability — done")
                except (ImportError, Exception) as exc:
                    logger.warning("Step 10/12 explainability — skipped (%s)", exc)
            result.steps_completed.append("explainability")

            # Step 11: Select and persist winner
            winner_info = select_and_persist_winner(
                results_list, pipelines, feature_names, registry_dir,
            )
            result.winner_info = winner_info
            result.steps_completed.append("select_winner")
            logger.info("Step 11/12 select_winner — %s", winner_info.get("winner_name"))

            # Step 12: Deploy winner
            deploy_info = deploy_winner_model(registry_dir, serving_dir)
            result.deploy_info = deploy_info
            result.steps_completed.append("deploy_model")
            logger.info("Step 12/12 deploy_model — done")

        # Finalise
        result.completed_at = datetime.now(timezone.utc).isoformat()
        result.status = "completed"
        _save_run_result(result, registry_dir)
        logger.info("Pipeline run %s completed successfully.", run_id)

    except Exception:
        result.completed_at = datetime.now(timezone.utc).isoformat()
        result.status = "failed"
        result.error = traceback.format_exc()
        _save_run_result(result, registry_dir)
        logger.error(json.dumps({"event": "training_error", "run_id": run_id, "error": result.error}))
        raise

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": %(message)s}',
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    parser = argparse.ArgumentParser(
        description="Run the stock prediction training pipeline",
    )
    parser.add_argument("--tickers", type=str, help="Comma-separated ticker list")
    parser.add_argument("--registry-dir", default=os.environ.get("MODEL_REGISTRY_DIR", "model_registry"))
    parser.add_argument("--serving-dir", default=os.environ.get("SERVING_DIR", "/models/active"))
    parser.add_argument("--skip-shap", action="store_true")
    parser.add_argument("--linear-only", action="store_true",
        help="Train only linear models (faster, for E2E validation). "
             "Also enabled via LINEAR_ONLY=true env var.")
    parser.add_argument(
        "--horizons", type=str, default=None,
        help="Comma-separated horizon days for multi-horizon mode (e.g. 1,7,30)",
    )
    parser.add_argument(
        "--skip-sktime",
        action="store_true",
        default=False,
        help="Skip sktime statistical forecasting model training.",
    )
    parser.add_argument(
        "--skip-sktime-regression",
        action="store_true",
        default=False,
        help="Skip sktime time series regression model training (MiniROCKET, ROCKET, etc.).",
    )
    parser.add_argument(
        "--use-fred",
        action="store_true",
        default=False,
        help="Fetch FRED macro series, write to feast_fred_macro, and join 14 macro columns "
             "into the training feature matrix. Also enabled via USE_FRED=true env var.",
    )
    args = parser.parse_args()

    tickers_str = args.tickers or os.environ.get("TICKERS")
    tickers = tickers_str.split(",") if tickers_str else None
    horizons_list = (
        [int(h.strip()) for h in args.horizons.split(",")]
        if args.horizons
        else None
    )
    linear_only = args.linear_only or os.environ.get("LINEAR_ONLY", "").lower() in ("1", "true", "yes")
    use_fred = args.use_fred or os.environ.get("USE_FRED", "").lower() in ("1", "true", "yes")
    run_result = run_training_pipeline(
        tickers=tickers,
        registry_dir=args.registry_dir,
        serving_dir=args.serving_dir,
        skip_shap=args.skip_shap,
        horizons=horizons_list,
        linear_only=linear_only,
        include_sktime=not args.skip_sktime,
        include_sktime_regression=not args.skip_sktime_regression,
        use_fred=use_fred,
    )
    logger.info(json.dumps({"event": "pipeline_complete", "result": run_result.to_dict()}, default=str))
