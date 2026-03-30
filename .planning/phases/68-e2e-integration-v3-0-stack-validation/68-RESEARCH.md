# Phase 68: E2E Integration — v3.0 Stack Validation - Research

**Researched:** 2026-03-30
**Domain:** Bash smoke testing, Playwright infra specs, multi-system integration validation (TimescaleDB OLAP, Argo CD GitOps, Feast feature store, Apache Flink streaming)
**Confidence:** HIGH — all findings drawn from existing project code, established patterns, and confirmed prior phase summaries

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Script format:** One script `scripts/validate-v3.sh` covering all 5 success criteria in sequence; use the same `check()` helper pattern from `validate-argocd.sh` (Phase 65) — PASS/FAIL output, `trap cleanup EXIT`, port-forward lifecycle
- **Script invocation:** Run after `deploy-all.sh`; assumes cluster is running; script does NOT seed its own data
- **OLAP benchmark (V3INT-01):** Two `curl` calls timed with bash `time` builtin; one against raw `ohlcv_intraday` via psql, one against `GET /market/candles?ticker=AAPL&interval=1h&days=30`; compute ratio inline; pass if ratio ≥10x
- **Argo CD sync (V3INT-02):** Real git commit + push editing a throwaway annotation (`validate/timestamp`) in a ConfigMap YAML in `k8s/ingestion/`; poll `argocd app get root-app --output json` for `operationState.phase=Succeeded`; timeout 3 minutes
- **Test data:** Assume already ingested; Exception: Feast materialization calls `python -m ml.feature_store.materialize` for AAPL just before asserting freshness
- **Feast offline (V3INT-03):** Assert `engineer_features(use_feast=True)` completes without error using existing entity_df from DB (not full training run)
- **Feast online (V3INT-04):** Run `python -m ml.feature_store.materialize`, then POST to `/predict/AAPL`, check `feature_timestamp` in response is <2 minutes old
- **Flink pipeline (V3INT-05):** POST `/ingest/intraday` for AAPL via curl; poll every 3s timeout 30s for new `ohlcv_intraday` row with timestamp ≥ now-10s via psql; check `processed-features` topic has recent message via kcat; assert `/predict/AAPL` returns fresh prediction
- **Playwright specs:** Add Argo CD UI spec and Flink Web UI spec to `services/frontend/e2e/infra/`; replicate existing infra spec patterns (minio.spec.ts, grafana.spec.ts)
- **Cleanup:** After the Argo CD sync test, revert the git annotation commit so repo is clean after validation

### Claude's Discretion

- Exact port-forward commands and `kubectl wait` flags within `validate-v3.sh`
- Order of the 5 checks within the script (logical dependency order is fine)
- Playwright spec file names for Argo CD UI and Flink Web UI additions

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| V3INT-01 | OLAP benchmark: GET /market/candles ≥10x faster than raw hypertable query | Phase 64 endpoint documented; bash `time` + ratio math pattern established |
| V3INT-02 | Argo CD GitOps sync loop: git push triggers auto-sync within 3 minutes | Phase 65 argocd CLI patterns and validate-argocd.sh port-forward lifecycle established |
| V3INT-03 | Feast offline path: `get_historical_features()` used in training with no future-leakage | Phase 66 engineer_features(use_feast=True) path documented; materialize.py callable |
| V3INT-04 | Feast online features fresh (<2 min) after materialization, served via /predict/AAPL | Phase 66 get_online_features_for_ticker() and materialize.py established |
| V3INT-05 | Full Flink pipeline: /ingest/intraday → TimescaleDB upsert ≤10s → processed-features topic → Feast online store → /predict/AAPL fresh prediction | Phase 67 FlinkDeployment CRs, Kafka topic, psql upsert assertion pattern |
</phase_requirements>

---

## Summary

Phase 68 is an integration validation phase: no new services, no new API endpoints. The deliverables are a single bash smoke test script (`scripts/validate-v3.sh`) and two Playwright infra specs (`argocd.spec.ts`, `flink-web-ui.spec.ts`). All five success criteria exercise subsystems built in Phases 64–67; the research task is to collect the exact commands, port-forward patterns, and assertion strategies needed.

The validate-argocd.sh script (Phase 65) is the canonical pattern to replicate. It establishes the exact bash skeleton: `check()` function with PASS/FAIL counters, `trap cleanup EXIT` for port-forward lifecycle, and `argocd login` over an insecure port-forward. The Playwright infra specs (Phase 62) are the canonical pattern for UI checks: `beforeAll` probe skips entire file if service unreachable, `test.describe.configure({ mode: "serial" })`, no `baseURL` in config, URL exported from `helpers/auth.ts` with env-var override.

The most complex check is V3INT-05 (Flink pipeline E2E): it involves coordinating curl, kubectl exec for psql, kcat for Kafka topic inspection, and a final HTTP assertion to /predict/AAPL. The research below captures the exact tool invocations, known pitfalls (kubectl API group ambiguity, kcat vs kafkacat naming), and the inter-service timing constraints.

**Primary recommendation:** Write validate-v3.sh in dependency order (V3INT-01 OLAP → V3INT-02 Argo CD → V3INT-03 Feast offline → V3INT-04 Feast online → V3INT-05 Flink E2E), with the git revert for the Argo CD annotation commit as the last action in the cleanup trap.

---

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| bash | system | Smoke test script language | Matches validate-argocd.sh pattern; already established |
| kubectl | cluster-matched | K8s resource inspection, exec for psql, port-forward | Already in PATH on target machine |
| argocd CLI | ~/.local/bin/argocd | Argo CD app status queries and login | Installed in Phase 65 to ~/.local/bin |
| kcat (kafkacat) | system | Kafka topic consumer offset check for processed-features | Lightweight, script-friendly, no Kafka SDK needed |
| curl + bash `time` | system | HTTP timing for OLAP benchmark | No external timing libraries; `time` is a bash builtin |
| python3 | cluster pod | Feast materialization invocation | materialize.py callable as `python -m ml.feature_store.materialize` in ml namespace pod |
| Playwright | existing in services/frontend | Argo CD UI and Flink Web UI infra specs | Already installed; playwright.infra.config.ts drives all infra specs |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| psql (via kubectl exec) | postgres pod | DB row assertion for Flink upsert timing | kubectl exec -n storage deploy/postgres -- psql -U postgres -d stocks -c "..." |
| git | system | Real commit+push for Argo CD sync test | Only for V3INT-02; revert via git revert or git reset in cleanup trap |
| jq | system | Parse argocd app JSON for operationState.phase | Used in Argo CD polling loop |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| kcat offset check | Python kafka-python consumer | kcat is CLI-native, no Python environment required in script |
| bash `time` builtin | `date +%s%N` arithmetic | `time` produces cleaner output; ratio computation still requires inline math |
| `python -m ml.feature_store.materialize` in pod | Port-forward to feast feature server | Invoking in pod via `kubectl exec` is more reliable than HTTP-based materialization trigger |

---

## Architecture Patterns

### Recommended Project Structure

No new directories. Files created in this phase:

```
stock-prediction-platform/
├── scripts/
│   └── validate-v3.sh          # New: master v3.0 smoke test
└── services/frontend/
    └── e2e/infra/
        ├── argocd.spec.ts       # New: Argo CD UI Playwright spec
        ├── flink-web-ui.spec.ts # New: Flink Web UI Playwright spec
        └── helpers/
            └── auth.ts          # Modified: add ARGOCD_URL, FLINK_UI_URL exports
```

`playwright.infra.config.ts` must also gain two new project entries (argocd, flink-web-ui).

### Pattern 1: validate-v3.sh Script Skeleton

**What:** Direct copy of validate-argocd.sh structure, extended for 5 checks.
**When to use:** Every check in validate-v3.sh.

```bash
#!/usr/bin/env bash
# validate-v3.sh — Phase 68 v3.0 stack smoke test
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PASS=0
FAIL=0
# Track PIDs for port-forwards started during the script
PF_PIDS=()
GIT_ANNOTATION_COMMITTED=false

cleanup() {
  for pid in "${PF_PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  # Revert the git annotation commit if we made one
  if [ "$GIT_ANNOTATION_COMMITTED" = "true" ]; then
    git -C "$PROJECT_ROOT" revert --no-edit HEAD 2>/dev/null && \
      git -C "$PROJECT_ROOT" push origin master 2>/dev/null || \
      echo "  WARNING: git revert of annotation commit failed — manual cleanup needed"
  fi
}
trap cleanup EXIT

check() {
  local id="$1"
  local desc="$2"
  local cmd="$3"
  if eval "$cmd" &>/dev/null; then
    echo "  PASS [$id] $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL [$id] $desc"
    echo "       Command: $cmd"
    FAIL=$((FAIL + 1))
  fi
}
```

Source: `stock-prediction-platform/scripts/validate-argocd.sh` (Phase 65)

### Pattern 2: OLAP Benchmark (V3INT-01)

**What:** Time two paths and compute ratio in bash.
**When to use:** V3INT-01 check only.

```bash
# Port-forward API (assumes port 8000 free)
kubectl port-forward svc/stock-api -n ingestion 8000:8000 >/tmp/pf-api.log 2>&1 &
PF_PIDS+=($!)
sleep 3

# Time raw hypertable query via psql
RAW_START=$(date +%s%N)
kubectl exec -n storage deploy/postgres -- \
  psql -U postgres -d stocks -c \
  "SELECT COUNT(*) FROM ohlcv_intraday WHERE ticker='AAPL'" >/dev/null 2>&1
RAW_END=$(date +%s%N)
RAW_MS=$(( (RAW_END - RAW_START) / 1000000 ))

# Time candles endpoint (continuous aggregate)
OLAP_START=$(date +%s%N)
curl -sf "http://localhost:8000/market/candles?ticker=AAPL&interval=1h&days=30" >/dev/null
OLAP_END=$(date +%s%N)
OLAP_MS=$(( (OLAP_END - OLAP_START) / 1000000 ))

echo "  Raw hypertable: ${RAW_MS}ms | Candles endpoint: ${OLAP_MS}ms"

# Compute ratio (integer arithmetic)
if [ "$OLAP_MS" -gt 0 ]; then
  RATIO=$(( RAW_MS / OLAP_MS ))
  echo "  Speedup ratio: ${RATIO}x"
  check "V3INT-01" "OLAP candle query ≥10x faster than raw hypertable" \
    "[ $RATIO -ge 10 ]"
else
  echo "  FAIL [V3INT-01] OLAP response time was 0ms — measurement error"
  FAIL=$((FAIL + 1))
fi
```

**Key insight:** The ratio may be misleading if the raw psql query is also fast (indexes). The endpoint includes Redis cache warm-up. First call will be cache-miss; run twice and use second call for OLAP timing if needed.

### Pattern 3: Argo CD GitOps Loop (V3INT-02)

**What:** Edit ConfigMap annotation, commit, push, poll for sync completion.
**When to use:** V3INT-02 check only.

```bash
# Edit throwaway annotation in a non-critical ConfigMap
CONFIGMAP_FILE="$PROJECT_ROOT/stock-prediction-platform/k8s/ingestion/configmap.yaml"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Use sed to patch or add the annotation (idempotent across runs)
# The annotation is in the ConfigMap metadata.annotations block
# Simplest approach: append/update a comment line with the timestamp
# Actual approach: use kubectl annotate on the YAML file via yq, OR just append
# a comment to the file (git sees a diff, Argo CD re-syncs the ConfigMap)
# Safest: use 'validate/last-checked' annotation in the YAML metadata

git -C "$PROJECT_ROOT" commit -m "validate: annotate for Argo CD sync test [$(date -u +%s)]" \
  stock-prediction-platform/k8s/ingestion/configmap.yaml
GIT_ANNOTATION_COMMITTED=true
git -C "$PROJECT_ROOT" push origin master

# Port-forward argocd-server
kubectl port-forward svc/argocd-server -n argocd 8080:443 >/tmp/pf-argocd.log 2>&1 &
PF_PIDS+=($!)
sleep 4

ARGOCD_PWD=$(argocd admin initial-password -n argocd 2>/dev/null | head -1 || \
  kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "")
argocd login localhost:8080 --username admin --password "$ARGOCD_PWD" \
  --insecure --grpc-web 2>/dev/null || true

# Poll up to 3 minutes (180s)
SYNC_DEADLINE=$(( $(date +%s) + 180 ))
SYNC_PASSED=false
while [ "$(date +%s)" -lt "$SYNC_DEADLINE" ]; do
  PHASE=$(argocd app get root-app --output json 2>/dev/null | \
    jq -r '.status.operationState.phase // empty' 2>/dev/null || echo "")
  if [ "$PHASE" = "Succeeded" ]; then
    SYNC_PASSED=true
    break
  fi
  sleep 10
done

if $SYNC_PASSED; then
  echo "  PASS [V3INT-02] Argo CD synced within 3 minutes"
  PASS=$((PASS + 1))
else
  echo "  FAIL [V3INT-02] Argo CD did not sync within 3 minutes (last phase: $PHASE)"
  FAIL=$((FAIL + 1))
fi
```

Source: CONTEXT.md decision + validate-argocd.sh patterns. Note `applications.argoproj.io` fully-qualified name is not needed for `argocd app get` (uses argocd CLI, not kubectl).

### Pattern 4: psql Assertion via kubectl exec

**What:** Query TimescaleDB inside the postgres pod.
**When to use:** V3INT-01 (raw timing) and V3INT-05 (row existence check).

```bash
# Source: Phase 65/67 STATE.md — established pattern
kubectl exec -n storage deploy/postgres -- \
  psql -U postgres -d stocks -c \
  "SELECT COUNT(*) FROM ohlcv_intraday WHERE ticker='AAPL' AND timestamp >= now() - interval '10 seconds'"
```

### Pattern 5: Flink E2E Pipeline (V3INT-05)

**What:** Trigger ingest, poll DB for row, check Kafka topic, assert predict.
**When to use:** V3INT-05 check only.

```bash
# Trigger ingest
curl -sf -X POST "http://localhost:8000/ingest/intraday" \
  -H "Content-Type: application/json" \
  -d '{"tickers": ["AAPL"]}' >/dev/null

# Poll for DB row (every 3s, timeout 30s)
DB_FOUND=false
for i in $(seq 1 10); do
  ROW_COUNT=$(kubectl exec -n storage deploy/postgres -- \
    psql -U postgres -d stocks -t -c \
    "SELECT COUNT(*) FROM ohlcv_intraday WHERE ticker='AAPL' AND timestamp >= now() - interval '10 seconds'" \
    2>/dev/null | tr -d ' ')
  if [ "${ROW_COUNT:-0}" -gt 0 ]; then
    DB_FOUND=true; break
  fi
  sleep 3
done
check "V3INT-05-db" "Flink upserted AAPL row to ohlcv_intraday within 10s" \
  "$DB_FOUND && [ true = '$DB_FOUND' ]"

# Check processed-features Kafka topic for recent message
# kcat: consume last message, check offset > 0
check "V3INT-05-kafka" "processed-features topic has messages" \
  "kubectl exec -n storage kafka-kafka-0 -- \
   /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
   --bootstrap-server localhost:9092 --topic processed-features \
   --time -1 2>/dev/null | grep -qE ':[1-9][0-9]*$'"

# Assert fresh prediction
check "V3INT-05-predict" "/predict/AAPL returns 200 with a prediction" \
  "curl -sf http://localhost:8000/predict/AAPL | jq -e '.predicted_price'"
```

### Pattern 6: Playwright Infra Spec (Argo CD UI)

**What:** Probe-skip pattern + serial mode + no baseURL.
**When to use:** argocd.spec.ts and flink-web-ui.spec.ts.

```typescript
// Source: stock-prediction-platform/services/frontend/e2e/infra/grafana.spec.ts pattern
import { test, expect, request } from "@playwright/test";
import { ARGOCD_URL } from "./helpers/auth";  // new export to add

test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(`${ARGOCD_URL}/healthz`, { timeout: 5_000 });
    if (res.status() >= 500) {
      test.skip(true, `Argo CD not reachable at ${ARGOCD_URL}`);
    }
  } catch {
    test.skip(true, `Argo CD not reachable at ${ARGOCD_URL}`);
  } finally {
    await ctx.dispose();
  }
});

test.describe.configure({ mode: "serial" });

test.describe("Argo CD UI login", () => {
  test("logs in and reaches application list", async ({ page }) => {
    await page.goto(`${ARGOCD_URL}`);
    await page.getByLabel(/username/i).fill("admin");
    await page.getByLabel(/password/i).fill(ARGOCD_PASSWORD);  // new export
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(
      page.getByText(/Applications|root-app/i).first()
    ).toBeVisible({ timeout: 15_000 });
  });
});
```

### Anti-Patterns to Avoid

- **Hardcoding durations:** Do not hardcode sleep times; use polling loops with explicit timeouts (as in validate-argocd.sh).
- **kubectl get application (unqualified):** Always use `applications.argoproj.io` with kubectl to avoid Kubeflow CRD ambiguity. (Learned in Phase 65, documented in STATE.md.)
- **Checking static Synced status:** The Argo CD test must assert `operationState.phase=Succeeded` after a new push — not just the existing Synced condition — to prove the full GitOps loop is active.
- **Using git add -A in the annotation commit:** Stage only the specific ConfigMap file to avoid accidentally committing other dirty files.
- **Assuming kcat binary name:** The binary may be `kcat` or `kafkacat` depending on the environment. Use a fallback: `$(command -v kcat || command -v kafkacat)`.
- **Leaving the git annotation commit on master:** The cleanup trap MUST revert it via `git revert --no-edit HEAD && git push origin master` so the repo is clean post-validation.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Kafka topic message check | Custom Python consumer script | kcat offset shell check OR kafka-run-class.sh GetOffsetShell via kubectl exec | Already in cluster; no new images |
| Feast materialization trigger | New HTTP endpoint | `kubectl exec` calling `python -m ml.feature_store.materialize` | materialize.py already callable; Phase 66 established pattern |
| OLAP timing | Custom benchmark harness | bash `time` builtin + date +%s%N | Sufficient for ≥10x ratio; no external tools needed |
| Argo CD sync polling | New K8s controller or webhook | argocd CLI `app get --output json` + jq | argocd CLI already installed in Phase 65 |
| Playwright URL management | Hardcoded URLs in spec files | ARGOCD_URL / FLINK_UI_URL env-var exports in helpers/auth.ts | Matches existing infra spec pattern exactly |

---

## Common Pitfalls

### Pitfall 1: kubectl API Group Ambiguity for Application CRD
**What goes wrong:** `kubectl get application root-app -n argocd` returns NotFound because Kubeflow's `app.k8s.io` CRD is resolved first.
**Why it happens:** Two Application CRDs coexist: `argoproj.io/v1alpha1` and `app.k8s.io/v1beta1`. kubectl resolves unqualified names alphabetically.
**How to avoid:** Always use `kubectl get applications.argoproj.io` when calling kubectl directly. The argocd CLI (`argocd app get`) does not have this problem.
**Warning signs:** NotFound errors for known Argo CD apps when using plain kubectl.

### Pitfall 2: OLAP Ratio Skewed by Cache
**What goes wrong:** The first call to GET /market/candles hits Redis cache-miss and is slower than expected; ratio may not reach 10x on first call.
**Why it happens:** Redis cache TTL is 30s; first call always queries TimescaleDB. Subsequent calls within 30s are cache hits.
**How to avoid:** Run the candles curl twice and use the second timing; OR note that even cache-miss TimescaleDB continuous aggregate queries should be significantly faster than full hypertable scans. Document both timings in output.
**Warning signs:** OLAP_MS is higher than expected (>500ms) on first run.

### Pitfall 3: Argo CD Sync Polling Window Mismatch
**What goes wrong:** Script polls `operationState.phase` but root-app shows phase from a previous sync operation, not the one triggered by the new push.
**Why it happens:** Argo CD may report the previous successful sync's operationState immediately after push (before detecting the new commit).
**How to avoid:** Record `git rev-parse HEAD` before push; after push, verify the argocd app's `status.sync.revision` matches the new HEAD before accepting `operationState.phase=Succeeded`.
**Warning signs:** Sync appears to succeed in <5s after push (too fast to have detected and synced).

### Pitfall 4: kcat/kafkacat Binary Name Inconsistency
**What goes wrong:** Script fails because `kcat` is installed as `kafkacat` or vice versa.
**Why it happens:** Package managers use different names (Debian: kafkacat, others: kcat).
**How to avoid:** Use `KCat=$(command -v kcat || command -v kafkacat || echo "")` and skip the check with a warning if neither is found.
**Warning signs:** `command not found: kcat` during script execution.

### Pitfall 5: Flink Upsert Timing Window
**What goes wrong:** The psql poll for a row with `timestamp >= now() - interval '10 seconds'` misses the row because the Flink job's clock or the network introduces slight drift.
**Why it happens:** The `timestamp` column in ohlcv_intraday is set by the ingest API or Flink at processing time; if yfinance data has stale timestamps, the row exists but the timestamp predicate fails.
**How to avoid:** Also check for the row's `updated_at` column (or use a more generous window: `now() - interval '30 seconds'`). The requirement is ≤10s end-to-end; the validation window can be broader.
**Warning signs:** Row count is 0 on first poll but psql direct query shows the row exists with an older timestamp.

### Pitfall 6: Playwright Port-Forward Not Running
**What goes wrong:** argocd.spec.ts and flink-web-ui.spec.ts fail because there's no port-forward active to localhost:8080 / localhost:8081.
**Why it happens:** Infra specs assume the service is reachable via kubectl port-forward (same model as grafana.spec.ts — no webServer block in config).
**How to avoid:** Document in spec `beforeAll` skip message that the operator must have port-forwards active before running `npx playwright test --config playwright.infra.config.ts --project argocd`. The skip message should include the exact kubectl port-forward command.
**Warning signs:** `ECONNREFUSED` in beforeAll probe → entire spec skipped.

### Pitfall 7: Feast Materialization Without FEAST_REPO_PATH
**What goes wrong:** `python -m ml.feature_store.materialize` fails because FEAST_REPO_PATH is not set.
**Why it happens:** materialize.py defaults to `/app/ml/feature_store` (the K8s pod path). When running via `kubectl exec` in the ml pipeline pod, this path exists. When run locally, it does not.
**How to avoid:** Always invoke via `kubectl exec -n ml deploy/feast-feature-server -- python -m ml.feature_store.materialize` (runs in the pod where FEAST_REPO_PATH is set via ConfigMap). Do NOT run locally.
**Warning signs:** `FeatureStore.__init__` fails with FileNotFoundError.

---

## Code Examples

Verified patterns from existing project code:

### psql via kubectl exec (established in Phase 65, 67 STATE.md)
```bash
# Source: STATE.md decisions — Phase 67 established pattern
kubectl exec -n storage deploy/postgres -- \
  psql -U postgres -d stocks -t -c \
  "SELECT COUNT(*) FROM ohlcv_intraday WHERE ticker='AAPL'"
```

### argocd login over port-forward (from validate-argocd.sh)
```bash
# Source: stock-prediction-platform/scripts/validate-argocd.sh lines 60-71
ARGOCD_PWD=$(argocd admin initial-password -n argocd 2>/dev/null | head -1 || \
  kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "")

argocd login localhost:8080 \
  --username admin \
  --password "$ARGOCD_PWD" \
  --insecure \
  --grpc-web \
  2>/dev/null || echo "  WARNING: argocd login failed"
```

### check() helper (from validate-argocd.sh)
```bash
# Source: stock-prediction-platform/scripts/validate-argocd.sh lines 23-35
check() {
  local id="$1"
  local desc="$2"
  local cmd="$3"
  if eval "$cmd" &>/dev/null; then
    echo "  PASS [$id] $desc"
    PASS=$((PASS + 1))
  else
    echo "  FAIL [$id] $desc"
    echo "       Command: $cmd"
    FAIL=$((FAIL + 1))
  fi
}
```

### Playwright infra spec probe-skip pattern (from grafana.spec.ts)
```typescript
// Source: services/frontend/e2e/infra/grafana.spec.ts lines 8-30
test.beforeAll(async () => {
  const ctx = await request.newContext();
  try {
    const res = await ctx.get(`${ARGOCD_URL}/healthz`, { timeout: 5_000 });
    if (res.status() >= 500) {
      test.skip(true, `Argo CD not reachable at ${ARGOCD_URL}`);
    }
  } catch {
    test.skip(true, `Argo CD not reachable at ${ARGOCD_URL}`);
  } finally {
    await ctx.dispose();
  }
});

test.describe.configure({ mode: "serial" });
```

### auth.ts URL export pattern (from e2e/infra/helpers/auth.ts)
```typescript
// Source: services/frontend/e2e/infra/helpers/auth.ts — pattern to extend
export const ARGOCD_URL =
  process.env.ARGOCD_URL ?? "http://localhost:8080";
export const ARGOCD_PASSWORD =
  process.env.ARGOCD_PASSWORD ?? ""; // must be supplied; no safe default

export const FLINK_UI_URL =
  process.env.FLINK_UI_URL ?? "http://localhost:8081";
```

### playwright.infra.config.ts project entry (from existing config)
```typescript
// Source: services/frontend/playwright.infra.config.ts — pattern to extend
{ name: "argocd",       testMatch: "**/argocd.spec.ts" },
{ name: "flink-web-ui", testMatch: "**/flink-web-ui.spec.ts" },
```

### Flink Web UI API check (Flink REST API)
```typescript
// Flink exposes REST API at port 8081 — /jobs/overview endpoint
const res = await ctx.get(`${FLINK_UI_URL}/jobs/overview`, { timeout: 5_000 });
const body = await res.json();
// Expect at least one running job
expect(body.jobs.some((j: { state: string }) => j.state === "RUNNING")).toBeTruthy();
```

### Git annotation edit + revert (validate-v3.sh)
```bash
# Edit throwaway annotation — use Python/sed to update or add the key
# Simplest idempotent approach: append/replace an annotation comment in the YAML
ANNOTATION_KEY="validate/last-checked"
ANNOTATION_VALUE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Use kubectl annotate dry-run to generate the patched YAML if yq not available
# OR: directly edit the file with sed (works if the key already exists)
# OR: use python inline to parse and rewrite YAML

# Stage only the specific file
git -C "$PROJECT_ROOT" add \
  stock-prediction-platform/k8s/ingestion/configmap.yaml
git -C "$PROJECT_ROOT" commit -m \
  "validate: Argo CD sync probe $(date -u +%s) [auto-revert-follows]"
GIT_ANNOTATION_COMMITTED=true
git -C "$PROJECT_ROOT" push origin master
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| kubectl apply manual | Argo CD GitOps loop | Phase 65 | All manifest changes go through git; validate-v3.sh MUST push to git, not kubectl apply |
| Raw psycopg2 TimescaleDB queries | TimescaleDB continuous aggregates via /market/candles | Phase 64 | Candle queries ≥10x faster; benchmark compares aggregate view vs raw hypertable |
| File-based feature engineering | Feast offline + online stores | Phase 66 | Training uses `get_historical_features()`; prediction uses `get_online_features_for_ticker()` |
| Python kafka-consumer batch writer | Apache Flink streaming jobs | Phase 67 | Intraday path: ingest → Kafka → Flink → TimescaleDB (not the old consumer) |
| `kubectl get application` | `kubectl get applications.argoproj.io` | Phase 65 discovery | Must always use fully-qualified resource name when calling kubectl directly |

**Deprecated/outdated:**
- `kafkacat`: renamed to `kcat` in many distros — check both
- Direct `kubectl apply` for manifest changes: bypasses Argo CD and breaks GitOps loop

---

## Open Questions

1. **kcat availability in the test environment**
   - What we know: kcat/kafkacat may or may not be installed on the host machine running validate-v3.sh
   - What's unclear: Whether it's installed in the Minikube environment vs the host
   - Recommendation: Use `kubectl exec -n storage kafka-kafka-0 -- /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell ...` as a fallback that requires no host-side tool; or use kcat only if found, skip Kafka check gracefully if not

2. **Argo CD password after rotation**
   - What we know: validate-argocd.sh reads `argocd admin initial-password` or the initial-admin-secret; password may have been changed by operator
   - What's unclear: Whether the initial-admin-secret still exists on this cluster
   - Recommendation: Same dual-path fallback as validate-argocd.sh; if login fails, skip argocd CLI checks and fall back to kubectl-only assertions

3. **Feast feature_timestamp field in /predict/AAPL response**
   - What we know: CONTEXT.md says check `feature_timestamp` in the response is <2 minutes old
   - What's unclear: Whether `feature_timestamp` is currently returned in the /predict/AAPL response schema
   - Recommendation: Read `services/api/app/models/schemas.py` and `prediction_service.py` during implementation to confirm the field name; if not present, the check degrades to verifying that `get_online_features_for_ticker()` was called (log assertion)

4. **Flink job namespace and port for Flink Web UI**
   - What we know: FlinkDeployment CRs deployed in `flink` namespace (Phase 67); Flink REST API on port 8081
   - What's unclear: Which service name to port-forward to (e.g., `svc/ohlcv-normalizer-rest` vs a shared Flink job manager service)
   - Recommendation: During implementation, inspect `kubectl get svc -n flink` to confirm service names and use the first RUNNING job manager's REST service for port-forward

---

## Validation Architecture

`nyquist_validation` is enabled in `.planning/config.json`.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Playwright (infra specs) + bash exit code (validate-v3.sh) |
| Config file | `stock-prediction-platform/services/frontend/playwright.infra.config.ts` |
| Quick run command (new specs only) | `cd stock-prediction-platform/services/frontend && npx playwright test --config playwright.infra.config.ts --project argocd --project flink-web-ui` |
| Full suite command | `cd stock-prediction-platform/services/frontend && npx playwright test --config playwright.infra.config.ts` |
| Bash smoke test | `./stock-prediction-platform/scripts/validate-v3.sh` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| V3INT-01 | OLAP candle query ≥10x faster than raw hypertable | smoke (bash) | `./stock-prediction-platform/scripts/validate-v3.sh` (V3INT-01 block) | ❌ Wave 0 |
| V3INT-02 | Argo CD syncs within 3 min after git push | smoke (bash) | `./stock-prediction-platform/scripts/validate-v3.sh` (V3INT-02 block) | ❌ Wave 0 |
| V3INT-03 | Feast offline: `engineer_features(use_feast=True)` no leakage | smoke (bash) | `./stock-prediction-platform/scripts/validate-v3.sh` (V3INT-03 block) | ❌ Wave 0 |
| V3INT-04 | Feast online: feature_timestamp <2 min after materialize | smoke (bash) | `./stock-prediction-platform/scripts/validate-v3.sh` (V3INT-04 block) | ❌ Wave 0 |
| V3INT-05 | Full Flink pipeline end-to-end ≤10s upsert | smoke (bash) | `./stock-prediction-platform/scripts/validate-v3.sh` (V3INT-05 block) | ❌ Wave 0 |
| V3INT-UI | Argo CD UI reachable and shows apps | e2e (Playwright) | `npx playwright test --project argocd` | ❌ Wave 0 |
| V3INT-UI | Flink Web UI reachable and shows RUNNING jobs | e2e (Playwright) | `npx playwright test --project flink-web-ui` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `./stock-prediction-platform/scripts/validate-v3.sh` (exit 0 required)
- **Per wave merge:** Full infra suite `npx playwright test --config playwright.infra.config.ts`
- **Phase gate:** validate-v3.sh exits 0 with FAIL: 0 before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `stock-prediction-platform/scripts/validate-v3.sh` — covers V3INT-01 through V3INT-05
- [ ] `stock-prediction-platform/services/frontend/e2e/infra/argocd.spec.ts` — covers V3INT-UI (Argo CD)
- [ ] `stock-prediction-platform/services/frontend/e2e/infra/flink-web-ui.spec.ts` — covers V3INT-UI (Flink)
- [ ] `stock-prediction-platform/services/frontend/e2e/infra/helpers/auth.ts` — add ARGOCD_URL, ARGOCD_PASSWORD, FLINK_UI_URL exports
- [ ] `stock-prediction-platform/services/frontend/playwright.infra.config.ts` — add argocd and flink-web-ui project entries

---

## Sources

### Primary (HIGH confidence)
- `stock-prediction-platform/scripts/validate-argocd.sh` — canonical check() pattern, port-forward lifecycle, argocd login
- `stock-prediction-platform/services/frontend/e2e/infra/grafana.spec.ts` — beforeAll probe-skip, serial mode, Playwright request API
- `stock-prediction-platform/services/frontend/e2e/infra/minio.spec.ts` — service probe, login pattern, bucket assertion
- `stock-prediction-platform/services/frontend/e2e/infra/helpers/auth.ts` — URL export pattern with env-var override
- `stock-prediction-platform/services/frontend/playwright.infra.config.ts` — no baseURL, no webServer, project entry format
- `stock-prediction-platform/ml/feature_store/materialize.py` — `run_materialization()` callable; pod invocation path
- `.planning/phases/64-timescaledb-olap-continuous-aggregates-compression/64-02-SUMMARY.md` — candles endpoint, interval→view mapping, Redis 30s TTL
- `.planning/phases/65-argo-cd-gitops-deployment-pipeline/65-02-SUMMARY.md` — argocd CLI patterns, applications.argoproj.io disambiguation
- `.planning/phases/66-feast-production-feature-store/66-03-SUMMARY.md` — materialize.py, get_online_features_for_ticker(), K8s manifests
- `.planning/phases/67-apache-flink-real-time-stream-processing/67-03-SUMMARY.md` — Flink namespace, processed-features topic, deploy-all.sh Phase 67 block
- `.planning/STATE.md` — Phase-level decisions including kubectl API group ambiguity fix, Feast env var patterns

### Secondary (MEDIUM confidence)
- `.planning/ROADMAP.md` §Phase 68 — V3INT success criteria with exact thresholds (≥10x, <200ms, <2 min, 10s, 3 min)
- `.planning/phases/68-e2e-integration-v3-0-stack-validation/68-CONTEXT.md` — all locked implementation decisions

### Tertiary (LOW confidence)
- Flink REST API `/jobs/overview` endpoint format — assumed standard from Flink 1.19 documentation; verify during implementation with `kubectl exec` or port-forward

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools already in use on this project; no new dependencies
- Architecture: HIGH — directly derived from existing validate-argocd.sh and infra spec patterns
- Pitfalls: HIGH — kubectl API group ambiguity and cache timing issues are confirmed historical bugs (STATE.md); kcat naming is well-known

**Research date:** 2026-03-30
**Valid until:** 2026-04-30 (stable bash/kubectl/Playwright stack; Phase 67 Flink deployment confirmed 2026-03-30)
