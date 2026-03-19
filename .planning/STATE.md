---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
stopped_at: Completed 05-01-PLAN.md
last_updated: "2026-03-19T08:43:57.042Z"
progress:
  total_phases: 30
  completed_phases: 4
  total_plans: 12
  completed_plans: 11
---

# STATE.md — Project Memory

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-18)

**Core value:** The winner ML model is always the best-performing, drift-aware regressor — automatically retrained and redeployed whenever prediction quality degrades.
**Current focus:** Phase 05 — kafka-via-strimzi

## Current Status

- **Active phase:** 5
- **Phase name:** Kafka via Strimzi
- **Overall progress:** 4 / 30 phases complete

## Phase Completion Log

| Phase | Name | Status | Completed |
|-------|------|--------|-----------|
| 1 | Repo & Folder Scaffold | Complete (3/3 plans) | 2026-03-18 |
| 2 | Minikube & K8s Namespaces | Complete (2/2 plans) | 2026-03-18 |
| 3 | FastAPI Base Service | Complete (3/3 plans) | 2026-03-19 |
| 4 | PostgreSQL + TimescaleDB | Complete (3/3 plans) | 2026-03-19 |
| 5 | Kafka via Strimzi | Not started | — |
| 6 | Yahoo Finance Ingestion Service | Not started | — |
| 7 | FastAPI Ingestion Endpoints | Not started | — |
| 8 | K8s CronJobs for Ingestion | Not started | — |
| 9 | Kafka Consumers — Batch Writer | Not started | — |
| 10 | Technical Indicators | Not started | — |
| 11 | Lag Features & Transformer Pipelines | Not started | — |
| 12 | Linear & Regularized Models | Not started | — |
| 13 | Tree-Based & Boosting Models | Not started | — |
| 14 | Distance, SVM & Neural Models | Not started | — |
| 15 | Evaluation Framework & Model Selection | Not started | — |
| 16 | SHAP Explainability | Not started | — |
| 17 | Kubeflow Pipeline — Data & Feature Components | Not started | — |
| 18 | Kubeflow Pipeline — Training & Eval Components | Not started | — |
| 19 | Kubeflow Pipeline — Selection, Persistence & Deployment | Not started | — |
| 20 | Kubeflow Pipeline — Full Definition & Trigger | Not started | — |
| 21 | Drift Detection System | Not started | — |
| 22 | Drift Auto-Retrain Trigger | Not started | — |
| 23 | FastAPI Prediction & Model Endpoints | Not started | — |
| 24 | FastAPI Market Endpoints | Not started | — |
| 25 | React App Bootstrap & Navigation | Not started | — |
| 26 | Frontend — /models Page | Not started | — |
| 27 | Frontend — /forecasts Page | Not started | — |
| 28 | Frontend — /dashboard Page | Not started | — |
| 29 | Frontend — /drift Page | Not started | — |
| 30 | Integration Testing & Seed Data | Not started | — |

## Decisions

- **Phase 1 Plan 01:** Created __init__.py for all ml/ subdirectories to ensure importability as Python packages
- **Phase 1 Plan 01:** Used minimal stub pattern (docstring + future annotations only) per specification
- [Phase 01]: Replaced full docker-compose.yml with stub-only definitions (image+ports) per plan specification
- [Phase 01]: Used stdlib LoggerFactory instead of PrintLoggerFactory for filter_by_level compatibility
- [Phase 02]: Used 120s timeout for kubectl wait node readiness
- [Phase 02]: Plain echo output with === separators, no colour codes for CI compatibility
- [Phase 02]: check_command function in setup-minikube.sh, inline checks in deploy-all.sh
- [Phase 02 Plan 02]: No code changes needed -- scripts from Plan 01 executed correctly on first run against live cluster
- [Phase 03 Plan 01]: Used lifespan context manager (not deprecated on_startup/on_shutdown)
- [Phase 03 Plan 01]: Added -p no:logfire to pytest.ini to work around broken logfire plugin in environment
- [Phase 03 Plan 02]: Used imagePullPolicy: Never for local Minikube development (no registry needed)
- [Phase 03 Plan 02]: Installed curl in runtime Docker stage for HEALTHCHECK command
- [Phase 03 Plan 02]: Copied /usr/local/bin from builder to ensure uvicorn binary available in runtime stage
- [Phase 04]: Used dry-run=client -o yaml | kubectl apply pattern for idempotent Secret and ConfigMap creation
- [Phase 04]: Removed phantom postgres-service.yaml reference from deploy-all.sh — Service is embedded in postgresql-deployment.yaml
- [Phase 04]: Corrected deploy-all.sh file names: postgres-* prefix -> postgresql-*, postgres-configmap.yaml -> configmap.yaml
- [Phase 04-01]: CREATE EXTENSION without CASCADE: TimescaleDB image has no unmet dependencies; explicit is more predictable
- [Phase 04-01]: Transaction wrapping (BEGIN/COMMIT) in init.sql prevents half-initialized database state
- [Phase 04-01]: updated_at trigger on stocks table provides database-level updated_at guarantee
- [Phase 04-03]: No file changes needed in Plan 03 — artefacts from Plans 01 and 02 deployed correctly on first run
- [Phase 04-03]: Human checkpoint used as final DB gate — automated smoke tests cover CI, human visual confirms full schema correctness
- [Phase 05]: Strimzi operator YAML downloaded and committed for offline reproducibility (not fetched at runtime)
- [Phase 05]: Used targeted sed (namespace: myproject -> storage) to avoid replacing unrelated namespace refs
- [Phase 05]: Operator install in setup-minikube.sh with 300s wait; workloads in deploy-all.sh (established pattern)

## Last Session

- **Stopped at:** Completed 05-01-PLAN.md
- **Timestamp:** 2026-03-19T07:50:02Z

## Notes

(Add notes here as work progresses)
