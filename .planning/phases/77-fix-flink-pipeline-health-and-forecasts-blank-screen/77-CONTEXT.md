# Phase 77: Fix Flink Pipeline Health and Forecasts Blank Screen — Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Two independent bug fixes:
1. **Flink `ohlcv_normalizer` crash-loop** — 1160 restarts, 0 completed checkpoints, 3K+ failed checkpoints. Investigate and fix all likely root causes: MinIO checkpoint storage (secrets not copied to flink namespace), JDBC PostgreSQL sink connectivity, Kafka source connectivity, and deploy-all.sh secret copy step.
2. **Forecasts page blank screen** — `return null` during loading shows nothing. Replace with skeleton loading state + fix silent mock-data fallback on partial query failure.

No new features, no new pages, no data pipeline changes beyond fixing the broken Flink job.

</domain>

<decisions>
## Implementation Decisions

### Forecasts Loading State
- Replace `if (isLoading) return null` with a skeleton loading state
- PageHeader and HorizonToggle bar render immediately (they don't depend on data)
- 10 MUI Skeleton rows fill the table area during loading
- Skeleton rows should match the column count of ForecastTable

### Forecasts Partial Failure Fix
- Remove the `generateMockForecasts()` fallback that silently masks query failures
- **If `bulkQuery` fails alone**: show `ErrorFallback` — forecast data is unavailable, no table render
- **If `marketQuery` fails alone**: render the table with real bulk prediction data; display `—` (em-dash) for missing `company_name` and `sector` columns (consistent with null-display pattern from Phase 75)
- **If both fail**: show `ErrorFallback` (existing behavior, keep)
- Error condition changes from `isError = bulkQuery.isError && marketQuery.isError` to two separate checks

### Flink Root Cause — All Failure Points to Fix
Fix all four candidate failure points:
1. **MinIO checkpoint storage** — Verify `minio-secrets` is copied to the `flink` namespace before FlinkDeployment is applied; verify `model-artifacts` bucket exists and the `flink-checkpoints/ohlcv-normalizer` prefix is reachable
2. **JDBC connector + PostgreSQL** — Verify `stock-platform-secrets` is copied to the `flink` namespace; verify JDBC driver JAR is present in the Flink image
3. **Kafka source connectivity** — Verify `kafka-kafka-bootstrap.storage.svc.cluster.local:9092` is reachable from the flink namespace and the `intraday-data` topic exists
4. **deploy-all.sh secret copy step** — Verify the script copies both `stock-platform-secrets` and `minio-secrets` from `storage` namespace to `flink` namespace before applying FlinkDeployments; add the step if missing

### Checkpoint Strategy
- Keep existing checkpoint config: RocksDB + incremental checkpoints to MinIO (`s3://model-artifacts/flink-checkpoints/ohlcv-normalizer`)
- Fix root cause (secrets, bucket), do NOT simplify or disable checkpointing
- Add bucket/prefix verification to the plan: confirm `model-artifacts` bucket exists and `flink-s3-fs-presto` plugin can authenticate before considering checkpointing fixed

### Claude's Discretion
- Exact MUI Skeleton component props (variant, height, animation)
- Whether to extract the skeleton state into a named component or inline it
- kubectl validation command ordering in the plan

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Forecasts page
- `stock-prediction-platform/services/frontend/src/pages/Forecasts.tsx` — Current page with `return null` loading bug and mock fallback; isLoading/isError logic is at lines 155-163
- `stock-prediction-platform/services/frontend/src/components/forecasts/ForecastTable.tsx` — Column definitions; skeleton rows must match column count
- `stock-prediction-platform/services/frontend/src/api/queries.ts` — `useBulkPredictions()`, `useAvailableHorizons()`, `useMarketOverview()` hooks

### Flink job
- `stock-prediction-platform/k8s/flink/flinkdeployment-ohlcv-normalizer.yaml` — FlinkDeployment; checkpoint config, secret refs, and ENABLE_BUILT_IN_PLUGINS env var
- `stock-prediction-platform/k8s/flink/flink-config-configmap.yaml` — ConfigMap with Kafka/Postgres addresses
- `stock-prediction-platform/services/flink-jobs/ohlcv_normalizer/ohlcv_normalizer.py` — Job entrypoint; reads KAFKA_BOOTSTRAP_SERVERS, POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

### Deploy script (secret copy step)
- Find deploy-all.sh or equivalent in `stock-prediction-platform/` root or `scripts/` — verify it copies `stock-platform-secrets` and `minio-secrets` from `storage` namespace to `flink` namespace before applying FlinkDeployments

No external ADRs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MUI Skeleton` — already used in other components in the codebase; use same import pattern
- `ErrorFallback` component — already imported in Forecasts.tsx; use for both bulk-fail and both-fail cases
- `generateMockForecasts()` — currently in `src/utils/mockForecastData.ts`; will be REMOVED from production code path (keep file, remove the call in Forecasts.tsx)

### Established Patterns
- Null/missing value display: `—` (em-dash) — established in Phase 75 for null numeric values; apply to missing company_name/sector when marketQuery fails
- Error state: `ErrorFallback` with `message` + `onRetry` props — already in Forecasts.tsx
- Skeleton loading: check Dashboard.tsx or other pages for existing skeleton patterns to reuse

### Integration Points
- Forecasts.tsx loading gate: replace `if (isLoading) return null` (line 162) with skeleton JSX; keep PageHeader + HorizonToggle rendering outside the loading gate
- Forecasts.tsx error logic: replace single combined `isError` check with two separate checks — `bulkQuery.isError` alone → `ErrorFallback`; `marketQuery.isError` alone → continue render with `—` fallback
- `allRows` useMemo (lines ~120-128): remove `generateMockForecasts(horizon)` branch; when `bulkQuery.isError`, return `[]` or let the earlier `ErrorFallback` short-circuit
- deploy-all.sh: the secret copy comment in `flinkdeployment-ohlcv-normalizer.yaml` references `kubectl get secret ... | sed ... | kubectl apply` — find if this is already scripted

</code_context>

<specifics>
## Specific Ideas

- Skeleton rows: Use `Array.from({ length: 10 }).map((_, i) => <TableRow key={i}>...)` pattern inside ForecastTable or as an inline block in Forecasts.tsx
- The `return null` during loading is the primary blank-screen cause — a one-line change with the skeleton added adjacent to it
- For the Flink fix, the FlinkDeployment YAML already has the correct comment explaining the secret copy requirement — the deploy script gap is the most likely root cause of all 4 failure modes

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 77-fix-flink-pipeline-health-and-forecasts-blank-screen*
*Context gathered: 2026-04-02*
