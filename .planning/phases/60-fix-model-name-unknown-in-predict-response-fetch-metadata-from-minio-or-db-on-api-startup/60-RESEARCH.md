# Phase 60: Fix model_name "unknown" in Predict Response — Research

**Researched:** 2026-03-25
**Domain:** FastAPI API startup metadata loading, MinIO S3 client, PostgreSQL model_registry table
**Confidence:** HIGH

---

## Summary

The `/predict/{ticker}` and `/predict/bulk` endpoints return `"model_name": "unknown"` because `_kserve_inference()` and `_legacy_inference()` in `prediction_service.py` attempt to resolve the model name by reading `metadata.json` from `settings.SERVING_DIR` (default `/models/active`). In the KServe deployment, that path is a MinIO S3 location (`s3://model-artifacts/serving/active/`) — the local filesystem path is never populated. Since the file doesn't exist locally, the code falls through to the hardcoded default `"unknown"`.

The fix has two complementary parts: (1) at API startup (in the `lifespan` handler), fetch model metadata from either MinIO (preferred, when `STORAGE_BACKEND=s3`) or the PostgreSQL `model_registry` table (fallback when DB is available), and cache it in a module-level state object; (2) update the inference functions to use that cached metadata instead of attempting a local filesystem read at request time.

This is a cosmetic bug — `predicted_price` is correct. The fix is well-scoped: no changes to the ML pipeline, KServe, MinIO infrastructure, or DB schema are required. The metadata (model_name, scaler_variant, version) is already written to `s3://model-artifacts/serving/active/metadata.json` by the deployer (`_deploy_winner_s3` in `deployer.py`) and to the `model_registry` table with `is_active=True` by `registry.activate_model()`.

**Primary recommendation:** Load model metadata eagerly at startup into a module-level cache. Read from MinIO's `serving/active/metadata.json` when `STORAGE_BACKEND=s3`; fall back to querying `model_registry WHERE is_active=true` if MinIO is unavailable; leave `model_name=None` (not "unknown") if both sources fail. Expose the cache via a `get_active_model_metadata()` helper so inference functions call it instead of reading the filesystem.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| boto3 | 1.37.x (latest) | S3/MinIO client — already in `ml/requirements.txt` | Project already uses it in `ml/models/s3_storage.py`; `S3Storage.from_env()` encapsulates the connection pattern |
| sqlalchemy (async) | 2.0.x | DB query for model_registry fallback | Already wired in `app/models/database.py` with `get_async_session()` / `get_engine()` patterns |
| pydantic-settings | 2.x | Settings already handles `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` via env | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.27.x | Alternative HTTP client for MinIO if boto3 is not in API requirements | Only if boto3 cannot be added to services/api/requirements.txt |

**Installation — API service requirements.txt:**
```bash
# boto3 is already in ml/requirements.txt.
# The API Dockerfile now copies ml/ into the image (Phase 59 change),
# so boto3 availability depends on whether ml/ deps are installed there.
# Safest: add boto3 explicitly to services/api/requirements.txt.
pip install boto3
```

**Version verification:**
```bash
npm view boto3 version   # not npm — boto3 is Python
pip index versions boto3 2>/dev/null | head -1
# As of 2026-03-25: boto3 1.37.x
```

---

## Root Cause Analysis

### The Bug Path (KServe mode, `STORAGE_BACKEND=s3`)

```
GET /predict/AAPL
  -> _kserve_inference(serving_dir="/models/active")
       base_srv = Path("/models/active")          # local filesystem path
       metadata_path = base_srv / "metadata.json" # /models/active/metadata.json
       if metadata_path.exists():                 # FALSE — file is in MinIO, not local FS
           ...
       model_display = "unknown"                  # falls through to hardcoded default
```

The model deployer writes `metadata.json` to `s3://model-artifacts/serving/active/metadata.json` via `_deploy_winner_s3()`. The API's local filesystem at `/models/active/` is empty — no PVC mount, no init container.

### The Same Bug Path (Legacy mode, `STORAGE_BACKEND=local`)

```
GET /predict/AAPL  (KSERVE_ENABLED=False)
  -> _legacy_inference(serving_dir="/models/active")
       metadata_path = Path("/models/active/metadata.json")
       if metadata_path.exists():   # Works ONLY if PVC is mounted
           ...
       model_name = "unknown"       # falls through if PVC not mounted
```

The legacy path would work if the API Pod had a PVC volume mount at `/models/active`. The Phase 57 cleanup removed the model-serving Deployment (which had the PVC mount); the API Pod in `ingestion` namespace never had that mount.

### Why DB Also Returns "unknown" Sometimes

`load_model_comparison_from_db()` queries `model_registry` but is called from `/models/comparison`, not from `/predict`. The predict endpoints never query the DB for model metadata — they only attempt the local filesystem read.

---

## Architecture Patterns

### Recommended Pattern: Startup Cache + Getter

```
app/services/
  model_metadata_cache.py    # new: startup loader + in-memory cache
app/main.py                  # updated: call load_active_model_metadata() in lifespan
app/services/prediction_service.py  # updated: replace filesystem read with get_cached_metadata()
app/config.py                # updated: add MINIO_* settings if not present
k8s/ingestion/configmap.yaml # updated: add MINIO_* and SERVING_DIR env vars for API pod
```

### Pattern 1: Module-Level Metadata Cache

**What:** A module-level dict `_active_metadata: dict | None` populated once at startup, accessed by a getter that returns a safe default if empty.

**When to use:** The metadata changes only when a new model is deployed (weekly retrain cycle). Reading it per-request from MinIO would add 50–200ms latency per predict call. Caching at startup is correct here.

**Example:**
```python
# app/services/model_metadata_cache.py
_active_metadata: dict | None = None

def get_active_model_metadata() -> dict:
    """Return cached active model metadata. Returns safe defaults if not loaded."""
    if _active_metadata is None:
        return {"model_name": None, "scaler_variant": None, "version": None}
    return _active_metadata

async def load_active_model_metadata() -> None:
    """Fetch metadata from MinIO or DB at startup. Called from lifespan."""
    global _active_metadata
    # Try MinIO first (authoritative source)
    result = await _fetch_from_minio()
    if result is None:
        # Fall back to DB query
        result = await _fetch_from_db()
    _active_metadata = result  # May still be None if both fail — that's OK
```

### Pattern 2: MinIO Fetch via boto3 / S3Storage

The `S3Storage` class in `ml/models/s3_storage.py` already implements `download_bytes(bucket, key)`. The API can reuse this pattern.

```python
# Fetch metadata.json from MinIO
import json, os
import boto3
from botocore.exceptions import ClientError

async def _fetch_from_minio() -> dict | None:
    endpoint = os.environ.get("MINIO_ENDPOINT")
    if not endpoint:
        return None
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=os.environ["MINIO_ROOT_USER"],
            aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        )
        bucket = os.environ.get("MINIO_BUCKET_MODELS", "model-artifacts")
        serving_prefix = os.environ.get("SERVING_DIR", "serving/active").strip("/")
        key = f"{serving_prefix}/metadata.json"
        obj = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(obj["Body"].read())
    except (ClientError, KeyError, json.JSONDecodeError):
        logger.warning("MinIO metadata fetch failed", exc_info=True)
        return None
```

Note: boto3 calls are synchronous. Wrap with `asyncio.to_thread()` or run in a thread pool executor to avoid blocking the event loop.

### Pattern 3: DB Fallback

```python
async def _fetch_from_db() -> dict | None:
    from sqlalchemy import text as sa_text
    from app.models.database import get_async_session, get_engine
    if get_engine() is None:
        return None
    try:
        async with get_async_session() as session:
            row = (await session.execute(sa_text("""
                SELECT model_name, version, metrics_json
                FROM model_registry
                WHERE is_active = true
                LIMIT 1
            """))).mappings().first()
        if not row:
            return None
        metrics = row.get("metrics_json") or {}
        return {
            "model_name": row["model_name"],
            "scaler_variant": metrics.get("scaler_variant"),
            "version": row.get("version"),
        }
    except Exception:
        logger.exception("DB metadata fallback failed")
        return None
```

### Pattern 4: Updating Inference Functions

Both `_kserve_inference()` and `_legacy_inference()` have the same filesystem-read block. Replace:

```python
# BEFORE (in both functions)
model_display = "unknown"
if ab_model is not None:
    model_display = ab_model["model_name"]
else:
    metadata_path = base_srv / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            meta = json.load(f)
            model_display = meta.get("model_name", "unknown")
            if meta.get("scaler_variant"):
                model_display = f"{meta['model_name']}_{meta['scaler_variant']}"
```

```python
# AFTER
from app.services.model_metadata_cache import get_active_model_metadata

if ab_model is not None:
    model_display = ab_model["model_name"]
else:
    cached = get_active_model_metadata()
    model_name_str = cached.get("model_name")
    scaler = cached.get("scaler_variant")
    if model_name_str and scaler:
        model_display = f"{model_name_str}_{scaler}"
    elif model_name_str:
        model_display = model_name_str
    else:
        model_display = "unknown"  # only if startup load failed
```

### Pattern 5: Lifespan Integration

```python
# In app/main.py lifespan()
from app.services.model_metadata_cache import load_active_model_metadata

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    ...
    if settings.DATABASE_URL:
        init_engine(...)

    # NEW: Load active model metadata (MinIO or DB)
    await load_active_model_metadata()
    logger.info("active model metadata loaded")

    yield
    ...
```

### Pattern 6: K8s ConfigMap Updates

The API Pod (in `ingestion` namespace) currently has no MinIO env vars. The `ingestion-config` ConfigMap must be updated to expose:

```yaml
# k8s/ingestion/configmap.yaml additions
data:
  MINIO_ENDPOINT: "http://minio.storage.svc.cluster.local:9000"
  MINIO_BUCKET_MODELS: "model-artifacts"
  SERVING_DIR: "serving/active"
```

The MinIO credentials (`MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`) should come from the existing `minio-secrets` Secret:

```yaml
# k8s/ingestion/fastapi-deployment.yaml — add secretRef
envFrom:
  - configMapRef:
      name: ingestion-config
  - secretRef:
      name: minio-secrets    # NEW
```

### Anti-Patterns to Avoid

- **Reading metadata.json per-request:** Adds 50–200ms MinIO latency on every `/predict` call. Cache at startup.
- **Silently swallowing startup failures:** If MinIO and DB both fail at startup, log a WARNING but continue — metadata is cosmetic, predictions still work.
- **Hardcoding `model_name = "unknown"` as a non-None default:** `None` is more honest than "unknown" — callers can distinguish "not loaded" from a real model named "unknown".
- **Blocking the event loop with boto3:** boto3's `s3.get_object()` is synchronous. Use `asyncio.to_thread()` or run once during startup (where blocking is acceptable in the lifespan context).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| S3 client for MinIO | Custom HTTP client | `boto3` / `S3Storage.from_env()` | Already used in `ml/models/s3_storage.py`; handles retries, signing, error normalization |
| DB session management | Raw psycopg2 | `get_async_session()` from `app/models/database.py` | Project standard; handles pooling and cleanup |
| JSON parsing from bytes | Custom reader | `json.loads(bytes_data)` | Trivial stdlib |
| Thread pool for sync boto3 | Custom thread pool | `asyncio.to_thread()` (Python 3.9+) | Already available in Python 3.11 used by project |

---

## Common Pitfalls

### Pitfall 1: boto3 not in API requirements.txt
**What goes wrong:** `ImportError: No module named 'boto3'` when `_fetch_from_minio()` is called.
**Why it happens:** `boto3` lives in `ml/requirements.txt`, not in `services/api/requirements.txt`. The Phase 59 Dockerfile change copies the `ml/` source code but does not install `ml/`'s Python dependencies inside the API image.
**How to avoid:** Add `boto3` to `services/api/requirements.txt`. Verify with `pip list | grep boto3` inside the API container.
**Warning signs:** `ModuleNotFoundError` in API startup logs for `boto3` or `botocore`.

### Pitfall 2: MinIO credentials not available to API Pod
**What goes wrong:** `KeyError: 'MINIO_ROOT_USER'` or `NoCredentialsError` from boto3.
**Why it happens:** `minio-secrets` K8s Secret is in the `storage` namespace; API Pod is in `ingestion` namespace. The Secret must either be copied or the Deployment must reference it explicitly.
**How to avoid:** Check `k8s/storage/minio-secrets.yaml` — if it's in `storage` namespace, create a copy in `ingestion` or use a cross-namespace secret operator. Simplest: add `secretRef: name: minio-secrets` to the `fastapi-deployment.yaml` `envFrom` block (the secret must exist in the `ingestion` namespace).
**Warning signs:** `MINIO_ROOT_USER` not set in API Pod env; boto3 `NoCredentialsError` in startup logs.

### Pitfall 3: SERVING_DIR value mismatch between ML pipeline and API
**What goes wrong:** API fetches from `serving/active/metadata.json` but deployer writes to `serving/active/metadata.json` — this is correct. However if `SERVING_DIR` env var in the API ConfigMap differs from the `SERVING_DIR` in `ml-pipeline-config`, the key will be wrong.
**Why it happens:** ML ConfigMap has `SERVING_DIR: "serving/active"` (relative, no leading slash). API `config.py` default is `SERVING_DIR: "/models/active"` (absolute, local filesystem path).
**How to avoid:** The API's MinIO fetch should use the raw `serving/active` prefix form (no leading slash), not `settings.SERVING_DIR`. Add a new setting `MINIO_SERVING_PREFIX: str = "serving/active"` or strip the leading slash from `SERVING_DIR`.
**Warning signs:** `NoSuchKey` error from MinIO on the metadata.json get call.

### Pitfall 4: Startup failure blocks the app
**What goes wrong:** Uncaught exception in `load_active_model_metadata()` prevents API from starting.
**Why it happens:** Network errors, missing credentials, or MinIO not yet ready when API starts.
**How to avoid:** Wrap the entire load function in a broad `try/except Exception` — log WARNING, leave cache as `None`, continue startup. The predict endpoint still works (with `model_name = "unknown"` fallback).

### Pitfall 5: Stale metadata after retrain
**What goes wrong:** A new model is deployed to MinIO, but API still returns old `model_name` from startup cache.
**Why it happens:** Metadata is loaded once at startup; in-memory cache is never refreshed.
**How to avoid:** Two options — (a) Accept staleness: retrain is weekly, API Pods are typically restarted on deploy anyway; (b) Add a manual refresh endpoint `POST /admin/reload-metadata`. For Phase 60, option (a) is sufficient. The issue only becomes important if the API runs for weeks without restart.

### Pitfall 6: boto3 call blocks async event loop
**What goes wrong:** `/predict` requests slow down while `load_active_model_metadata()` blocks the event loop during startup.
**Why it happens:** boto3's S3 operations are synchronous. Calling them from an `async def` function without `await asyncio.to_thread(...)` blocks the loop.
**How to avoid:** In the startup context (lifespan), blocking is acceptable since no requests are served yet. However, use `asyncio.to_thread(_sync_minio_fetch)` for correctness.

---

## Code Examples

### Verified Pattern: Lifespan Startup Hook

```python
# Source: existing app/main.py (lifespan pattern, Phase 3 decision)
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.DATABASE_URL:
        init_engine(settings.DATABASE_URL, ...)
    if settings.REDIS_URL:
        init_redis(settings.REDIS_URL)
    # NEW hook follows this pattern:
    await load_active_model_metadata()
    yield
    await dispose_engine()
```

### Verified Pattern: Async Session Query

```python
# Source: existing prediction_service.py load_model_comparison_from_db()
async with get_async_session() as session:
    result = await session.execute(query)
    rows = result.mappings().all()
```

### Verified Pattern: S3Storage.from_env()

```python
# Source: ml/models/s3_storage.py
s3 = S3Storage.from_env()  # reads MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD
data = s3.download_bytes(bucket, key)  # returns bytes
meta = json.loads(data)
```

### Verified Pattern: asyncio.to_thread for sync boto3

```python
# Python 3.9+ stdlib — no additional deps
import asyncio

def _sync_fetch_metadata() -> dict | None:
    """Synchronous boto3 call — runs in thread pool."""
    ...

async def _fetch_from_minio() -> dict | None:
    return await asyncio.to_thread(_sync_fetch_metadata)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| PVC-mounted `/models/active/metadata.json` | S3 `serving/active/metadata.json` in MinIO | Phase 52-53 (MinIO backend), Phase 57 (PVC serving removed) | API filesystem read no longer works; need S3 read at startup |
| `model-serving` Deployment with PVC mount | KServe InferenceService + MinIO | Phase 55-57 | API pod never mounts the model artifacts volume |
| Per-request filesystem read in `_kserve_inference` | Startup cache load | Phase 60 (this phase) | Eliminates latency on every predict call; correct for KServe mode |

**Deprecated/outdated:**
- Local filesystem read of `metadata.json` in `_kserve_inference` and `_legacy_inference`: not broken in legacy/local mode (if PVC is mounted), but irrelevant in the KServe production path. Should remain as a final fallback for local dev.

---

## Deployment Architecture (Phase 60)

```
API Startup (lifespan):
  1. init_engine() [existing]
  2. init_redis()  [existing]
  3. load_active_model_metadata() [NEW]
      |
      +-- Try: boto3.get_object(s3://model-artifacts/serving/active/metadata.json)
      |         -> parse JSON -> cache {model_name, scaler_variant, version}
      |
      +-- Fallback: SELECT model_name, metrics_json FROM model_registry WHERE is_active=true
      |         -> parse row -> cache
      |
      +-- Last resort: cache = None, log WARNING, continue startup

Per Request (/predict/AAPL):
  _kserve_inference()
    model_display = get_active_model_metadata().get("model_name") or "unknown"
```

---

## Open Questions

1. **Should metadata refresh on retrain without restart?**
   - What we know: Training CronJob runs weekly (Sunday 03:00 UTC). API Pods typically restart on Docker image push. Kubernetes liveness probes restart unhealthy pods.
   - What's unclear: Is there a formal "model deployed" signal the API should react to?
   - Recommendation: For Phase 60, accept startup-only load (stale for up to 7 days). Document a refresh endpoint as Phase 61+ enhancement.

2. **minio-secrets Secret namespace availability**
   - What we know: `minio-secrets` is defined in `k8s/storage/minio-secrets.yaml`. The API Pod is in `ingestion` namespace.
   - What's unclear: Whether a copy of `minio-secrets` already exists in `ingestion` namespace from prior phases.
   - Recommendation: Check during plan execution with `kubectl get secret minio-secrets -n ingestion`. If missing, copy it or add `kubectl create secret` to `deploy-all.sh`.

3. **`serving_config.json` vs `metadata.json` — which has the definitive model_name?**
   - What we know: The deployer writes BOTH `serving_config.json` (has `model_name`, `scaler_variant`, `version`, `oos_metrics`) AND copies `metadata.json` from the registry. `serving_config.json` is the cleaner authoritative source.
   - Recommendation: Read `serving_config.json` at startup (it's the deployer-controlled file) rather than `metadata.json`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.x |
| Config file | `services/api/pytest.ini` |
| Quick run command | `pytest services/api/tests/test_prediction_service.py -x -v` |
| Full suite command | `pytest services/api/tests/ -x -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRED-MNAME-01 | `get_active_model_metadata()` returns cached dict after `load_active_model_metadata()` succeeds | unit | `pytest services/api/tests/test_model_metadata_cache.py -x` | Wave 0 (new file) |
| PRED-MNAME-02 | `get_active_model_metadata()` returns `{"model_name": None}` when both MinIO and DB fail | unit | `pytest services/api/tests/test_model_metadata_cache.py::test_fallback_returns_none_model -x` | Wave 0 (new file) |
| PRED-MNAME-03 | `/predict/AAPL` response has non-"unknown" `model_name` when cache is populated | unit | `pytest services/api/tests/test_predict.py::test_predict_model_name_not_unknown -x` | Extend existing test_predict.py |
| PRED-MNAME-04 | MinIO fetch uses `serving/active/serving_config.json` path (not local filesystem) | unit | `pytest services/api/tests/test_model_metadata_cache.py::test_minio_fetch_uses_s3_path -x` | Wave 0 (new file) |
| PRED-MNAME-05 | DB fallback query targets `model_registry WHERE is_active=true` | unit | `pytest services/api/tests/test_model_metadata_cache.py::test_db_fallback_queries_active_model -x` | Wave 0 (new file) |

### Sampling Rate
- **Per task commit:** `pytest services/api/tests/test_model_metadata_cache.py -x -v`
- **Per wave merge:** `pytest services/api/tests/ -x -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `services/api/tests/test_model_metadata_cache.py` — covers PRED-MNAME-01 through PRED-MNAME-05 (new file needed)
- [ ] `services/api/app/services/model_metadata_cache.py` — the module under test (new file needed)

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `stock-prediction-platform/services/api/app/services/prediction_service.py` lines 279-289, 441-449 — exact bug location confirmed
- Direct code inspection: `stock-prediction-platform/ml/pipelines/components/deployer.py` `_deploy_winner_s3()` — confirms `metadata.json` and `serving_config.json` are written to MinIO
- Direct code inspection: `stock-prediction-platform/services/api/app/main.py` — lifespan handler pattern
- Direct code inspection: `stock-prediction-platform/ml/models/s3_storage.py` — `S3Storage.from_env()` pattern for MinIO access
- Phase 59 VERIFICATION.md (line 99): "model_name returns 'unknown' — metadata.json ConfigMap mount not added — cosmetic, does not affect predicted_price"
- Phase 59 Plan 03 SUMMARY.md (line 202): "model_name shows 'unknown' — features.json ConfigMap mount covers features but metadata.json mount not added"

### Secondary (MEDIUM confidence)
- `k8s/ingestion/configmap.yaml` — confirms `MINIO_*` env vars are absent from API ConfigMap (verified by inspection)
- `k8s/ml/configmap.yaml` — confirms `SERVING_DIR: "serving/active"` naming convention used by ML pipeline

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Root cause: HIGH — confirmed by Phase 59 SUMMARY + VERIFICATION + direct code trace
- Standard stack: HIGH — reuses existing project libraries (boto3, sqlalchemy async)
- Architecture: HIGH — follows established patterns in main.py lifespan + prediction_service.py DB fallbacks
- Pitfalls: HIGH — based on code inspection of the actual environment constraints

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain — no external API changes expected)
