---
phase: 08-k8s-cronjobs-for-ingestion
plan: "01"
subsystem: infra
tags: [kubernetes, cronjob, httpx, python, ingestion, fastapi]

requires:
  - phase: 07-fastapi-ingestion-endpoints
    provides: /ingest/intraday and /ingest/historical FastAPI endpoints the CronJobs call

provides:
  - cronjob-intraday.yaml: K8s CronJob running every 5 min on NYSE weekday hours (*/5 14-21 * * 1-5)
  - cronjob-historical.yaml: K8s CronJob running weekly on Sundays at 02:00 UTC (0 2 * * 0)
  - trigger_intraday.py: Python script POSTing to /ingest/intraday, exit 0/1
  - trigger_historical.py: Python script POSTing to /ingest/historical, exit 0/1
  - 18-test suite covering success, HTTP error, connection error, timeout, URL, timeout kwarg, zero records, read error

affects: [09-kafka-consumers-batch-writer, 34-k8s-ml-cronjobs-model-serving, deploy-all.sh]

tech-stack:
  added: [httpx==0.27.0]
  patterns:
    - CronJob containers reuse the stock-api:latest image (imagePullPolicy Never for Minikube)
    - envFrom configMapRef ingestion-config injects API_BASE_URL and TRIGGER_TIMEOUT_SECONDS
    - concurrencyPolicy Forbid prevents overlapping ingest runs
    - Python trigger scripts follow exit-code contract (0=success, 1=any failure)

key-files:
  created:
    - stock-prediction-platform/k8s/ingestion/cronjob-intraday.yaml
    - stock-prediction-platform/k8s/ingestion/cronjob-historical.yaml
    - stock-prediction-platform/services/api/app/jobs/__init__.py
    - stock-prediction-platform/services/api/app/jobs/trigger_intraday.py
    - stock-prediction-platform/services/api/app/jobs/trigger_historical.py
    - stock-prediction-platform/services/api/tests/test_cronjob_triggers.py
  modified:
    - stock-prediction-platform/services/api/requirements.txt (httpx==0.27.0 added)
    - stock-prediction-platform/scripts/deploy-all.sh (Phase 8 CronJob apply block added)

key-decisions:
  - "timeZone: America/New_York on intraday CronJob aligns schedule with NYSE hours (09:30-16:05 ET)"
  - "No timeZone field on historical CronJob — defaults to cluster UTC, appropriate for weekly off-hours run"
  - "startingDeadlineSeconds: 60 for intraday (tight), 300 for historical (more lenient — weekly)"
  - "TRIGGER_TIMEOUT_SECONDS: 300 intraday / 600 historical injected via env; read by httpx timeout"
  - "imagePullPolicy: Never for both CronJobs — local Minikube dev, no remote registry needed"
  - "backoffLimit: 3 gives three pod retry attempts before marking Job failed"

patterns-established:
  - "Trigger script pattern: read env → httpx.post → raise_for_status → log → exit code"
  - "Two distinct httpx exception branches: HTTPStatusError (4xx/5xx) and RequestError (network)"
  - "CronJob containers are thin callers — no business logic, just HTTP trigger + exit code"

requirements-completed: [INGEST-04, INGEST-05]

duration: 15min
completed: 2026-03-25
---

# Phase 8 Plan 01: K8s CronJob Manifests, Trigger Scripts, and Deployment Wiring Summary

**Two K8s CronJobs (intraday every 5 min on NYSE weekdays, historical weekly on Sundays) using httpx Python trigger scripts and 18-test coverage for success/error/timeout/URL/zero-records paths.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-25T00:00:00Z
- **Completed:** 2026-03-25T00:15:00Z
- **Tasks:** 7 (T01-T07)
- **Files modified:** 8

## Accomplishments

- Two K8s CronJob manifests with correct schedules, concurrencyPolicy Forbid, restartPolicy OnFailure, and ConfigMap environment injection
- Python trigger modules (`trigger_intraday.py`, `trigger_historical.py`) with exit-code contract (0=success, 1=any failure) using httpx
- 18-test pytest suite covering both trigger modules: success, HTTP error, connection error, timeout, URL correctness, timeout kwarg, zero records, and ReadError paths
- `httpx==0.27.0` added to requirements.txt; deploy-all.sh wired with Phase 8 `kubectl apply` block after FastAPI deployment

## Task Commits

Each task was committed atomically:

1. **Task 01: Create cronjob-intraday.yaml** - pre-existing (committed in prior execution)
2. **Task 02: Create cronjob-historical.yaml** - pre-existing (committed in prior execution)
3. **Task 03: Create trigger_intraday.py** - pre-existing (committed in prior execution)
4. **Task 04: Create trigger_historical.py** - pre-existing (committed in prior execution)
5. **Task 05: Ensure httpx in requirements.txt** - pre-existing (committed in prior execution)
6. **Task 06: Wire CronJob manifests into deploy-all.sh** - pre-existing (committed in prior execution)
7. **Task 07: Write unit tests** - `b76aa01` (feat: complete 18-test suite for CronJob trigger modules)

**Plan metadata:** committed with docs commit below

## Files Created/Modified

- `stock-prediction-platform/k8s/ingestion/cronjob-intraday.yaml` - Intraday CronJob: `*/5 14-21 * * 1-5`, timeZone America/New_York, concurrencyPolicy Forbid
- `stock-prediction-platform/k8s/ingestion/cronjob-historical.yaml` - Historical CronJob: `0 2 * * 0`, concurrencyPolicy Forbid, 1Gi RAM limit
- `stock-prediction-platform/services/api/app/jobs/__init__.py` - Package marker
- `stock-prediction-platform/services/api/app/jobs/trigger_intraday.py` - HTTP trigger with exit-code contract
- `stock-prediction-platform/services/api/app/jobs/trigger_historical.py` - HTTP trigger with exit-code contract
- `stock-prediction-platform/services/api/tests/test_cronjob_triggers.py` - 18 tests (9 intraday + 9 historical)
- `stock-prediction-platform/services/api/requirements.txt` - Added `httpx==0.27.0`
- `stock-prediction-platform/scripts/deploy-all.sh` - Phase 8 CronJob apply block

## Decisions Made

- `timeZone: "America/New_York"` on intraday CronJob aligns cron expression with NYSE hours (09:30–16:05 ET)
- No `timeZone` on historical CronJob — UTC default is appropriate for a quiet-window weekly run
- `imagePullPolicy: Never` for both CronJobs to use locally-built Minikube image without a registry
- `TRIGGER_TIMEOUT_SECONDS: 300` (intraday) vs `600` (historical) reflects relative job complexity

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Tests] Expanded test suite from 9 to 18 tests**
- **Found during:** Task 07 verification
- **Issue:** Existing test file had only 9 tests (5 intraday + 4 historical) instead of the 18 specified; missing: posts_correct_url, uses_timeout, zero_records, read_error for intraday; and custom_base_url, posts_correct_url, uses_timeout, zero_records, read_error for historical
- **Fix:** Added 9 missing test functions matching the plan specification exactly
- **Files modified:** `stock-prediction-platform/services/api/tests/test_cronjob_triggers.py`
- **Verification:** `python -m pytest tests/test_cronjob_triggers.py -v` — 18 passed
- **Committed in:** `b76aa01`

---

**Total deviations:** 1 auto-fixed (missing tests completed to match plan specification)
**Impact on plan:** All 18 planned tests now present and passing. No scope creep.

## Issues Encountered

None — all infrastructure files (YAML manifests, Python scripts, requirements.txt, deploy-all.sh wiring) were already correctly in place from prior execution. Only the test count gap required remediation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 9 (Kafka Consumers — Batch Writer) can proceed: CronJobs will trigger the FastAPI ingest endpoints that produce to Kafka topics
- Both CronJobs are wired into deploy-all.sh and will apply on next full deploy
- kubectl dry-run validation confirms both YAMLs are syntactically valid K8s objects

---
*Phase: 08-k8s-cronjobs-for-ingestion*
*Completed: 2026-03-25*

## Self-Check: PASSED

- FOUND: stock-prediction-platform/k8s/ingestion/cronjob-intraday.yaml
- FOUND: stock-prediction-platform/k8s/ingestion/cronjob-historical.yaml
- FOUND: stock-prediction-platform/services/api/app/jobs/trigger_intraday.py
- FOUND: stock-prediction-platform/services/api/app/jobs/trigger_historical.py
- FOUND: stock-prediction-platform/services/api/tests/test_cronjob_triggers.py
- FOUND: .planning/phases/08-k8s-cronjobs-for-ingestion/08-01-SUMMARY.md
- FOUND: commit b76aa01 (feat: complete 18-test suite)
