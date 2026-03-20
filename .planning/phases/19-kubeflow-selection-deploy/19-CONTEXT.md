# Phase 19: Kubeflow Pipeline — Selection, Persistence & Deployment Components — Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Build pipeline-level orchestration for steps 8–11 of the 11-step Kubeflow training
pipeline: explainability (SHAP), winner selection, model persistence, and deployment
of the winning model as a live serving endpoint.

Most of the core logic already exists from Phases 15–16 (`model_selector.py`,
`explainer.py`, `registry.py`). This phase adds the **deployment component**
(KF-12 — entirely new) and enhances the model registry with activation/deactivation
tracking needed for production serving.

### Pipeline steps owned by this phase (4 of 11)

| Step | Req   | Component           | Input                                               | Output                                                            |
|------|-------|---------------------|-----------------------------------------------------|-------------------------------------------------------------------|
| 8    | KF-09 | `explainability`    | results, pipelines, X, feature_names                | SHAP summaries for top-N models stored in registry                |
| 9    | KF-10 | `winner_selection`  | results, pipelines, feature_names                   | Winner persisted, registry updated with is_winner=True            |
| 10   | KF-11 | `model_persistence` | winner + top models, pipelines                      | All artifacts (pipeline, metadata, features, SHAP) saved          |
| 11   | KF-12 | `deployment`        | winner registry path                                | Model copied to serving path, marked is_active, config written    |

### Files touched

- `ml/models/registry.py` — **update** with `activate_model()`, `deactivate_all()`, `get_active_model()` methods
- `ml/pipelines/components/deployer.py` — **create** deployment component
- `ml/pipelines/components/__init__.py` — **update** exports for `deploy_winner_model`
- `ml/tests/test_registry.py` — **update** tests for new activation methods
- `ml/tests/test_deployer.py` — **create** tests for deploy_winner_model

### What already exists (no changes needed)

- `ml/pipelines/components/explainer.py` — `explain_top_models()` (KF-09, Phase 16) ✓
- `ml/pipelines/components/model_selector.py` — `select_and_persist_winner()` (KF-10 + KF-11, Phase 15) ✓
- `ml/tests/test_explainer.py` — full coverage ✓
- `ml/tests/test_model_selector.py` — full coverage ✓
- `k8s/ml/model-serving.yaml` — K8s Deployment + Service for serving endpoint ✓

</domain>

<decisions>
## Decisions

### Component Architecture: Same pattern as Phases 17–18 — Pure Python Functions

All components remain plain Python functions with no KFP SDK dependency.
Wrapped in `@dsl.component` decorators in Phase 20.

### Explainability (KF-09): Already complete — no changes

`explain_top_models()` in `explainer.py` already:
- Ranks models, takes top-N
- Computes SHAP (TreeExplainer / LinearExplainer / KernelExplainer fallback)
- Stores `shap_importance.json` and `shap_values.json` in the registry version directory
- Returns per-model feature importance dict

Fully tested in `test_explainer.py`. No changes needed.

### Winner selection (KF-10): Already complete — no changes

`select_and_persist_winner()` in `model_selector.py` already:
- Calls `select_winner()` from ranking module
- Saves winner to registry via `ModelRegistry.save_winner()` with `is_winner=True`
- Saves top-4 runners-up as well
- Returns winner info dict

Fully tested in `test_model_selector.py`. No changes needed.

### Model persistence (KF-11): Already complete — no changes

`select_and_persist_winner()` persists:
- `pipeline.pkl` (fitted sklearn Pipeline containing scaler + model)
- `metadata.json` (model name, scaler, best_params, oos_metrics, fold_metrics, fold_stability, rank, is_winner)
- `features.json` (ordered feature names list)

For top-5 models (winner + 4 runners-up). `explain_top_models()` adds SHAP artifacts.
No additional persistence logic needed.

### Deployment (KF-12): New component — `deployer.py`

New function `deploy_winner_model()` orchestrates the deployment of the winner
model as a serving endpoint:

```python
def deploy_winner_model(
    registry_dir: str = "model_registry",
    serving_dir: str = "/models/active",
) -> dict:
```

Steps:
1. Find the current winner in the registry (`registry.get_winner()`)
2. Deactivate any previously active model (`registry.deactivate_all()`)
3. Copy winner artifacts (pipeline.pkl, metadata.json, features.json, SHAP files)
   to the serving directory
4. Write a `serving_config.json` with:
   - `model_name`, `scaler_variant`, `version`
   - `features` (list), `artifact_path`
   - `deployed_at` (ISO timestamp)
   - `is_active: true`
5. Activate the winner in the registry (`registry.activate_model()`)
6. Return deployment summary dict

### Registry Enhancements: `is_active` tracking

The `ModelRegistry` needs three new methods:

```python
def activate_model(self, model_name: str, scaler_variant: str, version: int) -> None:
    """Set is_active=True in the model's metadata.json."""

def deactivate_all(self) -> int:
    """Set is_active=False for all models. Returns count of deactivated."""

def get_active_model(self) -> dict | None:
    """Return the currently active model metadata, or None."""
```

`is_active` is distinct from `is_winner`:
- `is_winner=True`: This model won the ranking competition
- `is_active=True`: This model is currently deployed and serving predictions

A model can be a winner but not yet active (before deployment) or active but
not the latest winner (between retraining and redeployment).

### Serving directory layout

```
/models/active/
    serving_config.json      # Deployment config read by API
    pipeline.pkl             # Fitted sklearn Pipeline
    metadata.json            # Full model metadata
    features.json            # Ordered feature names
    shap_importance.json     # (if available) SHAP importance
    shap_values.json         # (if available) SHAP values
```

This matches the `model-serving.yaml` volume mount at `/models` with the API
reading from the `active/` subdirectory.

### Error handling

- `deploy_winner_model()` raises `FileNotFoundError` if no winner exists in registry
- `deploy_winner_model()` raises `FileNotFoundError` if winner's artifacts are missing
- `activate_model()` raises `FileNotFoundError` if model/version doesn't exist

### Test strategy

**Plan 19-01 (Registry activation + deployer):**
- `test_registry.py` updates: `TestActivation` class (activate, deactivate_all, get_active_model)
- `test_deployer.py`: `TestDeployWinnerModel` — full deployment lifecycle tests using tmp_path

Tests use `tmp_path` fixtures throughout. No real K8s or filesystem operations outside test directories.

</decisions>

<canonical_refs>
## Canonical References

### Upstream (Phases 15–18, complete)
- `ml/pipelines/components/model_trainer.py` — `train_all_models_pipeline()` → `(list[TrainingResult], dict[str, Pipeline])`
- `ml/pipelines/components/evaluator.py` — `evaluate_models()` → `list[RankedModel]`, `generate_comparison_report()`, `generate_cv_report()`
- `ml/pipelines/components/explainer.py` — `explain_top_models()` → `dict[str, dict]`
- `ml/pipelines/components/model_selector.py` — `select_and_persist_winner()` → `dict`
- `ml/models/registry.py` — `ModelRegistry` (save_model, save_winner, load_model, list_models, get_winner, delete_model)
- `ml/evaluation/ranking.py` — `rank_models()`, `select_winner()`, `RankedModel`, `WinnerResult`
- `ml/evaluation/shap_analysis.py` — `get_shap_summary()`, `compute_shap_values()`, `compute_feature_importance()`
- `ml/models/model_configs.py` — `ModelConfig`, `TrainingResult`

### Infrastructure
- `k8s/ml/model-serving.yaml` — K8s Deployment + Service (mounts `/models` volume, runs uvicorn on port 8000)

### Downstream (Phase 20)
- `ml/pipelines/training_pipeline.py` — will wire all 11 components into a Kubeflow DSL pipeline
- Components will be wrapped in `@dsl.component` decorators with Parquet I/O
</canonical_refs>
