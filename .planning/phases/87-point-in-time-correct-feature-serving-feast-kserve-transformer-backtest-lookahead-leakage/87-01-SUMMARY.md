---
phase: 87-point-in-time-correct-feature-serving-feast-kserve-transformer-backtest-lookahead-leakage
plan: "01"
subsystem: infra
tags: [kserve, feast, transformer, redis, online-features, point-in-time, python]

# Dependency graph
requires:
  - phase: 86-nav-icons
    provides: "stable frontend baseline before transformer service addition"
provides:
  - "FeastTransformer(kserve.Model) service with preprocess() hook for Feast online feature enrichment"
  - "Dockerfile for feast-transformer container image (python:3.11-slim)"
  - "Unit tests for PIT-02 and PIT-03 behaviour (4 tests, no live Feast/Redis required)"
affects:
  - "87-03 — KServe InferenceService YAML will attach this transformer container"
  - "Future inference latency benchmarks — FeatureStore singleton avoids per-request registry fetch"

# Tech tracking
tech-stack:
  added:
    - "kserve==0.16.0 (InferRequest, InferInput, InferResponse, Model, ModelServer)"
    - "feast[postgres,redis]==0.61.0 (FeatureStore online store read from Redis)"
  patterns:
    - "FeatureStore singleton: init once in __init__, reuse across preprocess() calls"
    - "HTTP 400 (InvalidInput) on bad/unknown entity — not HTTP 503 (transient failure)"
    - "Feature key mapping: colon-to-double-underscore for Feast to_dict() output keys"

key-files:
  created:
    - "stock-prediction-platform/services/feast-transformer/feast_transformer.py"
    - "stock-prediction-platform/services/feast-transformer/requirements.txt"
    - "stock-prediction-platform/services/feast-transformer/Dockerfile"
    - "stock-prediction-platform/services/api/tests/test_feast_transformer.py"
  modified: []

key-decisions:
  - "HTTP 400 (kserve.errors.InvalidInput) on all-None features, not HTTP 503: unresolvable entity is a client error, not a service failure"
  - "FeatureStore initialised once at __init__ time to avoid 50-200ms per-request registry fetch"
  - "ONLINE_FEATURES list order matches feast_store.py _ONLINE_FEATURES: [close, daily_return, rsi_14, macd_line, lag_1, rolling_mean_5]"
  - "None feature values substituted with 0.0 (partial-None case) — only all-None triggers 400"

patterns-established:
  - "KServe transformer pattern: extend Model, implement preprocess() + postprocess(), init FeatureStore once"
  - "Test isolation via __new__ + manual attribute injection allows mocking without live FeatureStore"

requirements-completed: [PIT-02, PIT-03]

# Metrics
duration: 2min
completed: "2026-04-03"
---

# Phase 87 Plan 01: FeastTransformer Service Summary

**KServe Feast Transformer service with FeatureStore singleton, V2 InferRequest assembly, HTTP 400 on unknown ticker, and 4 passing unit tests (no live Feast/Redis needed)**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-03T08:49:31Z
- **Completed:** 2026-04-03T08:51:35Z
- **Tasks:** 2 completed
- **Files modified:** 4

## Accomplishments

- Created `FeastTransformer(kserve.Model)` with `preprocess()`, `postprocess()`, `_get_features()` and `__main__` ModelServer entry point
- FeatureStore initialised once at `__init__` time — avoids 50-200ms per-request registry fetch overhead; confirmed by `test_feast_store_initialised_once`
- preprocess() raises `kserve.errors.InvalidInput` (HTTP 400) when all feature values are None — semantically correct (bad entity, not transient service failure)
- 4 unit tests cover PIT-02 (V2 InferRequest assembly) and PIT-03 (HTTP 400 on no features), plus None-to-zero substitution and FeatureStore singleton guarantee

## Task Commits

Each task was committed atomically:

1. **Task 1: Create FeastTransformer service (feast_transformer.py, requirements.txt, Dockerfile)** - `a406755` (feat)
2. **Task 2: Write unit tests for FeastTransformer (test_feast_transformer.py)** - `fc84ebf` (test)

**Plan metadata:** (docs commit follows this summary)

## Files Created/Modified

- `stock-prediction-platform/services/feast-transformer/feast_transformer.py` - FeastTransformer kserve.Model subclass with preprocess/postprocess/\_get\_features
- `stock-prediction-platform/services/feast-transformer/requirements.txt` - kserve==0.16.0, feast[postgres,redis]==0.61.0
- `stock-prediction-platform/services/feast-transformer/Dockerfile` - python:3.11-slim, HEALTHCHECK on /v2/health/ready, CMD python feast\_transformer.py
- `stock-prediction-platform/services/api/tests/test_feast_transformer.py` - 4 unit tests covering PIT-02 and PIT-03

## Decisions Made

- **HTTP 400 vs 503**: ROADMAP originally described PIT-03 as "raises HTTP 503". Changed to HTTP 400 (`kserve.errors.InvalidInput`) because an unknown/unmaterialised ticker is a client-side bad-request entity error, not a transient service unavailability. HTTP 503 would mislead callers into retrying.
- **FeatureStore singleton**: Feast's synchronous Redis client initialises registry metadata on construction (50-200ms). Storing `self._store` in `__init__` avoids this overhead on every preprocess() call.
- **ONLINE\_FEATURES key order**: Confirmed 6-feature order `[close, daily_return, rsi_14, macd_line, lag_1, rolling_mean_5]` matches `feast_store.py` `_ONLINE_FEATURES` — the same list used during training feature materialisation.
- **None-to-zero substitution**: Partial-None features (some features available, some not) are substituted with 0.0 so inference can proceed. Only all-None (ticker completely unmaterialised) raises InvalidInput.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- `kserve` was not installed in the API test environment (not in `requirements.txt`). Installed `kserve==0.16.0` into the dev environment to run tests. This is correct behaviour — the test file lives in the API test suite for organisational convenience but tests a separate service whose own `requirements.txt` carries kserve.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `services/feast-transformer/` artifact is ready for Plan 87-03 which adds it as a KServe InferenceService transformer container
- Tests validate the core PIT-02 and PIT-03 behaviour without live infrastructure
- No blockers

---
*Phase: 87-point-in-time-correct-feature-serving-feast-kserve-transformer-backtest-lookahead-leakage*
*Completed: 2026-04-03*

## Self-Check: PASSED

- feast_transformer.py: FOUND
- requirements.txt: FOUND
- Dockerfile: FOUND
- test_feast_transformer.py: FOUND
- 87-01-SUMMARY.md: FOUND
- Commit a406755 (Task 1): FOUND
- Commit fc84ebf (Task 2): FOUND
