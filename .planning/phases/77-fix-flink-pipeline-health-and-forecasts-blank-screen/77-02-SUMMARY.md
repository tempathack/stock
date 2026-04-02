---
phase: 77-fix-flink-pipeline-health-and-forecasts-blank-screen
plan: "02"
subsystem: infra
tags: [flink, kubernetes, minio, s3, secrets, kafka, checkpoints]

# Dependency graph
requires:
  - phase: 67-apache-flink
    provides: flinkdeployment-ohlcv-normalizer.yaml and flink-s3-fs-presto S3 plugin
provides:
  - ohlcv-normalizer FlinkDeployment running STABLE with completed MinIO checkpoints
  - Root cause analysis: minio-secrets injects wrong env var names (MINIO_ROOT_USER/PASSWORD) vs required AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY
  - Fix: minio-s3-credentials secret used in FlinkDeployment spec
affects:
  - any future flink job deployments that write checkpoints to MinIO via flink-s3-fs-presto
  - deploy-all.sh consumers that copy secrets to flink namespace

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Flink S3 plugin (flink-s3-fs-presto) requires AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY env var names — not MINIO_ROOT_USER/PASSWORD"
    - "Use minio-s3-credentials secret (not minio-secrets) for Flink checkpoint bucket access"

key-files:
  created: []
  modified:
    - stock-prediction-platform/k8s/flink/flinkdeployment-ohlcv-normalizer.yaml

key-decisions:
  - "Root cause was wrong secret reference in FlinkDeployment: minio-secrets maps MINIO_ROOT_USER/MINIO_ROOT_PASSWORD which flink-s3-fs-presto ignores; minio-s3-credentials maps AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY which is what the plugin reads"
  - "Fix applied via kubectl replace (runtime op) — YAML on disk (flinkdeployment-ohlcv-normalizer.yaml) already contained the correct minio-s3-credentials ref from the committed fix in 7fe0ef1"
  - "Tasks 1 and 2 were runtime-only diagnostic and restart operations — no new file commits needed"

patterns-established:
  - "Flink S3 credentials pattern: always reference minio-s3-credentials secret (provides AWS_* env vars), never minio-secrets (provides MINIO_ROOT_* env vars)"

requirements-completed: [FLINK-FIX-01]

# Metrics
duration: 30min
completed: 2026-04-02
---

# Phase 77 Plan 02: Fix Flink S3 Credential Mapping Summary

**ohlcv-normalizer crash-loop (1160 restarts, 0 checkpoints) resolved by switching from minio-secrets to minio-s3-credentials secret, providing AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY env vars required by flink-s3-fs-presto**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-04-02T17:35:00Z
- **Completed:** 2026-04-02T18:05:00Z
- **Tasks:** 3 (2 auto + 1 human-verify)
- **Files modified:** 1 (YAML on disk — committed in 7fe0ef1 before this plan executed)

## Accomplishments
- Diagnosed root cause: flink-s3-fs-presto ignores MINIO_ROOT_USER/PASSWORD, requires AWS_ACCESS_KEY_ID/SECRET_ACCESS_KEY
- Confirmed both required secrets (stock-platform-secrets, minio-s3-credentials) present in flink namespace
- ohlcv-normalizer FlinkDeployment reached RUNNING/STABLE with 0 pod restarts and checkpoints chk-7, chk-8, chk-9 written to s3://model-artifacts/flink-checkpoints/ohlcv-normalizer/

## Task Commits

Tasks 1 and 2 were runtime-only diagnostic and restart operations (kubectl commands, no file changes). The file fix was committed prior to this plan's execution:

1. **Task 1: Diagnose flink namespace state and fix secrets** - runtime ops only (no commit)
2. **Task 2: Restart ohlcv-normalizer with correct credentials** - runtime ops only (no commit)
3. **Task 3: Human verify — FlinkDeployment READY with checkpoints** - human-approved

**Pre-existing fix commit:** `7fe0ef1` (fix(77-02): fix Flink S3 credential mapping for checkpoint bucket access)

## Files Created/Modified
- `stock-prediction-platform/k8s/flink/flinkdeployment-ohlcv-normalizer.yaml` - Changed secretRef from `minio-secrets` to `minio-s3-credentials` (committed 7fe0ef1)

## Decisions Made
- Root cause was wrong secret reference: `minio-secrets` provides `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` which the Flink S3 plugin does not read. `minio-s3-credentials` provides `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` which flink-s3-fs-presto expects.
- The YAML fix was already committed (7fe0ef1) before plan execution. Runtime tasks applied the fix via `kubectl replace`.
- Verification confirmed chk-7, chk-8, chk-9 written successfully to MinIO, proving end-to-end S3 connectivity restored.

## Deviations from Plan

None — plan executed exactly as written. The pre-committed YAML fix (7fe0ef1) was the file change; tasks 1-2 were intentionally runtime-only per plan design.

## Issues Encountered

The original diagnosis in the plan interfaces section was slightly off — it assumed minio-secrets was the correct secret to copy and that the issue was secrets being absent. The actual issue was that minio-secrets was present but provides wrong env var names. minio-s3-credentials was the correct secret all along. The YAML fix committed in 7fe0ef1 had already identified and corrected this.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Flink ohlcv-normalizer is RUNNING/STABLE with active MinIO checkpoints
- Real-time OHLCV data normalization from Kafka into TimescaleDB is restored
- Future Flink jobs should reference minio-s3-credentials (not minio-secrets) for S3/MinIO access

---
*Phase: 77-fix-flink-pipeline-health-and-forecasts-blank-screen*
*Completed: 2026-04-02*
