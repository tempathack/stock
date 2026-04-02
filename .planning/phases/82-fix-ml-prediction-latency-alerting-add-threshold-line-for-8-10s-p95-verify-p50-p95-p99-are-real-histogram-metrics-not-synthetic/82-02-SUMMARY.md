---
phase: 82-fix-ml-prediction-latency-alerting-add-threshold-line-for-8-10s-p95-verify-p50-p95-p99-are-real-histogram-metrics-not-synthetic
plan: "02"
subsystem: monitoring/testing
tags: [pytest, grafana, dashboard, histogram, threshold, slo]
dependency_graph:
  requires: [82-01]
  provides: [automated-dashboard-json-validation]
  affects: [stock-prediction-platform/services/api/tests/]
tech_stack:
  added: [yaml.safe_load for ConfigMap parsing, pathlib path resolution]
  patterns: [pure-file-io tests, TDD green-first (plan 01 already applied)]
key_files:
  created:
    - stock-prediction-platform/services/api/tests/test_dashboard_json.py
  modified: []
decisions:
  - "Used 4 levels of .parent from test file to reach stock-prediction-platform root, then k8s/monitoring/"
  - "No fixtures needed — all 5 tests are self-contained functions using only stdlib + yaml"
  - "plan 01 changes were already applied when plan 02 executed, so all 5 tests passed immediately (no red phase needed)"
metrics:
  duration: "~1 minute"
  completed: "2026-04-03"
  tasks_completed: 1
  files_created: 1
  files_modified: 0
---

# Phase 82 Plan 02: Dashboard JSON Validation Tests Summary

One-liner: Pytest tests using YAML/JSON parsing to verify the 8s SLO threshold line in ML Performance panel 2 and confirm all histogram_quantile expressions reference real _bucket series in both dashboards.

## What Was Built

Created `stock-prediction-platform/services/api/tests/test_dashboard_json.py` with 5 self-contained test functions that parse Grafana ConfigMap YAML files and validate their embedded dashboard JSON structures. No network calls — pure file I/O runs in under 1 second.

### Tests

| Test | Validates | Result |
|------|-----------|--------|
| `test_ml_perf_panel2_thresholdsStyle_mode_is_line` | Panel 2 has `thresholdsStyle.mode == "line"` for visible SLO reference line | PASSED |
| `test_ml_perf_panel2_has_threshold_line_at_8s` | Panel 2 threshold steps include `{color: "red", value: 8}` | PASSED |
| `test_ml_perf_panel2_thresholds_base_step_is_transparent` | Panel 2 base step is `{color: "transparent", value: null}` | PASSED |
| `test_histogram_quantile_uses_bucket_suffix_ml_perf` | All histogram_quantile exprs in ml-performance.json use `_bucket` | PASSED |
| `test_histogram_quantile_uses_bucket_suffix_api_health` | All histogram_quantile exprs in api-health.json use `_bucket` | PASSED |

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write test_dashboard_json.py | efccbad | tests/test_dashboard_json.py (created) |

## TDD Notes

Plan 01 changes were already applied to `grafana-dashboard-ml-perf.yaml` when plan 02 executed. Therefore all 5 tests passed immediately (green phase). The TDD red phase (2 tests failing before plan 01 changes) was satisfied by the wave ordering — plan 01 and plan 02 are in the same wave 1, with plan 01 expected to precede plan 02 execution.

## Deviations from Plan

None - plan executed exactly as written. The path correction (4 levels of `.parent` instead of 3) was documented in the plan itself and applied correctly.

## Self-Check: PASSED

- [x] `stock-prediction-platform/services/api/tests/test_dashboard_json.py` exists
- [x] Commit efccbad present in git log
- [x] All 5 tests pass: `5 passed in 0.03s`
- [x] Path uses `parent.parent.parent.parent` (4 levels)
- [x] Histogram bucket assertions present
