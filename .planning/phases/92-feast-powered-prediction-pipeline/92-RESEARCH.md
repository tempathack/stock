# Phase 92: Feast-Powered Prediction Pipeline - Research

**Researched:** 2026-04-03
**Domain:** Feast feature store integration — offline training + online inference
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Feature Set Scope**
- Use all available Feast features: OHLCV technical indicators (from `feast_writer` Flink job) + Reddit sentiment scores (`positive_ratio`, `negative_ratio`, `avg_sentiment`, `mention_count` from `sentiment_writer`)
- Horizon target unchanged: t+7 price return
- Entity key: ticker-only for online inference (latest features); ticker + date for offline training (historical point-in-time joins)
- At inference time, use latest available online features regardless of staleness — add `feature_freshness_seconds` field to `PredictionResponse` for observability
- Point-in-time join at training time uses existing `pit_validator.py` logic

**Training Pipeline Feast Integration**
- Replace **`data_loader` step (step 1)** of the 11-step Kubeflow pipeline — instead of querying `ohlcv_daily` and computing indicators locally, pull historical feature dataset from Feast offline store via `get_historical_features()`
- Offline store: PostgreSQL (already configured in `ml/feature_store/feature_repo.py`)
- All downstream pipeline steps (label generation, CV, training, evaluation, winner selection) remain unchanged
- **Retrain from scratch** — do not fine-tune existing winner; the new feature distribution (with sentiment) warrants full retraining
- After winner selection, serialize Feast feature view column names to `features.json` alongside `pipeline.pkl`

**Inference Path Switchover**
- Add `FEAST_INFERENCE_ENABLED: bool = False` to `config.py`
- When `True`: call Feast online store via the existing `get_online_features_for_ticker()` stub (rewritten), align to `features.json`, pass to `pipeline.predict()`
- When `False`: fall back to current `_legacy_inference()` — existing behavior unchanged
- Rewrite `get_online_features_for_ticker()` (currently at `prediction_service.py:943`, defined but never called)
- Do NOT call KServe in this path — `FEAST_INFERENCE_ENABLED` and `KSERVE_ENABLED` are independent flags

**Fallback Strategy**
- If Feast online store is unavailable OR feature timestamp is older than **10 minutes**: fall back to `_legacy_inference()` automatically
- 10-minute threshold matches Flink checkpoint interval
- Log fallback reason (`feast_unavailable` / `feast_stale`) and emit `feast_stale_features_total` Prometheus counter
- Fallback must be silent to the caller — `PredictionResponse` format unchanged

### Claude's Discretion
- Exact Feast SDK call pattern (`get_online_features` vs `store.get_online_features` vs entity rows format)
- How to handle tickers with no sentiment data in Feast (fill with 0.0 or feature mean)
- Alembic migration needs (if any new tables required)
- Whether to add Feast feature staleness panel to Grafana dashboard

### Deferred Ideas (OUT OF SCOPE)
- Surfacing `feature_freshness_seconds` in the frontend prediction UI — future phase
- Adding Feast feature staleness panel to Grafana — could be a small add-on phase or done within phase 92 at Claude's discretion
- Extending Feast feature set with new feature views (e.g., fundamentals, earnings) — separate phase
- A/B testing old vs new model (OHLCV-only vs OHLCV+sentiment) — could use existing `AB_TESTING_ENABLED` flag in a future phase
</user_constraints>

---

## Summary

Phase 92 completes the originally-intended architecture: the codebase already has all Feast infrastructure (feature repo, push sources, Redis online store, PostgreSQL offline store, PIT validator, Flink writers feeding both indicator and sentiment views), and the prediction service even has a `get_online_features_for_ticker()` stub at line 943 that was built for this purpose but never wired in.

The work is split across two tracks that must be coordinated: (1) training pipeline — replace step 1 (`data_loader`) with a Feast `get_historical_features()` call that includes all four feature views (ohlcv_stats_fv, technical_indicators_fv, lag_features_fv, reddit_sentiment_fv) and retrain from scratch; (2) inference path — add `FEAST_INFERENCE_ENABLED` flag, rewrite the stub to fetch all features from the Redis online store, handle missing sentiment gracefully (fill 0.0), check feature freshness against the 10-minute threshold, fall back silently to `_legacy_inference()` when stale/unavailable, and emit a Prometheus counter for observability.

The critical coupling point is `features.json`: the training pipeline must serialize the Feast-sourced column names so the inference path can align the feature vector to exactly the same columns the model was trained on. This already happens in `deployer.py` for the legacy path — phase 92 extends this to write the Feast feature names rather than the locally-computed indicator names.

**Primary recommendation:** Treat the two tracks as parallel tasks with a shared gate: training first (produces new `features.json` with sentiment columns), inference path second (reads that `features.json` to align online features), then flip the flag.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| feast[postgres,redis] | 0.61.0 | Feature store — offline (PostgreSQL) + online (Redis) | Already installed; confirmed in `ml/requirements.txt` |
| pandas | (existing) | Entity DataFrame construction, historical feature DataFrame | Required by Feast `get_historical_features()` return type |
| prometheus_client | (existing) | `feast_stale_features_total` counter | Pattern already in `services/api/app/metrics.py` |
| starlette.concurrency.run_in_threadpool | (existing) | Wrap sync Feast Redis calls in async handlers | Pattern already used in `feast_online_service.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psycopg2 | (existing) | PostgreSQL offline store backend (Feast uses it internally) | Indirect — Feast manages connections |
| redis-py | (existing) | Redis online store backend | Indirect — Feast manages connections |
| pydantic-settings | (existing) | `FEAST_INFERENCE_ENABLED` flag on `Settings` | Already the config pattern |

**No new packages required.** All dependencies are present.

**Installation:** No action needed — `feast[postgres,redis]==0.61.0` already in requirements.

---

## Architecture Patterns

### Full Feature List — Training vs Inference

The key decision is which features to include. The existing `_TRAINING_FEATURES` list in `ml/features/feast_store.py` covers three views (30 features). Phase 92 extends this to add the four sentiment columns from `reddit_sentiment_fv`.

**Offline (training) features — all four views:**
```
ohlcv_stats_fv:open, high, low, close, volume, daily_return, vwap            (7)
technical_indicators_fv:rsi_14, macd_line, macd_signal, bb_upper, bb_lower,
                          atr_14, adx_14, ema_20, obv                         (9)
lag_features_fv:lag_1..lag_21, rolling_mean_5/10/21, rolling_std_5/10/21      (14)
reddit_sentiment_fv:avg_sentiment, mention_count, positive_ratio, negative_ratio (4 — top_subreddit excluded, String type)
```
Total: 34 numeric features + the entity/timestamp columns.

**Online (inference) features — all numeric columns from all four views** (same 34 features, fetched from Redis).

### Pattern 1: Feast Offline — `get_historical_features()` for Training

**What:** Build an entity DataFrame covering all tickers × all trading dates, then call `store.get_historical_features()` to get PIT-correct features.

**When to use:** Step 1 of the training pipeline, replacing the raw Postgres query + local indicator computation.

```python
# Source: ml/features/feast_store.py + ml/feature_store/pit_validator.py
import pandas as pd
from ml.features.feast_store import get_store

def load_feast_training_data(
    tickers: list[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Replace data_loader.load_data() — returns wide feature DataFrame."""
    dates = pd.date_range(start=start_date, end=end_date, freq="B")  # business days
    rows = [
        {"ticker": t, "event_timestamp": pd.Timestamp(d, tz="UTC")}
        for t in tickers
        for d in dates
    ]
    entity_df = pd.DataFrame(rows)
    store = get_store()
    return store.get_historical_features(
        entity_df=entity_df,
        features=_ALL_TRAINING_FEATURES,  # 34-feature list including sentiment
    ).to_df()
```

Key: The returned DataFrame already has all indicator columns computed — step 2 (feature engineering) no longer needs to re-compute OHLCV indicators; it should be skipped or become a no-op passthrough when `use_feast_data=True`.

### Pattern 2: Feast Online — `store.get_online_features()` for Inference

**What:** The synchronous SDK call that reads from Redis. Must be wrapped with `run_in_threadpool` in async handlers.

**When to use:** Inside the rewritten `get_online_features_for_ticker()` when `FEAST_INFERENCE_ENABLED=True`.

```python
# Source: feast_online_service.py:get_sentiment_features() — exact pattern to mirror
from feast import FeatureStore
from app.config import settings

def _fetch_all_feast_features(ticker: str) -> dict | None:
    """Synchronous. Call via run_in_threadpool."""
    store = FeatureStore(repo_path=settings.FEAST_STORE_PATH)
    result = store.get_online_features(
        features=[
            "ohlcv_stats_fv:open",
            # ... all 34 numeric features
            "reddit_sentiment_fv:avg_sentiment",
            "reddit_sentiment_fv:mention_count",
            "reddit_sentiment_fv:positive_ratio",
            "reddit_sentiment_fv:negative_ratio",
        ],
        entity_rows=[{"ticker": ticker.upper()}],
    ).to_dict()
    return result
```

The `.to_dict()` return format is `{"feature_name": [value], ...}` — values are lists of length 1. Access with `result.get("avg_sentiment", [None])[0]`.

### Pattern 3: Feature Freshness Check (10-minute threshold)

**What:** Check the Feast online feature timestamp before using it. The `reddit_sentiment_fv` has `ttl=timedelta(minutes=10)` in `feature_repo.py` — features older than 10 minutes should trigger fallback.

```python
import time

def _get_feast_feature_age_seconds(result: dict) -> float | None:
    """Extract feature age from Feast result metadata if available.
    Falls back to checking the __event_timestamp__ field if present."""
    ts_list = result.get("__event_timestamp__")
    if not ts_list or ts_list[0] is None:
        return None
    ts = ts_list[0]
    if hasattr(ts, "timestamp"):
        return time.time() - ts.timestamp()
    return None
```

Note: Feast 0.61.0 may or may not return `__event_timestamp__` in `to_dict()` — verify during implementation. An alternative is to check if the returned values are all `None` (Redis TTL expiry means the key is gone). The fallback trigger should be: `result_is_none OR all_values_none OR age > 600`.

### Pattern 4: Feature Alignment via `features.json`

**What:** After Feast training, `features.json` must contain the exact column names as returned by Feast's `to_df()` (which strips the `view_name:` prefix — e.g., `"rsi_14"` not `"technical_indicators_fv:rsi_14"`). At inference time, the online feature dict keys from `.to_dict()` also omit the view prefix.

```python
# Training: save Feast column names (minus entity/timestamp cols)
feature_cols = [c for c in feast_df.columns
                if c not in ("ticker", "event_timestamp")]
with open(features_path, "w") as f:
    json.dump(feature_cols, f)

# Inference: align online features to features.json
import numpy as np
import pandas as pd

def _align_feast_features(raw: dict, feature_names: list[str]) -> pd.DataFrame:
    row = {}
    for col in feature_names:
        val_list = raw.get(col)
        val = val_list[0] if val_list else None
        row[col] = 0.0 if val is None else float(val)  # fill missing with 0.0
    X = pd.DataFrame([row])[feature_names]
    return X.replace([np.inf, -np.inf], np.nan).fillna(0.0)
```

### Pattern 5: Feature Flag — `FEAST_INFERENCE_ENABLED`

**What:** Mirror the existing `KSERVE_ENABLED` flag pattern exactly.

```python
# config.py addition (Group 17)
FEAST_INFERENCE_ENABLED: bool = False
```

```python
# prediction_service.py:get_live_prediction() — third branch
if _settings.FEAST_INFERENCE_ENABLED:
    result = await _feast_inference(ticker=ticker, serving_dir=serving_dir,
                                    horizon=horizon, ab_model=ab_model)
    if result is not None:
        return result
    # Fall through to legacy on None (fallback already handled inside _feast_inference)

return await _legacy_inference(...)
```

The `_feast_inference()` function handles its own fallback internally — it never raises, returns `None` only for unrecoverable errors (missing pipeline.pkl), and logs the fallback reason.

### Recommended File Structure (changes only)

```
ml/features/feast_store.py          # extend _TRAINING_FEATURES to add sentiment view
ml/pipelines/components/data_loader.py  # add feast_load_data() alongside existing load_data()
ml/pipelines/training_pipeline.py   # step 1: branch on use_feast_data flag
ml/pipelines/components/deployer.py # extend to write feast_features.json or update features.json format
services/api/app/config.py          # add FEAST_INFERENCE_ENABLED: bool = False
services/api/app/metrics.py         # add feast_stale_features_total counter
services/api/app/models/schemas.py  # add feature_freshness_seconds: float | None to PredictionResponse
services/api/app/services/prediction_service.py  # rewrite get_online_features_for_ticker(); add _feast_inference()
k8s/ml/configmap.yaml               # add FEAST_INFERENCE_ENABLED: "false"
```

### Anti-Patterns to Avoid

- **Calling Feast from async context directly:** Feast's Redis client is synchronous. Always wrap with `run_in_threadpool` or `asyncio.to_thread()`. The existing `feast_online_service.py` shows the correct pattern.
- **Assuming Feast returns clean column names:** `get_historical_features().to_df()` drops the `view_name:` prefix. `get_online_features().to_dict()` also drops it. The `features.json` must use the unprefixed names consistently.
- **Checking sentiment TTL via feature_repo.py TTL:** The `reddit_sentiment_fv` TTL (`timedelta(minutes=10)`) controls Feast's offline store retrieval window, not Redis key expiry. Redis TTL must be set separately in `feast materialize` or handled by checking `None` values at inference time.
- **Modifying downstream pipeline steps:** Steps 2-12 of `training_pipeline.py` must remain unchanged. Only step 1 (`data_loader`) is replaced. The `engineer_features()` call in step 2 will receive a DataFrame that already has all indicator columns — the step must handle this gracefully (i.e., skip recomputation when columns already present).
- **Putting Feast fallback as a new chain layer in `predict.py`:** The fallback must happen inside `_feast_inference()`, not as a new entry in the predict router's fallback chain. See `code_context` in CONTEXT.md.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Point-in-time correct join for training | Custom SQL windowing query | `store.get_historical_features(entity_df)` | Feast handles temporal alignment, TTL, and multi-view joins natively |
| Feature freshness timestamps | Custom Redis TTL polling | Check `None` values from `.to_dict()` + Redis TTL behavior | Feast Redis online store automatically expires keys per TTL |
| Multi-view feature fetch in one call | Multiple separate Redis reads | Single `store.get_online_features(features=[...all views...])` call | Feast batches the Redis reads internally |
| Missing sentiment fill strategy | ML imputation pipeline | `0.0` fill for missing sentiment features | Matches the existing `_legacy_inference()` fill pattern at line 683 |
| Thread-safety for sync Feast client | Custom async wrapper | `starlette.concurrency.run_in_threadpool` | Already used in `feast_online_service.py` — proven pattern |

**Key insight:** Feast does the heavy lifting for PIT correctness and multi-view joins. The main implementation work is wiring feature names between training and inference, not re-implementing feature retrieval logic.

---

## Common Pitfalls

### Pitfall 1: `features.json` Column Name Mismatch
**What goes wrong:** Training writes Feast column names (e.g., `"rsi_14"`) but inference code looks up Redis keys with view-prefixed names (e.g., `"technical_indicators_fv__rsi_14"`).
**Why it happens:** `to_df()` and `to_dict()` both strip prefixes, but it's easy to accidentally use the full `"view:feature"` notation.
**How to avoid:** In tests, assert that `features.json` column names exactly match the keys returned by `store.get_online_features().to_dict()` for the same feature list.
**Warning signs:** All prediction values come out as `0.0` (every feature maps to missing → fill 0.0).

### Pitfall 2: Sentiment Data Missing for Many Tickers
**What goes wrong:** The `sentiment_writer` only pushes data for tickers with active Reddit activity. Most S&P 500 tickers will have `None` for all four sentiment columns in the online store.
**Why it happens:** Reddit coverage is sparse. `reddit_sentiment_fv` TTL is 10 minutes, so even tickers that were covered will frequently be expired.
**How to avoid:** Fill all `None` sentiment values with `0.0` before inference. The model will learn 0.0 as the "no sentiment data" sentinel during training (where historical sentiment is also sparse). Confirm that `features.json` includes sentiment columns even when training rows have many nulls — use `fillna(0.0)` in the training preprocessing step.
**Warning signs:** `feature_freshness_seconds` always None; predictions identical to legacy path.

### Pitfall 3: `feature_engineer` Step Recomputing on Top of Feast Features
**What goes wrong:** Step 2 of the pipeline (`engineer_features()`) re-computes technical indicators from OHLCV, overwriting the Feast-retrieved indicator values.
**Why it happens:** The training pipeline currently calls `engineer_features(data_dict)` unconditionally. If `data_dict` comes from Feast (already has `rsi_14`, etc.), this step will re-compute them from raw OHLCV if raw OHLCV columns are present.
**How to avoid:** When the Feast data loader is used, the return type is a flat wide DataFrame (not `{ticker: DataFrame}` per-ticker). The pipeline step 1 replacement must signal to step 2 that features are pre-computed — either by passing a `feast_mode=True` flag or by structuring the returned DataFrame to skip re-computation. A clean approach: return Feast data in the same dict format as `load_data()` but with indicator columns pre-populated; `engineer_features()` already checks for existing columns and skips re-computation.
**Warning signs:** Log shows step 2 running `compute_all_indicators` after step 1 used Feast.

### Pitfall 4: Feast Registry Cache Causing Stale Schema
**What goes wrong:** `feature_store.yaml` sets `cache_ttl_seconds: 60`. During development, if `feast apply` runs but the in-process cache hasn't expired, `get_online_features()` may reference the old schema.
**Why it happens:** Feast SQL registry caches FeatureView definitions in memory. Adding `reddit_sentiment_fv` to the online feature request requires the schema to be current.
**How to avoid:** After any `feature_repo.py` change, restart the API pod. During development, use `FeatureStore(repo_path=..., config=...)` with `cache_ttl_seconds=0` in tests.
**Warning signs:** `feast.errors.FeatureViewNotFoundException` in logs.

### Pitfall 5: `run_in_threadpool` vs `asyncio.to_thread`
**What goes wrong:** Mixing `asyncio.to_thread()` (used in `feast_service.py:measure_feast_online_latency_ms`) and `run_in_threadpool` (used in `feast_online_service.py`) in the same code path creates inconsistency.
**Why it happens:** Two different patterns exist in the codebase for wrapping sync Feast calls.
**How to avoid:** Use `run_in_threadpool` consistently in the prediction service path (matching `feast_online_service.py`). Reserve `asyncio.to_thread` for standalone utilities.
**Warning signs:** Event loop blocking or `RuntimeError: no running event loop`.

---

## Code Examples

### Training: Building the Entity DataFrame for All Tickers

```python
# Source: ml/feature_store/pit_validator.py:build_entity_df_for_backtest() — pattern to extend
import pandas as pd

def build_training_entity_df(
    tickers: list[str],
    start_date: str,  # "2022-01-01"
    end_date: str,    # "2025-12-31"
) -> pd.DataFrame:
    """Build entity DataFrame for Feast historical training data pull."""
    dates = pd.date_range(start=start_date, end=end_date, freq="B")
    rows = []
    for ticker in tickers:
        for d in dates:
            rows.append({
                "ticker": ticker,
                "event_timestamp": pd.Timestamp(d, tz="UTC"),
            })
    return pd.DataFrame(rows)
```

### Inference: Rewriting `get_online_features_for_ticker()`

```python
# Source: feast_online_service.py:get_sentiment_features() — exact pattern to follow
# prediction_service.py:957 — stub to replace

_ALL_ONLINE_FEATURES = [
    "ohlcv_stats_fv:open", "ohlcv_stats_fv:high", "ohlcv_stats_fv:low",
    "ohlcv_stats_fv:close", "ohlcv_stats_fv:volume",
    "ohlcv_stats_fv:daily_return", "ohlcv_stats_fv:vwap",
    "technical_indicators_fv:rsi_14", "technical_indicators_fv:macd_line",
    "technical_indicators_fv:macd_signal", "technical_indicators_fv:bb_upper",
    "technical_indicators_fv:bb_lower", "technical_indicators_fv:atr_14",
    "technical_indicators_fv:adx_14", "technical_indicators_fv:ema_20",
    "technical_indicators_fv:obv",
    "lag_features_fv:lag_1", "lag_features_fv:lag_2", "lag_features_fv:lag_3",
    "lag_features_fv:lag_5", "lag_features_fv:lag_7", "lag_features_fv:lag_10",
    "lag_features_fv:lag_14", "lag_features_fv:lag_21",
    "lag_features_fv:rolling_mean_5", "lag_features_fv:rolling_mean_10",
    "lag_features_fv:rolling_mean_21", "lag_features_fv:rolling_std_5",
    "lag_features_fv:rolling_std_10", "lag_features_fv:rolling_std_21",
    "reddit_sentiment_fv:avg_sentiment", "reddit_sentiment_fv:mention_count",
    "reddit_sentiment_fv:positive_ratio", "reddit_sentiment_fv:negative_ratio",
]

def get_online_features_for_ticker(ticker: str) -> dict | None:
    """Rewrite of the stub at prediction_service.py:957.
    Synchronous — call via run_in_threadpool.
    Returns flat dict {col_name: value} or None on failure.
    """
    try:
        from feast import FeatureStore
        from app.config import settings as _settings
        store = FeatureStore(repo_path=_settings.FEAST_STORE_PATH)
        result = store.get_online_features(
            features=_ALL_ONLINE_FEATURES,
            entity_rows=[{"ticker": ticker.upper()}],
        ).to_dict()
        # Flatten list-of-one to scalar, fill None with 0.0
        return {k: (v[0] if v and v[0] is not None else 0.0)
                for k, v in result.items()
                if k != "ticker"}
    except Exception as exc:
        logger.warning("get_online_features_for_ticker failed for %s: %s", ticker, exc)
        return None
```

### Prometheus Counter Registration

```python
# Source: services/api/app/metrics.py — extend this file
from prometheus_client import Counter

feast_stale_features_total = Counter(
    "feast_stale_features_total",
    "Total Feast feature fallbacks due to staleness or unavailability",
    ["ticker", "reason"],  # reason: feast_unavailable | feast_stale
)
```

### `PredictionResponse` Schema Extension

```python
# Source: services/api/app/models/schemas.py — add optional field
class PredictionResponse(BaseModel):
    ticker: str
    prediction_date: str
    predicted_date: str
    predicted_price: float
    model_name: str
    confidence: float | None = None
    horizon_days: int | None = None
    assigned_model_id: int | None = None
    feature_freshness_seconds: float | None = None  # NEW: seconds since Feast features were last written
```

---

## Existing Infrastructure Inventory

This is a complete picture of what exists and needs no changes vs what needs modification:

| File | Status | Change Needed |
|------|--------|--------------|
| `ml/feature_store/feature_repo.py` | EXISTS — 4 feature views defined | No change; `reddit_sentiment_fv` already there |
| `ml/feature_store/feature_store.yaml` | EXISTS — PostgreSQL offline + Redis online | No change |
| `ml/features/feast_store.py` | EXISTS — `_TRAINING_FEATURES` (30 cols, no sentiment) | Extend `_TRAINING_FEATURES` to add 4 sentiment cols |
| `ml/feature_store/pit_validator.py` | EXISTS — PIT entity builder + leakage checker | No change; use `build_entity_df_for_backtest()` as reference |
| `services/api/app/services/feast_online_service.py` | EXISTS — `get_sentiment_features()` + streaming pattern | Use as call pattern reference; no change |
| `services/api/app/services/feast_service.py` | EXISTS — freshness queries | No change |
| `services/api/app/services/prediction_service.py` | EXISTS — stub at line 957, `get_live_prediction()` at 372 | Rewrite stub; add `_feast_inference()`; add branch in `get_live_prediction()` |
| `ml/pipelines/components/data_loader.py` | EXISTS — Postgres only | Add `load_feast_data()` function alongside; keep `load_data()` intact |
| `ml/pipelines/training_pipeline.py` | EXISTS — step 1 calls `load_data()` | Branch step 1 on `use_feast_data` param; step 2 passthrough guard |
| `ml/pipelines/components/deployer.py` | EXISTS — copies `features.json` from registry | No change needed; `features.json` is written by model_selector/evaluator; ensure Feast column names flow through |
| `services/api/app/config.py` | EXISTS — Group 16 ends at Elasticsearch | Add `FEAST_INFERENCE_ENABLED: bool = False` as Group 17 |
| `services/api/app/metrics.py` | EXISTS — 3 counters/histograms | Add `feast_stale_features_total` counter |
| `services/api/app/models/schemas.py` | EXISTS — `PredictionResponse` at line 11 | Add `feature_freshness_seconds: float | None = None` |
| `k8s/ml/configmap.yaml` | EXISTS — has `FEAST_REPO_PATH` | Add `FEAST_INFERENCE_ENABLED: "false"` |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Postgres query + local indicator compute in `data_loader.py` | Feast `get_historical_features()` offline PostgreSQL | Phase 92 | Training data includes pre-computed indicators AND sentiment; no duplicate computation |
| `_legacy_inference()` path: fetch OHLCV → compute indicators → predict | `_feast_inference()` path: fetch Redis online features → align → predict | Phase 92 | Sentiment features available at inference; sub-millisecond feature retrieval |
| `features.json` contains locally-computed column names | `features.json` contains Feast view column names (same names, different source) | Phase 92 | Feature vector alignment is now canonical through the feature store |

**The `get_online_features_for_ticker()` stub at line 957 was already built for exactly this purpose** — the phase is completing the originally-intended architecture, not introducing a new pattern.

---

## Open Questions

1. **`engineer_features()` step with Feast data**
   - What we know: `training_pipeline.py` step 2 calls `engineer_features(data_dict)` unconditionally. Feast data loader returns a flat wide DataFrame, not `{ticker: raw_ohlcv_df}`.
   - What's unclear: Whether `engineer_features()` gracefully skips recomputation when indicator columns already exist, or blindly re-computes from OHLCV.
   - Recommendation: Read `ml/pipelines/components/feature_engineer.py` before implementing step 1 replacement. The pipeline step 1 return value format must match what step 2 expects, OR step 2 must be guarded with `if not use_feast_data`.

2. **Feast `__event_timestamp__` in `to_dict()` return**
   - What we know: The 10-minute freshness check needs a feature timestamp. `feast_service.py` queries `feast_metadata` table. `to_dict()` may include `__event_timestamp__` or `event_timestamp` as a key.
   - What's unclear: Whether Feast 0.61.0 exposes the timestamp through `to_dict()` or only through the `OnlineFeaturesResponse` object's internal attributes.
   - Recommendation: In `_feast_inference()`, attempt to read `__event_timestamp__` from the dict. If absent, fall back to a `time.time()` vs Redis key creation time heuristic, or just check if any numeric values are `None` (implies TTL expired).

3. **Alembic migration for any new tables**
   - What we know: The context explicitly calls this out as Claude's discretion. The four Feast feature views use existing tables (`feast_ohlcv_stats`, `feast_technical_indicators`, `feast_lag_features`). No new offline tables are needed for sentiment (sentiment is push-only to Redis, not persisted to PostgreSQL offline store since `reddit_sentiment_fv` uses a placeholder `indicators_source`).
   - What's unclear: Whether any new training-time tables (e.g., a `feast_training_runs` audit table) should be added.
   - Recommendation: No Alembic migration is needed for phase 92. The offline store tables already exist; sentiment training data will simply have nulls for most historical rows, filled with 0.0.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (confirmed via `ml/tests/pytest.ini`, `services/api/pytest.ini`) |
| Config file | `ml/tests/pytest.ini` and `services/api/pytest.ini` |
| Quick run command (ML) | `cd stock-prediction-platform && python -m pytest ml/tests/test_feast_store.py ml/tests/test_data_loader.py -x -q` |
| Quick run command (API) | `cd stock-prediction-platform && python -m pytest services/api/tests/test_prediction_service.py -x -q` |
| Full suite command (ML) | `cd stock-prediction-platform/ml && python -m pytest tests/ -q` |
| Full suite command (API) | `cd stock-prediction-platform/services/api && python -m pytest tests/ -q` |

### Phase Behaviors → Test Map

| Behavior | Test Type | Automated Command | File Status |
|----------|-----------|-------------------|-------------|
| `get_historical_features()` called with 34-feature list including sentiment | unit | `pytest ml/tests/test_feast_store.py -x -q` | EXISTS — extend |
| Feast training data loader returns correct column names | unit | `pytest ml/tests/test_data_loader.py::TestFeastDataLoader -x` | Wave 0 gap |
| `get_online_features_for_ticker()` fetches all views and flattens to dict | unit | `pytest services/api/tests/test_prediction_service.py::TestFeastInference -x` | Wave 0 gap |
| Missing sentiment values filled with 0.0 | unit | same file above | Wave 0 gap |
| Stale/unavailable Feast triggers `_legacy_inference()` fallback | unit | same file above | Wave 0 gap |
| `feast_stale_features_total` counter incremented on fallback | unit | same file above | Wave 0 gap |
| `feature_freshness_seconds` populated in `PredictionResponse` | unit | `pytest services/api/tests/test_predict.py -x` | Wave 0 gap |
| `FEAST_INFERENCE_ENABLED=True` uses Feast path; `False` uses legacy | unit | same test file | Wave 0 gap |
| `features.json` column names match Feast online dict keys | unit | `pytest ml/tests/test_feast_store.py -x` | Wave 0 gap (new test case) |

### Sampling Rate
- **Per task commit:** Quick run command for the affected component
- **Per wave merge:** Full suite for both ml/ and services/api/
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `ml/tests/test_data_loader.py::TestFeastDataLoader` — unit tests for `load_feast_data()` with mocked `FeatureStore`
- [ ] `services/api/tests/test_prediction_service.py::TestFeastInference` — unit tests for rewritten `get_online_features_for_ticker()`, `_feast_inference()`, fallback logic, counter emissions
- [ ] New test case in `ml/tests/test_feast_store.py` — assert `_TRAINING_FEATURES` (after extension) includes all 4 sentiment columns and that column names match `to_dict()` key format

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `ml/features/feast_store.py` — existing `_TRAINING_FEATURES` list, `get_historical_features()`, `get_online_features()` call patterns
- Direct code inspection: `services/api/app/services/feast_online_service.py` — proven `store.get_online_features()` call pattern + `run_in_threadpool` wrapper
- Direct code inspection: `ml/feature_store/feature_repo.py` — all four FeatureView definitions including `reddit_sentiment_fv` with TTL
- Direct code inspection: `ml/feature_store/feature_store.yaml` — Feast 0.61.0, PostgreSQL offline, Redis online
- Direct code inspection: `services/api/app/services/prediction_service.py:957` — stub location and existing `get_live_prediction()` branch pattern
- Direct code inspection: `services/api/app/config.py` — existing `KSERVE_ENABLED` flag pattern to mirror
- Direct code inspection: `services/api/app/metrics.py` — prometheus_client Counter pattern
- Direct code inspection: `ml/pipelines/training_pipeline.py` — step 1 location and `data_dict` passing convention

### Secondary (MEDIUM confidence)
- Feast 0.61.0 `to_dict()` return format: inferred from `feast_online_service.py` usage (`.to_dict()` returns `{"feature_name": [value_list]}`). Consistent with Feast documentation patterns.
- `__event_timestamp__` availability in `to_dict()`: LOW confidence — needs verification during implementation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages confirmed present in requirements.txt; no new dependencies
- Architecture: HIGH — all patterns drawn directly from existing working code in the repo
- Pitfalls: MEDIUM-HIGH — derived from code inspection; `feature_engineer` interaction (pitfall 3) needs verification
- Validation architecture: HIGH — test framework confirmed, gap analysis based on code inspection

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable — Feast 0.61.0 pinned; no moving targets)
