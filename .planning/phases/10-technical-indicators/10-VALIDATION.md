---
phase: 10
slug: technical-indicators
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | stock-prediction-platform/ml/tests/pytest.ini |
| **Quick run command** | `cd stock-prediction-platform && python -m pytest ml/tests/test_indicators.py -q --tb=short` |
| **Full suite command** | `cd stock-prediction-platform && python -m pytest ml/tests/test_indicators.py -v --tb=short` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 10-01-01 | 01 | 1 | FEAT-01 | unit | `pytest ml/tests/test_indicators.py -k "rsi" -q` | ⬜ pending |
| 10-01-02 | 01 | 1 | FEAT-02 | unit | `pytest ml/tests/test_indicators.py -k "macd" -q` | ⬜ pending |
| 10-01-03 | 01 | 1 | FEAT-03 | unit | `pytest ml/tests/test_indicators.py -k "stochastic" -q` | ⬜ pending |
| 10-02-01 | 02 | 1 | FEAT-04 | unit | `pytest ml/tests/test_indicators.py -k "sma" -q` | ⬜ pending |
| 10-02-02 | 02 | 1 | FEAT-05 | unit | `pytest ml/tests/test_indicators.py -k "ema" -q` | ⬜ pending |
| 10-02-03 | 02 | 1 | FEAT-06 | unit | `pytest ml/tests/test_indicators.py -k "adx" -q` | ⬜ pending |
| 10-03-01 | 03 | 2 | FEAT-07 | unit | `pytest ml/tests/test_indicators.py -k "bollinger" -q` | ⬜ pending |
| 10-03-02 | 03 | 2 | FEAT-08 | unit | `pytest ml/tests/test_indicators.py -k "atr" -q` | ⬜ pending |
| 10-03-03 | 03 | 2 | FEAT-09 | unit | `pytest ml/tests/test_indicators.py -k "rolling_vol" -q` | ⬜ pending |
| 10-04-01 | 04 | 2 | FEAT-10 | unit | `pytest ml/tests/test_indicators.py -k "obv" -q` | ⬜ pending |
| 10-04-02 | 04 | 2 | FEAT-11 | unit | `pytest ml/tests/test_indicators.py -k "vwap" -q` | ⬜ pending |
| 10-04-03 | 04 | 2 | FEAT-12 | unit | `pytest ml/tests/test_indicators.py -k "volume_sma" -q` | ⬜ pending |
| 10-04-04 | 04 | 2 | FEAT-13 | unit | `pytest ml/tests/test_indicators.py -k "ad_line" -q` | ⬜ pending |
| 10-04-05 | 04 | 2 | FEAT-14 | unit | `pytest ml/tests/test_indicators.py -k "returns" -q` | ⬜ pending |
| 10-04-06 | 04 | 2 | ALL | unit | `pytest ml/tests/test_indicators.py -k "all_indicators" -q` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `ml/tests/__init__.py` — test package init
- [ ] `ml/tests/conftest.py` — shared fixtures (sample OHLCV DataFrame)
- [ ] `ml/tests/test_indicators.py` — test stubs for all 14 indicators

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Indicator values match real market data | ALL | Requires reference data from external source | Compare computed RSI/MACD/etc. against TradingView or another TA tool for AAPL daily data |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
