---
phase: 3
slug: fastapi-base-service
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Wave 0 installs) + curl for integration |
| **Config file** | `stock-prediction-platform/services/api/pytest.ini` (Wave 0 creates) |
| **Quick run command** | `cd stock-prediction-platform/services/api && python -c "from app.main import app; print(app.title)"` |
| **Full suite command** | `cd stock-prediction-platform/services/api && pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** `python -c "from app.main import app; print(app.title)"`
- **After every plan wave:** `pytest tests/ -x -q` (once test stubs exist)
- **Before `/gsd:verify-work`:** Full suite green + `curl http://localhost:8000/health` returns 200
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | API-01 | smoke | `python -c "from app.config import settings; print(settings.SERVICE_NAME)"` | ✅ | ⬜ pending |
| 3-01-02 | 01 | 1 | API-01 | smoke | `python -c "from app.main import app; assert app.title == 'Stock Prediction API'"` | ✅ | ⬜ pending |
| 3-01-03 | 01 | 1 | API-02 | smoke | `python -c "from app.routers.health import router; print(router.prefix)"` | ✅ | ⬜ pending |
| 3-02-01 | 02 | 1 | API-03 | shell | `docker build -t stock-api:latest stock-prediction-platform/services/api/` | ✅ | ⬜ pending |
| 3-03-01 | 03 | 2 | API-04 | live | `kubectl get deployment stock-api -n ingestion -o jsonpath='{.status.availableReplicas}'` | N/A | ⬜ pending |
| 3-03-02 | 03 | 2 | API-02 | live | `kubectl port-forward svc/stock-api -n ingestion 8000:8000 & sleep 3 && curl -sf http://localhost:8000/health` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `stock-prediction-platform/services/api/pytest.ini` — pytest config pointing to `tests/` directory
- [ ] `stock-prediction-platform/services/api/tests/test_health.py` — stub with `test_health_returns_200` and `test_health_response_shape`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker image builds and container starts | API-03 | Requires Docker daemon + Minikube context | `docker build -t stock-api:latest services/api/ && minikube image load stock-api:latest` |
| Pod reaches Running state in cluster | API-04 | Requires live cluster | `kubectl get pods -n ingestion -l app=stock-api` — expect STATUS=Running |
| /health reachable via port-forward | API-02 | Requires live cluster | `kubectl port-forward svc/stock-api -n ingestion 8000:8000` then `curl http://localhost:8000/health` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
