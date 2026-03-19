# Phase 14: Distance, SVM & Neural Models — Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Add 3 sklearn regressors (KNeighborsRegressor, SVR, MLPRegressor) to the model training
infrastructure. Reuses all Phase 12–13 infrastructure: `train_single_model`, `_build_pipeline`,
`ModelConfig`, `TrainingResult`, `register_model_family`, metrics, CV.

Each model trained with all 3 scaler variants → 3 × 3 = 9 training runs.

Files touched:
- `ml/models/model_configs.py` — add DISTANCE_NEURAL_MODELS dict + registration
- `ml/models/__init__.py` — export new dict
- `ml/pipelines/components/model_trainer.py` — add `train_distance_neural_models()` batch fn + update `train_all_models()`
- `ml/tests/test_model_configs.py` — extend with distance/neural config tests
- `ml/tests/test_model_trainer.py` — extend with distance/neural trainer tests

</domain>

<decisions>
## Decisions

### Models (3)
- **KNeighborsRegressor** (MODEL-13): Distance-based regressor. `algorithm='auto'` default.
- **SVR with RBF kernel** (MODEL-14): `kernel='rbf'` in default_params. Highly sensitive to feature scaling — pipeline scaler handles this.
- **MLPRegressor** (MODEL-15): Neural network regressor. `early_stopping=True`, `n_iter_no_change=10`, `max_iter=500` to bound wall time (success criteria #4).

### Search Spaces
- KNeighborsRegressor: n_neighbors [3,5,7,9,11,15,21], weights [uniform, distance], metric [euclidean, manhattan]; n_iter=30
- SVR: C logspace(-2, 2, 10), gamma [scale, auto, 0.001, 0.01, 0.1], epsilon linspace(0.01, 0.5, 10); n_iter=30
- MLPRegressor: hidden_layer_sizes [(64,), (128,), (64,32), (128,64)], alpha logspace(-5, -1, 10), learning_rate_init [0.001, 0.005, 0.01]; n_iter=30

### Family Registration
- Register as `_MODEL_FAMILIES["distance_neural"]` — consistent with existing "linear", "tree", "booster" families

### Scaling Sensitivity
- SVR with RBF is extremely sensitive to feature scale — StandardScaler typically best, but all 3 variants tested per convention
- KNN also benefits from scaling; MLPRegressor requires it for convergence

### MLP Wall Time Guard
- `early_stopping=True` + `n_iter_no_change=10` ensures MLP doesn't run forever
- `max_iter=500` as hard ceiling in default_params

### Existing Infrastructure Reused (no changes needed)
- `train_single_model()` — works with any sklearn-compatible estimator
- `_build_pipeline()` — scaler + model pipeline construction
- `walk_forward_evaluate()` — TimeSeriesSplit CV metrics
- `RandomizedSearchCV` — hyperparameter tuning with `neg_root_mean_squared_error`
- `SCALER_VARIANTS` — standard, quantile, minmax
</decisions>
