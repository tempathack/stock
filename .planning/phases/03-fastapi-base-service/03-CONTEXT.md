# Phase 3: FastAPI Base Service - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the FastAPI application skeleton: wire `main.py`, `config.py`, and `health.py`, produce a working multi-stage Dockerfile, and write K8s Deployment + Service manifests that deploy the container to the `ingestion` namespace. All other router stubs (ingest, predict, models, market) exist from Phase 1 but are NOT wired up or implemented here. This phase ends when `GET /health` returns 200 via `kubectl port-forward`.

</domain>

<decisions>
## Implementation Decisions

### Health Endpoint — GET /health
- Returns HTTP 200 always (as long as process is alive — no dependency checks at this phase)
- Response JSON: `{"service": "<SERVICE_NAME>", "version": "<APP_VERSION>", "status": "ok"}` — exactly 3 fields
- `service` and `version` read from env vars `SERVICE_NAME` (default: `"stock-api"`) and `APP_VERSION` (default: `"1.0.0"`)
- Mounted at root: `GET /health` — no API prefix
- Uses a typed Pydantic response model (`HealthResponse`) for schema documentation

### Dockerfile Build Stages
- Base image: `python:3.11-slim` for both build and final stages
- Multi-stage: builder stage installs deps (`pip install --no-cache-dir -r requirements.txt`), final stage copies only installed packages and app code
- Non-root user: create `appuser` with UID 1000, `USER appuser` in final stage
- `HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1` with `--interval=30s --timeout=10s --start-period=10s --retries=3`
- `EXPOSE 8000`, `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`

### K8s Deployment + Service
- Namespace: `ingestion`
- Replicas: 1
- Resource requests: `250m` CPU / `512Mi` RAM; limits: `1` CPU / `1Gi` RAM
- Service type: `ClusterIP`, port 8000 → targetPort 8000
- Service DNS: `stock-api.ingestion.svc.cluster.local:8000`
- Both `livenessProbe` and `readinessProbe` → `httpGet /health port 8000`
  - `initialDelaySeconds: 15`, `periodSeconds: 10`, `failureThreshold: 3`
- Image: `stock-api:latest` (local Minikube image — loaded via `minikube image load`)
- `imagePullPolicy: Never` (Minikube local image, not from registry)

### config.py — Pydantic BaseSettings
- `class Settings(BaseSettings)` with `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`
- Single `settings = Settings()` singleton at module level, imported by routers
- All non-base groups are `Optional` with defaults so missing env vars don't crash at Phase 3
- **Group 1 — Service identity (required at Phase 3):**
  - `SERVICE_NAME: str = "stock-api"`
  - `APP_VERSION: str = "1.0.0"`
  - `LOG_LEVEL: str = "INFO"`
- **Group 2 — Database (Optional, used from Phase 4):**
  - `DATABASE_URL: Optional[str] = None`
  - `DB_POOL_SIZE: int = 10`
  - `DB_MAX_OVERFLOW: int = 20`
- **Group 3 — Kafka (Optional, used from Phase 5):**
  - `KAFKA_BOOTSTRAP_SERVERS: str = "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"`
  - `INTRADAY_TOPIC: str = "intraday-data"`
  - `HISTORICAL_TOPIC: str = "historical-data"`
- **Group 4 — Feature flags:**
  - `DEBUG: bool = False`
  - `ENVIRONMENT: str = "dev"`

### Claude's Discretion
- Exact structlog integration wiring in `main.py` (already implemented in `utils/logging.py`)
- Whether to include `lifespan` context manager vs `on_startup` event
- CORS middleware settings (not required by any spec at this phase)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing stubs to implement
- `stock-prediction-platform/services/api/app/main.py` — stub to implement
- `stock-prediction-platform/services/api/app/config.py` — stub to implement
- `stock-prediction-platform/services/api/app/routers/health.py` — stub to implement
- `stock-prediction-platform/services/api/Dockerfile` — placeholder to replace

### Already-complete assets (read, don't modify)
- `stock-prediction-platform/services/api/requirements.txt` — all deps pinned, do not change
- `stock-prediction-platform/services/api/app/utils/logging.py` — structlog utility from Phase 1, wire into main.py
- `stock-prediction-platform/k8s/ingestion/configmap.yaml` — env vars already defined for ingestion namespace; K8s Deployment should reference this ConfigMap

### Requirements
- `.planning/REQUIREMENTS.md` §API-01, API-02, API-03, API-04 — acceptance criteria for this phase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/utils/logging.py` — full structlog JSON logging utility with `get_logger()` helper; wire into `main.py` app startup
- `app/routers/__init__.py`, `app/models/__init__.py`, `app/services/__init__.py` — package structure already in place
- `app/routers/health.py` — stub with correct module docstring; just needs the router and endpoint added
- `k8s/ingestion/configmap.yaml` — defines `LOG_LEVEL`, `KAFKA_BOOTSTRAP_SERVERS`, `INTRADAY_TOPIC`, `HISTORICAL_TOPIC`, `API_BASE_URL` — reference this ConfigMap in the Deployment `envFrom`

### Established Patterns
- All Python files have `from __future__ import annotations` and module docstring (Phase 1 pattern — maintain this)
- Structlog JSON logging is the project standard (Phase 1) — `main.py` must call `configure_logging()` at startup
- All config via environment variables — `settings = Settings()` is the single source of truth, no `os.getenv()` calls in routers

### Integration Points
- Deployment references `ingestion-config` ConfigMap (already exists from Phase 1 scaffold)
- `deploy-all.sh` Phase 3 stub section (commented out) needs to be uncommented once manifests are ready
- Service name `stock-api` must match `API_BASE_URL` in `ingestion/configmap.yaml`

</code_context>

<specifics>
## Specific Ideas

- No specific UI/UX references — this is a pure API phase
- K8s manifest naming convention already established: `app: stock-api`, `app.kubernetes.io/part-of: stock-prediction-platform`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-fastapi-base-service*
*Context gathered: 2026-03-18*
