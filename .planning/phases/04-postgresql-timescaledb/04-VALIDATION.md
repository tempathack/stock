---
phase: 4
slug: postgresql-timescaledb
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash assertions + psql queries (no pytest needed — pure SQL/shell) |
| **Config file** | none |
| **Quick run command** | `bash -n stock-prediction-platform/db/init.sql` (syntax) + `grep -c "CREATE TABLE" stock-prediction-platform/db/init.sql` |
| **Full suite command** | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "\dt"` (requires live cluster) |
| **Estimated runtime** | ~3 seconds (static); ~10 seconds (live) |

---

## Sampling Rate

- **After every task commit:** `bash -n db/init.sql && grep -c "CREATE TABLE" db/init.sql`
- **After every plan wave:** Static grep checks on all modified files
- **Before `/gsd:verify-work`:** Live psql inspection via kubectl exec
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | DB-03 | shell | `grep -c "CREATE TABLE" stock-prediction-platform/db/init.sql \| grep -q "^6$"` | ✅ | ⬜ pending |
| 4-01-02 | 01 | 1 | DB-02 | shell | `grep -q "CREATE EXTENSION IF NOT EXISTS timescaledb" stock-prediction-platform/db/init.sql` | ✅ | ⬜ pending |
| 4-01-03 | 01 | 1 | DB-04 | shell | `grep -q "PRIMARY KEY (ticker, date)" stock-prediction-platform/db/init.sql` | ✅ | ⬜ pending |
| 4-01-04 | 01 | 1 | DB-05 | shell | `grep -c "CREATE INDEX" stock-prediction-platform/db/init.sql \| grep -qv "^0$"` | ✅ | ⬜ pending |
| 4-01-05 | 01 | 1 | DB-06 | shell | `grep -q "create_hypertable" stock-prediction-platform/db/init.sql` | ✅ | ⬜ pending |
| 4-02-01 | 02 | 1 | DB-07 | shell | `grep -q "postgresql-init-sql" stock-prediction-platform/scripts/setup-minikube.sh` | ✅ | ⬜ pending |
| 4-02-02 | 02 | 1 | DB-01 | shell | `grep -q "postgresql-deployment.yaml" stock-prediction-platform/scripts/deploy-all.sh` | ✅ | ⬜ pending |
| 4-03-01 | 03 | 2 | DB-01 | live | `kubectl get pods -n storage -l app=postgresql -o jsonpath='{.items[0].status.phase}'` | N/A | ⬜ pending |
| 4-03-02 | 03 | 2 | DB-02 | live | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "\dx" \| grep -q timescaledb` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. This phase only writes SQL and shell scripts — no test framework installation needed.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| All 6 tables exist in database | DB-03 | Requires live cluster | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "\dt"` |
| Composite PKs verified | DB-04 | Requires live cluster | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "\d ohlcv_daily"` |
| Hypertables created | DB-06 | Requires live cluster | `kubectl exec -n storage deploy/postgresql -- psql -U stockuser -d stockdb -c "SELECT * FROM timescaledb_information.hypertables;"` |
| PVC bound and pod Running | DB-01 | Requires live cluster | `kubectl get pvc -n storage && kubectl get pods -n storage` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
