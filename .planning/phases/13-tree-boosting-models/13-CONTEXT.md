# Phase 13: Tree-Based & Boosting Models — Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Add 6 sklearn tree/ensemble regressors + 3 optional boosters (XGBoost, LightGBM, CatBoost)
to the model training infrastructure. Reuses all Phase 12 infrastructure: `train_single_model`,
`_build_pipeline`, `ModelConfig`, `TrainingResult`, `register_model_family`, metrics, CV.

Each model trained with all 3 scaler variants → up to 9 × 3 = 27 training runs.

Files touched:
- `ml/models/model_configs.py` — add TREE_MODELS, BOOSTER_MODELS dicts + registration
- `ml/models/__init__.py` — export new dicts
- `ml/pipelines/components/model_trainer.py` — add `train_tree_models()` batch function
- `ml/tests/test_model_configs.py` — extend with tree + booster config tests
- `ml/tests/test_model_trainer.py` — extend with tree trainer tests

</domain>

<decisions>
## Decisions

### Sklearn Tree Models (6 core)
- RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor,
  ExtraTreesRegressor, DecisionTreeRegressor, AdaBoostRegressor
- All set `random_state=42` in default_params for reproducibility

### Optional Boosters (3)
- XGBoost (XGBRegressor), LightGBM (LGBMRegressor), CatBoost (CatBoostRegressor)
- Conditional imports via try/except — only added if package installed
- CatBoost: `verbose=0` in default_params to suppress training output
- XGBoost: `verbosity=0`
- LightGBM: `verbose=-1`
- All confirmed installed: xgboost 3.2.0, lightgbm 4.6.0, catboost 1.2.10

### Search Spaces
- RandomForest: n_estimators, max_depth, min_samples_split, max_features (n_iter=50)
- GradientBoosting: n_estimators, learning_rate, max_depth, subsample (n_iter=50)
- HistGradientBoosting: learning_rate, max_iter, max_depth (n_iter=30)
- ExtraTrees: n_estimators, max_depth (n_iter=30)
- DecisionTree: max_depth, min_samples_split (no tuning — small grid, direct fit)
- AdaBoost: n_estimators, learning_rate (n_iter=30)
- XGBoost: n_estimators, learning_rate, max_depth, subsample, colsample_bytree (n_iter=50)
- LightGBM: n_estimators, learning_rate, num_leaves, max_depth (n_iter=50)
- CatBoost: iterations, learning_rate, depth (n_iter=30)

### Registration
- `register_model_family("tree", TREE_MODELS)` at module level
- `register_model_family("booster", BOOSTER_MODELS)` at module level (only populated entries)

### Reuse
- `train_single_model()` from Phase 12 handles everything
- `train_tree_models()` follows same pattern as `train_linear_models()`

</decisions>

<canonical_refs>
## Canonical References

### Upstream (Phase 12, complete)
- `ml/models/model_configs.py` — ModelConfig, TrainingResult, LINEAR_MODELS, register_model_family
- `ml/pipelines/components/model_trainer.py` — train_single_model, _build_pipeline, save_training_results
- `ml/evaluation/metrics.py` — compute_all_metrics
- `ml/evaluation/cross_validation.py` — create_time_series_cv, walk_forward_evaluate
- `ml/features/transformations.py` — SCALER_VARIANTS, build_scaler_pipeline

### Downstream
- Phase 14: adds DISTANCE_NEURAL_MODELS
- Phase 15: uses all training results for ranking/winner selection

</canonical_refs>
