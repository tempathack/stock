# Phase 62: Playwright E2E — Infra UI Coverage - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Write Playwright E2E tests for every non-React UI exposed by deploy-all.sh: Grafana login + 3 dashboards + 2 datasources, Prometheus query execution + targets + alerts, MinIO Console login + bucket existence + object navigation, Kubeflow Pipelines UI navigation, and Kubernetes Dashboard cluster overview. Tests hit the live deployed stack — no route interceptors, no mocks. A standalone `playwright.infra.config.ts` with multi-project setup (one project per service/port) is included.

</domain>

<decisions>
## Implementation Decisions

### Service availability policy
- All 5 services use the same policy: HTTP probe in `beforeAll`, skip entire file if service is unreachable
- Probe timeout: 5 seconds (tolerant of slow port-forwards)
- Skip with a descriptive message: `test.skip(true, 'Grafana not reachable at http://localhost:3000')`
- This applies uniformly to Grafana, Prometheus, MinIO, Kubeflow, and K8s Dashboard — no "required vs optional" distinction
- Fail on test failures, not on connectivity failures

### Credential sourcing
- Env vars with hardcoded dev defaults — zero config for standard local setup
- All credentials defined in `helpers/auth.ts`, which all spec files import
- Defaults: `GRAFANA_USER ?? 'admin'`, `GRAFANA_PASSWORD ?? 'admin'`, `MINIO_USER ?? 'CHANGEME'`, `MINIO_PASSWORD ?? 'CHANGEME'`
- No dotenv/`.env.infra` file — plain env var reads with inline fallbacks

### K8s Dashboard auth
- Token supplied via `KUBERNETES_DASHBOARD_TOKEN` env var
- If not set: `test.skip(true, 'KUBERNETES_DASHBOARD_TOKEN not set — run: kubectl -n kubernetes-dashboard create token kubernetes-dashboard')` — no Skip button fallback
- Dashboard URL: hardcoded default `http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/` with `K8S_DASHBOARD_URL` env var override
- `loginK8sDashboard(page, token)` helper in `helpers/auth.ts`

### Claude's Discretion
- Exact selector strategy for third-party UIs (role-based, text-based, or CSS selectors)
- Retry/wait logic within tests for slow-rendering panels (Grafana charts especially)
- Exact structure of `playwright.infra.config.ts` multi-project projects array

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Infra services
- `stock-prediction-platform/scripts/deploy-all.sh` — Port assignments and service startup order for all 5 services
- `stock-prediction-platform/k8s/storage/minio-configmap.yaml` — MinIO default credentials (CHANGEME/CHANGEME)
- `stock-prediction-platform/k8s/monitoring/prometheus-configmap.yaml` — Prometheus scrape jobs and expected job labels

### Grafana provisioning
- `stock-prediction-platform/monitoring/grafana/provisioning/dashboards/` — Dashboard definitions (dashboard titles, panel names)
- `stock-prediction-platform/monitoring/grafana/provisioning/datasources/` — Datasource definitions (Prometheus uid: prometheus, Loki uid: loki)

### Existing Playwright infrastructure
- `stock-prediction-platform/services/frontend/playwright.config.ts` — Existing config (baseURL 3000, fullyParallel, webServer) — new infra config must NOT inherit webServer
- `stock-prediction-platform/services/frontend/e2e/fixtures/api.ts` — Existing fixture pattern (for reference only — infra tests don't use fixtures)

No external specs — requirements fully captured in decisions above and existing plans.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `stock-prediction-platform/services/frontend/playwright.config.ts`: Existing config pattern — `playwright.infra.config.ts` follows same defineConfig structure but with `webServer` removed (infra services are already running, not started by Playwright)
- `stock-prediction-platform/services/frontend/e2e/` directory: Infra tests go in `tests/e2e/infra/` subdirectory within the same frontend package

### Established Patterns
- Phase 61 used `fullyParallel: false` for spec files needing serial execution — infra tests similarly should use `fullyParallel: false` (live services, shared state)
- Phase 61 pattern: `test.beforeEach` for per-test setup, `beforeAll` for suite-level (service probe belongs in `beforeAll`)
- No route interceptors in infra tests — this is the key difference from Phase 61 specs

### Integration Points
- New `playwright.infra.config.ts` at `stock-prediction-platform/services/frontend/` (same level as existing config)
- New npm scripts in `stock-prediction-platform/services/frontend/package.json` — `test:infra` runs separate from `test:e2e`
- Auth helpers at `tests/e2e/infra/helpers/auth.ts` — shared by all 5 spec files

</code_context>

<specifics>
## Specific Ideas

- The HTTP probe in `beforeAll` should use the Playwright `request` fixture (not Node `fetch`) to stay within Playwright's request context
- K8s Dashboard skip message should include the exact kubectl command to generate the token, making it self-documenting for developers

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 62-playwright-e2e-infra-grafana-prometheus-minio-kubeflow-k8s-dashboard*
*Context gathered: 2026-03-25*
