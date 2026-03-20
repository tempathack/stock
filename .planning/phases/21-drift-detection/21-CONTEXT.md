# Phase 21: Drift Detection System — Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement all three drift detectors (data drift, prediction drift, concept drift),
a daily drift check orchestrator (monitor), and drift event logging. The drift
detection system operates as a pure-Python library that can be tested without a
database or Kubernetes — DB persistence is optional and gated behind psycopg2
availability.

### Requirements covered

| Req    | Description                                                  |
|--------|--------------------------------------------------------------|
| DRIFT-01 | Data drift detector using KS-test and PSI on feature distributions |
| DRIFT-02 | Prediction drift detector (rolling prediction error threshold) |
| DRIFT-03 | Concept drift detector (recent vs. historical model performance) |
| DRIFT-04 | Daily drift check job (triggered after ingestion)            |
| DRIFT-05 | Drift events logged to drift_logs table with type, severity, details |

### Files to rewrite (currently stubs)

- `ml/drift/detector.py` — **rewrite** from stub → three drift detector classes
- `ml/drift/monitor.py` — **rewrite** from stub → daily drift check orchestrator
- `ml/drift/trigger.py` — **rewrite** from stub → drift event logging + trigger bridge
- `ml/drift/__init__.py` — **update** exports

### Test files to create

- `ml/tests/test_detector.py` — unit tests for all three drift detectors
- `ml/tests/test_monitor.py` — tests for the drift check orchestrator
- `ml/tests/test_trigger.py` — tests for drift event logging

### What already exists (no changes needed)

- `db/init.sql` — drift_logs table schema:
  ```sql
  CREATE TABLE IF NOT EXISTS drift_logs (
      id           BIGSERIAL    PRIMARY KEY,
      drift_type   VARCHAR(50)  NOT NULL,
      severity     VARCHAR(20)  NOT NULL,
      details_json JSONB        NOT NULL,
      detected_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
  );
  ```
- `ml/pipelines/drift_pipeline.py` — `trigger_retraining()` (Phase 20) ✓
- `ml/pipelines/training_pipeline.py` — `run_training_pipeline()` (Phase 20) ✓

</domain>

<decisions>
## Decisions

### Three detector classes in detector.py

**DataDriftDetector:**
- Compares training feature distributions against recent data (last 7 days by default)
- Uses two-sample Kolmogorov-Smirnov test (`scipy.stats.ks_2samp`) per feature
- Computes Population Stability Index (PSI) per feature
- Reports drift if either KS p-value < threshold (default 0.01) OR PSI > threshold (default 0.2)
- Returns `DriftResult` dataclass with per-feature details

**PredictionDriftDetector:**
- Compares rolling prediction error (MAE) against historical baseline
- Takes recent predictions + actuals and computes rolling MAE over configurable window
- Flags drift if recent MAE exceeds baseline MAE × multiplier (default 1.5)
- Does NOT require the model itself — only predictions and actual values

**ConceptDriftDetector:**
- Compares recent model performance (last N days) vs. historical performance
- Uses a sliding window approach: recent_metrics vs. historical_metrics
- Flags drift if recent RMSE is significantly worse than historical RMSE
- Uses a configurable degradation threshold (default 1.3 = 30% worse)

### DriftResult dataclass

```python
@dataclass
class DriftResult:
    drift_type: str           # "data_drift" | "prediction_drift" | "concept_drift"
    is_drifted: bool          # True if drift detected
    severity: str             # "none" | "low" | "medium" | "high"
    details: dict             # Type-specific details (KS stats, PSI, MAE, etc.)
    timestamp: str            # ISO timestamp
    features_affected: list[str]  # For data drift: list of drifted features
```

### PSI (Population Stability Index) implementation

Computed as: PSI = Σ (actual% - expected%) × ln(actual% / expected%)
where actual% and expected% are binned proportions. Uses 10 quantile bins by default.
Clipping applied to avoid log(0).

### Monitor orchestrator (monitor.py)

`DriftMonitor` class that:
1. Takes reference data (training), recent data, predictions, and actuals
2. Runs all three detectors
3. Aggregates results into a `DriftCheckResult`
4. Optionally persists drift events to drift_logs table (gated behind DB availability)

### Severity levels

- `"none"`: No drift detected
- `"low"`: Marginal drift (close to threshold)
- `"medium"`: Clear drift exceeding threshold
- `"high"`: Severe drift (≥2× threshold)

### DB persistence is optional

Drift event logging to the drift_logs table is gated behind psycopg2 availability.
A `DriftLogger` class in trigger.py handles:
- In-memory accumulation of drift events (always available)
- File-based logging to JSONL (always available)
- PostgreSQL persistence (optional, requires psycopg2)

This ensures the drift detection system is fully testable without a database.

### trigger.py bridges detection to retraining

`trigger.py` contains:
- `DriftLogger` — persists drift events
- `evaluate_and_trigger()` — runs drift check, logs events, and optionally triggers
  `trigger_retraining()` from Phase 20 if drift detected

</decisions>
