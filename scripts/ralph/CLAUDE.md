# Ralph Agent Instructions — Stock Prediction Platform

You are an autonomous coding agent. You work on the **stock-prediction-platform** project. Each iteration you implement exactly ONE user story from `scripts/ralph/prd.json`, run quality checks, commit, and move on.

---

## Project Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI (Python 3.11), Uvicorn |
| Database | PostgreSQL 15 + TimescaleDB, Redis 7 |
| Streaming | Apache Kafka via Strimzi operator |
| ML | scikit-learn, XGBoost, LightGBM, CatBoost, SHAP |
| ML Ops | Kubeflow Pipelines v2.3, KServe v0.14 |
| Model Storage | MinIO (S3-compatible) |
| Frontend | React (Vite), **MUI v5**, Recharts, Lightweight Charts |
| Infra | Minikube / Kubernetes, Docker (multi-stage) |
| Monitoring | Prometheus, Grafana, Loki, Promtail, Alertmanager |
| Testing | pytest (backend), Playwright (E2E frontend + infra) |

---

## Directory Layout

```
stock-prediction-platform/
├── services/
│   ├── api/                   # FastAPI backend
│   │   ├── app/routers/       # ingest.py, predict.py, models.py, market.py, health.py
│   │   ├── app/services/      # yahoo_finance.py, kafka_producer.py, prediction_service.py
│   │   └── tests/             # pytest tests
│   ├── kafka-consumer/        # Batch DB writer
│   └── frontend/              # React/Vite app
│       ├── src/
│       │   ├── pages/         # Dashboard.tsx, Forecasts.tsx, Models.tsx, Drift.tsx, Backtest.tsx
│       │   ├── components/    # Feature-organized components
│       │   ├── theme/         # MUI theme (index.ts) — create if not exists
│       │   └── api/           # API client
│       ├── e2e/               # Playwright specs
│       │   ├── *.spec.ts      # Main app specs (dashboard, forecasts, models, drift, backtest)
│       │   ├── infra/         # Infra specs (grafana, prometheus, minio, kubeflow, k8s-dashboard)
│       │   ├── fixtures/      # api.ts fixture functions
│       │   └── helpers/       # auth.ts, production-guard.ts (create if not exists)
│       ├── playwright.config.ts           # Fixture-based CI config
│       ├── playwright.infra.config.ts     # Infra services config
│       └── playwright.production.config.ts  # Production config (create)
├── ml/                        # ML pipeline components
├── k8s/                       # Kubernetes manifests
│   ├── monitoring/            # Prometheus, Grafana, Alertmanager, Loki, Promtail
│   ├── ml/kubeflow/           # KFP install, compile job
│   └── dashboard/             # K8s Dashboard manifest (create if missing)
├── scripts/
│   ├── deploy-all.sh          # Full stack deploy + port-forwards
│   ├── run-production-tests.sh  # Production E2E runner (create)
│   └── submit-pipeline.sh     # KFP pipeline submit (create if missing)
├── monitoring/
│   └── prometheus.yml
└── docker-compose.yml
```

---

## Your Task Per Iteration

1. Read `scripts/ralph/prd.json` — find highest priority story where `passes: false`
2. Read `scripts/ralph/progress.txt` — check **Codebase Patterns** section first
3. Check out or create branch from `prd.json branchName` field if not already on it
4. Implement the story fully
5. Run quality checks (see below)
6. If checks pass, commit ALL changes: `feat: [Story ID] - [Story Title]`
7. Set `passes: true` for the completed story in `prd.json`
8. Append progress to `scripts/ralph/progress.txt`

---

## Quality Checks

```bash
# TypeScript compile check (REQUIRED for any frontend change)
cd stock-prediction-platform/services/frontend && npx tsc --noEmit 2>&1 | head -30

# Frontend build (REQUIRED — catches bundling errors)
cd stock-prediction-platform/services/frontend && npm run build 2>&1 | tail -20

# Backend tests (run for any Python change)
cd stock-prediction-platform && python -m pytest services/api/tests/ -x -q -p no:logfire 2>&1 | tail -20

# Playwright test list (verify no import errors after spec changes)
cd stock-prediction-platform/services/frontend && npx playwright test --config=playwright.config.ts --list 2>&1 | tail -20
cd stock-prediction-platform/services/frontend && npx playwright test --config=playwright.production.config.ts --list 2>&1 | tail -20
```

**Rules:**
- Frontend TypeScript must compile with 0 errors before committing
- `npm run build` must succeed before committing
- Backend pytest failures in modified modules must be fixed before committing
- Playwright `--list` must produce no TypeScript/import errors

---

## Critical Codebase Patterns

**Playwright:**
- ALL main app spec files use `test.describe.configure({ mode: 'serial' })` — never remove this
- Playwright LIFO route matching: register specific routes LAST (they match first)
- `rolling-performance` route must be registered BEFORE `models/drift` in drift.spec.ts
- Infra tests use graceful `test.skip()` (service unreachable) and `test.fixme()` (service up but no data)
- `test.fixme()` is NOT a failure — it means infrastructure not bootstrapped yet, which is expected
- Playwright infra config: no webServer block, no baseURL, workers: 1

**MUI v5:**
- Theme lives in `src/theme/index.ts`, wrapped via `<ThemeProvider>` in `src/main.tsx`
- Use `@mui/x-data-grid` for all tabular data (replaces custom tables)
- Use `@mui/x-charts <BarChart layout="horizontal">` for SHAP feature importance
- Use `@mui/lab <Timeline>` for drift events, `<LoadingButton>` for async actions
- Dark theme background: `#0a0e1a` (default), `#111827` (paper/cards)
- Primary color: `#00bcd4` (Bloomberg cyan)
- Install @mui/lab separately: `npm install @mui/lab`

**FastAPI:**
- All endpoints return 502 (not 500) for upstream failures (Yahoo Finance, Kafka)
- `/predict/bulk` must be registered before `/{ticker}` — path variable capture bug
- psycopg2 imports are lazy (inside functions) so API starts without DB
- Protected namespaces disabled on Pydantic models with `model_name` field

**Python / ML:**
- yfinance >= 1.0: use `.droplevel(1)` after `.download()` for MultiIndex columns
- SHAP imports guarded with `_shap_available` flag (numba requires numpy<2.0)
- All pytest runs: add `-p no:logfire` flag
- Target is percentage return (pct_change), not raw future price
- TimeSeriesSplit only — NO random splits, NO shuffling

**Kubernetes:**
- Use `imagePullPolicy: Never` for all local Minikube deployments
- K8s secrets cannot cross namespaces — copy via: `kubectl get secret <n> -n storage -o yaml | kubectl apply -n <target>`
- K8s Dashboard uses hash routing (`#/!/`) — use DOM clicks not `waitForURL`
- KFP Pipelines UI also uses hash routing (`#/pipelines`)
- `kubectl port-forward` PIDs tracked in `/tmp/pf-*.pid`

**Docker:**
- Build images in Minikube context: `eval $(minikube docker-env)` before `docker build`
- All images tagged `:latest` for local dev

---

## Progress Report Format

APPEND to `scripts/ralph/progress.txt` (never overwrite):

```
## [Date/Time] - [Story ID]: [Story Title]
- What was implemented
- Files created/modified
- **Learnings for future iterations:**
  - Key patterns or gotchas
---
```

Update the `## Codebase Patterns` section at the top of progress.txt if you discover something non-obvious that future iterations should know.

---

## GSD Phase Cross-Reference

Before marking any story `passes: true`, cross-check it against the GSD planning phases in `.planning/phases/`. The phases document what was *planned and built* — use them to verify nothing was missed.

**Key phases to reference:**

| Phase | What to verify |
|-------|---------------|
| 25–29 | All 4 frontend pages exist and have all components listed in phase plans |
| 37–38 | Prometheus metrics exposed by FastAPI + Grafana dashboards present with correct panel names |
| 39 | Loki/Promtail log aggregation → verify Loki datasource in Grafana |
| 42 | Ensemble stacking model → must appear in /models/comparison as a trained model |
| 43 | Multi-horizon predictions (1d, 7d, 30d) → /predict/bulk?horizon= works for all 3 |
| 45 | WebSocket live prices → if implemented, verify ws:// endpoint is live |
| 46 | Backtesting UI → Backtest page fully functional |
| 47 | Redis caching → verify /predict/bulk response time < 500ms on second call |
| 49 | A/B model testing → /models/comparison shows A/B test results if configured |
| 51 | MinIO deployment → model-artifacts and drift-logs buckets exist |
| 54–55 | KServe InferenceService → check if active in ml namespace |
| 59 | Minikube E2E flow → all port-forwards reachable |
| 61–63 | Playwright E2E specs → all 5 main specs passing |
| 62 | Infra specs (Grafana, Prometheus, MinIO, Kubeflow, K8s Dashboard) → all probing correctly |

**How to use:** When a story says "verify X endpoint", open the relevant phase plan in `.planning/phases/<phase-number>/` to see the exact implementation details, endpoint schemas, and acceptance criteria. If the production behavior doesn't match the phase plan's acceptance criteria, fix the gap.

**Phase plan location:** `.planning/phases/<phase-number>/<phase-number>-01-PLAN.md` (or similar)

---

## Stop Condition

After completing a story, check if ALL stories in prd.json have `passes: true`.

If yes → reply with:
```
<promise>COMPLETE</promise>
```

If no → end your response normally. Ralph will spawn a new context for the next story.

---

## Important Rules

- ONE story per iteration — do not attempt multiple stories
- Never modify `scripts/ralph/ralph.sh`
- Commit atomically — one commit per story
- Do not skip quality checks — broken code compounds across iterations
- Read `scripts/ralph/progress.txt` Codebase Patterns section before every iteration
- The prd.json is at `scripts/ralph/prd.json` relative to the repo root
