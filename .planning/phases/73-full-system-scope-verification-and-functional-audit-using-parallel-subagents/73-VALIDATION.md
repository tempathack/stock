---
phase: 73
slug: full-system-scope-verification-and-functional-audit-using-parallel-subagents
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 73 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | none — audit phase produces markdown reports, not runnable tests |
| **Config file** | none |
| **Quick run command** | `ls .planning/phases/73-*/AUDIT*.md 2>/dev/null` |
| **Full suite command** | `grep -c "✓\|✗\|⚠" .planning/phases/73-*/73-AUDIT.md 2>/dev/null` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `ls .planning/phases/73-*/AUDIT*.md 2>/dev/null`
- **After every plan wave:** Run `grep -c "✓\|✗\|⚠" .planning/phases/73-*/73-AUDIT.md 2>/dev/null`
- **Before `/gsd:verify-work`:** AUDIT.md must exist with all domains populated
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 73-01-01 | 01 | 1 | AUDIT-COORD | file-exists | `test -f .planning/phases/73-*/73-AUDIT.md` | ❌ W0 | ⬜ pending |
| 73-02-01 | 02 | 2 | AUDIT-API | grep | `grep "API Layer" .planning/phases/73-*/73-AUDIT.md` | ❌ W0 | ⬜ pending |
| 73-03-01 | 03 | 2 | AUDIT-ML | grep | `grep "ML Pipeline" .planning/phases/73-*/73-AUDIT.md` | ❌ W0 | ⬜ pending |
| 73-04-01 | 04 | 2 | AUDIT-KAFKA | grep | `grep "Kafka/Flink" .planning/phases/73-*/73-AUDIT.md` | ❌ W0 | ⬜ pending |
| 73-05-01 | 05 | 2 | AUDIT-FE | grep | `grep "Frontend" .planning/phases/73-*/73-AUDIT.md` | ❌ W0 | ⬜ pending |
| 73-06-01 | 06 | 2 | AUDIT-OBS | grep | `grep "Observability" .planning/phases/73-*/73-AUDIT.md` | ❌ W0 | ⬜ pending |
| 73-07-01 | 07 | 2 | AUDIT-INFRA | grep | `grep "Infrastructure" .planning/phases/73-*/73-AUDIT.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.planning/phases/73-.../73-AUDIT.md` — coordinator creates skeleton with domain sections before subagents populate them

*Wave 0 is minimal: coordinator plan (73-01) creates the skeleton AUDIT.md file that domain auditors write into.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Grafana dashboard panels show live data | Phase 72 ConfigMaps | Requires running cluster with real metrics | Start cluster, open Grafana, verify no "No data" panels in ML-perf and kafka dashboards |
| Phase 70 StreamingFeaturesPanel wired in Dashboard | Phase 70 In-Progress item | Requires browser + running frontend | Open dashboard UI, verify streaming features panel renders with live data |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
