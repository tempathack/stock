## Phase 41 · Plan 01 — Execution Summary

**Status:** DONE  
**Requirement:** DBHARD-08  
**Executed:** 2026-03-23

### Artifacts

| Action | File | Description |
|--------|------|-------------|
| CREATE | `k8s/storage/backup-pvc.yaml` | 10Gi PVC for backup dump files |
| CREATE | `k8s/storage/cronjob-backup.yaml` | Daily pg_dump CronJob with retention |
| MODIFY | `scripts/deploy-all.sh` | Added Phase 41 backup deployment block |

### What Was Built

- **PVC** `postgresql-backup-pvc` — 10Gi ReadWriteOnce (standard) in `storage` namespace with platform labels
- **CronJob** `postgresql-backup` — runs daily at 04:00 UTC, `concurrencyPolicy: Forbid`, 30min timeout
  - Uses `timescale/timescaledb:latest-pg15` (matches PostgreSQL deployment image for `pg_dump` version parity)
  - Produces `/backups/stockdb_YYYYMMDD_HHMMSS.dump` files in custom format (`-Fc`)
  - Connects to `postgresql.storage.svc.cluster.local:5432` as `stockuser` using `PGPASSWORD` from `stock-platform-secrets`
  - Retention: keeps last 7 daily + 4 weekly (Sunday) backups; prunes all others
  - Resources: 100m–500m CPU, 256Mi–512Mi memory
- **deploy-all.sh** — Phase 41 block inserted after Phase 36 RBAC, before Phase 5 Kafka

### Manual Restore

```bash
kubectl exec -n storage <pg-pod> -- pg_restore -U stockuser -d stockdb /backups/<file>.dump
```

### Verification Checklist

- [x] backup-pvc.yaml: name, namespace, labels, 10Gi, RWO, standard
- [x] cronjob-backup.yaml: schedule 0 4 * * *, Forbid, backoffLimit 2, activeDeadlineSeconds 1800
- [x] cronjob-backup.yaml: pg_dump -Fc with correct host/port/user/db
- [x] cronjob-backup.yaml: retention (7 daily + 4 weekly Sunday, 28-day cutoff)
- [x] cronjob-backup.yaml: PGPASSWORD from secretKeyRef, backup-data volume from PVC
- [x] cronjob-backup.yaml: resources requests/limits match plan
- [x] deploy-all.sh: Phase 41 block applies backup-pvc then cronjob-backup
