# Phase 3: FastAPI Base Service - Research

**Researched:** 2026-03-18
**Domain:** FastAPI application skeleton, Docker multi-stage builds, Kubernetes Deployment/Service
**Confidence:** HIGH

## Summary

Phase 3 implements the FastAPI application skeleton with a health endpoint, a production multi-stage Dockerfile, and Kubernetes manifests to deploy the container in the `ingestion` namespace. All decisions are locked in CONTEXT.md -- the exact JSON response shape, Dockerfile stages, K8s resource limits, and config.py structure are fully specified. The pinned `requirements.txt` already contains all needed dependencies (`fastapi==0.111.0`, `uvicorn==0.29.0`, `pydantic==2.7.1`, `pydantic-settings==2.2.1`, `structlog==24.2.0`).

The implementation is straightforward because the stubs exist, the package structure is in place, and the logging utility is already complete. The primary risk areas are: (1) ensuring the Dockerfile multi-stage build correctly copies only the virtualenv/site-packages, (2) ensuring the K8s manifests reference the existing `ingestion-config` ConfigMap via `envFrom`, and (3) ensuring the `deploy-all.sh` Phase 3 section gets uncommented with the correct file names.

**Primary recommendation:** Implement in 3 waves: config.py + health.py + main.py (pure Python), then Dockerfile (build + verify locally), then K8s manifests + deploy-all.sh integration.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Health endpoint: GET /health returns 200 with `{"service": "<SERVICE_NAME>", "version": "<APP_VERSION>", "status": "ok"}` -- exactly 3 fields
- `service` and `version` from env vars `SERVICE_NAME` (default: `"stock-api"`) and `APP_VERSION` (default: `"1.0.0"`)
- Mounted at root (no API prefix), uses typed Pydantic `HealthResponse` model
- Dockerfile: `python:3.11-slim`, multi-stage (builder + final), `appuser` UID 1000, `HEALTHCHECK CMD curl`, `EXPOSE 8000`, uvicorn CMD
- K8s: namespace `ingestion`, 1 replica, requests 250m/512Mi, limits 1CPU/1Gi, ClusterIP port 8000, both probes on /health, `imagePullPolicy: Never`
- Image name: `stock-api:latest`
- config.py: Pydantic BaseSettings with 4 groups (service identity, database, kafka, feature flags), all optional except service identity defaults
- `requirements.txt` is pinned and must NOT be modified

### Claude's Discretion
- Exact structlog integration wiring in main.py (call `configure_logging()` or import to trigger module-level config)
- Whether to use `lifespan` context manager vs `on_startup` event
- CORS middleware settings (not required at this phase)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | FastAPI app skeleton with config.py, main.py, router structure | config.py (Pydantic BaseSettings), main.py (FastAPI app + router inclusion), health router; package structure already exists from Phase 1 |
| API-02 | GET /health endpoint returning service status | HealthResponse Pydantic model, APIRouter, reads SERVICE_NAME/APP_VERSION from settings singleton |
| API-03 | Dockerfile for FastAPI service (multi-stage) | python:3.11-slim builder + runtime, pip install in builder, copy site-packages, appuser:1000, HEALTHCHECK curl |
| API-04 | K8s Deployment + Service YAML for FastAPI in ingestion namespace | Deployment with envFrom ingestion-config ConfigMap, ClusterIP Service, liveness/readiness probes, resource limits |
</phase_requirements>

## Standard Stack

### Core (from pinned requirements.txt -- DO NOT CHANGE VERSIONS)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.111.0 | Web framework | Pinned in requirements.txt |
| uvicorn[standard] | 0.29.0 | ASGI server | Pinned in requirements.txt |
| pydantic | 2.7.1 | Data validation, response models | Pinned in requirements.txt |
| pydantic-settings | 2.2.1 | BaseSettings for env var config | Pinned in requirements.txt |
| structlog | 24.2.0 | JSON structured logging | Pinned in requirements.txt, utility already built |

### Supporting (used at this phase)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-json-logger | 2.0.7 | stdlib JSON formatter (structlog dep chain) | Already wired in logging.py |

### Not Used at This Phase
All other libraries in requirements.txt (sqlalchemy, asyncpg, confluent-kafka, yfinance, pandas, etc.) are installed but not imported. The config.py defines their settings as Optional with defaults so the app boots without them.

**Installation:** No changes needed -- `requirements.txt` is complete and pinned.

## Architecture Patterns

### Recommended Project Structure (already scaffolded)
```
services/api/
├── Dockerfile               # Multi-stage build (implement)
├── requirements.txt         # Pinned deps (DO NOT MODIFY)
└── app/
    ├── __init__.py
    ├── main.py              # FastAPI app, lifespan, router inclusion (implement)
    ├── config.py            # Pydantic BaseSettings singleton (implement)
    ├── routers/
    │   ├── __init__.py
    │   ├── health.py        # GET /health (implement)
    │   ├── ingest.py        # stub -- NOT wired at Phase 3
    │   ├── predict.py       # stub -- NOT wired at Phase 3
    │   ├── models.py        # stub -- NOT wired at Phase 3
    │   └── market.py        # stub -- NOT wired at Phase 3
    ├── models/
    │   ├── __init__.py
    │   ├── schemas.py       # stub
    │   └── database.py      # stub
    ├── services/             # all stubs
    └── utils/
        ├── __init__.py
        ├── logging.py       # COMPLETE from Phase 1 -- wire into main.py
        └── indicators.py    # stub
```

### K8s Manifests (new files)
```
k8s/ingestion/
├── configmap.yaml              # EXISTS -- has LOG_LEVEL, KAFKA_*, API_BASE_URL
├── fastapi-deployment.yaml     # NEW -- deploy-all.sh expects this name
├── fastapi-service.yaml        # NEW -- deploy-all.sh expects this name
├── cronjob-intraday.yaml       # EXISTS (stub)
└── cronjob-historical.yaml     # EXISTS (stub)
```

### Pattern 1: Pydantic BaseSettings Singleton
**What:** Single `Settings` class with `model_config = SettingsConfigDict(env_file=".env", extra="ignore")`, instantiated once at module level.
**When to use:** Always -- this is the project's single source of truth for configuration.
**Key detail for FastAPI 0.111.0 + pydantic-settings 2.2.1:** Import from `pydantic_settings`, not `pydantic`. The `SettingsConfigDict` is also imported from `pydantic_settings`.

```python
# Source: pydantic-settings docs
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Group 1 -- Service identity
    SERVICE_NAME: str = "stock-api"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # Group 2 -- Database (Phase 4+)
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Group 3 -- Kafka (Phase 5+)
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"
    INTRADAY_TOPIC: str = "intraday-data"
    HISTORICAL_TOPIC: str = "historical-data"

    # Group 4 -- Feature flags
    DEBUG: bool = False
    ENVIRONMENT: str = "dev"

settings = Settings()
```

**Confidence:** HIGH -- pydantic-settings 2.2.1 uses `SettingsConfigDict` (v2 API), not the old `class Config` inner class.

### Pattern 2: FastAPI Lifespan Context Manager (Recommended over on_startup)
**What:** Use `@asynccontextmanager` lifespan function instead of deprecated `on_startup`/`on_shutdown` events.
**Why:** `on_startup` and `on_shutdown` are deprecated in FastAPI 0.111.0 in favor of the lifespan pattern. The lifespan approach also properly supports async context cleanup.

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: configure logging, log service info
    logger.info("service starting", service=settings.SERVICE_NAME, version=settings.APP_VERSION)
    yield
    # Shutdown
    logger.info("service shutting down")

app = FastAPI(
    title="Stock Prediction API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)
```

**Confidence:** HIGH -- lifespan is the standard pattern in FastAPI 0.100+ (we have 0.111.0).

### Pattern 3: Router with Typed Response Model
**What:** Use `response_model` on the endpoint for OpenAPI schema generation.

```python
from fastapi import APIRouter
from pydantic import BaseModel

class HealthResponse(BaseModel):
    service: str
    version: str
    status: str

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        service=settings.SERVICE_NAME,
        version=settings.APP_VERSION,
        status="ok",
    )
```

### Pattern 4: Structlog Wiring in main.py
**What:** The `utils/logging.py` module runs `structlog.configure()` at import time. Simply importing `get_logger` triggers configuration. No explicit `configure_logging()` call is needed.
**How:** `from app.utils.logging import get_logger` at top of main.py is sufficient.

**Confidence:** HIGH -- verified by reading the existing `logging.py` source; configuration happens at module level (lines 52-76).

### Pattern 5: Dockerfile Multi-Stage Build
**What:** Builder stage installs pip deps into a known location, final stage copies only the installed packages.

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY ./app ./app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key details:**
- `curl` must be installed in the final stage for HEALTHCHECK (not included in python:3.11-slim by default)
- Copy both `site-packages` AND `/usr/local/bin` (for uvicorn binary)
- `COPY ./app ./app` not `COPY . .` -- only copy the app package, not requirements.txt or other build artifacts

### Anti-Patterns to Avoid
- **Importing os.getenv() in routers:** Always use `settings.SERVICE_NAME`, never `os.environ.get()`. The settings singleton is the single source of truth (project convention).
- **Using `on_startup` decorator:** Deprecated in FastAPI 0.111.0. Use lifespan context manager.
- **Wiring stub routers at Phase 3:** Only `health.py` should be included via `app.include_router()`. Other routers (ingest, predict, models, market) are NOT wired until their respective phases.
- **Modifying requirements.txt:** Pinned and locked. Do not add, remove, or change any version.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Env var config | Manual os.getenv() | pydantic-settings BaseSettings | Type coercion, .env support, validation, defaults |
| Health check response | Plain dict return | Pydantic BaseModel response_model | OpenAPI schema, type safety, consistent serialization |
| JSON logging | Custom JSON formatter | structlog (already built in utils/logging.py) | Contextvar support, request_id injection, tested |
| K8s config injection | Hardcoded env values in Deployment | envFrom ConfigMap ref | Already exists as ingestion-config, single source of truth |

## Common Pitfalls

### Pitfall 1: Missing curl in python:3.11-slim
**What goes wrong:** HEALTHCHECK fails silently because `curl` is not installed in slim images.
**Why it happens:** `python:3.11-slim` strips all non-essential packages.
**How to avoid:** `RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*` in the final stage.
**Warning signs:** Container starts but K8s marks it unhealthy after `failureThreshold` x `periodSeconds`.

### Pitfall 2: uvicorn Binary Not Copied in Multi-Stage
**What goes wrong:** `CMD ["uvicorn", ...]` fails with "command not found" because uvicorn installs a console script in `/usr/local/bin/`.
**Why it happens:** Only copying `site-packages` misses the entry-point scripts.
**How to avoid:** Also `COPY --from=builder /usr/local/bin /usr/local/bin` in the final stage.
**Warning signs:** Container exits immediately with code 127.

### Pitfall 3: K8s Probes Hitting Wrong Port
**What goes wrong:** Liveness/readiness probes return connection refused.
**Why it happens:** `containerPort`, probe port, and uvicorn `--port` must all be 8000.
**How to avoid:** Triple-check all three match: Dockerfile EXPOSE, uvicorn CMD, K8s probe port, Service targetPort.

### Pitfall 4: ConfigMap Not Applied Before Deployment
**What goes wrong:** `envFrom` references `ingestion-config` but ConfigMap doesn't exist.
**Why it happens:** Deploy ordering not enforced.
**How to avoid:** `deploy-all.sh` already applies ConfigMap before Phase 3 section. Verify the ConfigMap is applied in the ingestion namespace section.

### Pitfall 5: Image Not Loaded into Minikube
**What goes wrong:** Deployment stuck in `ErrImagePull` or `ImagePullBackOff`.
**Why it happens:** `imagePullPolicy: Never` requires the image to exist in Minikube's Docker daemon.
**How to avoid:** Build with `minikube image build -t stock-api:latest ./services/api/` or `docker build` + `minikube image load stock-api:latest`.
**Warning signs:** `kubectl describe pod` shows image pull errors.

### Pitfall 6: pydantic v2 Import Path for Settings
**What goes wrong:** `ImportError` if importing BaseSettings from `pydantic` instead of `pydantic_settings`.
**Why it happens:** pydantic v2 moved settings to a separate package.
**How to avoid:** Always `from pydantic_settings import BaseSettings, SettingsConfigDict`.

## Code Examples

### config.py -- Complete Implementation Pattern
```python
"""Application configuration loaded from environment variables."""

from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Service identity
    SERVICE_NAME: str = "stock-api"
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # Database (Phase 4+)
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Kafka (Phase 5+)
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"
    INTRADAY_TOPIC: str = "intraday-data"
    HISTORICAL_TOPIC: str = "historical-data"

    # Feature flags
    DEBUG: bool = False
    ENVIRONMENT: str = "dev"


settings = Settings()
```

### main.py -- Complete Implementation Pattern
```python
"""FastAPI application entry point for the stock prediction API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import health
from app.utils.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown logic."""
    logger.info(
        "service starting",
        service=settings.SERVICE_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
    )
    yield
    logger.info("service shutting down")


app = FastAPI(
    title="Stock Prediction API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(health.router)
```

### health.py -- Complete Implementation Pattern
```python
"""Health check router for the stock prediction API."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings


class HealthResponse(BaseModel):
    """Health check response schema."""

    service: str
    version: str
    status: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        service=settings.SERVICE_NAME,
        version=settings.APP_VERSION,
        status="ok",
    )
```

### K8s Deployment Pattern (matches existing project conventions)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stock-api
  namespace: ingestion
  labels:
    app: stock-api
    app.kubernetes.io/part-of: stock-prediction-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: stock-api
  template:
    metadata:
      labels:
        app: stock-api
    spec:
      containers:
        - name: stock-api
          image: stock-api:latest
          imagePullPolicy: Never
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: ingestion-config
          env:
            - name: SERVICE_NAME
              value: "stock-api"
            - name: APP_VERSION
              value: "1.0.0"
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 10
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 10
            failureThreshold: 3
```

### K8s Service Pattern
```yaml
apiVersion: v1
kind: Service
metadata:
  name: stock-api
  namespace: ingestion
  labels:
    app: stock-api
    app.kubernetes.io/part-of: stock-prediction-platform
spec:
  type: ClusterIP
  selector:
    app: stock-api
  ports:
    - port: 8000
      targetPort: 8000
      protocol: TCP
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `on_startup`/`on_shutdown` events | `lifespan` context manager | FastAPI 0.100+ | Must use lifespan; old events still work but deprecated |
| `from pydantic import BaseSettings` | `from pydantic_settings import BaseSettings` | Pydantic v2.0 | Separate package, different import path |
| `class Config:` inner class | `model_config = SettingsConfigDict(...)` | Pydantic v2.0 | Class-level attribute, not inner class |

## Integration Points

### deploy-all.sh (lines 30-33)
The script has Phase 3 section commented out, expecting these exact filenames:
```bash
# kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/fastapi-deployment.yaml"
# kubectl apply -f "$PROJECT_ROOT/k8s/ingestion/fastapi-service.yaml"
```
These lines must be uncommented after manifests are created.

### ingestion-config ConfigMap (already exists)
Contains: `KAFKA_BOOTSTRAP_SERVERS`, `INTRADAY_TOPIC`, `HISTORICAL_TOPIC`, `API_BASE_URL`, `LOG_LEVEL`.
The Deployment should use `envFrom` to inject all of these. Additional env vars (`SERVICE_NAME`, `APP_VERSION`) that are NOT in the ConfigMap should be set as explicit `env` entries in the Deployment spec.

### Service DNS
Service must resolve as `stock-api.ingestion.svc.cluster.local:8000` -- this matches the `API_BASE_URL` value in the ingestion ConfigMap and the frontend deployment's `VITE_API_URL`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (not yet configured for this service) |
| Config file | None -- see Wave 0 |
| Quick run command | `python -c "from app.config import settings; print(settings.SERVICE_NAME)"` |
| Full suite command | `pytest tests/ -x` (once tests exist) |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | FastAPI app loads with config, router structure | smoke | `python -c "from app.main import app; print(app.title)"` | No -- Wave 0 |
| API-02 | GET /health returns 200 with correct JSON | integration | `curl -sf http://localhost:8000/health \| python -m json.tool` | No -- Wave 0 |
| API-03 | Dockerfile builds successfully, container starts | smoke | `docker build -t stock-api:latest . && docker run --rm -d -p 8000:8000 stock-api:latest` | No -- manual |
| API-04 | K8s Deployment + Service: pod running, service reachable | smoke | `kubectl get pods -n ingestion -l app=stock-api -o jsonpath='{.items[0].status.phase}'` | No -- manual |

### Sampling Rate
- **Per task commit:** `python -c "from app.main import app; print(app.title)"`
- **Per wave merge:** `curl -sf http://localhost:8000/health` (requires running container)
- **Phase gate:** Full validation via `kubectl port-forward svc/stock-api -n ingestion 8000:8000` then `curl http://localhost:8000/health`

### Wave 0 Gaps
- [ ] No pytest infrastructure exists for this service yet (acceptable -- Phase 3 is smoke-tested via curl and kubectl)
- [ ] Docker build verification is manual (Minikube context)
- [ ] K8s deployment verification is manual (requires running cluster)

## Open Questions

1. **CORS middleware at Phase 3?**
   - What we know: Not required by any spec. Frontend is not connected until much later phases (25+).
   - Recommendation: Skip CORS at Phase 3 (Claude's discretion area). Can be trivially added later with `app.add_middleware(CORSMiddleware, ...)`.

2. **deploy-all.sh uncommenting**
   - What we know: Lines 30-33 are commented out. The planner needs to decide whether this phase uncomments them or if that's a manual step.
   - Recommendation: Include uncommenting in the plan as a task. The implementation should uncomment and verify the script runs cleanly.

## Sources

### Primary (HIGH confidence)
- `stock-prediction-platform/services/api/requirements.txt` -- pinned dependency versions verified
- `stock-prediction-platform/services/api/app/utils/logging.py` -- structlog configuration verified (module-level execution)
- `stock-prediction-platform/k8s/ingestion/configmap.yaml` -- ConfigMap keys verified
- `stock-prediction-platform/k8s/frontend/deployment.yaml` -- K8s label/naming conventions verified
- `stock-prediction-platform/scripts/deploy-all.sh` -- Phase 3 file names verified (lines 30-33)

### Secondary (MEDIUM confidence)
- FastAPI lifespan pattern: standard in FastAPI 0.100+ (verified via training knowledge of FastAPI 0.111.0 release)
- pydantic-settings v2 API: `SettingsConfigDict` is the v2 pattern (verified by presence of `pydantic-settings==2.2.1` in requirements)

### Tertiary (LOW confidence)
- None -- all findings verified against project source code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions pinned in requirements.txt, no choices to make
- Architecture: HIGH -- all patterns locked in CONTEXT.md, matching existing project conventions
- Pitfalls: HIGH -- common Docker/K8s issues well-documented, verified against project specifics

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable -- pinned deps, locked decisions)
