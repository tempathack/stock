---
phase: 94
slug: fred-macro-feature-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 94 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `stock-prediction-platform/ml/tests/pytest.ini` |
| **Quick run command** | `cd stock-prediction-platform && python -m pytest ml/tests/test_data_loader.py -x -q` |
| **Full suite command** | `cd stock-prediction-platform && python -m pytest ml/tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd stock-prediction-platform && python -m pytest ml/tests/test_data_loader.py -x -q`
- **After every plan wave:** Run `cd stock-prediction-platform && python -m pytest ml/tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 94-01-01 | 01 | 0 | fetch contract | unit | `pytest ml/tests/test_data_loader.py::TestFetchFredMacro -x` | ❌ W0 | ⬜ pending |
| 94-01-02 | 01 | 0 | ffill gaps | unit | `pytest ml/tests/test_data_loader.py::TestFetchFredMacro::test_ffill -x` | ❌ W0 | ⬜ pending |
| 94-01-03 | 01 | 0 | create table idempotent | unit | `pytest ml/tests/test_data_loader.py::TestCreateFredMacroTable -x` | ❌ W0 | ⬜ pending |
| 94-01-04 | 01 | 0 | upsert rows | unit | `pytest ml/tests/test_data_loader.py::TestWriteFredMacroToDB -x` | ❌ W0 | ⬜ pending |
| 94-01-05 | 01 | 0 | _TRAINING_FEATURES 14 fred entries | unit | `pytest ml/tests/test_feast_store.py::TestTrainingFeatures -x` | ❌ W0 | ⬜ pending |
| 94-01-06 | 01 | 0 | fred_macro_fv registered | unit | `pytest ml/tests/test_feature_repo.py -x` | ❌ W0 | ⬜ pending |
| 94-01-07 | 01 | 0 | missing API key raises | unit | `pytest ml/tests/test_data_loader.py::TestFetchFredMacroMissingKey -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `ml/tests/test_data_loader.py` — add `TestFetchFredMacro`, `TestCreateFredMacroTable`, `TestWriteFredMacroToDB` test classes (mock `fredapi.Fred` and `psycopg2.connect`)
- [ ] `ml/tests/test_feast_store.py` — add assertion that all 14 `fred_macro_fv:*` entries are in `_TRAINING_FEATURES`
- [ ] `ml/tests/test_feature_repo.py` — new file; import-level check that `fred_macro_fv` and `fred_macro_source` are defined in `feature_repo.py`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| FRED_API_KEY wired into K8s Secret | K8s secret | No cluster in CI | `kubectl get secret stock-platform-secrets -n ingestion -o jsonpath='{.data.FRED_API_KEY}'` — verify non-empty |
| CronJob reads FRED_API_KEY via secretKeyRef | K8s manifest | Argo CD apply | Check `kubectl describe cronjob` after Argo sync shows env var present |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
