---
phase: 67-apache-flink-real-time-stream-processing
plan: "03"
subsystem: infra
tags: [flink, kafka, minio, helm, kubernetes, deploy-scripts]

# Dependency graph
requires:
  - phase: 67-01
    provides: FlinkDeployment CRs for ohlcv-normalizer, indicator-stream, feast-writer
  - phase: 67-02
    provides: Flink job code, Grafana dashboard ConfigMap, all k8s/flink manifests
  - phase: 51
    provides: MinIO object storage with model-artifacts bucket
  - phase: 5
    provides: Kafka cluster and Strimzi operator
provides:
  - minio-init-job.yaml creates flink-checkpoints/.keep placeholder for RocksDB fault tolerance
  - setup-minikube.sh installs Flink Kubernetes Operator v1.11.0 via Helm with idempotency guard
  - deploy-all.sh Phase 67 block builds 3 Flink Docker images, copies secrets to flink namespace, applies all FlinkDeployment CRs
  - Grafana Flink dashboard applied in Phase 38 block
affects: [phase-68-e2e-integration, phase-69-analytics-ui]

# Tech tracking
tech-stack:
  added: [flink-kubernetes-operator v1.11.0 (Helm)]
  patterns: [idempotent Helm install with helm list guard, secret copy pattern extended to flink namespace, placeholder object for MinIO prefix creation]

key-files:
  created: []
  modified:
    - stock-prediction-platform/k8s/storage/minio-init-job.yaml
    - stock-prediction-platform/scripts/setup-minikube.sh
    - stock-prediction-platform/scripts/deploy-all.sh

key-decisions:
  - "Use webhook.create=false for Flink Operator Helm install to avoid cert-manager certificate pressure on Minikube (cert-manager already used by KServe/Phase 54)"
  - "MinIO flink-checkpoints prefix created via echo | mc pipe placeholder object — MinIO has no explicit subdirectory creation API"
  - "Phase 67 block placed between Phase 9 (Kafka consumer) and Phase 33 (ML pipeline) in deploy-all.sh — Flink depends on Kafka, ML pipeline is independent"
  - "Idempotency guard for Helm install via helm list -n flink | grep flink-kubernetes-operator"

patterns-established:
  - "Flink Operator install: helm install with --create-namespace --set webhook.create=false --wait"
  - "Secret copy pattern reused for flink namespace: stock-platform-secrets + minio-secrets"

requirements-completed:
  - FLINK-06
  - FLINK-07
  - FLINK-08

# Metrics
duration: 2min
completed: 2026-03-30
---

# Phase 67 Plan 03: Flink Infrastructure Integration Summary

**Flink Operator Helm install, MinIO checkpoint prefix, and deploy-all.sh Phase 67 block wiring all three Flink stream processing jobs into one-shot cluster deployment**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-30T08:40:29Z
- **Completed:** 2026-03-30T08:41:55Z
- **Tasks:** 2/3 auto tasks complete (Task 3 is human-verify checkpoint — awaiting verification)
- **Files modified:** 3

## Accomplishments

- minio-init-job.yaml creates `flink-checkpoints/.keep` placeholder object so RocksDB checkpoint writes find an existing prefix
- setup-minikube.sh gains a Phase 67 block to install Flink Kubernetes Operator v1.11.0 via Helm with idempotency guard and CRD verification
- deploy-all.sh gains a Phase 67 block that: applies RBAC and processed-features topic, copies stock-platform-secrets and minio-secrets to flink namespace, builds all 3 Flink Docker images, applies all 3 FlinkDeployment CRs, and waits up to 180s for RUNNING state

## Task Commits

Each task was committed atomically:

1. **Task 1: MinIO flink-checkpoints prefix + Flink Operator Helm install** - `f2bdc1b` (feat)
2. **Task 2: deploy-all.sh Phase 67 block** - `1cd5fdf` (feat)
3. **Task 3: Smoke validation checkpoint** - pending human verification

## Files Created/Modified

- `stock-prediction-platform/k8s/storage/minio-init-job.yaml` - Added flink-checkpoints/.keep placeholder creation after drift-logs bucket
- `stock-prediction-platform/scripts/setup-minikube.sh` - Added Phase 67 Flink Operator Helm install block with idempotency guard
- `stock-prediction-platform/scripts/deploy-all.sh` - Added Phase 67 block (RBAC, topic, secret copy, Docker builds, FlinkDeployment apply, wait loop) + grafana-dashboard-flink.yaml apply

## Decisions Made

- Use `webhook.create=false` for Flink Operator Helm install to avoid cert-manager certificate pressure on Minikube (cert-manager already used by KServe from Phase 54)
- MinIO flink-checkpoints prefix created via `echo "" | mc pipe local/model-artifacts/flink-checkpoints/.keep` — MinIO has no explicit subdirectory creation API
- Phase 67 block placed between Phase 9 (Kafka consumer) and Phase 33 (ML pipeline) in deploy-all.sh
- Idempotency guard: `helm list -n flink | grep flink-kubernetes-operator`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**Task 3 (human-verify checkpoint) requires manual verification:**

1. Run `scripts/setup-minikube.sh` (or `scripts/deploy-all.sh` for full stack) to deploy the Flink Operator and all three FlinkDeployment CRs
2. Verify all 3 FlinkDeployments reach RUNNING/STABLE state
3. Verify processed-features Kafka topic exists with 3 partitions
4. Verify Prometheus scrapes flink_ metrics from task manager pods
5. Verify Grafana "Apache Flink — Stream Processing" dashboard renders
6. Perform Kafka broker restart resilience test (FLINK-08)
7. Run `pytest tests/flink/ -v`

See full verification steps in 67-03-PLAN.md Task 3.

## Next Phase Readiness

- All deployment scripts updated — run `scripts/deploy-all.sh` to deploy full Flink stack
- Phase 68 (E2E Integration) can proceed after human verification of Task 3 passes
- Phase 69 (/analytics UI) depends on Phase 68 API endpoints

---
*Phase: 67-apache-flink-real-time-stream-processing*
*Completed: 2026-03-30*
