# Deferred Items — Phase 75

## Pre-existing test failure (out of scope for plan 04)

**test_metrics.py::test_prediction_latency_histogram_exists**

- **Found during:** Phase 75 plan 04 — full suite run
- **Status:** FAILED before plan 04 changes (confirmed by git stash test)
- **Root cause:** `prediction_latency_seconds` histogram metric not emitted by the `/predict/{ticker}` endpoint (the metrics response does not include the expected metric name)
- **Impact:** Non-blocking — does not affect OOS metrics or forecast confidence fixes
- **Recommendation:** Phase 82 (fix-ml-prediction-latency-alerting) should investigate this
