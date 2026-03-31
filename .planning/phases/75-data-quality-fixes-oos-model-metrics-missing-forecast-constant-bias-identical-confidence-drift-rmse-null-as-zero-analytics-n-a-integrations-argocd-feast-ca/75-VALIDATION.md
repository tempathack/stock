---
phase: 75
slug: data-quality-fixes-oos-model-metrics-missing-forecast-constant-bias-identical-confidence-drift-rmse-null-as-zero-analytics-n-a-integrations-argocd-feast-ca
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 75 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `stock-prediction-platform/services/api/pytest.ini` |
| **Quick run command** | `cd stock-prediction-platform/services/api && python -m pytest tests/test_analytics_argocd.py tests/test_analytics_feast.py tests/test_models_router.py tests/test_prediction_service.py -x -q` |
| **Full suite command** | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command above
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Bug Area | Test Type | Automated Command | File Exists | Status |
|---------|------|------|----------|-----------|-------------------|-------------|--------|
| 75-01-01 | 01 | 1 | Diagnostics | manual | DB queries — output review | ✅ | ⬜ pending |
| 75-01-02 | 01 | 1 | OOS Metrics | unit | `pytest tests/test_prediction_service.py tests/test_models_router.py -x -q` | ✅ | ⬜ pending |
| 75-01-03 | 01 | 1 | Forecast Bias | unit | `pytest tests/test_prediction_service.py -x -q` | ✅ | ⬜ pending |
| 75-02-01 | 02 | 2 | Drift RMSE | manual | Visual check in browser | N/A | ⬜ pending |
| 75-02-02 | 02 | 2 | ArgoCD | unit | `pytest tests/test_analytics_argocd.py -x -q` | ✅ (needs update) | ⬜ pending |
| 75-02-03 | 02 | 2 | Feast Latency | unit | `pytest tests/test_analytics_feast.py -x -q` | ✅ (needs new test) | ⬜ pending |
| 75-02-04 | 02 | 2 | CA Last Refresh | unit | `pytest tests/test_analytics_flink.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_analytics_feast.py` — add test for `measure_feast_online_latency_ms()` function
- [ ] `tests/test_analytics_argocd.py` — update for kubernetes Python client mock (K8s CRD path, replacing REST API path)
- [ ] Verify `kubernetes` package in `stock-prediction-platform/services/api/requirements.txt` — add if missing

*Existing infrastructure (pytest, pytest-asyncio, existing test files) covers remaining requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Drift page renders `—` not `0.0000` for null previous-model RMSE | Phase 75 goal | No frontend test suite | Navigate to /drift, check ActiveModelCard previous-model RMSE field shows `—` when previous_model is null |
| Analytics page shows real ArgoCD sync status | Phase 75 goal | Requires live K8s cluster | Navigate to /analytics, SystemHealthSummary Argo CD card shows "Synced" or "OutOfSync" (not "N/A") |
| Analytics page shows real Feast latency in ms | Phase 75 goal | Requires live Feast service | Navigate to /analytics, Feast Latency card shows a numeric ms value (not "N/A") |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
