# Phase 22: Drift Auto-Retrain Trigger — Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire drift detection to automatic retraining and add post-retrain prediction
generation. Most infrastructure is already in place from Phases 20-21:

- `evaluate_and_trigger()` already calls `trigger_retraining()` → `run_training_pipeline()` (DRIFT-06 ✓)
- `run_training_pipeline()` already selects winner and deploys (DRIFT-07 partial ✓)
- **Missing:** Prediction generation function that uses the active model to generate and store predictions for all tickers (DRIFT-07 completion)

### Requirements covered

| Req    | Description                                                  |
|--------|--------------------------------------------------------------|
| DRIFT-06 | Auto-trigger retraining pipeline on drift detection        |
| DRIFT-07 | Post-retrain: winner selected, deployed, predictions regenerated |

### Files to create/update

- `ml/pipelines/components/predictor.py` — **create** prediction generator using active model
- `ml/drift/trigger.py` — **update** to call predictor after successful retrain
- `ml/tests/test_predictor.py` — **create** prediction tests
- `ml/tests/test_drift_retrain_integration.py` — **create** end-to-end drift→retrain→predict test

### What already exists

- `ml/drift/trigger.py` — `evaluate_and_trigger()` with auto_retrain flag ✓
- `ml/pipelines/drift_pipeline.py` — `trigger_retraining()` ✓
- `ml/pipelines/training_pipeline.py` — `run_training_pipeline()` with full 11-step pipeline ✓
- `ml/drift/detector.py` — all three detectors ✓
- `ml/drift/monitor.py` — `DriftMonitor.check()` ✓

</domain>

<decisions>
## Decisions

### Prediction generator in predictor.py

A `generate_predictions()` function that:
1. Loads the active model from the serving directory
2. For each ticker, loads recent OHLCV data and engineers features
3. Runs predictions through the loaded pipeline
4. Returns predictions as a list of dicts matching the predictions table schema
5. DB persistence is optional (gated behind psycopg2)

### evaluate_and_trigger wiring

After successful retrain, `evaluate_and_trigger()` calls `generate_predictions()`
to regenerate all predictions using the new model. This is optional and controlled
by a `regenerate_predictions` flag (default True).

### File-based prediction storage

Predictions are stored as JSON in `{registry_dir}/predictions/latest.json` in
addition to optional DB persistence. This ensures the prediction generation
functionality is fully testable without a database.

</decisions>
