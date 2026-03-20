# Phase 18: Kubeflow Pipeline — Training & Eval Components — Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the pipeline-level orchestration components for steps 4–7 of the 11-step
Kubeflow training pipeline: data preparation (DataFrame → numpy), model training,
cross-validation reporting, evaluation/ranking, and model comparison.

This phase bridges the per-ticker DataFrames from Phase 17 (`label_generator`
output) to the model training and evaluation infrastructure built in Phases 12–15.
The core ML logic already exists — this phase adds the **pipeline glue** that
consolidates multi-ticker data, calls the training functions, and surfaces CV /
ranking / comparison results as distinct pipeline step outputs.

### Pipeline steps owned by this phase (4 of 11)

| Step | Req   | Component           | Input                                   | Output                                                     |
|------|-------|---------------------|-----------------------------------------|------------------------------------------------------------|
| 4    | KF-05 | `train_models`      | data_dict, feature_names                | `list[TrainingResult]`, `dict[str, Pipeline]`              |
| 5    | KF-06 | `cross_validation`  | `list[TrainingResult]`                  | CV fold report (per-model per-fold metrics)                |
| 6    | KF-07 | `evaluation`        | `list[TrainingResult]`                  | `list[RankedModel]`                                        |
| 7    | KF-08 | `model_comparison`  | `list[RankedModel]`                     | Comparison report dict                                     |

### Files touched

- `ml/pipelines/components/model_trainer.py` — **update** to return fitted pipelines alongside results
- `ml/pipelines/components/evaluator.py` — already complete, no changes needed
- `ml/pipelines/components/__init__.py` — **update** exports for new functions
- `ml/tests/test_model_trainer.py` — **update** tests for new pipeline-facing functions
- `ml/tests/test_evaluator.py` — already complete, no changes needed

</domain>

<decisions>
## Decisions

### Component Architecture: Same pattern as Phase 17 — Pure Python Functions

All components remain plain Python functions with no KFP SDK dependency.
They will be wrapped in `@dsl.component` decorators in Phase 20.

### Data Consolidation: Multi-ticker → Single Training Set

The `label_generator` output is `dict[str, pd.DataFrame]` (per-ticker).
Model training requires a single `(X_train, y_train, X_test, y_test)` split.

New function `prepare_training_data()` in `model_trainer.py`:
- Concatenates all per-ticker DataFrames into one large DataFrame
- Sorts by DatetimeIndex to maintain temporal ordering
- Performs a temporal train/test split (default 80/20)
- Extracts target column (`target_7d`) from feature columns
- Returns `(X_train, y_train, X_test, y_test)` as numpy arrays

This keeps the temporal-split logic in one place and ensures no data leakage
from future dates into the training set.

### Pipeline-level `train_all_models_pipeline()` function

New top-level function that serves as the KF-05 component entry point:
- Takes `data_dict: dict[str, pd.DataFrame]` and `feature_names: list[str]`
- Calls `prepare_training_data()` to get numpy arrays
- Calls existing `train_all_models()` to train all model families
- Collects fitted pipelines by re-fitting the best config for each result
- Returns `(list[TrainingResult], dict[str, Pipeline])`

**Pipeline collection strategy:** The existing `train_single_model()` returns
only `TrainingResult`, not the fitted pipeline. Rather than refactoring the
deeply-tested function, `train_all_models_pipeline()` will call `train_single_model()`
to get results, then reconstruct and fit the winning pipeline for each model.
This is clean because:
1. `_build_pipeline(config, scaler)` already exists and is public enough to reuse
2. For tuned models, `TrainingResult.best_params` captures the best params
3. One extra fit per model is negligible vs. the CV/tuning that already ran

### Cross-Validation Report Component (KF-06)

The CV fold metrics are already embedded in each `TrainingResult.fold_metrics`.
The KF-06 component extracts and formats these into a structured report:

```python
def generate_cv_report(results: list[TrainingResult]) -> dict:
    """Extract per-model, per-fold CV metrics into a structured report."""
```

Returns a dict with:
- `total_models`: int
- `n_folds`: int (from first result)
- `models`: list of per-model entries with fold_metrics, mean/std per metric, fold_stability
- `aggregate`: summary statistics across all models

This is a **new function** in `evaluator.py` — it complements the existing
`evaluate_models()` (KF-07) and `generate_comparison_report()` (KF-08).

### Evaluation (KF-07) and Model Comparison (KF-08)

Already implemented in `evaluator.py`:
- `evaluate_models()` → `list[RankedModel]` (KF-07)
- `generate_comparison_report()` → dict (KF-08)

No code changes needed for these. The `__init__.py` already exports them.
Tests already pass. Simply verify they work with the pipeline data flow.

### Train/Test Split Ratio

Default `test_ratio=0.2` — last 20% of time-ordered data held out.
This is configurable but matches the pattern used by the existing
`train_single_model()` callers (Phase 12–14 tests all used 80/20).

### Target column name

Assumed to be `target_7d` (matching `label_generator` with default `horizon=7`).
The `prepare_training_data()` function accepts `target_col` as a parameter
for flexibility with non-default horizons.

### Test Strategy

Tests split into two concerns:

**Plan 18-01 (data prep + training orchestration):**
- `prepare_training_data()`: consolidation, temporal ordering, split ratios, numpy output, edge cases
- `train_all_models_pipeline()`: returns correct types, collects pipelines, pipelines are fitted
- Uses `sample_ohlcv_df` conftest fixture processed through `engineer_features` + `generate_labels`

**Plan 18-02 (CV report):**
- `generate_cv_report()`: structure, per-model entries, fold counts, aggregate stats
- Uses synthetic `TrainingResult` objects (same pattern as existing `test_evaluator.py`)

</decisions>

<canonical_refs>
## Canonical References

### Upstream (Phase 17, complete)
- `ml/pipelines/components/data_loader.py` — `load_data()` → `dict[str, pd.DataFrame]`
- `ml/pipelines/components/feature_engineer.py` — `engineer_features()` → `dict[str, pd.DataFrame]`
- `ml/pipelines/components/label_generator.py` — `generate_labels()` → `(dict[str, pd.DataFrame], list[str])`

### Core ML (Phases 12–15, complete)
- `ml/pipelines/components/model_trainer.py` — `train_single_model()`, `train_all_models()`, `_build_pipeline()`, `save_training_results()`
- `ml/pipelines/components/evaluator.py` — `evaluate_models()`, `generate_comparison_report()`
- `ml/evaluation/cross_validation.py` — `create_time_series_cv()`, `walk_forward_evaluate()`
- `ml/evaluation/ranking.py` — `rank_models()`, `select_winner()`, `RankedModel`, `WinnerResult`
- `ml/evaluation/metrics.py` — `compute_all_metrics()`
- `ml/models/model_configs.py` — `ModelConfig`, `TrainingResult`, `LINEAR_MODELS`, `TREE_MODELS`, `BOOSTER_MODELS`, `DISTANCE_NEURAL_MODELS`
- `ml/features/transformations.py` — `SCALER_VARIANTS`, `build_scaler_pipeline()`

### Peer components (complete, pattern reference)
- `ml/pipelines/components/model_selector.py` — `select_and_persist_winner()` (takes `list[TrainingResult]` + `dict[str, Pipeline]`)
- `ml/pipelines/components/explainer.py` — `explain_top_models()` (takes `list[TrainingResult]` + `dict[str, Pipeline]`)

### Downstream (Phases 19–20)
- Phase 19: `explainability`, `winner_selection`, `model_persistence`, `deployment` components — consume `list[TrainingResult]` + `dict[str, Pipeline]`
- Phase 20: Full KFP DSL pipeline definition wrapping all 11 components

### Test infrastructure
- `ml/tests/conftest.py` — `sample_ohlcv_df()` fixture (250-row synthetic OHLCV)
- `ml/tests/test_model_trainer.py` — existing tests for `train_single_model`, batch functions, persistence
- `ml/tests/test_evaluator.py` — existing tests for `evaluate_models`, `generate_comparison_report`

</canonical_refs>
