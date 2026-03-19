# Phase 13: Tree-Based & Boosting Models - Context

**Gathered:** 2026-03-19
**Status:** Complete

<domain>
## Phase Boundary

Add 6 sklearn tree/ensemble regressors and 3 optional booster models (XGBoost, LightGBM, CatBoost) to the model registry. Reuses Phase 12 training infrastructure (train_single_model, pipeline build, metrics, CV).

Files touched:
- `ml/models/model_configs.py` — TREE_MODELS, BOOSTER_MODELS dicts + registration
- `ml/models/__init__.py` — re-exports
- `ml/pipelines/components/model_trainer.py` — train_tree_models, train_all_models
- `ml/tests/test_model_configs.py` — tree + booster config tests
- `ml/tests/test_model_trainer.py` — tree + booster training tests
</domain>

<decisions>
- TREE_MODELS: 6 sklearn models with search spaces, all random_state=42
- BOOSTER_MODELS: conditional imports (try/except ImportError)
- RF and GBM get n_iter=50; others default 30
- CatBoost verbose=0, LightGBM verbose=-1, XGBoost verbosity=0
- train_tree_models supports include_boosters=False flag
- train_all_models combines linear + tree results
- Upgraded xgboost→3.2.0, lightgbm→4.6.0, catboost→1.2.10 for NumPy 2.x compat
</decisions>
