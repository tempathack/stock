# Phase 12: Linear & Regularized Models - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Train all 6 linear-family sklearn regressors with TimeSeriesSplit cross-validation
and hyperparameter tuning via RandomizedSearchCV. Each model is trained with all 3
scaler variants (standard, quantile, minmax). Results are stored as JSON artifacts.

This phase builds the **core training infrastructure** reused by Phases 13–14.

Files touched:
- `ml/evaluation/metrics.py` — R², MAE, RMSE, MAPE, directional accuracy, fold stability
- `ml/evaluation/cross_validation.py` — TimeSeriesSplit wrapper (≥5 folds, no shuffling)
- `ml/models/model_configs.py` — model configs, search spaces, TrainingResult dataclass
- `ml/pipelines/components/model_trainer.py` — generic training logic
- `ml/evaluation/__init__.py` — re-exports
- `ml/models/__init__.py` — re-exports
- `ml/tests/test_metrics.py` — new
- `ml/tests/test_cross_validation.py` — new
- `ml/tests/test_model_configs.py` — new
- `ml/tests/test_model_trainer.py` — new

Kubeflow component stubs (`data_loader.py`, `feature_engineer.py`, `label_generator.py`,
`evaluator.py`, `model_selector.py`) are **left as stubs** — those are Phases 17–19.

</domain>

<decisions>
## Decisions

### Scaler Strategy
- Train every model with all 3 scaler variants (standard, quantile, minmax)
- Each (model, scaler) combination is a separate training run
- Best variant per model determined by OOS RMSE

### Tuning Strategy
- RandomizedSearchCV with TimeSeriesSplit as `cv` parameter
- `n_iter=30` for tuned models, `scoring="neg_root_mean_squared_error"`
- Models without search spaces (LinearRegression, BayesianRidge) skip tuning

### Search Spaces (MODEL-21)
- Ridge: alpha ∈ np.logspace(-3, 3, 50)
- Lasso: alpha ∈ np.logspace(-4, 1, 50)
- ElasticNet: alpha ∈ np.logspace(-4, 1, 30), l1_ratio ∈ np.linspace(0.1, 0.9, 9)
- HuberRegressor: epsilon ∈ np.linspace(1.1, 2.0, 10)

### Result Storage
- JSON artifacts to disk (not DB — that's Phase 15/registry)
- TrainingResult dataclass with: model_name, scaler_variant, best_params, fold_metrics, oos_metrics, pipeline (pickle path)

### Metrics (computed per fold + aggregated)
- R² (sklearn r2_score)
- MAE (sklearn mean_absolute_error)
- RMSE (sqrt of MSE)
- MAPE (mean absolute percentage error)
- Directional Accuracy (% of predictions matching sign of actual change)
- Fold Stability (std of OOS RMSE across folds)

### TimeSeriesSplit
- n_splits=5 (≥5 per requirement)
- No shuffling (inherent to TimeSeriesSplit)
- Gap=0 (standard setting)

### Pipeline Structure
- `Pipeline([("scaler", ScalerInstance), ("model", Regressor)])`
- Scaler fits inside each CV fold — no leakage

</decisions>

<canonical_refs>
## Canonical References

### Upstream (complete)
- `ml/features/indicators.py` — 14 indicator functions
- `ml/features/lag_features.py` — lag features, rolling stats, target, drop
- `ml/features/transformations.py` — scaler pipeline factory
- `ml/features/__init__.py` — public exports
- `ml/tests/conftest.py` — `sample_ohlcv_df` fixture (250 rows)

### Target files (stubs to implement)
- `ml/evaluation/metrics.py`
- `ml/evaluation/cross_validation.py`
- `ml/models/model_configs.py`
- `ml/pipelines/components/model_trainer.py`

### Downstream consumers (future)
- Phase 13: adds TREE_MODELS to model_configs.py
- Phase 14: adds DISTANCE_NEURAL_MODELS
- Phase 15: uses metrics + training results for ranking/winner selection

</canonical_refs>
