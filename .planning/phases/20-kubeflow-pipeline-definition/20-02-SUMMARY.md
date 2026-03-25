---
phase: 20-kubeflow-pipeline-definition
plan: "02"
subsystem: ml
tags: [kubeflow, kfp, drift-trigger, retraining, kfp-yaml, pipeline-compilation, jsonl-log]

# Dependency graph
requires:
  - phase: 20-kubeflow-pipeline-definition
    plan: "01"
    provides: run_training_pipeline(), PipelineRunResult, PIPELINE_VERSION
  - phase: 17-kubeflow-data-feature-components
    provides: DBSettings

provides:
  - ml/pipelines/drift_pipeline.py — trigger_retraining() entry point with reason tracking
  - ml/pipelines/drift_pipeline.py — compile_kfp_pipeline() KFP v2 YAML generation
  - ml/pipelines/drift_pipeline.py — submit_pipeline_run() KFP API submission stub
  - ml/tests/test_drift_pipeline.py — 6 tests (5 trigger + 1 conditional KFP compile)
  - ml/pipelines/__init__.py — updated with trigger_retraining export
  - retraining_log.jsonl — JSONL log of all retraining triggers

affects: [21-drift-detection, 22-drift-auto-retrain, 23-fastapi-prediction-endpoints]

# Tech tracking
tech-stack:
  added: [kfp>=2.0 (optional, for KFP compilation), PyYAML (transitive kfp dep)]
  patterns:
    - trigger_retraining() entry point pattern with reason enum (manual/data_drift/prediction_drift/concept_drift/scheduled)
    - JSONL append log for retraining history queryable by /drift frontend page
    - KFP v2 IR YAML written directly (avoids @dsl.component inspect.getsource limitation for inline closures)

key-files:
  created:
    - stock-prediction-platform/ml/tests/test_drift_pipeline.py
  modified:
    - stock-prediction-platform/ml/pipelines/drift_pipeline.py
    - stock-prediction-platform/ml/pipelines/__init__.py

key-decisions:
  - "trigger_retraining() entry point with reason tracking (manual/data_drift/prediction_drift/concept_drift/scheduled)"
  - "Retraining log appended as JSONL to {registry_dir}/runs/retraining_log.jsonl"
  - "compile_kfp_pipeline() writes KFP v2.1.0 IR YAML directly — avoids @dsl.component inspect.getsource failure for inline closures"
  - "components/__init__.py uses graceful psycopg2 import fallback for data_loader exports"
  - "KFP compilation test conditional on kfp availability (pytest.importorskip)"

patterns-established:
  - "Drift trigger chain: reason-tagged trigger_retraining() -> run_training_pipeline() -> _append_retraining_log()"
  - "JSONL log pattern: append-only JSON lines for queryable history without full file rewrites"

requirements-completed: [KF-15]

# Metrics
duration: 30min
completed: 2026-03-20
---

# Phase 20 Plan 02: Drift Trigger + KFP Pipeline Definition + Tests Summary

**Drift-triggered retraining entry point with reason tracking, JSONL audit log, and KFP v2 YAML pipeline compilation**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-03-20T10:45:00Z
- **Completed:** 2026-03-20T11:15:00Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- trigger_retraining() with reason parameter (manual/data_drift/prediction_drift/concept_drift/scheduled) for Phase 22 wiring
- JSONL retraining log ({registry_dir}/runs/retraining_log.jsonl) — append-only, queryable by /drift page
- compile_kfp_pipeline() produces valid KFP v2.1.0 IR YAML (tested with kfp 2.16.0)
- submit_pipeline_run() stub for KFP API submission (gated on kfp availability)
- 6 tests: 5 trigger tests + 1 conditional KFP compile test — all passing

## Task Commits

The initial implementation was part of a prior bulk commit (fbc1e78). A fix was committed in this execution:

1. **KFP compile fix** - `5ab5356` (fix(20-02): fix compile_kfp_pipeline to produce valid KFP v2 YAML)

## Files Created/Modified
- `stock-prediction-platform/ml/pipelines/drift_pipeline.py` — trigger_retraining(), _append_retraining_log(), compile_kfp_pipeline(), submit_pipeline_run()
- `stock-prediction-platform/ml/tests/test_drift_pipeline.py` — 5 trigger tests + 1 conditional KFP compile test
- `stock-prediction-platform/ml/pipelines/__init__.py` — trigger_retraining added to exports

## Decisions Made
- compile_kfp_pipeline() writes KFP v2.1.0 IR YAML directly using PyYAML rather than using @dsl.component decorator — the decorator calls inspect.getsource() which fails for inline-defined closures, so direct YAML generation is more reliable
- KFP compilation test uses pytest.importorskip("kfp") to be conditional on kfp availability
- retraining_log.jsonl uses append mode (open(path, "a")) for atomicity without full-file rewrites
- S3 backend supported for log appending via STORAGE_BACKEND=s3 env var (same pattern as training_pipeline.py)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed compile_kfp_pipeline() KFP v2 decorator incompatibility**
- **Found during:** Task 2 (write drift pipeline tests + run)
- **Issue:** Original implementation used @dsl.component with inline closure that failed inspect.getsource() when called from test context; also had bool pipeline param which KFP v2.16 rejects
- **Fix:** Replaced decorator approach with direct KFP v2.1.0 IR YAML spec generation via PyYAML; removed bool param
- **Files modified:** drift_pipeline.py
- **Verification:** TestCompileKfpPipeline::test_compile_creates_yaml passes (kfp 2.16.0)
- **Committed in:** 5ab5356 (fix(20-02))

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug fix)
**Impact on plan:** Required for correctness — KFP compile test would fail without this fix.

## Issues Encountered
- KFP v2.16.0 rejects `bool` as pipeline primitive parameter type
- @dsl.component requires inspect.getsource() which doesn't work for dynamically-defined nested functions
- Both issues resolved by switching to direct IR YAML generation

## Next Phase Readiness
- trigger_retraining() ready for Phase 22's drift auto-retrain wiring
- retraining_log.jsonl format established for Phase 23's /drift endpoint
- KFP YAML stub compilable and ready for Phase 21+ full component wiring

## Self-Check: PASSED

- drift_pipeline.py: FOUND
- test_drift_pipeline.py: FOUND
- Commit 5ab5356: FOUND (fix(20-02): fix compile_kfp_pipeline)
- Commit fbc1e78: FOUND (feat: phases 15-23)
- TestCompileKfpPipeline::test_compile_creates_yaml: PASSED
- All Phase 20 fast tests: 15/15 PASSED

---
*Phase: 20-kubeflow-pipeline-definition*
*Completed: 2026-03-20*
