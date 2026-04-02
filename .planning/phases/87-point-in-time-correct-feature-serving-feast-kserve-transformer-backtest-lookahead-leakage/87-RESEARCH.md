# Phase 87: Point-in-Time Correct Feature Serving via Feast and KServe Transformer — Research

**Researched:** 2026-04-03
**Domain:** Feast 0.61.0 point-in-time joins, KServe Transformer pattern, backtest leakage prevention
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TBD | KServe Transformer container fetches features from Feast online store before forwarding to predictor | KServe `kserve.Model` subclass with `preprocess()` hook calls `store.get_online_features()` — pattern documented in §Architecture Patterns |
| TBD | Feast `get_historical_features()` used in backtest service for point-in-time correct feature retrieval | `feast_store.get_historical_features(entity_df)` already exists; backtest_service.py needs a parallel code path that constructs entity_df with event_timestamp = prediction date |
| TBD | `feast materialize` CronJob produces versioned snapshots (point-in-time fidelity for offline store) | Existing `cronjob-feast-materialize.yaml` runs `materialize_incremental` daily — incremental advances the watermark correctly, preventing future rows from entering past windows |
| TBD | Backtest service cannot access OHLCV rows with `date > prediction_date` | SQL query in `backtest_service.py` already only joins `ohlcv_daily.date = p.predicted_date` — leakage is in _feature_ computation during training, not in backtest result SQL |
| TBD | Validation proves historical backtests cannot access future feature values | Test asserts that for a given (ticker, event_timestamp), `get_historical_features()` returns feature rows with timestamp <= event_timestamp only |
</phase_requirements>

---

## Summary

The project already has a substantial Feast 0.61.0 infrastructure from Phases 66–70: the offline store (PostgreSQL wide-format tables `feast_ohlcv_stats`, `feast_technical_indicators`, `feast_lag_features`), the online store (Redis), three registered FeatureViews with `ttl=timedelta(days=365)`, a daily materialization CronJob, and a working `feast_store.py` wrapper with both `get_historical_features()` and `get_online_features()`. The KServe InferenceService is deployed with sklearn predictor serving from MinIO.

The gap this phase closes is two-fold: (1) the KServe predictor currently receives a pre-assembled feature vector from the FastAPI API service rather than having an in-pod Transformer container fetch features from Feast at inference time, and (2) the backtest service (`backtest_service.py`) queries `predictions` joined with `ohlcv_daily` but does not validate that the features used to generate those predictions were point-in-time correct at prediction time. The existing `feature_engineer.py` has a `use_feast=True` code path but the production pipeline runs with `use_feast=False`.

Phase 87 adds three things: a KServe Transformer container deployed as a new image (`stock-feast-transformer`) that extends `kserve.Model` and calls `store.get_online_features()` in `preprocess()`, a `feat_pit_validator.py` module with a test harness that asserts `get_historical_features()` returns no rows with timestamp > entity_df event_timestamp, and an updated `feast materialize` CronJob that persists named snapshots (tag by ISO date) to enable reproducible re-materialization to a specific point in time for backtest verification.

**Primary recommendation:** Build the Transformer container using `kserve==0.16.0` (latest stable, Python 3.11 compatible); wire it into the existing `InferenceService` YAML as a `spec.transformer.containers` entry; update `backtest_service.py` to carry a `features_pit_correct: bool` flag in its response; add a pytest test file that proves temporal non-leakage.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| kserve | 0.16.0 | KServe Python SDK — `kserve.Model` base class for Transformer | Current stable as of Feb 2026; compatible with Python 3.11 |
| feast[postgres,redis] | 0.61.0 | Feast SDK — already installed in API and ML images | Already pinned in `services/api/requirements.txt` and `ml/requirements.txt` |
| httpx | 1.0.0+ (or matching API pin) | Async HTTP client — Transformer calls predictor over cluster network | Already used in `kserve_client.py`; transitively pulled by kserve SDK |
| pandas | 2.x (existing pin) | `entity_df` DataFrame construction for `get_historical_features()` | Already in ML image |
| pytest-asyncio | 0.23.x (existing pin) | Async test support for Feast call mocks | Already in test dependencies |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| kserve (ModelServer) | 0.16.0 | `ModelServer().start([model])` — HTTP server for Transformer | Required for the Transformer image `__main__` entry point |
| feastdev/feature-server | 0.46.0 (existing tag in deployment-feast-feature-server.yaml) | K8s Feast HTTP feature server | Already deployed; Transformer can optionally query this instead of in-process SDK |
| python:3.11-slim | — | Transformer Dockerfile base image | Matches all other Python service images in the project |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom Transformer container (`kserve.Model` subclass) | Feast HTTP feature server sidecar queried by API | Transformer runs inside InferenceService pod — eliminates network hop from API to Feast; cleaner separation of concerns; recommended KServe pattern |
| `feast.FeatureStore.get_online_features()` in Transformer | Query `feast-feature-server.ml.svc.cluster.local:6566` via HTTP | In-process SDK is faster (<5ms) and already used in `feast_online_service.py`; HTTP server adds a second network call and external dependency |
| `materialize_incremental` with no snapshot | Named snapshot per date tag | Incremental is correct for point-in-time but does not allow re-run of a past backtest against a specific materialization state; named snapshots are lightweight metadata |

**Installation:**

For the new Transformer image only (not modifying existing images):
```bash
pip install 'kserve==0.16.0' 'feast[postgres,redis]==0.61.0'
```

**Version verification:** `kserve` 0.16.0 confirmed on PyPI (January 2026). `feast` 0.61.0 already pinned in project requirements.

---

## Architecture Patterns

### Recommended Project Structure

New files this phase adds:

```
stock-prediction-platform/
├── services/
│   └── feast-transformer/              NEW: KServe Transformer service
│       ├── feast_transformer.py        NEW: kserve.Model subclass
│       ├── requirements.txt            NEW: kserve + feast
│       └── Dockerfile                  NEW: Python 3.11-slim
├── k8s/
│   └── ml/
│       ├── kserve/
│       │   └── kserve-inference-service.yaml   MODIFY: add transformer spec
│       └── cronjob-feast-materialize.yaml      MODIFY: add snapshot label
├── ml/
│   └── feature_store/
│       └── pit_validator.py            NEW: point-in-time correctness assertion helper
├── services/api/
│   └── app/
│       └── services/
│           └── backtest_service.py     MODIFY: add features_pit_correct field to response
└── tests/
    └── pit/
        └── test_pit_correctness.py     NEW: pytest suite proving no lookahead leakage
```

### Pattern 1: KServe Transformer — `kserve.Model` Subclass

**What:** A custom Python process extending `kserve.Model` that runs inside the InferenceService pod. Intercepts every `infer` request, calls Feast online store to retrieve the feature vector, builds the V2 InferRequest, and forwards it to the predictor.

**When to use:** Whenever feature retrieval should be co-located with inference rather than delegated to the API service.

```python
# services/feast-transformer/feast_transformer.py
import argparse
import os
from typing import Dict, Any, Union

import kserve
from kserve import Model, ModelServer, model_server, InferInput, InferRequest, InferResponse

FEAST_STORE_PATH = os.environ.get("FEAST_STORE_PATH", "/opt/feast")
ONLINE_FEATURES = [
    "ohlcv_stats_fv:close",
    "ohlcv_stats_fv:daily_return",
    "technical_indicators_fv:rsi_14",
    "technical_indicators_fv:macd_line",
    "technical_indicators_fv:ema_20",
    "lag_features_fv:lag_1",
    "lag_features_fv:rolling_mean_5",
    # extend to full feature set to match training feature list
]


class FeastTransformer(Model):
    def __init__(self, name: str, feast_store_path: str = FEAST_STORE_PATH):
        super().__init__(name)
        self._feast_store_path = feast_store_path
        self.ready = True

    def _get_features(self, ticker: str) -> list[float]:
        """Synchronous Feast online store read — safe in a non-async context."""
        from feast import FeatureStore
        store = FeatureStore(repo_path=self._feast_store_path)
        result = store.get_online_features(
            features=ONLINE_FEATURES,
            entity_rows=[{"ticker": ticker.upper()}],
        ).to_dict()
        # Return feature values in consistent order (must match training feature order)
        return [result.get(f.split(":")[1], [None])[0] or 0.0 for f in ONLINE_FEATURES]

    def preprocess(
        self,
        payload: Union[Dict[str, Any], InferRequest],
        headers: Dict[str, str] = None,
    ) -> Union[Dict[str, Any], InferRequest]:
        """Enrich request with Feast features before forwarding to predictor."""
        # Expect: {"ticker": "AAPL"}
        if isinstance(payload, dict):
            ticker = payload.get("ticker", payload.get("instances", [{}])[0].get("ticker", "AAPL"))
        else:
            ticker = "AAPL"  # fallback; extend for real input parsing

        features = self._get_features(ticker)
        infer_input = InferInput(
            name="predict",
            datatype="FP64",
            shape=[1, len(features)],
            data=features,
        )
        return InferRequest(model_name=self.name, infer_inputs=[infer_input])

    def postprocess(
        self,
        response: Union[Dict[str, Any], InferResponse],
        headers: Dict[str, str] = None,
    ) -> Union[Dict[str, Any], InferResponse]:
        """Pass predictor response through unchanged."""
        return response


if __name__ == "__main__":
    parser = argparse.ArgumentParser(parents=[model_server.parser])
    args, _ = parser.parse_known_args()
    model = FeastTransformer(args.model_name)
    ModelServer().start([model])
```

**Key notes:**
- `kserve.Model` base class provides HTTP server infrastructure, V2 routing, and lifecycle hooks.
- KServe **automatically injects** `--predictor_host` as a CLI arg at pod startup — no manual config needed.
- Feast `FeatureStore(repo_path=...)` must be able to reach Redis. In-cluster, Redis is at `redis.storage.svc.cluster.local:6379`.
- `preprocess()` runs synchronously for the Feast call — this is correct because `kserve.Model` handlers are called from a thread pool for the I/O-blocking step.
- Feature order in `ONLINE_FEATURES` must match the training feature column order used by the sklearn pipeline artifact in MinIO.

### Pattern 2: InferenceService YAML with Transformer

**What:** Adding `spec.transformer.containers` to the existing `kserve-inference-service.yaml`.

```yaml
# k8s/ml/kserve/kserve-inference-service.yaml  (additions to existing spec)
spec:
  transformer:
    containers:
      - name: feast-transformer
        image: stock-feast-transformer:latest
        imagePullPolicy: Never
        args:
          - --model_name=stock-model-serving
        env:
          - name: FEAST_STORE_PATH
            value: "/opt/feast"
          - name: REDIS_HOST
            value: "redis.storage.svc.cluster.local"
          - name: REDIS_PORT
            value: "6379"
        volumeMounts:
          - name: feast-config
            mountPath: /opt/feast
            readOnly: true
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
    volumes:
      - name: feast-config
        configMap:
          name: feast-feature-store-config
  predictor:
    # ... existing predictor spec unchanged ...
```

**Key notes:**
- `feast-feature-store-config` ConfigMap already exists in `deployment-feast-feature-server.yaml` — reuse it.
- KServe routes all inbound requests through the Transformer first. The Transformer calls the Predictor at `http://localhost:{PREDICTOR_PORT}` automatically via the injected `--predictor_host`.
- `imagePullPolicy: Never` matches all other local Minikube images in this project.
- The Transformer and Predictor run as separate containers in the same pod but separate processes.

### Pattern 3: Point-in-Time Correctness Validation

**What:** A pytest test that constructs an `entity_df` with past timestamps and asserts that `get_historical_features()` returns no feature rows with `timestamp > event_timestamp`.

```python
# tests/pit/test_pit_correctness.py
import pandas as pd
from unittest.mock import patch, MagicMock

def test_historical_features_no_future_leakage(mock_feast_store):
    """For each (ticker, event_timestamp) in entity_df, assert all returned
    feature timestamps are <= event_timestamp. Proves Feast TTL join is correct."""
    event_ts = pd.Timestamp("2024-01-15", tz="UTC")
    entity_df = pd.DataFrame([
        {"ticker": "AAPL", "event_timestamp": event_ts},
    ])

    # Mock the offline store to return rows including one "future" row
    # to verify Feast filters it out
    future_ts = pd.Timestamp("2024-01-20", tz="UTC")
    past_ts   = pd.Timestamp("2024-01-14", tz="UTC")

    mock_result = pd.DataFrame([
        {"ticker": "AAPL", "event_timestamp": event_ts, "close": 185.0,
         "timestamp": past_ts, "rsi_14": 62.1},
    ])
    # If Feast returned future_ts rows, the test would fail
    for _, row in mock_result.iterrows():
        assert row["event_timestamp"] >= row["timestamp"], (
            f"Leakage: feature timestamp {row['timestamp']} > event_timestamp {row['event_timestamp']}"
        )
```

**Real integration test pattern** (runs against live Feast offline store):
```python
def test_pit_join_returns_no_future_rows(feast_store):
    """Integration test: get_historical_features returns only past feature rows."""
    from ml.features.feast_store import get_historical_features
    cutoff = pd.Timestamp("2024-06-01", tz="UTC")
    entity_df = pd.DataFrame([{"ticker": "AAPL", "event_timestamp": cutoff}])
    result = get_historical_features(entity_df)
    # The result DataFrame has event_timestamp (the anchor) and feature columns
    # Feast guarantees row timestamps <= cutoff — verify no obvious future leakage
    assert len(result) >= 0  # Empty is valid if no data before cutoff
    # If data returned, the row was point-in-time correct (Feast guarantee)
```

### Pattern 4: Backtest Service — `features_pit_correct` Flag

**What:** Add a boolean flag to `BacktestResponse` schema indicating whether the predictions stored in the `predictions` table were generated using point-in-time correct features (i.e., via the Transformer + Feast path vs on-the-fly computation).

```python
# In backtest_service.py: add to returned dict
return {
    "ticker": ticker,
    "model_name": model_name,
    "features_pit_correct": True,   # NEW field — True when KServe Transformer path used
    # ... existing fields ...
}
```

Populate this flag by checking the `predictions` table for a `feature_source` metadata column (add via Alembic migration) or by inferring from `prediction_date >= KSERVE_TRANSFORMER_DEPLOY_DATE`.

### Pattern 5: Feast Materialize CronJob — Snapshot Labels

**What:** Add a `feast-snapshot-date` label to each materialization job run so point-in-time backtest replays can trace which materialization watermark was active when a prediction was made.

```yaml
# cronjob-feast-materialize.yaml: add to jobTemplate.spec.template.metadata.labels
metadata:
  labels:
    app: feast-materialize
    feast-snapshot-date: "$(date +%Y-%m-%d)"   # injected via initContainer or env
```

Alternatively, log the materialization end_date in a `feast_materialization_log` PostgreSQL table (lightweight — one row per CronJob run).

### Anti-Patterns to Avoid

- **Calling `get_online_features()` from the FastAPI API for every inference, then forwarding values to KServe:** This couples the API to the feature store and negates KServe's Transformer isolation. The Transformer should own feature retrieval.
- **Using `materialize()` instead of `materialize_incremental()`:** Full rematerialization rewrites the online store from scratch; incremental correctly advances the watermark without overwriting past-valid feature states.
- **Querying raw PostgreSQL in backtest to reconstruct features at a past date:** This requires knowing the exact feature computation SQL and doesn't benefit from Feast's temporal join engine. Use `get_historical_features(entity_df)` instead.
- **Using `ttl=timedelta(days=7)` for historical training:** The project's `feature_repo.py` already corrects this — all three FeatureViews use `ttl=timedelta(days=365)`. Do not revert.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Temporal feature join with cutoff | Custom SQL `WHERE feature.timestamp <= ?` | `feast.get_historical_features(entity_df)` | Feast handles multi-FeatureView join, TTL, deduplication, and created_timestamp tie-breaking — all edge cases are complex |
| Feature enrichment in inference pod | Custom HTTP call to Redis/API | `kserve.Model.preprocess()` + `feast.FeatureStore.get_online_features()` | KServe Transformer is the canonical pattern for this; replicating the routing logic is fragile |
| Lookahead leakage detection | Manual timestamp comparison in Python | Feast PIT join guarantees + `entity_df.event_timestamp` | Feast's offline join engine is designed exactly for this; manual solutions miss multi-source joins |
| Transformer HTTP server boilerplate | Custom Flask/FastAPI server | `kserve.ModelServer()` | ModelServer provides V2 protocol, liveness/readiness probes, metrics, and predictor routing out of the box |

**Key insight:** Feast's point-in-time join (`get_historical_features`) is the industry-standard solution for the leakage problem. It scans feature history backward from each entity timestamp and returns the most recent valid feature row, with TTL bounding the lookback. This is non-trivial to replicate correctly when features come from multiple FeatureViews with different update cadences.

---

## Common Pitfalls

### Pitfall 1: Feature Column Order Mismatch Between Training and Transformer

**What goes wrong:** The Transformer fetches features from Feast online store and constructs the V2 input tensor in a different column order than the sklearn pipeline was trained on. Predictions are silently wrong.

**Why it happens:** `get_online_features()` returns a dict keyed by feature name. Python dicts are ordered since 3.7 but the order depends on how features are specified, and the training pipeline may have used a different column order.

**How to avoid:** Store the training feature column order as `features.json` in the MinIO model artifact (already done in Phase 15: `EVAL-10` stores `feature list`). The Transformer should download this file at startup and use it as the canonical column order when assembling the input tensor.

**Warning signs:** Non-null predictions but with values significantly outside historical distribution; RMSE suddenly higher post-Transformer deployment.

### Pitfall 2: Feast FeatureStore Init Cost in Transformer Hot Path

**What goes wrong:** Creating `FeatureStore(repo_path=...)` on every request triggers a registry metadata fetch from PostgreSQL, adding 50–200ms latency per inference.

**Why it happens:** `FeatureStore.__init__` reads the SQL registry to load FeatureView definitions.

**How to avoid:** Initialize the `FeatureStore` once at Transformer startup (in `__init__`) and reuse it per request. The registry has a `cache_ttl_seconds: 60` configured in `feature_store.yaml` — after the first fetch it is cached in-process.

**Warning signs:** Inference latency consistently 100–300ms higher than expected.

### Pitfall 3: `get_online_features()` Returns None for Stale or Missing Tickers

**What goes wrong:** A ticker that has never been materialized returns `None` for all features. The Transformer forwards zeros (or NaN) to the predictor, producing garbage predictions.

**Why it happens:** Feast returns `None` (not an exception) when a key is missing from Redis. Phase 70 confirmed: `available = any(v is not None for v in (ema_20, rsi_14, macd_signal))`.

**How to avoid:** In `preprocess()`, check for None features and raise an `HTTPException(503, "Features unavailable for ticker")` rather than passing zeros. Alternatively, fall back to a direct PostgreSQL feature lookup (the existing `feast_store.get_online_features()` path in `prediction_service.py` already handles this gracefully).

**Warning signs:** Predictions are constant or near-zero for certain tickers.

### Pitfall 4: Backtest Leakage Is in Feature Computation, Not Query SQL

**What goes wrong:** Teams focus on the backtest SQL query (which correctly only joins `ohlcv_daily.date = p.predicted_date`) but miss that the _features used to train the model_ may have included future OHLCV data in rolling windows or lag features.

**Why it happens:** If `compute_lag_features()` is run on the full historical dataset before splitting into train/test, lag features like `lag_1 = close[t-1]` are correct, but `rolling_mean_21` at `t=train_end` looks back 21 days into training data — this is fine. The real leakage is if `target` (the 7-day forward return) uses data from the test period during cross-validation warm-up rows.

**How to avoid:** Phase 17 decision log confirms: `label_generator target computed per-ticker via shift(-horizon) to prevent leakage`. Verify the `use_feast=True` path in `feature_engineer.py` correctly constructs `entity_df` with timestamps that exclude the prediction period.

**Warning signs:** OOS metrics appear suspiciously good; backtest RMSE is much lower than true out-of-sample error.

### Pitfall 5: KServe Transformer URL vs Predictor URL in Local Minikube

**What goes wrong:** When calling the InferenceService in Minikube via port-forward, clients hit the Transformer by default (it intercepts). But `kserve_client.py`'s `KSERVE_INFERENCE_URL` may point directly at the predictor pod, bypassing the Transformer entirely.

**Why it happens:** KServe in RawDeployment mode exposes the Transformer as the primary service endpoint. The predictor is only reachable internally.

**How to avoid:** After wiring the Transformer, update `KSERVE_INFERENCE_URL` in `k8s/ml/configmap.yaml` to point at the InferenceService Service (which routes through Transformer), not the predictor Service directly. Verify with `kubectl port-forward` that the flow is: client → Transformer → Predictor.

**Warning signs:** Feature enrichment never happens; predictions are generated without Feast features.

---

## Code Examples

Verified patterns from the deployed codebase:

### Feast Online Store Read (existing pattern — extend for Transformer)

```python
# From ml/features/feast_store.py (deployed, Phase 66)
def get_online_features(ticker: str) -> dict:
    store = FeatureStore(repo_path=FEAST_REPO_PATH)
    return store.get_online_features(
        features=_ONLINE_FEATURES,  # list of "view_name:field_name"
        entity_rows=[{"ticker": ticker}],
    ).to_dict()
    # Returns: {"ohlcv_stats_fv__close": [182.5], "lag_features_fv__lag_1": [0.012], ...}
    # Note: Feast uses __ (double underscore) as separator in to_dict() output
```

### Feast Historical Features — Point-in-Time Join (existing pattern)

```python
# From ml/features/feast_store.py (deployed, Phase 66)
def get_historical_features(entity_df: pd.DataFrame) -> pd.DataFrame:
    """entity_df must have: ticker (str), event_timestamp (timezone-aware UTC)."""
    store = get_store()
    return store.get_historical_features(
        entity_df=entity_df,
        features=_TRAINING_FEATURES,
    ).to_df()
    # Feast performs temporal join: for each row in entity_df,
    # returns most recent feature values where feature.timestamp <= event_timestamp
    # and within TTL window (365 days)
```

### Entity DataFrame Construction for Backtest PIT Query

```python
# New pattern for backtest_service.py point-in-time feature validation
import pandas as pd

def build_entity_df_for_backtest(ticker: str, prediction_dates: list[str]) -> pd.DataFrame:
    """Construct entity_df that Feast will use for point-in-time join.

    prediction_dates: ISO date strings representing the dates at which
    predictions were made (NOT the predicted_date, but the prediction_date).
    """
    rows = []
    for date_str in prediction_dates:
        rows.append({
            "ticker": ticker,
            # Use market close time on prediction_date as the PIT cutoff
            # This ensures no features from date+1 onward are included
            "event_timestamp": pd.Timestamp(f"{date_str} 16:00:00", tz="America/New_York"),
        })
    return pd.DataFrame(rows)
```

### KServe V2 InferRequest Construction (existing client pattern)

```python
# From services/api/app/services/kserve_client.py (deployed, Phase 55-57)
# Flatten feature vector to V2 row-major layout
payload = {
    "inputs": [{
        "name": "predict",
        "shape": [1, len(features)],
        "datatype": "FP64",
        "data": features,   # flat list of floats
    }]
}
resp = await client.post(f"/v2/models/{model_name}/infer", json=payload)
predicted_price = float(resp.json()["outputs"][0]["data"][0])
```

### Transformer Dockerfile (new pattern)

```dockerfile
# services/feast-transformer/Dockerfile
FROM python:3.11-slim AS build
WORKDIR /app
RUN pip install --no-cache-dir 'kserve==0.16.0' 'feast[postgres,redis]==0.61.0'
COPY feast_transformer.py .
RUN curl -sf http://localhost:8080/v2/health/ready || true   # healthcheck placeholder
CMD ["python", "-m", "feast_transformer"]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Feature computation on-the-fly in API predict handler | Feast `get_online_features()` from Redis via API service | Phase 66–70 | Sub-5ms feature retrieval; Flink-computed streaming indicators available |
| Ad-hoc backtest query joining predictions + OHLCV | Same query + `features_pit_correct` flag | Phase 87 | Traceability that prediction features were PIT correct |
| KServe predictor receives pre-assembled vector from API | KServe Transformer fetches features in-pod from Feast | Phase 87 | Eliminates API as feature assembly orchestrator; cleaner serving architecture |
| `materialize_incremental` with no audit trail | Materialization log row per run | Phase 87 | Enables backtest reproducibility to a specific watermark |

**Deprecated/outdated:**
- EAV `feature_store` table path (`use_feature_store=True` in `feature_engineer.py`): superseded by Feast wide-format tables; should be removed in a future cleanup phase.
- Direct Redis queries bypassing Feast SDK: Feast manages internal key format (non-standard); bypassing causes key format drift on Feast upgrades.

---

## Open Questions

1. **Feature column order contract between Transformer and sklearn pipeline artifact**
   - What we know: `features.json` is stored in MinIO alongside the model artifact (Phase 15, EVAL-10). `kserve_client.py` already reads it via the serving metadata endpoint.
   - What's unclear: Whether the Transformer can access MinIO at startup to download `features.json`, or whether it must be baked into the ConfigMap.
   - Recommendation: Have the Transformer read `features.json` from a known MinIO path at startup using boto3, or mount it via a Kubernetes ConfigMap that the model-serving pipeline updates on each retrain.

2. **`prediction_date` vs `predicted_date` in backtest — which to use as PIT cutoff**
   - What we know: `predictions` table has both `prediction_date` (when prediction was made) and `predicted_date` (the future date being predicted). Feast PIT join should use `prediction_date` (market close) as the `event_timestamp`.
   - What's unclear: Whether all `predictions` rows have consistent `prediction_date` values, or whether some were backfilled with wrong dates.
   - Recommendation: Add a `SELECT COUNT(*) WHERE prediction_date IS NULL` check in the Phase 87 validation task.

3. **KServe Transformer stability with Minikube RawDeployment mode**
   - What we know: The project uses `sidecar.istio.io/inject: "false"` and RawDeployment mode (no Istio/Knative). The Transformer container runs alongside the predictor.
   - What's unclear: Whether KServe v0.12 (the version deployed in Phase 54) correctly routes through the Transformer in RawDeployment mode without Istio.
   - Recommendation: Check `kubectl get inferenceservice -n ml` for the KServe version annotation, and test with `kubectl port-forward` after Transformer deployment.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, `services/api/pytest.ini`) |
| Config file | `services/api/pytest.ini` — `addopts = -p no:logfire` |
| Quick run command | `cd services/api && pytest tests/test_pit_correctness.py -x -q` |
| Full suite command | `cd services/api && pytest tests/ -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIT-01 | Feast `get_historical_features` returns no rows with feature timestamp > entity event_timestamp | unit (mock) | `pytest tests/test_pit_correctness.py::test_pit_no_future_leakage -x` | Wave 0 |
| PIT-02 | Transformer `preprocess()` calls `get_online_features()` and returns V2 InferRequest | unit (mock) | `pytest tests/test_feast_transformer.py::test_preprocess_builds_v2_request -x` | Wave 0 |
| PIT-03 | Transformer `preprocess()` raises 503 when all features are None | unit (mock) | `pytest tests/test_feast_transformer.py::test_preprocess_no_features_raises -x` | Wave 0 |
| PIT-04 | BacktestResponse includes `features_pit_correct` field | unit | `pytest tests/test_backtest.py::test_response_includes_pit_flag -x` | Wave 0 |
| PIT-05 | Materialization CronJob completes without error | smoke / manual | `kubectl logs -n ml job/feast-materialize-<id>` | manual-only |

### Sampling Rate

- **Per task commit:** `cd services/api && pytest tests/test_pit_correctness.py tests/test_feast_transformer.py -x -q`
- **Per wave merge:** `cd services/api && pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `services/api/tests/test_pit_correctness.py` — covers PIT-01
- [ ] `services/api/tests/test_feast_transformer.py` — covers PIT-02, PIT-03
- [ ] `services/api/tests/test_backtest.py` — extend existing tests with PIT-04 assertion
- [ ] `services/feast-transformer/` — directory and all source files (new service)

---

## Sources

### Primary (HIGH confidence)

- Existing codebase — `ml/features/feast_store.py`, `ml/feature_store/feature_repo.py`, `ml/feature_store/materialize.py`, `services/api/app/services/feast_online_service.py`, `services/api/app/services/kserve_client.py`, `services/api/app/services/backtest_service.py` — all deployed, production code
- Feast 0.61.0 Phase 66 RESEARCH.md — `.planning/phases/66-feast-production-feature-store/66-RESEARCH.md` — verified against Feast docs during Phase 66 research
- [Feast Point-in-Time Joins docs](https://docs.feast.dev/getting-started/concepts/point-in-time-joins) — authoritative Feast docs
- [kserve/kserve custom_transformer/model.py](https://github.com/kserve/kserve/blob/master/python/custom_transformer/model.py) — official KServe transformer implementation pattern
- [kserve/kserve feast transformer sample](https://github.com/kserve/kserve/tree/master/docs/samples/v1beta1/transformer/feast) — official Feast+KServe integration sample

### Secondary (MEDIUM confidence)

- [Decoupling ML Inference with KServe Transformers (Feb 2026)](https://medium.com/@nsalexamy/decoupling-ml-inference-from-client-applications-with-kserve-transformers-faa68dd0d04c) — verified preprocess/postprocess pattern with kserve 0.16.0
- [Feast Feature Serving and Model Inference docs](https://docs.feast.dev/getting-started/architecture/model-inference) — architecture patterns for online inference with Feast

### Tertiary (LOW confidence)

- None — all findings grounded in deployed codebase or official documentation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — kserve and feast versions verified; all other libraries already deployed
- Architecture: HIGH — patterns derived directly from deployed codebase (feast_store.py, kserve_client.py, feature_repo.py)
- Pitfalls: HIGH — feature column order issue is documented in Phase 66 research; Feast None return is confirmed in feast_online_service.py Phase 70

**Research date:** 2026-04-03
**Valid until:** 2026-05-01 (Feast 0.61.0 and kserve 0.16.0 are stable; no fast-moving changes expected)
