# Phase 94: FRED Macro Feature Pipeline - Research

**Researched:** 2026-04-04
**Domain:** FRED API data collection, TimescaleDB wide-table ingestion, Feast FeatureView registration, K8s Secret wiring
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Table Schema**
- Separate table: `feast_fred_macro` — do not extend `feast_yfinance_macro`
- Wide format: one row per date, one column per FRED series (14 columns) — same pattern as `feast_yfinance_macro`
- TimescaleDB hypertable on `timestamp` column, same as existing macro table
- VIXCLS dropped from the fetch list — VIX already covered by `yfinance_macro_fv`
- 14 series to collect: DGS2, DGS10, T10Y2Y, T10Y3M, BAMLH0A0HYM2, DBAA, T10YIE, DCOILWTICO, DTWEXBGS, DEXJPUS, ICSA, NFCI, CPIAUCSL, PCEPILFE

**Gap Handling (Low-Frequency Series)**
- Forward-fill with no limit — carry last known value indefinitely until a new reading arrives
- Applies to all series but is especially relevant for ICSA (weekly), NFCI (weekly), CPIAUCSL (monthly), PCEPILFE (monthly)
- Implementation: `pandas.DataFrame.ffill()` after upserting into `feast_fred_macro` on the daily date spine

**Feast FeatureView Design**
- New `fred_macro_fv` FeatureView registered in `feature_repo.py` alongside existing `yfinance_macro_fv`
- `PostgreSQLSource` pointing to `feast_fred_macro`, same pattern as `yfinance_macro_source`
- No entity key — date-keyed only (same as `yfinance_macro_fv`)
- All 14 FRED features added to `_TRAINING_FEATURES` in `feast_store.py` (currently in `ml/features/feast_store.py`)
- Training join pulls both `yfinance_macro_fv` and `fred_macro_fv` — combined macro context of 19 features (5 yfinance + 14 FRED)
- Inference path updated to also pull `fred_macro_fv` features from Feast online store

**CronJob + Secret Wiring**
- Add FRED fetch to existing ingestion CronJob — no new K8s CronJob object
- `FRED_API_KEY` added to existing `stock-platform-secrets` K8s Secret, referenced via `secretKeyRef` in the CronJob pod spec
- CronJob reads `FRED_API_KEY` the same way `DATABASE_URL` and `POSTGRES_PASSWORD` are read today

### Claude's Discretion
- Exact FRED API client library (e.g. `fredapi` Python package vs direct HTTP)
- Retry/backoff strategy for FRED API rate limits
- Column naming convention for FRED series in the wide table (e.g. `dgs2`, `t10y2y`, `bamlh0a0hym2`)
- Test fixtures / mock FRED responses for RED-state TDD plan

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 94 adds a FRED (Federal Reserve Economic Data) macro data pipeline that is structurally identical to the Phase 93 yfinance macro pipeline. The pattern is already proven: a Python collector fetches external data, writes rows to a TimescaleDB wide-format table (`feast_fred_macro`), and Feast registers a `PostgreSQLSource` + `FeatureView` so training and inference can pull the data via `get_historical_features()` and `get_online_features()`.

The 14 FRED series span interest rates (DGS2, DGS10, T10Y2Y, T10Y3M), credit spreads (BAMLH0A0HYM2, DBAA), inflation expectations (T10YIE, PCEPILFE, CPIAUCSL), commodity prices (DCOILWTICO), trade-weighted USD (DTWEXBGS, DEXJPUS), and labor/financial conditions (ICSA, NFCI). These are a mix of daily, weekly, and monthly series from FRED. The `fredapi` Python package (v0.5.2, latest on PyPI) provides a thin wrapper around the FRED REST API and is the standard community choice. The direct HTTP alternative (requests + JSON) works but adds boilerplate that `fredapi` eliminates.

The only structural difference from Phase 93 is that `feast_fred_macro` is **date-keyed only** — there is no `ticker` column. FRED series are market-wide macro data, not per-stock. The Feast join in `get_historical_features()` will therefore need to align on `event_timestamp` (date) with no entity key, matching how `yfinance_macro_fv` already works in the existing codebase. The entire pattern — table creation, upsert helper, FeatureView definition, `_TRAINING_FEATURES` extension — is a copy-adapt of the Phase 93 yfinance implementation.

**Primary recommendation:** Use `fredapi==0.5.2` in `ml/requirements.txt` and `services/api/requirements.txt`. Model `fetch_fred_macro()` directly after `_fetch_yfinance_macro_wide()` in `data_loader.py`. Copy `create_macro_table()` / `write_yfinance_macro_to_db()` with the new table name and 14 FRED columns. Add `fred_macro_source` + `fred_macro_fv` to `feature_repo.py` and 14 entries to `_TRAINING_FEATURES` in `feast_store.py`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fredapi | 0.5.2 | Python wrapper for FRED REST API | Official community library; `Fred.get_series()` returns a pandas Series with DatetimeIndex; handles pagination and retries internally; zero boilerplate vs raw HTTP |
| pandas | 2.2.2 (already pinned) | DataFrame manipulation, ffill, date_range | Already in both requirements.txt files |
| psycopg2-binary | 2.9.9 (already pinned) | PostgreSQL upsert for `feast_fred_macro` | Already used in `data_loader.py` for all table writes |
| tenacity | 8.3.0 (already pinned) | Retry/backoff on FRED API calls | Already used in `yahoo_finance.py` for identical pattern |
| feast[postgres,redis] | 0.61.0 (already pinned) | Register `fred_macro_fv` FeatureView | Already running |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | (transitive via fredapi) | HTTP transport | fredapi uses it internally; no direct dependency needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| fredapi | requests + FRED REST directly | Raw HTTP avoids the package but adds URL construction, pagination, date parsing — all handled by fredapi. Use fredapi. |
| fredapi | pandas_datareader FRED reader | pandas_datareader FRED backend also exists but is a heavier dependency and less actively maintained for FRED specifically |

**Installation (add to ml/requirements.txt and services/api/requirements.txt):**
```bash
fredapi==0.5.2
```

**Version verification:** Confirmed 0.5.2 is the current PyPI latest as of 2026-04-04.

---

## Architecture Patterns

### Recommended Project Structure

The collector lives alongside the existing yfinance macro collector. No new directories needed.

```
ml/
├── pipelines/components/
│   └── data_loader.py         # ADD: fetch_fred_macro(), create_fred_macro_table(), write_fred_macro_to_db()
├── features/
│   └── feast_store.py         # EXTEND: _TRAINING_FEATURES += 14 fred_macro_fv:* entries
├── feature_store/
│   └── feature_repo.py        # ADD: fred_macro_source, fred_macro_fv
├── tests/
│   └── test_data_loader.py    # EXTEND: tests for fetch_fred_macro, create_fred_macro_table, write_fred_macro_to_db
services/api/app/services/
└── yahoo_finance.py           # ADD: fetch_fred_macro() — same signature as fetch_yfinance_macro()
k8s/
├── ingestion/
│   └── cronjob-historical.yaml  # EXTEND: add FRED_API_KEY env var (secretKeyRef)
└── ml/
    └── cronjob-training.yaml    # EXTEND: add FRED_API_KEY env var (secretKeyRef)
```

### Pattern 1: FRED Series Fetch (fredapi)

**What:** Fetch one or more FRED series for a date range; pivot to wide DataFrame.
**When to use:** Any time FRED daily/weekly/monthly data is needed.

```python
# Source: fredapi docs (https://github.com/mortada/fredapi)
import os
from fredapi import Fred
import pandas as pd

FRED_SERIES = [
    "DGS2", "DGS10", "T10Y2Y", "T10Y3M",
    "BAMLH0A0HYM2", "DBAA", "T10YIE",
    "DCOILWTICO", "DTWEXBGS", "DEXJPUS",
    "ICSA", "NFCI", "CPIAUCSL", "PCEPILFE",
]

def fetch_fred_macro(start_date: str, end_date: str) -> pd.DataFrame:
    fred = Fred(api_key=os.environ["FRED_API_KEY"])
    frames = {}
    for series_id in FRED_SERIES:
        s = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
        # s is a pandas.Series with DatetimeIndex, name=None
        frames[series_id.lower()] = s
    # Wide DataFrame: index=date, one column per series
    wide = pd.DataFrame(frames)
    # Reindex to daily date spine and forward-fill gaps (weekly/monthly series)
    date_spine = pd.date_range(start=start_date, end=end_date, freq="D")
    wide = wide.reindex(date_spine).ffill()
    wide.index.name = "date"
    return wide
```

### Pattern 2: TimescaleDB Wide Table (no ticker column)

**What:** `feast_fred_macro` follows the same DDL as `feast_yfinance_macro` but has no `ticker` column because FRED data is market-wide.
**When to use:** All Feast FeatureViews that are date-keyed without entity.

```sql
-- Pattern from data_loader.py _CREATE_MACRO_TABLE_SQL
CREATE TABLE IF NOT EXISTS feast_fred_macro (
    timestamp       TIMESTAMPTZ      NOT NULL,
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    dgs2            DOUBLE PRECISION,
    dgs10           DOUBLE PRECISION,
    t10y2y          DOUBLE PRECISION,
    t10y3m          DOUBLE PRECISION,
    bamlh0a0hym2    DOUBLE PRECISION,
    dbaa            DOUBLE PRECISION,
    t10yie          DOUBLE PRECISION,
    dcoilwtico      DOUBLE PRECISION,
    dtwexbgs        DOUBLE PRECISION,
    dexjpus         DOUBLE PRECISION,
    icsa            DOUBLE PRECISION,
    nfci            DOUBLE PRECISION,
    cpiaucsl        DOUBLE PRECISION,
    pcepilfe        DOUBLE PRECISION,
    PRIMARY KEY (timestamp)
);
SELECT create_hypertable('feast_fred_macro', 'timestamp', if_not_exists => TRUE);
```

Note: No `ticker` column and no `(ticker, timestamp)` composite key. Primary key is `timestamp` alone.

### Pattern 3: Feast FeatureView — date-keyed, no entity

**What:** `fred_macro_fv` mirrors `yfinance_macro_fv` with no entity binding. The Feast point-in-time join aligns on `event_timestamp` only.
**When to use:** Any market-wide signal without a per-stock dimension.

```python
# Source: feature_repo.py yfinance_macro_fv as direct template
fred_macro_source = PostgreSQLSource(
    name="fred_macro_source",
    query=(
        "SELECT timestamp, dgs2, dgs10, t10y2y, t10y3m, "
        "bamlh0a0hym2, dbaa, t10yie, dcoilwtico, dtwexbgs, "
        "dexjpus, icsa, nfci, cpiaucsl, pcepilfe "
        "FROM feast_fred_macro"
    ),
    timestamp_field="timestamp",
    created_timestamp_column="created_at",
)

fred_macro_fv = FeatureView(
    name="fred_macro_fv",
    entities=[],          # No entity — date-keyed only, same as yfinance_macro_fv
    ttl=timedelta(days=365),
    schema=[
        Field(name="dgs2",         dtype=Float64),
        Field(name="dgs10",        dtype=Float64),
        Field(name="t10y2y",       dtype=Float64),
        Field(name="t10y3m",       dtype=Float64),
        Field(name="bamlh0a0hym2", dtype=Float64),
        Field(name="dbaa",         dtype=Float64),
        Field(name="t10yie",       dtype=Float64),
        Field(name="dcoilwtico",   dtype=Float64),
        Field(name="dtwexbgs",     dtype=Float64),
        Field(name="dexjpus",      dtype=Float64),
        Field(name="icsa",         dtype=Float64),
        Field(name="nfci",         dtype=Float64),
        Field(name="cpiaucsl",     dtype=Float64),
        Field(name="pcepilfe",     dtype=Float64),
    ],
    source=fred_macro_source,
)
```

### Pattern 4: _TRAINING_FEATURES Extension

```python
# In ml/features/feast_store.py — append after existing yfinance_macro_fv entries
_TRAINING_FEATURES: list[str] = [
    # ... existing 35 features ...
    "fred_macro_fv:dgs2",
    "fred_macro_fv:dgs10",
    "fred_macro_fv:t10y2y",
    "fred_macro_fv:t10y3m",
    "fred_macro_fv:bamlh0a0hym2",
    "fred_macro_fv:dbaa",
    "fred_macro_fv:t10yie",
    "fred_macro_fv:dcoilwtico",
    "fred_macro_fv:dtwexbgs",
    "fred_macro_fv:dexjpus",
    "fred_macro_fv:icsa",
    "fred_macro_fv:nfci",
    "fred_macro_fv:cpiaucsl",
    "fred_macro_fv:pcepilfe",
]
# Total: 49 features (35 existing + 14 FRED)
```

### Pattern 5: K8s Secret Wiring

```yaml
# In cronjob-training.yaml and cronjob-historical.yaml — same pattern as POSTGRES_PASSWORD
env:
  - name: FRED_API_KEY
    valueFrom:
      secretKeyRef:
        name: stock-platform-secrets
        key: FRED_API_KEY
```

The `stock-platform-secrets` Secret object must have `FRED_API_KEY` added as a new key. Because this is GitOps (Argo CD), the secret value is managed externally (sealed secret or manual kubectl patch) — only the secretKeyRef reference goes in the committed YAML.

### Anti-Patterns to Avoid

- **Hardcoding FRED API key:** Never put `api_key=` literal in source code. Always `os.environ["FRED_API_KEY"]`.
- **Per-ticker rows in feast_fred_macro:** FRED data is date-keyed only — no `ticker` column. Adding one would create unnecessary fan-out (N tickers × D dates) and misrepresent the data structure.
- **Capping forward-fill:** The decision is `ffill()` with no limit. Do not add `limit=N` to ffill — ICSA/NFCI/CPI are valid until FRED publishes a revision.
- **New K8s CronJob for FRED:** The decision is to extend the existing ingestion CronJob, not create a new one.
- **Adding `feast apply` to the CronJob:** `feast apply` registers metadata. It should be run as a one-time migration step or in the Alembic/setup path, not inside a recurring CronJob.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FRED API auth + series fetch | Custom requests.get() with pagination | `fredapi.Fred.get_series()` | Handles auth header, observation pagination, date filtering, returns pandas Series directly |
| FRED observation date parsing | Manual date parsing | fredapi returns DatetimeIndex automatically | FRED uses string dates in JSON; fredapi parses them |
| Wide DataFrame pivot | Manual dict merging | `pd.DataFrame(frames)` after collecting series dict | fredapi returns Series per call; one-liner pivot |
| Forward-fill on date spine | Custom loop to carry values | `df.reindex(date_spine).ffill()` | pandas built-in; handles all gap types correctly |

**Key insight:** FRED series have irregular observation frequencies (daily/weekly/monthly) and revision dates. fredapi + pandas reindex+ffill is the idiomatic solution — hand-rolling date spine alignment is error-prone.

---

## Common Pitfalls

### Pitfall 1: FRED API Rate Limit (120 requests/minute)
**What goes wrong:** Fetching 14 series in rapid succession can hit the FRED rate limit (HTTP 429), especially if running multiple fetches in parallel or during backfill.
**Why it happens:** FRED limits unauthenticated calls heavily; authenticated (API key) calls are capped at 120/minute.
**How to avoid:** Add `time.sleep(0.5)` between series fetches or use tenacity retry with `wait_exponential`. The project already uses tenacity in `yahoo_finance.py` — apply the same pattern.
**Warning signs:** HTTP 429 responses logged with "Too Many Requests"; fetcher returns empty Series for some series.

### Pitfall 2: fredapi Returns NaN for Future Dates or Pre-History
**What goes wrong:** If `end_date` is beyond the last FRED observation (e.g., today for a monthly series), `get_series()` returns data up to the last known date; reindexing to a later date spine leaves trailing NaN until ffill propagates.
**Why it happens:** FRED only publishes data when observations are released. CPI is released monthly with a ~2-week lag.
**How to avoid:** Always `ffill()` after reindexing. The phase decision mandates this. `dropna(how="all")` should NOT be applied after ffill.
**Warning signs:** `feast_fred_macro` rows near the current date have NaN for CPIAUCSL/PCEPILFE/ICSA/NFCI.

### Pitfall 3: Column Naming Collision with FRED Series IDs
**What goes wrong:** FRED series IDs like `BAMLH0A0HYM2` contain digits; PostgreSQL column names with leading digits need quoting. Lowercasing avoids this.
**Why it happens:** FRED uses all-caps alphanumeric IDs; PostgreSQL is case-insensitive for unquoted names but sensitive for mixed-case quoted names.
**How to avoid:** Always use lowercase for column names: `bamlh0a0hym2`, `t10y2y`, `dcoilwtico`, etc. The Feast `Field(name=...)` and SQL DDL must match exactly.
**Warning signs:** Feast apply errors about field name mismatch; PostgreSQL INSERT errors about unknown column names.

### Pitfall 4: Feast FeatureView With Empty Entities List
**What goes wrong:** Feast's `get_historical_features()` join behavior changes when `entities=[]`. The join falls back to timestamp-only matching (no ticker key).
**Why it happens:** `yfinance_macro_fv` already uses `entities=[ticker]` in the existing code (see `feature_repo.py` line 151) even though the data is date-keyed. This means `yfinance_macro_fv` matches on both ticker and timestamp — every row in the entity DataFrame gets the macro value for that date regardless of ticker.
**How to avoid:** Use `entities=[ticker]` in `fred_macro_fv` for consistency with `yfinance_macro_fv`, even though `feast_fred_macro` has no ticker column. The Feast `PostgreSQLSource` query can broadcast the date-keyed value to all tickers by cross-joining on date — OR by keeping `entities=[ticker]` and querying without a ticker filter (Feast will join on timestamp only when ticker is not present in the source). Investigate the exact Feast behavior for `entities=[ticker]` with a source that has no ticker column before implementing.

**Critical note on entities:** Looking at the existing `yfinance_macro_fv` definition (feature_repo.py lines 151–163), it uses `entities=[ticker]` but the source table `feast_yfinance_macro` DOES have a `ticker` column. The FRED table `feast_fred_macro` does NOT have a ticker column by decision. The planner must decide: either (a) add a dummy `ticker` broadcast column to `feast_fred_macro` at upsert time (one row per ticker per date), or (b) use `entities=[]` in `fred_macro_fv` and accept the entityless join. Option (b) matches the locked decision "date-keyed only."

### Pitfall 5: Missing feast apply After Adding fred_macro_fv
**What goes wrong:** `_TRAINING_FEATURES` includes `fred_macro_fv:*` entries but `feast apply` was not run, so the FeatureView is not registered in the Feast SQL registry.
**Why it happens:** Feast metadata lives in the PostgreSQL registry table — code changes to `feature_repo.py` do not auto-propagate.
**How to avoid:** Include `feast apply` as an explicit step in the implementation plan, run from `ml/feature_store/` with correct env vars. This must happen before any training run that uses `fred_macro_fv`.
**Warning signs:** `FeatureView 'fred_macro_fv' not found in the registry` error during training.

### Pitfall 6: FRED_API_KEY Not in Ingestion Pod Spec
**What goes wrong:** The FRED fetch step runs inside the ingestion CronJob container but `FRED_API_KEY` is not mounted, causing `KeyError: 'FRED_API_KEY'` at runtime.
**Why it happens:** The ingestion CronJob currently reads env vars from `ingestion-config` ConfigMap only (no secret env vars). The training CronJob already reads from `stock-platform-secrets`.
**How to avoid:** Add the `secretKeyRef` env var block to `cronjob-historical.yaml` as well as the training CronJob. Confirm the secret key name matches what was added to `stock-platform-secrets`.
**Warning signs:** Pod logs show `KeyError` or `FRED_API_KEY not set`; ingestion job fails but training job succeeds (or vice versa).

---

## Code Examples

Verified patterns from the existing codebase:

### fetch_fred_macro() — modeled on _fetch_yfinance_macro_wide()

```python
# Source: data_loader.py _fetch_yfinance_macro_wide() as template
import os
from fredapi import Fred
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

_FRED_SERIES: list[str] = [
    "DGS2", "DGS10", "T10Y2Y", "T10Y3M",
    "BAMLH0A0HYM2", "DBAA", "T10YIE",
    "DCOILWTICO", "DTWEXBGS", "DEXJPUS",
    "ICSA", "NFCI", "CPIAUCSL", "PCEPILFE",
]

def fetch_fred_macro(start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch 14 FRED macro series; return wide daily DataFrame with ffill.

    Returns:
        DataFrame with DatetimeIndex (daily), columns: dgs2, dgs10, t10y2y, ...
    """
    fred = Fred(api_key=os.environ["FRED_API_KEY"])
    frames: dict[str, pd.Series] = {}
    for series_id in _FRED_SERIES:
        s = fred.get_series(
            series_id,
            observation_start=start_date,
            observation_end=end_date,
        )
        frames[series_id.lower()] = s

    wide = pd.DataFrame(frames)
    date_spine = pd.date_range(start=start_date, end=end_date, freq="D")
    wide = wide.reindex(date_spine).ffill()
    wide.index.name = "date"
    return wide
```

### write_fred_macro_to_db() — modeled on write_yfinance_macro_to_db()

```python
# Source: data_loader.py write_yfinance_macro_to_db() as template
_FRED_COLS = [
    "dgs2", "dgs10", "t10y2y", "t10y3m",
    "bamlh0a0hym2", "dbaa", "t10yie",
    "dcoilwtico", "dtwexbgs", "dexjpus",
    "icsa", "nfci", "cpiaucsl", "pcepilfe",
]

_UPSERT_FRED_SQL = """
    INSERT INTO feast_fred_macro
        (timestamp, {cols})
    VALUES (%s, {placeholders})
    ON CONFLICT (timestamp) DO UPDATE SET
        {updates},
        created_at = NOW();
""".format(
    cols=", ".join(_FRED_COLS),
    placeholders=", ".join(["%s"] * len(_FRED_COLS)),
    updates=", ".join(f"{c} = EXCLUDED.{c}" for c in _FRED_COLS),
)
```

### Existing secretKeyRef pattern from cronjob-training.yaml

```yaml
# Source: stock-prediction-platform/k8s/ml/cronjob-training.yaml lines 47-51
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: stock-platform-secrets
      key: DATABASE_URL_WRITER
# Add analogously:
- name: FRED_API_KEY
  valueFrom:
    secretKeyRef:
      name: stock-platform-secrets
      key: FRED_API_KEY
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pandas_datareader FRED backend | fredapi package directly | fredapi v0.5.x | fredapi is the maintained FRED-specific client; pandas_datareader FRED reader is still functional but less idiomatic |
| EAV (entity-attribute-value) feature tables | Wide-format per-group tables | Phase 92 Feast migration | Wide tables are native to Feast's PostgreSQL offline store; no pivoting at query time |
| Per-ticker rows for macro data | Date-keyed wide table | Phase 93 pattern (now extended) | Macro data is market-wide; broadcasting per ticker wastes storage and complicates joins |

**Deprecated/outdated:**
- `pandas_datareader.data.DataReader('DGS10', 'fred', ...)`: still works but fredapi is the standard for FRED-specific work; pandas_datareader FRED support is maintenance-only.

---

## Open Questions

1. **Feast entity behavior with entities=[] vs entities=[ticker] when source has no ticker column**
   - What we know: `yfinance_macro_fv` uses `entities=[ticker]` and `feast_yfinance_macro` has a ticker column. The locked decision says `fred_macro_fv` is "date-keyed only" with no ticker column.
   - What's unclear: Feast 0.61.0 behavior when `entities=[]` on a FeatureView — does `get_historical_features()` perform a correct timestamp-only join when the entity_df has a ticker column but the FeatureView does not?
   - Recommendation: The planner should test with a minimal fixture. The safe fallback is to include a broadcast ticker column in `feast_fred_macro` (written for every ticker in the ticker list at upsert time), identical to how `feast_yfinance_macro` works. This avoids any Feast entity-join edge case at the cost of row duplication.

2. **Whether ingestion CronJob runs the FRED fetch or only the training CronJob needs it**
   - What we know: CONTEXT.md says "Add FRED fetch to existing ingestion CronJob". The ingestion CronJob triggers `app.jobs.trigger_historical` which calls the API service. The training CronJob runs the ML pipeline.
   - What's unclear: Does the FRED fetch belong in the API ingestion service (`yahoo_finance.py` neighbor) or only in the ML pipeline (`data_loader.py`)?
   - Recommendation: The FRED fetch should live in both layers — the ingestion CronJob collects and stores data into `feast_fred_macro` (like the yfinance path), and the training CronJob reads from Feast. This matches the Phase 93 yfinance architecture.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (configured in `ml/tests/pytest.ini`) |
| Config file | `stock-prediction-platform/ml/tests/pytest.ini` |
| Quick run command | `cd stock-prediction-platform && python -m pytest ml/tests/test_data_loader.py -x -q` |
| Full suite command | `cd stock-prediction-platform && python -m pytest ml/tests/ -q` |

### Phase Requirements → Test Map

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| `fetch_fred_macro()` returns wide DataFrame with 14 columns | unit | `pytest ml/tests/test_data_loader.py::TestFetchFredMacro -x` | Wave 0 |
| `fetch_fred_macro()` forward-fills gaps for weekly/monthly series | unit | `pytest ml/tests/test_data_loader.py::TestFetchFredMacro::test_ffill -x` | Wave 0 |
| `create_fred_macro_table()` is idempotent | unit | `pytest ml/tests/test_data_loader.py::TestCreateFredMacroTable -x` | Wave 0 |
| `write_fred_macro_to_db()` upserts correct rows | unit | `pytest ml/tests/test_data_loader.py::TestWriteFredMacroToDB -x` | Wave 0 |
| `_TRAINING_FEATURES` contains all 14 fred_macro_fv entries | unit | `pytest ml/tests/test_feast_store.py::TestTrainingFeatures -x` | Wave 0 |
| `fred_macro_fv` registered in feature_repo | unit (import check) | `pytest ml/tests/test_feature_repo.py -x` | Wave 0 |
| FRED_API_KEY missing raises clear error | unit | `pytest ml/tests/test_data_loader.py::TestFetchFredMacroMissingKey -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform && python -m pytest ml/tests/test_data_loader.py -x -q`
- **Per wave merge:** `cd stock-prediction-platform && python -m pytest ml/tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `ml/tests/test_data_loader.py` — needs `TestFetchFredMacro`, `TestCreateFredMacroTable`, `TestWriteFredMacroToDB` test classes (mock fredapi.Fred and psycopg2.connect)
- [ ] `ml/tests/test_feast_store.py` — needs assertion that `fred_macro_fv:*` entries are in `_TRAINING_FEATURES`
- [ ] `ml/tests/test_feature_repo.py` — new file; import-level check that `fred_macro_fv` and `fred_macro_source` are defined

---

## Sources

### Primary (HIGH confidence)
- Existing codebase `feature_repo.py` — direct template for `fred_macro_fv` and `fred_macro_source`
- Existing codebase `data_loader.py` — direct template for `fetch_fred_macro()`, `create_fred_macro_table()`, `write_fred_macro_to_db()`
- Existing codebase `feast_store.py` — direct template for `_TRAINING_FEATURES` extension
- Existing codebase `cronjob-training.yaml` lines 47–51 — direct template for `secretKeyRef` pattern
- `pip index versions fredapi` — confirmed v0.5.2 is current PyPI latest

### Secondary (MEDIUM confidence)
- fredapi GitHub README (https://github.com/mortada/fredapi) — `Fred.get_series(series_id, observation_start, observation_end)` API confirmed; returns pandas.Series with DatetimeIndex
- FRED API docs (https://fred.stlouisfed.org/docs/api/fred/) — 14 series IDs confirmed as valid FRED series identifiers; rate limit 120 requests/minute for API key holders

### Tertiary (LOW confidence)
- Feast 0.61.0 behavior with `entities=[]` on a FeatureView in `get_historical_features()` — not directly verified against Feast source; based on understanding of Feast join mechanics. Requires testing in Wave 0 or a spike task.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — fredapi v0.5.2 confirmed from PyPI; all other dependencies already pinned in requirements.txt
- Architecture: HIGH — entire pattern is a copy-adapt of the Phase 93 yfinance implementation which is already working in the codebase
- Pitfalls: HIGH for FRED rate limits and column naming (general API knowledge); MEDIUM for Feast entities=[] edge case (needs verification)

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (fredapi is stable; Feast 0.61.0 pinned; FRED API is stable)
