# Phase 68: E2E Integration — v3.0 Stack Validation - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Run end-to-end validation of the complete v3.0 data platform proving all five success criteria:
1. OLAP candle query ≥10x faster than raw hypertable
2. Argo CD GitOps loop auto-syncs a pushed ConfigMap change within 3 minutes
3. Feast offline path (get_historical_features) used in training with no future-leakage
4. Feast online features are fresh (<2 min old) after materialization, served via /predict/AAPL
5. Full Flink pipeline: /ingest/intraday → TimescaleDB upsert within 10s → processed-features topic → Feast online store → /predict/AAPL with fresh features

New code is limited to: validate-v3.sh script, any Alembic migration needed for OLAP schema, and Playwright spec additions for Argo CD UI + Flink Web UI. No new API endpoints in this phase.

</domain>

<decisions>
## Implementation Decisions

### Validation Script Format
- One script: `scripts/validate-v3.sh` covering all 5 success criteria in sequence
- Use the same bash `check()` helper pattern established in `validate-argocd.sh` (Phase 65): PASS/FAIL output, `trap cleanup EXIT`, port-forward lifecycle
- Script is invoked after `deploy-all.sh` and assumes the cluster is running

### OLAP Benchmark (Success Criterion 1)
- Two `curl` calls timed with bash `time` builtin: one against raw `ohlcv_intraday` via a direct psql query, one against `GET /market/candles?ticker=AAPL&interval=1h&days=30`
- Compute ratio inline, log both durations and the ratio to stdout
- Pass criterion if ratio ≥10x

### Argo CD Sync Test (Success Criterion 2)
- Script makes a real git commit + push: edit a throwaway annotation (e.g., `validate/timestamp`) in a ConfigMap YAML, `git commit`, `git push origin master`
- Wait up to 3 minutes polling `argocd app get root-app --output json` for `operationState.phase=Succeeded` after the push
- Proves the full GitOps loop is actively working, not just checking static Synced status

### Test Data Strategy
- Script assumes data is already ingested — run after a normal `/ingest/intraday` call has populated the DB
- Script does NOT seed its own data; it only asserts against existing cluster state
- Exception: Feast materialization — the script calls `python -m ml.feature_store.materialize` for AAPL just before asserting online feature freshness

### Feast Validation (Success Criteria 3 & 4)
- Offline path: assert `engineer_features(use_feast=True)` completes without error on an existing entity_df from the DB (not a full training run — just the feature retrieval step)
- Online path: run `python -m ml.feature_store.materialize`, then POST to `/predict/AAPL` and check that `feature_timestamp` in the response is <2 minutes old

### Flink Pipeline Trigger (Success Criterion 5)
- Trigger: `POST /ingest/intraday` for AAPL (1 ticker) via curl — proves the full path including the ingestion API, not just Kafka injection
- Poll assertion: loop every 3s, timeout at 30s — check for a new `ohlcv_intraday` row with a timestamp ≥ now-10s via psql
- After DB row confirmed: check `processed-features` Kafka topic has a recent message (kafkacat/kcat consumer offset check), then assert `/predict/AAPL` returns a fresh prediction

### Claude's Discretion
- Exact port-forward commands and kubectl wait flags within validate-v3.sh
- Order of the 5 checks within the script (logical dependency order is fine)
- Playwright spec file names for Argo CD UI and Flink Web UI additions

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Validation pattern reference
- `stock-prediction-platform/scripts/validate-argocd.sh` — Established check() helper pattern, port-forward lifecycle, trap cleanup, PASS/FAIL output format to replicate

### OLAP endpoint (Phase 64)
- `.planning/phases/64-timescaledb-olap-continuous-aggregates-compression/64-02-SUMMARY.md` — GET /market/candles endpoint, interval→view mapping, supported intervals (1h, 1d)

### Argo CD (Phase 65)
- `.planning/phases/65-argo-cd-gitops-deployment-pipeline/65-02-SUMMARY.md` — argocd CLI patterns, app-of-apps structure, validate-argocd.sh design

### Feast (Phase 66)
- `.planning/phases/66-feast-production-feature-store/66-03-SUMMARY.md` — materialize.py invocation, online feature retrieval, get_online_features_for_ticker()

### Flink (Phase 67)
- `.planning/phases/67-apache-flink-real-time-stream-processing/67-03-SUMMARY.md` — Flink job deployment pattern, deploy-all.sh Phase 67 block, FlinkDeployment CR structure

### Playwright infra suite (Phase 62)
- `stock-prediction-platform/services/frontend/e2e/infra/` — Existing minio.spec.ts, grafana.spec.ts, kubeflow.spec.ts patterns to replicate for argocd and flink-web-ui specs

### Success criteria (source of truth)
- `.planning/ROADMAP.md` §"Phase 68: E2E Integration" — exact pass/fail thresholds (≥10x, <200ms, <2 min, 10s, 3 min)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `stock-prediction-platform/scripts/validate-argocd.sh` — check() helper, port-forward lifecycle, cleanup trap — copy and extend for validate-v3.sh
- `stock-prediction-platform/ml/feature_store/materialize.py` — `run_materialization()` callable as `python -m ml.feature_store.materialize`
- `stock-prediction-platform/services/frontend/e2e/infra/` — Playwright infra spec pattern (navigate to URL, assert heading/status element) to replicate for Argo CD UI + Flink Web UI specs

### Established Patterns
- Bash validation: check() with port-forward, PASS/FAIL, TOTAL_PASS/TOTAL_FAIL counter, exit code = number of failures
- Playwright infra specs: `page.goto(URL)`, `expect(page).toHaveTitle()`, basic element visibility assertions
- psql query in bash: `kubectl exec -n storage deploy/postgres -- psql -U postgres -d stocks -c "SELECT ..."`

### Integration Points
- validate-v3.sh runs after deploy-all.sh; requires cluster fully up (all phases deployed)
- Playwright argocd.spec.ts connects to Argo CD UI via port-forward or NodePort (check how existing infra specs handle URLs)
- Flink Web UI accessible at Flink REST port — FlinkDeployment exposes port 8081

</code_context>

<specifics>
## Specific Ideas

- The Argo CD sync test should edit a throwaway annotation key like `validate/last-checked` in a non-critical ConfigMap (e.g., one in k8s/ingestion/) so the git history is clean and the change is idempotent across runs
- After the Flink E2E check, the script should reset/revert the git annotation commit so the repo is clean after validation

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 68-e2e-integration-v3-0-stack-validation*
*Context gathered: 2026-03-30*
