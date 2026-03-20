---
phase: 24
slug: fastapi-market-endpoints
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | stock-prediction-platform/pytest.ini |
| **Quick run command** | `cd stock-prediction-platform && python -m pytest services/api/tests/test_market_router.py services/api/tests/test_market_service.py -v` |
| **Full suite command** | `cd stock-prediction-platform && python -m pytest services/api/tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform && python -m pytest services/api/tests/test_market_router.py services/api/tests/test_market_service.py -v`
- **After every plan wave:** Run `cd stock-prediction-platform && python -m pytest services/api/tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 24-01-01 | 01 | 1 | API-11 | unit | `python -m pytest services/api/tests/test_market_router.py::TestMarketOverview -v` | ✅ | ⬜ pending |
| 24-01-02 | 01 | 1 | API-12 | unit | `python -m pytest services/api/tests/test_market_router.py::TestMarketIndicators -v` | ✅ | ⬜ pending |
| 24-01-03 | 01 | 1 | API-11 | unit | `python -m pytest services/api/tests/test_market_service.py::TestGetMarketOverview -v` | ✅ | ⬜ pending |
| 24-01-04 | 01 | 1 | API-12 | unit | `python -m pytest services/api/tests/test_market_service.py::TestGetTickerIndicators -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
