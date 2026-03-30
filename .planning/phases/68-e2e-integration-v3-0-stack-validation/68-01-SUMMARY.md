---
phase: 68-e2e-integration-v3-0-stack-validation
plan: 01
subsystem: testing
tags: [bash, smoke-test, validate, timescaledb, argocd, feast, flink, kafka, playwright]

# Dependency graph
requires:
  - phase: 64-timescaledb-olap-continuous-aggregates-compression
    provides: GET /market/candles OLAP endpoint for benchmark timing
  - phase: 65-argo-cd-gitops-deployment-pipeline
    provides: argocd CLI, validate-argocd.sh check() pattern, port-forward lifecycle
  - phase: 66-feast-production-feature-store
    provides: ml.feature_store.materialize, feast-feature-server pod, engineer_features(use_feast=True)
  - phase: 67-apache-flink-real-time-stream-processing
    provides: processed-features Kafka topic, Flink OHLCV upsert pipeline, ohlcv_intraday.updated_at column

provides:
  - stock-prediction-platform/scripts/validate-v3.sh — master v3.0 smoke test script covering V3INT-01 through V3INT-05
  - Executable bash test covering OLAP benchmark, Argo CD GitOps sync, Feast offline/online, and full Flink E2E pipeline

affects:
  - phase 68 Playwright spec additions (argocd.spec.ts, flink-web-ui.spec.ts)
  - CI/CD pipeline integration — validate-v3.sh is the gate for v3.0 production readiness

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "check() bash helper with PASS/FAIL counters and PF_PIDS array — replicated from validate-argocd.sh"
    - "Nanosecond timing with date +%s%N for OLAP ratio computation"
    - "Python3 inline heredoc (PYEOF) for YAML annotation patching without yq"
    - "GIT_ANNOTATION_COMMITTED flag with trap cleanup EXIT for git revert on script exit"
    - "kcat/kafkacat binary fallback to kafka-run-class.sh in Kafka pod"
    - "V3INT-04 graceful degradation: feature_timestamp check falls back to predicted_price non-null"

key-files:
  created:
    - stock-prediction-platform/scripts/validate-v3.sh
  modified: []

key-decisions:
  - "validate/last-checked annotation patched with python3 inline heredoc (no yq dependency)"
  - "git add stages only configmap.yaml (never git add -A) — explicit stage for clean audit trail"
  - "V3INT-01 times raw psql COUNT as proxy for full hypertable scan cost; second curl call (cache-warm) as OLAP time"
  - "V3INT-05 uses updated_at column for 30-second window (not timestamp column) — avoids yfinance stale timestamp false negatives"
  - "V3INT-04 degrades gracefully when feature_timestamp absent: still asserts predicted_price is non-null"
  - "Argo CD poll checks both operationState.phase=Succeeded AND sync.revision matches NEW_HEAD prefix — prevents false-positive on prior sync"

patterns-established:
  - "Script-level cleanup trap reverts throwaway git commits made during validation"
  - "Port-forward PIDs collected in PF_PIDS array, killed in cleanup trap"
  - "Inline python3 heredoc pattern for YAML mutation without external tools"

requirements-completed: [V3INT-01, V3INT-02, V3INT-03, V3INT-04, V3INT-05]

# Metrics
duration: 2min
completed: 2026-03-30
---

# Phase 68 Plan 01: v3.0 Stack Validation Summary

**Bash smoke test validate-v3.sh covering all five v3.0 success criteria: OLAP >=10x benchmark, Argo CD 3-min GitOps sync loop, Feast offline/online feature paths, and full Flink ingest-to-predict pipeline**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-30T11:06:32Z
- **Completed:** 2026-03-30T11:08:30Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `validate-v3.sh` implementing the canonical `check()`/`cleanup`/`trap` skeleton from `validate-argocd.sh`
- V3INT-01: OLAP benchmark using nanosecond timing (`date +%s%N`); warm-up then timed second call; asserts `RATIO -ge 10`
- V3INT-02: Real git commit+push of `validate/last-checked` annotation into configmap.yaml; polls `operationState.phase=Succeeded` AND `sync.revision` match for up to 180s; cleanup trap reverts commit
- V3INT-03: Feast offline path via `kubectl exec -n ml deploy/feast-feature-server -- python3 -c "engineer_features(use_feast=True)"`
- V3INT-04: Feast online freshness — materializes via pod exec, checks `feature_timestamp` age <120s with graceful fallback to `predicted_price != null`
- V3INT-05: Full Flink E2E — triggers `/ingest/intraday`, polls `ohlcv_intraday.updated_at` every 3s up to 30s, checks `processed-features` Kafka offset, asserts `/predict/AAPL` prediction

## Task Commits

Each task was committed atomically:

1. **Task 1: Write validate-v3.sh** - `8a31769` (feat)

## Files Created/Modified

- `stock-prediction-platform/scripts/validate-v3.sh` - Master v3.0 smoke test; executable; 284 lines; passes `bash -n` syntax check; contains all 5 V3INT check IDs (25 occurrences)

## Decisions Made

- Used `python3` inline heredoc (`PYEOF`) to patch `validate/last-checked` annotation in configmap.yaml — no `yq` required, safe YAML edit via regex substitution
- `git add` stages only `stock-prediction-platform/k8s/ingestion/configmap.yaml` (never `git add -A`) — clean audit trail
- `GIT_ANNOTATION_COMMITTED=false` flag ensures cleanup trap only reverts if the annotation commit was actually made
- Argo CD poll verifies both `operationState.phase=Succeeded` AND `sync.revision` prefix-matches `NEW_HEAD` — avoids accepting a stale previous sync result
- V3INT-05 uses `updated_at >= now() - interval '30 seconds'` (not raw timestamp column) — avoids yfinance stale-timestamp false negatives per RESEARCH.md Pitfall 5

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Script is invoked after `deploy-all.sh` on a running cluster.

## Next Phase Readiness

- `validate-v3.sh` is complete and ready to run after `deploy-all.sh` on a healthy v3.0 cluster
- All 5 V3INT requirements addressed (V3INT-01 through V3INT-05)
- Playwright argocd.spec.ts and flink-web-ui.spec.ts infra specs are the remaining Phase 68 deliverables (separate plan)

---
*Phase: 68-e2e-integration-v3-0-stack-validation*
*Completed: 2026-03-30*
