# Phase 58: Fix docker-compose runtime: kafka-consumer configurable broker + ml-pipeline entrypoint fix - Research

**Researched:** 2026-03-24
**Domain:** Docker Compose service configuration, Python entrypoint patterns, pydantic-settings env var defaults
**Confidence:** HIGH

---

## Summary

Phase 58 fixes two independent runtime crashes that prevent the docker-compose stack from running successfully.

**Bug 1 — kafka-consumer broker hardcoded to K8s DNS name.** `ConsumerSettings.KAFKA_BOOTSTRAP_SERVERS` in `services/kafka-consumer/consumer/config.py` line 17 has a hardcoded default of `kafka-kafka-bootstrap.storage.svc.cluster.local:9092`. When the container starts inside docker-compose, this K8s Strimzi service DNS name cannot be resolved. The fix is a one-liner: change the pydantic-settings default to `kafka:9092` (the docker-compose service name) AND inject the correct value via `docker-compose.yml` environment block for both environments. The pattern already in use by the API service (`DATABASE_URL`, `REDIS_URL` injected in docker-compose.yml) is the template to follow.

**Bug 2 — ml-pipeline entrypoint calls `run_training_pipeline()` with no arguments.** `ml/Dockerfile` line 31 sets `CMD ["python", "-m", "ml.pipelines.training_pipeline"]`. The `__main__` guard in `training_pipeline.py` calls `run_training_pipeline(tickers=tickers, ...)` where `tickers` is `None` when `--tickers` arg is not given. The function immediately raises `ValueError: Provide either 'tickers' or 'data_dict'.` The fix is to add an environment-variable-driven default ticker list (reusing the `TICKER_SYMBOLS` pattern from `services/api/app/config.py`) so the pipeline can start without CLI args, OR change the docker-compose `command:` to pass `--tickers` or add a `TICKERS` env var that the `__main__` block reads.

**Primary recommendation:** Fix both issues by (1) changing the `KAFKA_BOOTSTRAP_SERVERS` default in `ConsumerSettings` to `kafka:9092` and injecting `KAFKA_BOOTSTRAP_SERVERS=kafka:9092` in the docker-compose `kafka-consumer` service block, and (2) modifying the `training_pipeline.py` `__main__` block to read a `TICKERS` env var (falling back to a default list) when `--tickers` is not given, and injecting `TICKERS` in the docker-compose `ml-pipeline` service block.

---

## Standard Stack

### Core (already present — no new dependencies needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic-settings | >=2.0 | Env-var-driven config with typed defaults | Already used in both services |
| confluent-kafka | installed | Kafka consumer connection | Already used in consumer/main.py |
| python argparse | stdlib | CLI arg parsing | Already used in training_pipeline.py __main__ |

No new libraries are required. Both fixes are configuration and code logic changes only.

**Installation:** None required.

---

## Architecture Patterns

### Pattern 1: pydantic-settings env var override

`ConsumerSettings` inherits from `pydantic_settings.BaseSettings`. All fields are automatically overridable by environment variables with the same name. The default value in the class body is the fallback used when no env var is set.

**Current state (broken):**
```python
# services/kafka-consumer/consumer/config.py line 17
KAFKA_BOOTSTRAP_SERVERS: str = "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"
```

**Fix pattern — change default AND inject in docker-compose:**
```python
# Change default to docker-compose-friendly value
KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
```

```yaml
# docker-compose.yml — kafka-consumer service block
kafka-consumer:
  image: stock-prediction-consumer:latest
  environment:
    - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    - DATABASE_URL=postgresql://stockuser:${POSTGRES_PASSWORD:-stockpassword}@postgres:5432/stockdb
  depends_on:
    - kafka
    - postgres
```

The K8s CronJob/Deployment injects the Strimzi service name via its own ConfigMap, so changing the code default to `kafka:9092` does not affect the K8s deployment. In K8s, the env var `KAFKA_BOOTSTRAP_SERVERS=kafka-kafka-bootstrap.storage.svc.cluster.local:9092` continues to be injected by the K8s `processing-config` ConfigMap, overriding the code default.

Note: The `api` service in `services/api/app/config.py` also has `KAFKA_BOOTSTRAP_SERVERS: str = "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"` on line 30. This is the same pattern and should receive the same treatment for consistency (API uses Kafka for produce, consumer uses it for consume).

### Pattern 2: Env-var fallback in `__main__` entrypoint

The `training_pipeline.py` `__main__` block already parses `--tickers` CLI arg. The gap is: when called via `CMD ["python", "-m", "ml.pipelines.training_pipeline"]` (no CLI args), `args.tickers` is `None`, which flows to `tickers = None` and triggers the ValueError.

**Current broken flow:**
```
Dockerfile CMD: python -m ml.pipelines.training_pipeline
  → args.tickers = None (no --tickers arg passed)
  → tickers = None
  → run_training_pipeline(tickers=None, ...)
  → ValueError: Provide either 'tickers' or 'data_dict'.
```

**Fix pattern — read TICKERS env var as fallback:**
```python
# In the __main__ block, after parsing args:
import os
tickers_str = args.tickers or os.environ.get("TICKERS")
tickers = tickers_str.split(",") if tickers_str else None

# Then run_training_pipeline will still raise if tickers remains None —
# but now the docker-compose service injects TICKERS env var.
```

**docker-compose.yml addition to ml-pipeline service:**
```yaml
ml-pipeline:
  build:
    context: .
    dockerfile: ml/Dockerfile
  image: stock-ml-pipeline:latest
  environment:
    - DATABASE_URL=postgresql://stockuser:${POSTGRES_PASSWORD:-stockpassword}@postgres:5432/stockdb
    - MODEL_REGISTRY_DIR=/data/model_registry
    - SERVING_DIR=/data/models/active
    - DRIFT_LOG_DIR=/data/drift_logs
    - TICKERS=AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,BRK-B,JPM,JNJ,V,PG,UNH,HD,MA,BAC,XOM,PFE,ABBV,CVX
  depends_on:
    - postgres
```

The ticker list above matches the `TICKER_SYMBOLS` default in `services/api/app/config.py` line 39. Reusing the same 20-stock dev subset maintains consistency.

Alternative: the ml-pipeline could be refactored to use a `MLPipelineSettings` pydantic-settings class (like the consumer uses `ConsumerSettings`), reading `TICKERS` from env with a default. This is cleaner but is more scope than needed for a runtime fix phase.

### Pattern 3: docker-compose `depends_on` ordering

The `kafka-consumer` service currently has no `depends_on`. It should declare `depends_on: [kafka, postgres]` so docker-compose starts it after the broker and DB are available. This is a minor addition in the same PR as the broker fix.

Note: `depends_on` in docker-compose v3+ only ensures container start order, not that Kafka is ready to accept connections. For a complete fix, the consumer's reconnect/retry behavior matters more (confluent-kafka handles broker reconnection automatically). But the `depends_on` addition prevents the race condition of the consumer starting before the Kafka container process begins.

### Recommended Project Structure (no changes)

Both fixes are in-place edits to existing files. No new files, no restructuring.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Env var injection | Custom config file loader | pydantic-settings BaseSettings (already present) | Already the project standard; env vars override defaults automatically |
| Broker address resolution | DNS lookup code | Docker network service name `kafka` | docker-compose provides built-in DNS for service names |
| Ticker list management | New config service | Env var `TICKERS` matching existing `TICKER_SYMBOLS` pattern | Minimal change, consistent with API config pattern |

---

## Common Pitfalls

### Pitfall 1: Fixing only the default, not injecting in docker-compose
**What goes wrong:** Changing `KAFKA_BOOTSTRAP_SERVERS` default to `kafka:9092` in the Python class makes local runs work but the docker-compose service block still has no `KAFKA_BOOTSTRAP_SERVERS` env var — if someone passes a different env file it breaks.
**Why it happens:** The default covers the "no env var present" case, but being explicit in docker-compose.yml is better practice for documentation and reproducibility.
**How to avoid:** Always add the explicit env var in the docker-compose service block alongside the default change.

### Pitfall 2: Breaking K8s deployment when changing the code default
**What goes wrong:** Changing the Python default from the K8s Strimzi service name to `kafka:9092` could appear to break K8s deployments.
**Why it happens:** The K8s deployment relies on the ConfigMap to inject `KAFKA_BOOTSTRAP_SERVERS`. If the ConfigMap injection is removed or the key name differs, the K8s pods would use `kafka:9092` which doesn't resolve inside the cluster.
**How to avoid:** Verify the K8s `processing-config` ConfigMap still injects `KAFKA_BOOTSTRAP_SERVERS=kafka-kafka-bootstrap.storage.svc.cluster.local:9092`. The env var override takes priority over the code default in all environments.
**Warning signs:** After the change, check `k8s/processing/configmap.yaml` for `KAFKA_BOOTSTRAP_SERVERS` key presence.

### Pitfall 3: ml-pipeline exits immediately after one training run
**What goes wrong:** Even after fixing the ValueError, `python -m ml.pipelines.training_pipeline` is a one-shot command — it trains and exits. In docker-compose, the container exits with code 0 (success) which may cause restart loops if `restart: on-failure` is set.
**Why it happens:** The ml-pipeline is a batch job, not a long-running service. docker-compose treats containers that exit as stopped.
**How to avoid:** This is expected behavior for a batch container. docker-compose will show the container as "Exited (0)". No fix needed unless a restart policy is added. The phase goal is just to avoid the ValueError crash (exit code 1).

### Pitfall 4: `DATABASE_URL` missing from kafka-consumer service block
**What goes wrong:** The `kafka-consumer` docker-compose service currently has no `environment` block at all. The `BatchWriter` will fail to create a connection pool if `settings.DATABASE_URL` is empty string (the current default).
**Why it happens:** `ConsumerSettings.DATABASE_URL` defaults to `""` which causes `psycopg2.pool.SimpleConnectionPool` to raise on empty DSN.
**How to avoid:** The `DATABASE_URL` env var must be added to the docker-compose `kafka-consumer` environment block alongside `KAFKA_BOOTSTRAP_SERVERS`. Both are required for the service to function.

### Pitfall 5: api service also has hardcoded K8s Kafka default
**What goes wrong:** `services/api/app/config.py` line 30 also has `KAFKA_BOOTSTRAP_SERVERS: str = "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"`. The docker-compose `api` service block (line 7-10 in docker-compose.yml) does not inject `KAFKA_BOOTSTRAP_SERVERS`. The API only produces to Kafka during ingest; if an ingest is called in the docker-compose context it would also fail.
**Why it happens:** Same root cause as the consumer — the default was written for K8s.
**How to avoid:** Optionally update the `api` service block in docker-compose.yml to inject `KAFKA_BOOTSTRAP_SERVERS=kafka:9092`. This is lower priority (consumer is the hard crash, api Kafka use is only on POST /ingest).

---

## Code Examples

### Fix 1: kafka-consumer/consumer/config.py (line 17 change)
```python
# Before
KAFKA_BOOTSTRAP_SERVERS: str = "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"

# After
KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
```

### Fix 2: docker-compose.yml kafka-consumer service block (full replacement)
```yaml
kafka-consumer:
  image: stock-prediction-consumer:latest
  environment:
    - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    - DATABASE_URL=postgresql://stockuser:${POSTGRES_PASSWORD:-stockpassword}@postgres:5432/stockdb
  depends_on:
    - kafka
    - postgres
```

### Fix 3: training_pipeline.py `__main__` block TICKERS env var read
```python
# In the __main__ block, after parser.parse_args():
import os  # (os is not yet imported at top level — add to top-level imports or here)
tickers_str = args.tickers or os.environ.get("TICKERS")
tickers = tickers_str.split(",") if tickers_str else None
horizons_list = (
    [int(h.strip()) for h in args.horizons.split(",")]
    if args.horizons
    else None
)
run_result = run_training_pipeline(
    tickers=tickers,
    registry_dir=args.registry_dir,
    serving_dir=args.serving_dir,
    skip_shap=args.skip_shap,
    horizons=horizons_list,
)
```

Note: `os` is already imported at the top of `training_pipeline.py` (line 7), so no new import is needed.

### Fix 4: docker-compose.yml ml-pipeline service block (TICKERS injection)
```yaml
ml-pipeline:
  build:
    context: .
    dockerfile: ml/Dockerfile
  image: stock-ml-pipeline:latest
  environment:
    - DATABASE_URL=postgresql://stockuser:${POSTGRES_PASSWORD:-stockpassword}@postgres:5432/stockdb
    - MODEL_REGISTRY_DIR=/data/model_registry
    - SERVING_DIR=/data/models/active
    - DRIFT_LOG_DIR=/data/drift_logs
    - TICKERS=AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,BRK-B,JPM,JNJ,V,PG,UNH,HD,MA,BAC,XOM,PFE,ABBV,CVX
  depends_on:
    - postgres
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded K8s service name as default | Env-var default appropriate for local runtime | Phase 58 | Consumer starts in docker-compose without error |
| `__main__` raises ValueError if no tickers arg | `__main__` reads TICKERS env var as fallback | Phase 58 | ml-pipeline starts without CLI args |

---

## Open Questions

1. **Should the ml-pipeline be a long-running service or one-shot batch job in docker-compose?**
   - What we know: The current Dockerfile uses a batch `CMD` (one-shot). In K8s it runs as a CronJob (also one-shot).
   - What's unclear: Whether docker-compose users expect to run it manually vs. automatically.
   - Recommendation: Leave it as one-shot. The phase goal is just to prevent the ValueError crash. The container exiting with code 0 after a successful training run is correct behavior.

2. **Should the K8s ConfigMap for processing namespace be audited for `KAFKA_BOOTSTRAP_SERVERS`?**
   - What we know: `ConsumerSettings` docstring says "Env vars injected by K8s configmap (processing-config)".
   - What's unclear: Whether `k8s/processing/configmap.yaml` currently contains `KAFKA_BOOTSTRAP_SERVERS`.
   - Recommendation: Out of scope for this phase (K8s path is working; only docker-compose is broken). Verify K8s ConfigMap is not affected by the default change. If the ConfigMap does not set `KAFKA_BOOTSTRAP_SERVERS`, the K8s pods would start using the new `kafka:9092` default — which would be a regression. Add a task to verify/add the K8s ConfigMap entry.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `stock-prediction-platform/services/kafka-consumer/pytest.ini` |
| Quick run command | `cd stock-prediction-platform/services/kafka-consumer && python -m pytest tests/ -x -q` |
| Full suite command | `cd stock-prediction-platform/services/kafka-consumer && python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FIX-KAFKA | ConsumerSettings reads KAFKA_BOOTSTRAP_SERVERS from env var | unit | `pytest tests/test_main.py -x -q` | ✅ existing |
| FIX-KAFKA | Default changed to `kafka:9092` | unit | New test in `tests/test_main.py` or `tests/conftest.py` | ❌ Wave 0 gap |
| FIX-ML | training_pipeline `__main__` reads TICKERS env var | unit | New test in `ml/tests/test_training_pipeline.py` | ✅ file exists |
| FIX-ML | ValueError NOT raised when TICKERS env var is set | unit | New test in ml tests | ✅ file exists |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform/services/kafka-consumer && python -m pytest tests/ -x -q`
- **Per wave merge:** Full consumer suite + `cd stock-prediction-platform && python -m pytest ml/tests/test_training_pipeline.py -x -q`
- **Phase gate:** Both test suites green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_main.py` or new test file — add test: `ConsumerSettings default KAFKA_BOOTSTRAP_SERVERS == "kafka:9092"` and `ConsumerSettings honors KAFKA_BOOTSTRAP_SERVERS env var override`
- [ ] `ml/tests/test_training_pipeline.py` — add test: `__main__`-like invocation with `TICKERS` env var set does not raise ValueError

*(Existing test infrastructure covers the rest — no framework install needed)*

---

## Sources

### Primary (HIGH confidence)
- Direct code reading: `services/kafka-consumer/consumer/config.py` — confirmed hardcoded default on line 17
- Direct code reading: `ml/Dockerfile` line 31 — confirmed CMD entrypoint
- Direct code reading: `ml/pipelines/training_pipeline.py` lines 178-179 — confirmed ValueError condition
- Direct code reading: `docker-compose.yml` — confirmed kafka-consumer has no environment block
- Direct code reading: `services/api/app/config.py` line 39 — confirmed 20-stock TICKER_SYMBOLS pattern
- Phase 57 verification note (line 162): "The `kafka-consumer` and `ml-pipeline` known exits are unrelated to phase 57 scope" — confirms these are known regressions

### Secondary (MEDIUM confidence)
- pydantic-settings BaseSettings documented behavior: env var with matching name overrides class default — verified by existing usage in ConsumerSettings and API Settings

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies, direct code inspection
- Architecture: HIGH — both bugs are single-line root causes with clear fix paths
- Pitfalls: HIGH — K8s ConfigMap regression risk is real and verifiable

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable codebase, no fast-moving dependencies)
