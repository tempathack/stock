# Phase 20: Kubeflow Pipeline — Full Definition & Trigger — Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Assemble all 11 pure-Python pipeline components (Phases 17–19) into an
end-to-end training pipeline orchestrator and a drift-triggered retraining
entry point. Add Parquet-based serialisation for inter-component data
transfer, pipeline versioning/run tracking, and a KFP DSL pipeline definition
that can be compiled and submitted to Kubeflow Pipelines.

### Requirements covered

| Req    | Description                                                  |
|--------|--------------------------------------------------------------|
| KF-13  | Full pipeline definition (`training_pipeline.py`)            |
| KF-14  | Pipeline is reproducible and versioned                       |
| KF-15  | Pipeline can be triggered manually or by drift detection     |

### Files touched

- `ml/pipelines/training_pipeline.py` — **rewrite** from stub → full orchestrator + KFP DSL pipeline
- `ml/pipelines/drift_pipeline.py` — **rewrite** from stub → drift-triggered retraining entry point
- `ml/pipelines/__init__.py` — **update** exports
- `ml/pipelines/serialization.py` — **create** Parquet I/O helpers for inter-component data transfer
- `ml/tests/test_training_pipeline.py` — **create** orchestrator unit + integration tests
- `ml/tests/test_drift_pipeline.py` — **create** drift trigger tests
- `ml/tests/test_serialization.py` — **create** Parquet round-trip tests

### What already exists (no changes needed)

- `ml/pipelines/components/data_loader.py` — `load_data()`, `load_ticker_data()`, `DBSettings` (Phase 17) ✓
- `ml/pipelines/components/feature_engineer.py` — `engineer_features()` (Phase 17) ✓
- `ml/pipelines/components/label_generator.py` — `generate_labels()` (Phase 17) ✓
- `ml/pipelines/components/model_trainer.py` — `prepare_training_data()`, `train_all_models_pipeline()` (Phase 18) ✓
- `ml/pipelines/components/evaluator.py` — `evaluate_models()`, `generate_comparison_report()`, `generate_cv_report()` (Phase 18) ✓
- `ml/pipelines/components/explainer.py` — `explain_top_models()` (Phase 16) ✓
- `ml/pipelines/components/model_selector.py` — `select_and_persist_winner()` (Phase 15) ✓
- `ml/pipelines/components/deployer.py` — `deploy_winner_model()` (Phase 19) ✓
- `ml/models/registry.py` — `ModelRegistry` with activation methods (Phase 19) ✓
- `k8s/ml/model-serving.yaml` — K8s Deployment + Service for serving endpoint ✓
- `ml/tests/test_pipeline_integration.py` — KF-09 → KF-12 integration tests (Phase 19) ✓

</domain>

<decisions>
## Decisions

### Architecture: Two-layer pipeline — Pure Python orchestrator + KFP DSL wrapper

**Layer 1 — `run_training_pipeline()`:** A plain Python function that chains all 11
components sequentially with in-memory data passing. This is the primary execution
mode for local development, testing, and the drift trigger. Requires no KFP SDK.

**Layer 2 — `stock_training_pipeline()`:** A `@dsl.pipeline`-decorated function that
wraps each component in `@dsl.component` and uses Parquet artifacts for inter-step
data serialisation. This is the production execution mode submitted to Kubeflow
Pipelines. Requires `kfp` SDK and a running KFP deployment.

The local orchestrator (Layer 1) is the testable, deterministic core. The KFP DSL
wrapper (Layer 2) adds containerisation and artifact tracking on top.

### Parquet serialisation for inter-component data transfer

Components in a KFP pipeline cannot pass in-memory DataFrames. A thin
`serialization.py` module provides two functions:

- `save_dataframes(data_dict, path)` — writes `dict[str, pd.DataFrame]` as one
  Parquet file per ticker into a directory
- `load_dataframes(path)` → `dict[str, pd.DataFrame]` — reads them back

The local orchestrator uses in-memory passing (no serialisation overhead). The KFP
DSL wrapper uses Parquet paths for artifact passing between steps.

### Pipeline versioning and run tracking

Each pipeline run produces a `PipelineRunResult` dataclass containing:
- `run_id`: UUID4 string, unique per run
- `pipeline_version`: Semantic version string (`"1.0.0"`)
- `started_at` / `completed_at`: ISO timestamps
- `status`: `"completed"` | `"failed"`
- `steps_completed`: list of step names that ran successfully
- `winner_info`: dict from `select_and_persist_winner()` output
- `deploy_info`: dict from `deploy_winner_model()` output

The run result is saved as `pipeline_run_{run_id}.json` in the registry directory,
providing a full audit trail of every pipeline execution (KF-14).

### Pipeline version stored in model metadata

The `pipeline_version` string is passed through to `select_and_persist_winner()` and
recorded alongside model artifacts, enabling traceability from any registered model
back to the pipeline version that produced it.

### Drift trigger: programmatic pipeline invocation

`drift_pipeline.py` defines `trigger_retraining()` which calls
`run_training_pipeline()` directly. This provides the programmatic trigger
required by KF-15 without requiring a running KFP deployment. Phase 22 will
add the actual drift detection logic; Phase 20 only wires the trigger mechanism.

For Kubeflow-native triggering, `submit_pipeline_run()` submits a compiled pipeline
YAML to the KFP client. This function is guarded behind a `kfp` import check and
documented but not unit-tested (requires live KFP infrastructure).

### Manual trigger support

Manual triggering works through three paths:
1. **Python API:** `run_training_pipeline(tickers=[...])` called directly
2. **CLI:** `python -m ml.pipelines.training_pipeline --tickers AAPL,MSFT,...`
3. **Kubeflow UI:** Submit the compiled pipeline YAML via the KFP dashboard

All three paths satisfy KF-15.

### Data loading strategy for local orchestrator

The local orchestrator's `run_training_pipeline()` accepts either:
- `tickers: list[str]` + `db_settings: DBSettings` — loads from PostgreSQL (production mode)
- `data_dict: dict[str, pd.DataFrame]` — uses pre-loaded data (test mode, bypasses DB)

This dual-input design enables full integration testing without a database.

### Error handling and partial failure tracking

If any step fails, the orchestrator catches the exception, records the failure in
`PipelineRunResult.status`, logs the error, and re-raises. The `steps_completed`
list enables diagnosing exactly how far the pipeline progressed before failure.

### KFP component wrapping pattern

Components are wrapped as lightweight KFP components using `@dsl.component` with
`packages_to_install` specifying the ML package dependencies. Each KFP component
reads/writes Parquet artifacts from/to `dsl.Output[dsl.Dataset]` /
`dsl.Input[dsl.Dataset]`. The actual computation delegates to the existing pure
Python functions.

The KFP pipeline is compiled to YAML/JSON via `kfp.compiler.Compiler().compile()`,
producing a portable pipeline spec that can be uploaded to any KFP v2 deployment.

### Test strategy

**Plan 20-01 (Serialization + Orchestrator + Versioning):**
- `test_serialization.py`: Parquet round-trip tests (save → load → compare)
- `test_training_pipeline.py`: Orchestrator tests using mock/patch on data_loader
  (to avoid DB dependency), real execution of all other components with synthetic data

**Plan 20-02 (Drift trigger + KFP compilation):**
- `test_drift_pipeline.py`: Tests for `trigger_retraining()` with pre-loaded data
- KFP compilation test: verify pipeline compiles to YAML without errors (gated on
  `kfp` availability)

</decisions>

<canonical_refs>
## Canonical References

### Upstream (Phases 17–19, complete)
- `ml/pipelines/components/data_loader.py` — `load_data(tickers, settings) → dict[str, pd.DataFrame]`
- `ml/pipelines/components/feature_engineer.py` — `engineer_features(data) → dict[str, pd.DataFrame]`
- `ml/pipelines/components/label_generator.py` — `generate_labels(data, horizon) → (dict[str, pd.DataFrame], list[str])`
- `ml/pipelines/components/model_trainer.py` — `prepare_training_data(data_dict, features) → (X_train, y_train, X_test, y_test)`
- `ml/pipelines/components/model_trainer.py` — `train_all_models_pipeline(data_dict, features) → (list[TrainingResult], dict[str, Pipeline])`
- `ml/pipelines/components/evaluator.py` — `evaluate_models(results) → list[RankedModel]`
- `ml/pipelines/components/evaluator.py` — `generate_comparison_report(ranked) → dict`
- `ml/pipelines/components/evaluator.py` — `generate_cv_report(results) → dict`
- `ml/pipelines/components/explainer.py` — `explain_top_models(results, pipelines, X, features) → dict[str, dict]`
- `ml/pipelines/components/model_selector.py` — `select_and_persist_winner(results, pipelines, features) → dict`
- `ml/pipelines/components/deployer.py` — `deploy_winner_model(registry_dir, serving_dir) → dict`
- `ml/models/registry.py` — `ModelRegistry` (save_model, save_winner, load_model, list_models, get_winner, activate_model, deactivate_all, get_active_model)

### Data flow through all 11 steps

```
Step  1: load_data(tickers, settings)          → data_dict: dict[str, DataFrame]
Step  2: engineer_features(data_dict)          → enriched_dict: dict[str, DataFrame]
Step  3: generate_labels(enriched_dict)        → (labelled_dict, feature_names)
Step  4: prepare_training_data(labelled_dict)  → (X_train, y_train, X_test, y_test)
Step  5: train_all_models_pipeline(...)        → (results, pipelines)
          [OR use prepare + train_all_models directly]
Step  6: generate_cv_report(results)           → cv_report: dict
Step  7: evaluate_models(results)              → ranked: list[RankedModel]
Step  8: generate_comparison_report(ranked)    → comparison: dict
Step  9: explain_top_models(results, ...)      → shap_output: dict
Step 10: select_and_persist_winner(...)        → winner_info: dict
Step 11: deploy_winner_model(...)              → deploy_info: dict
```

Note: Steps 4–5 can be collapsed into `train_all_models_pipeline()` which internally
calls `prepare_training_data()`. The orchestrator uses the individual calls for finer
step tracking.

### Infrastructure
- `k8s/ml/model-serving.yaml` — K8s Deployment + Service (mounts `/models` volume)
- `k8s/ml/kubeflow/` — Kubeflow Pipelines manifests (to be extended)

### Downstream (Phase 21–22)
- `ml/drift/detector.py` — will implement drift detection logic (Phase 21)
- `ml/drift/trigger.py` — will call `trigger_retraining()` from Phase 20 (Phase 22)

</canonical_refs>
