---
phase: 87
slug: point-in-time-correct-feature-serving-feast-kserve-transformer-backtest-lookahead-leakage
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 87 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | {path or "none — Wave 0 installs"} |
| **Quick run command** | `pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `pytest tests/ -q --timeout=60` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `pytest tests/ -q --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 87-01-01 | 01 | 1 | TBD | unit | `pytest tests/test_feast_transformer.py -x -q` | ❌ W0 | ⬜ pending |
| 87-01-02 | 01 | 1 | TBD | integration | `pytest tests/test_kserve_transformer.py -x -q` | ❌ W0 | ⬜ pending |
| 87-02-01 | 02 | 2 | TBD | unit | `pytest tests/test_backtest_pit.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_feast_transformer.py` — stubs for KServe Transformer + Feast online feature fetch
- [ ] `tests/test_kserve_transformer.py` — stubs for Transformer container preprocess() routing
- [ ] `tests/test_backtest_pit.py` — stubs for point-in-time backtest leakage validation
- [ ] `tests/conftest.py` — shared fixtures (Feast mock, feature vector fixture)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| KServe Transformer routes requests through preprocess() in RawDeployment mode | TBD | Requires live KServe cluster | Deploy Transformer, send inference request, verify Feast is called via logs |
| Backtest returns no future OHLCV rows for historical dates | TBD | Requires production data | Run backtest for a past date, verify no feature rows with timestamp > prediction date |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
