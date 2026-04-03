---
phase: 90-debezium-cdc-and-elasticsearch-integration
plan: 01
subsystem: infra
tags: [elasticsearch, kibana, debezium, cdc, postgresql, k8s, statefulset, wal]

# Dependency graph
requires:
  - phase: 04-postgresql-timescaledb
    provides: PostgreSQL Deployment in storage namespace (base to patch with WAL args)
provides:
  - Elasticsearch 8.13.4 StatefulSet + ClusterIP Service (port 9200) in storage namespace
  - Kibana 8.13.4 Deployment + NodePort Service (port 30601) in storage namespace
  - 10Gi PVC for Elasticsearch data persistence
  - PostgreSQL Deployment patched with wal_level=logical, max_replication_slots=5, max_wal_senders=5
affects:
  - 90-02 (Debezium connector — depends on ES running and PG WAL enabled)
  - any phase deploying Kafka CDC pipeline

# Tech tracking
tech-stack:
  added: [elasticsearch-8.13.4, kibana-8.13.4]
  patterns:
    - StatefulSet with external PVC (not volumeClaimTemplates) for single-replica ES
    - init container (busybox runAsUser=0) to fix data dir permissions before ES starts
    - PostgreSQL WAL flags injected via container args[] (not ConfigMap) for pod-restart activation

key-files:
  created:
    - stock-prediction-platform/k8s/storage/elasticsearch-statefulset.yaml
    - stock-prediction-platform/k8s/storage/elasticsearch-pvc.yaml
    - stock-prediction-platform/k8s/storage/kibana-deployment.yaml
  modified:
    - stock-prediction-platform/k8s/storage/postgresql-deployment.yaml

key-decisions:
  - "Used external PVC (not volumeClaimTemplates) for Elasticsearch StatefulSet — simpler lifecycle management for single-replica dev cluster"
  - "xpack.security.enabled=false — no auth complexity for internal dev/ops tooling"
  - "Kibana NodePort 30601 — accessible from host via minikube for ops visibility without Ingress"
  - "PostgreSQL WAL args injected directly in Deployment args[] — requires pod restart to activate, documented as known pitfall"

patterns-established:
  - "StatefulSet pattern: external PVC in volumes[] (not volumeClaimTemplates) for single-node storage services"
  - "Permission init container: busybox with runAsUser: 0 chowns data directory before main container starts"

requirements-completed: []

# Metrics
duration: 3min
completed: 2026-04-03
---

# Phase 90 Plan 01: Elasticsearch + Kibana Deploy + PostgreSQL WAL Patch Summary

**Elasticsearch 8.13.4 StatefulSet and Kibana 8.13.4 Deployment deployed in storage namespace with PostgreSQL patched for logical WAL replication enabling Debezium CDC**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-03T10:03:21Z
- **Completed:** 2026-04-03T10:04:16Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Elasticsearch 8.13.4 StatefulSet with single-node discovery, security disabled, 10Gi PVC, busybox init container for permissions
- Kibana 8.13.4 Deployment + NodePort 30601 pointing to elasticsearch.storage.svc.cluster.local:9200
- PostgreSQL Deployment patched with args[] enabling wal_level=logical, max_replication_slots=5, max_wal_senders=5 — required for Debezium pgoutput plugin

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Elasticsearch StatefulSet + PVC manifests** - `06a063e` (feat)
2. **Task 2: Create Kibana Deployment manifest + patch PostgreSQL WAL config** - `4fd8ade` (feat)

**Plan metadata:** `288aa26` (docs: complete plan)

## Files Created/Modified
- `stock-prediction-platform/k8s/storage/elasticsearch-statefulset.yaml` - StatefulSet (image 8.13.4) + ClusterIP Service, init container, 9200/9300 ports
- `stock-prediction-platform/k8s/storage/elasticsearch-pvc.yaml` - 10Gi ReadWriteOnce PVC in storage namespace
- `stock-prediction-platform/k8s/storage/kibana-deployment.yaml` - Kibana 8.13.4 Deployment + NodePort 30601
- `stock-prediction-platform/k8s/storage/postgresql-deployment.yaml` - Added args[] with wal_level=logical, max_replication_slots=5, max_wal_senders=5

## Decisions Made
- Used external PVC (not volumeClaimTemplates) for the Elasticsearch StatefulSet — simpler lifecycle for single-replica dev setup
- xpack.security.enabled=false — eliminates auth complexity for internal ops tooling
- Kibana on NodePort 30601 — accessible via minikube without needing an Ingress controller
- PostgreSQL WAL args added inline in Deployment spec args[] — requires pod restart after `kubectl apply` to take effect

## Deviations from Plan

None — plan executed exactly as written. Added `storageClassName: standard` to PVC (matching postgresql-pvc.yaml pattern) for minikube compatibility.

## Issues Encountered
None.

## User Setup Required
After applying manifests, a PostgreSQL pod restart is required for WAL settings to take effect:
```bash
kubectl rollout restart deployment/postgresql -n storage
```
Verify with: `kubectl exec -it <pg-pod> -n storage -- psql -U stockuser -d stockdb -c "SHOW wal_level;"`

## Next Phase Readiness
- Elasticsearch StatefulSet + Service ready for Debezium sink connector configuration
- Kibana available at NodePort 30601 for index pattern setup and ops visibility
- PostgreSQL WAL enabled — Debezium connector can use pgoutput plugin after pod restart
- Ready for Phase 90-02: Debezium connector deployment

---
*Phase: 90-debezium-cdc-and-elasticsearch-integration*
*Completed: 2026-04-03*

## Self-Check: PASSED
- elasticsearch-statefulset.yaml: FOUND
- elasticsearch-pvc.yaml: FOUND
- kibana-deployment.yaml: FOUND
- 90-01-SUMMARY.md: FOUND
- Commit 06a063e (Task 1): FOUND
- Commit 4fd8ade (Task 2): FOUND
- Commit 288aa26 (Plan metadata): FOUND
