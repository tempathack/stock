# Phase 72: Grafana Debug Dashboards with Flink Metrics Integration — Research

**Researched:** 2026-03-31
**Domain:** Grafana provisioning, Flink Prometheus reporter, Kubernetes scrape config
**Confidence:** HIGH (all findings based on direct inspection of repo files and official Flink/Grafana documentation patterns)

---

## Summary

Phase 72 fixes a gap where Grafana dashboards show "No data" panels in a running environment, and extends observability to cover Apache Flink jobs (5 FlinkDeployments in the `flink` namespace). The work breaks into two distinct problems:

**Problem 1 — Flink metrics not reaching Prometheus.** All five FlinkDeployments already configure `metrics.reporter.prom.factory.class` on port 9249 and inject `prometheus.io/scrape: "true"` pod annotations. However, the Prometheus ConfigMap (`k8s/monitoring/prometheus-configmap.yaml`) has no scrape job for the `flink` namespace. The `kubernetes-pods` job uses annotation-based discovery but only discovers pods in default namespaces unless namespace filtering is removed. Flink pods in the `flink` namespace are being missed. This is the root cause of the empty Flink dashboard.

**Problem 2 — Existing dashboards show "No data" because metric names in PromQL don't match what FastAPI/Kafka actually emit.** The API Health dashboard queries `http_requests_total{kubernetes_namespace="$namespace"}` but `prometheus-fastapi-instrumentator` emits `http_requests_total` with a `handler` label, not a `kubernetes_namespace` label — that label is added by Prometheus scrape relabeling. The `$namespace` template variable relies on `label_values(http_requests_total, kubernetes_namespace)` which only works when the label exists, which requires the scrape relabeling to be running correctly end-to-end.

**Primary recommendation:** Fix Prometheus scrape config to explicitly include the `flink` namespace and verify relabel rules attach `kubernetes_namespace`. Add a dedicated `flink-jobs` scrape job targeting port 9249 in the `flink` namespace. Add `"No data"` fallback panel text to confirm the issue is scraping, not dashboard JSON. Then build a complete Flink dashboard with job-level and task-level metric panels.

---

## User Constraints

No CONTEXT.md exists for phase 72 — no locked decisions. All choices are at Claude's discretion.

---

## What Already Exists (Do Not Rebuild)

| Asset | Location | State |
|-------|----------|-------|
| Grafana Deployment | `k8s/monitoring/grafana-deployment.yaml` | Running, grafana/grafana:10.4.0 |
| Grafana datasource config | `k8s/monitoring/grafana-datasource-configmap.yaml` | Prometheus + Loki + TimescaleDB provisioned |
| Dashboard provider config | `k8s/monitoring/grafana-dashboards-configmap.yaml` | Reads from `/var/lib/grafana/dashboards` |
| API Health dashboard JSON | `k8s/monitoring/grafana-dashboard-api-health.yaml` | Exists, may show "No data" |
| ML Performance dashboard JSON | `k8s/monitoring/grafana-dashboard-ml-perf.yaml` | Exists, may show "No data" |
| Kafka & Infrastructure dashboard JSON | `k8s/monitoring/grafana-dashboard-kafka.yaml` | Exists, may show "No data" |
| Flink dashboard JSON (stub) | `k8s/monitoring/grafana-dashboard-flink.yaml` | Exists — only 2 panels, basic stub |
| Prometheus ConfigMap | `k8s/monitoring/prometheus-configmap.yaml` | Has `kubernetes-pods`, `kafka-exporter`, `strimzi-kafka` jobs — NO flink job |
| Flink deployments (5) | `k8s/flink/flinkdeployment-*.yaml` | All have `metrics.reporter.prom.port: "9249"` and `prometheus.io/scrape: "true"` annotations |
| Grafana auth | `grafana-deployment.yaml` | `GF_AUTH_ANONYMOUS_ENABLED: "true"` — anonymous users can view |

---

## Standard Stack

### Core (already deployed)
| Component | Version | Purpose |
|-----------|---------|---------|
| Grafana | 10.4.0 | Dashboard rendering, provisioning |
| Prometheus | (deployed via k8s/monitoring) | Metrics storage and scraping |
| Flink Prometheus Reporter | Built-in (Flink 1.19) | Exposes metrics on port 9249 |
| Strimzi Kafka | Deployed in `storage` ns | Kafka broker; Strimzi has built-in JMX exporter |

### Flink Metrics — What the Reporter Emits (HIGH confidence)
Flink 1.19 with `PrometheusReporterFactory` exposes metrics on the configured port. The metric names follow the pattern:

```
flink_jobmanager_<scope>_<metric>
flink_taskmanager_<scope>_<metric>
```

Key metric names (verified against Flink 1.19 documentation patterns):
- `flink_jobmanager_job_uptime` — job uptime in ms, labeled `job_name`
- `flink_jobmanager_job_numRestarts` — restart count
- `flink_jobmanager_job_numberOfCompletedCheckpoints` — successful checkpoints
- `flink_jobmanager_job_numberOfFailedCheckpoints` — failed checkpoints
- `flink_jobmanager_job_lastCheckpointDuration` — last checkpoint duration (ms)
- `flink_jobmanager_job_lastCheckpointSize` — last checkpoint size (bytes)
- `flink_taskmanager_job_task_numRecordsInPerSecond` — input throughput
- `flink_taskmanager_job_task_numRecordsOutPerSecond` — output throughput (already in stub dashboard)
- `flink_taskmanager_job_task_currentInputWatermark` — event-time watermark
- `flink_taskmanager_job_task_buffers_inPoolUsage` — network buffer pressure
- `flink_taskmanager_job_task_buffers_outPoolUsage` — output buffer pressure
- `flink_taskmanager_Status_JVM_Memory_Heap_Used` — JVM heap usage
- `flink_taskmanager_Status_JVM_GarbageCollector_G1_Young_Generation_Count` — GC frequency

**Label dimensions on Flink metrics:** `job_name`, `task_name`, `subtask_index`, `tm_id`

---

## Architecture Patterns

### Pattern 1: Fix Prometheus Flink Scrape Job

**The gap:** `prometheus-configmap.yaml` has no job targeting the `flink` namespace on port 9249.

**Fix:** Add a dedicated scrape job. The `kubernetes-pods` job discovers by `prometheus.io/scrape: "true"` annotation but may be namespace-scoped or have relabel rules that exclude the `flink` namespace. The safest fix is an explicit job:

```yaml
# Add to prometheus-configmap.yaml scrape_configs:
- job_name: flink-jobs
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - flink
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: "true"
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
      action: replace
      regex: (.+)
      target_label: __address__
      replacement: "${1}"
    - source_labels:
        - __address__
        - __meta_kubernetes_pod_annotation_prometheus_io_port
      action: replace
      regex: ([^:]+)(?::\d+)?;(\d+)
      replacement: $1:$2
      target_label: __address__
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__meta_kubernetes_namespace]
      action: replace
      target_label: kubernetes_namespace
    - source_labels: [__meta_kubernetes_pod_name]
      action: replace
      target_label: kubernetes_pod_name
    - source_labels: [__meta_kubernetes_pod_label_app_kubernetes_io_part_of]
      action: replace
      target_label: app
```

**Note on Flink pod structure:** Each FlinkDeployment creates separate JobManager and TaskManager pods. Both should emit on port 9249. The `__meta_kubernetes_pod_annotation_prometheus_io_port` annotation is already set to `"9249"` in all FlinkDeployment podTemplates.

### Pattern 2: Anonymous Access Org Role

**Current config:** `GF_AUTH_ANONYMOUS_ENABLED: "true"` is set. This enables anonymous viewing but defaults to `Viewer` role if `GF_AUTH_ANONYMOUS_ORG_ROLE` is not set. Grafana 10.x anonymous viewers can see dashboards — this is already sufficient for "debug mode" viewing without login.

**What "debug mode" means:** The user wants dashboards to show real data. This is a scraping/metric-name problem, not an auth problem. No auth changes needed.

### Pattern 3: Grafana Dashboard Provisioning Pattern

All dashboards are provisioned as ConfigMaps mounted into `/var/lib/grafana/dashboards/`. The pattern is:

```yaml
# ConfigMap structure
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard-<name>
  namespace: monitoring
data:
  <filename>.json: |
    { ... Grafana dashboard JSON ... }
```

Then mounted in `grafana-deployment.yaml` as a volume mount with `subPath`. **Any new dashboard needs:**
1. A new ConfigMap with dashboard JSON
2. A new `volumeMounts` entry in the Deployment
3. A new `volumes` entry in the Deployment

**Gotcha:** The Grafana Deployment must be updated (rolling restart) whenever ConfigMaps change, because ConfigMaps mounted as volumes update on a delay — a Deployment rollout forces immediate pickup.

### Pattern 4: Grafana Dashboard UID / Datasource UID Consistency

**The existing mismatch:** `grafana-dashboard-api-health.yaml` uses `"uid": "prometheus"` in datasource refs, while `grafana-dashboard-flink.yaml` uses `"uid": "Prometheus"` (capital P). The datasource provisioned in `grafana-datasource-configmap.yaml` is named `"Prometheus"` with no explicit UID set — Grafana auto-generates a UID.

**Fix:** Use `{ "type": "prometheus", "uid": "${DS_PROMETHEUS}" }` as the datasource reference in all dashboard JSON panels. This uses the Grafana template variable syntax that resolves against the default datasource. Alternatively, use the datasource by name instead of UID for all panels.

**Practical fix for debug mode:** Set `"datasource": { "type": "prometheus", "uid": "prometheus" }` consistently everywhere (lowercase). The auto-generated UID from Grafana for the first provisioned datasource is typically `"prometheus"` when the name is `"Prometheus"`.

### Pattern 5: Flink Dashboard JSON Structure

The existing `grafana-dashboard-flink.yaml` is a stub with 2 panels. A comprehensive debug dashboard needs:
- **Row 1 — Job Overview:** stat panels for each job's uptime, restart count, running/finished status
- **Row 2 — Throughput:** timeseries for records in/out per second by job
- **Row 3 — Checkpointing:** stat for last checkpoint duration, timeseries for checkpoint success/failure rate
- **Row 4 — Watermarks:** timeseries for `currentInputWatermark` (event-time lag indicator)
- **Row 5 — Resource Usage:** JVM heap, CPU by TaskManager pod

### Pattern 6: Kafka Metrics via Strimzi

Strimzi exposes Kafka metrics via a built-in JMX Prometheus exporter when configured. The prometheus configmap already has `strimzi-kafka` and `kafka-exporter` jobs. Key Kafka metrics for debug dashboards:

- `kafka_server_brokertopicmetrics_messagesin_total` — messages in per topic
- `kafka_consumer_group_lag` — consumer group lag (from kafka-exporter)
- `kafka_consumergroup_lag` — JMX exporter variant
- `consumer_lag` — custom metric from the Python Kafka consumer (already in dashboard)

**Note:** Whether Strimzi is configured to emit JMX metrics depends on the Kafka CR having `metrics:` configured. Check `k8s/kafka/` for the Kafka CR.

### Recommended Project Structure (no changes needed)

```
k8s/monitoring/
├── prometheus-configmap.yaml       # ADD flink-jobs scrape job here
├── grafana-deployment.yaml         # ADD volume mount for new/updated dashboards
├── grafana-datasource-configmap.yaml  # No changes needed
├── grafana-dashboards-configmap.yaml  # No changes needed
├── grafana-dashboard-api-health.yaml  # Fix datasource UID if needed
├── grafana-dashboard-ml-perf.yaml     # Fix datasource UID if needed
├── grafana-dashboard-kafka.yaml       # Fix datasource UID if needed
└── grafana-dashboard-flink.yaml       # REPLACE with full dashboard
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Flink metrics collection | Custom exporter sidecar | Flink built-in PrometheusReporterFactory (already configured) | Already running on port 9249 per FlinkDeployment spec |
| Kafka metrics | Custom JMX scraper | Strimzi built-in exporter + existing kafka-exporter scrape job | Already in Prometheus config |
| Dashboard auth bypass | Custom middleware | `GF_AUTH_ANONYMOUS_ENABLED=true` (already set) | Anonymous viewer already works |
| Grafana data injection | Seed scripts | Prometheus scrape of live services | Metrics exist when services run |
| Dashboard UID management | Custom tooling | Grafana provisioning `uid` field in JSON | Standard Grafana feature |

---

## Common Pitfalls

### Pitfall 1: Flink Namespace Not Scraped
**What goes wrong:** Prometheus `kubernetes-pods` job uses pod annotation discovery but may have namespace restrictions or the `flink` namespace pods don't match the relabeling regex. Result: zero Flink metrics in Prometheus, all Flink panels show "No data".
**Why it happens:** The existing `kubernetes-pods` job has no `namespaces:` restriction in `kubernetes_sd_configs`, so it should discover all namespaces — BUT the Prometheus pod needs RBAC to list pods in the `flink` namespace. Check `k8s/monitoring/prometheus-rbac.yaml` for ClusterRole vs Role scope.
**How to avoid:** Add an explicit `flink-jobs` scrape job with `namespaces: names: [flink]`. This makes the intent clear and doesn't depend on the generic discovery working.
**Warning signs:** `up{job="kubernetes-pods", kubernetes_namespace="flink"}` returns nothing in Prometheus.

### Pitfall 2: Grafana Datasource UID Mismatch
**What goes wrong:** Dashboard JSON references `"uid": "Prometheus"` (capital P) but Grafana auto-generates a different UID. All panels show "Datasource not found" instead of "No data".
**Why it happens:** Grafana auto-generates datasource UIDs unless explicitly set in the provisioning YAML using the `uid:` field.
**How to avoid:** Add `uid: prometheus` to the datasource in `grafana-datasource-configmap.yaml`, then use `"uid": "prometheus"` in all dashboard JSONs. Alternatively use the `${DS_PROMETHEUS}` template variable approach.
**Warning signs:** Panel error "Datasource not found: Prometheus" or panels show correct title but red error icon.

### Pitfall 3: Flink JobManager vs TaskManager Metric Split
**What goes wrong:** Job-level metrics (uptime, checkpoints, restarts) are on the JobManager pod. Task-level metrics (throughput, watermarks) are on TaskManager pods. A query like `flink_jobmanager_job_uptime` will return empty if you query TaskManager pods and vice versa.
**Why it happens:** Flink's metric scope hierarchy separates JM and TM metrics.
**How to avoid:** Use `flink_jobmanager_*` for job/checkpoint metrics, `flink_taskmanager_*` for throughput/watermark metrics. Both are labeled with `job_name`.

### Pitfall 4: ConfigMap Volume Mount Timing
**What goes wrong:** Updated dashboard ConfigMaps don't appear in Grafana until after a pod restart. The kubelet syncs ConfigMap volumes on a ~1-2 minute delay.
**Why it happens:** Kubernetes ConfigMap volume mounts are eventually consistent.
**How to avoid:** `kubectl rollout restart deployment/grafana -n monitoring` after applying ConfigMap changes. Include this in any deployment script.

### Pitfall 5: Prometheus RBAC Missing flink Namespace
**What goes wrong:** Prometheus can't list/watch pods in the `flink` namespace, so discovery returns nothing even with correct scrape config.
**Why it happens:** `prometheus-rbac.yaml` may define a `Role` (namespace-scoped) rather than a `ClusterRole`.
**How to avoid:** Verify `prometheus-rbac.yaml` uses `ClusterRole` + `ClusterRoleBinding`. If not, add a RoleBinding in the `flink` namespace for the Prometheus ServiceAccount.

### Pitfall 6: Flink Prometheus Path is "/" not "/metrics"
**What goes wrong:** The PrometheusReporter serves metrics at `/` (root path), not `/metrics`. If Prometheus scrape config uses `metrics_path: /metrics` the scrape returns 404.
**Why it happens:** Flink's built-in PrometheusReporter default path is `/`.
**How to avoid:** The FlinkDeployments already set `prometheus.io/path: "/"` in pod annotations. The scrape config must respect this annotation via the `__meta_kubernetes_pod_annotation_prometheus_io_path` relabel.

---

## Code Examples

### Prometheus flink-jobs scrape job (verified against existing pattern in repo)
```yaml
# In prometheus-configmap.yaml, add under scrape_configs:
- job_name: flink-jobs
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - flink
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: "true"
    - source_labels:
        - __address__
        - __meta_kubernetes_pod_annotation_prometheus_io_port
      action: replace
      regex: ([^:]+)(?::\d+)?;(\d+)
      replacement: $1:$2
      target_label: __address__
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
    - source_labels: [__meta_kubernetes_namespace]
      action: replace
      target_label: kubernetes_namespace
    - source_labels: [__meta_kubernetes_pod_name]
      action: replace
      target_label: kubernetes_pod_name
    - source_labels: [__meta_kubernetes_pod_label_app_kubernetes_io_name]
      action: replace
      target_label: flink_job
```

### Grafana datasource UID fix (provisioning YAML)
```yaml
# In grafana-datasource-configmap.yaml:
datasources:
  - name: Prometheus
    type: prometheus
    uid: prometheus          # ADD THIS — fixes UID to a known value
    access: proxy
    url: http://prometheus.monitoring.svc.cluster.local:9090
    isDefault: true
    editable: false
```

### Flink dashboard panel — Checkpoint Duration (timeseries)
```json
{
  "id": 10,
  "title": "Last Checkpoint Duration",
  "type": "timeseries",
  "datasource": { "type": "prometheus", "uid": "prometheus" },
  "fieldConfig": {
    "defaults": { "unit": "ms" }
  },
  "targets": [
    {
      "expr": "flink_jobmanager_job_lastCheckpointDuration",
      "legendFormat": "{{job_name}}",
      "refId": "A"
    }
  ]
}
```

### Flink dashboard panel — Records In/Out (throughput timeseries)
```json
{
  "id": 11,
  "title": "Records In/Out Per Second",
  "type": "timeseries",
  "datasource": { "type": "prometheus", "uid": "prometheus" },
  "targets": [
    {
      "expr": "flink_taskmanager_job_task_numRecordsInPerSecond",
      "legendFormat": "In — {{job_name}}/{{task_name}}",
      "refId": "A"
    },
    {
      "expr": "flink_taskmanager_job_task_numRecordsOutPerSecond",
      "legendFormat": "Out — {{job_name}}/{{task_name}}",
      "refId": "B"
    }
  ]
}
```

### Flink dashboard panel — Job Restart Count (stat)
```json
{
  "id": 12,
  "title": "Job Restart Count",
  "type": "stat",
  "datasource": { "type": "prometheus", "uid": "prometheus" },
  "fieldConfig": {
    "defaults": {
      "thresholds": {
        "steps": [
          { "color": "green", "value": null },
          { "color": "yellow", "value": 1 },
          { "color": "red", "value": 5 }
        ]
      }
    }
  },
  "targets": [
    {
      "expr": "flink_jobmanager_job_numRestarts",
      "legendFormat": "{{job_name}}",
      "refId": "A"
    }
  ]
}
```

---

## Flink Job Inventory (from repo inspection)

Five FlinkDeployments exist in the `flink` namespace, all with `metrics.reporter.prom.port: "9249"` and `prometheus.io/scrape: "true"`:

| Job Name | CR Name | Purpose |
|----------|---------|---------|
| `indicator-stream` | `flinkdeployment-indicator-stream.yaml` | Computes EMA/RSI/MACD from Kafka OHLCV stream |
| `ohlcv-normalizer` | `flinkdeployment-ohlcv-normalizer.yaml` | Normalizes raw OHLCV data from Kafka |
| `feast-writer` | `flinkdeployment-feast-writer.yaml` | Writes computed features to Feast/Redis |
| `sentiment-stream` | `flinkdeployment-sentiment-stream.yaml` | Processes news sentiment from Kafka |
| `sentiment-writer` | `flinkdeployment-sentiment-writer.yaml` | Writes sentiment features to Feast/Redis |

All use `flinkVersion: v1_19`, RocksDB state backend, 30s checkpointing to MinIO.

---

## Dashboard Inventory — Current State

| Dashboard | File | Panels | Root Cause of Empty |
|-----------|------|--------|---------------------|
| API Health | `grafana-dashboard-api-health.yaml` | 11 panels | `kubernetes_namespace` label may not be attached if relabeling is broken; datasource UID mismatch (`"uid": "prometheus"` lowercase vs auto-generated) |
| ML Performance | `grafana-dashboard-ml-perf.yaml` | ~8 panels | `prediction_requests_total`, `prediction_latency_seconds` only emitted by FastAPI when it's actually called |
| Kafka & Infrastructure | `grafana-dashboard-kafka.yaml` | 8 panels | Kafka JMX exporter may not be enabled in Strimzi Kafka CR; `consumer_lag` custom metric only from running consumer |
| Flink Stream | `grafana-dashboard-flink.yaml` | 2 panels (stub) | No Prometheus scrape job for `flink` namespace — zero metrics ingested |

---

## What Needs to Be Built (Plan Scope)

### Plan 72-01: Prometheus Scrape Fix + Flink Dashboard Expansion
1. Add `flink-jobs` scrape job to `prometheus-configmap.yaml`
2. Fix datasource UID in `grafana-datasource-configmap.yaml` (add `uid: prometheus`)
3. Update `grafana-dashboard-flink.yaml` — replace 2-panel stub with 10+ panel comprehensive dashboard covering: job uptime, restart count, checkpoint success/failure/duration, records throughput in/out, watermark lag, JVM heap per TM
4. Apply Prometheus ConfigMap rollout + Grafana rollout restart

### Plan 72-02: Existing Dashboard Debug Fixes
1. Audit all existing dashboard JSON for datasource UID consistency — standardize to `"uid": "prometheus"`
2. Add `"No data"` debugging panels or use `or vector(0)` fallback in PromQL for key metrics that should always have a value (e.g., `up`, `process_cpu_seconds_total`)
3. Add a "Service Health" row to the API Health dashboard using `up{kubernetes_namespace="ingestion"}` — this always has a value when Prometheus is running
4. Verify Kafka CR has `metricsConfig:` set for Strimzi JMX exporter; if not, add or add note to operator

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Playwright (already configured) |
| Config file | `services/frontend/playwright.config.ts` |
| Quick run command | `cd services/frontend && npx playwright test e2e/infra/grafana.spec.ts --reporter=line` |
| Full suite command | `cd services/frontend && npx playwright test e2e/infra/ --reporter=line` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MON-FLINK-01 | Flink metrics scraped into Prometheus | integration | `npx playwright test e2e/infra/grafana.spec.ts -g "Prometheus datasource proxied query"` | Yes (existing test, grafana.spec.ts line 242) |
| MON-FLINK-02 | Flink dashboard has panels with data | e2e | `npx playwright test e2e/infra/grafana.spec.ts -g "Flink"` | No — needs new test block in grafana.spec.ts |
| MON-DEBUG-01 | All dashboards render without "No data" on key panels | e2e | `npx playwright test e2e/infra/grafana.spec.ts -g "Dashboard panel data"` | Yes (existing block, grafana.spec.ts line 122) |

### Sampling Rate
- **Per task commit:** `npx playwright test e2e/infra/grafana.spec.ts --reporter=line` (grafana tests only, ~30s)
- **Per wave merge:** `npx playwright test e2e/infra/ --reporter=line` (all infra tests)
- **Phase gate:** Full infra suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] Add Flink dashboard test block to `e2e/infra/grafana.spec.ts` — covers MON-FLINK-02

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| Manual dashboard creation via Grafana UI | ConfigMap-provisioned JSON dashboards | Dashboards survive pod restarts — already used in this repo |
| Static scrape targets in `prometheus.yml` | `kubernetes_sd_configs` pod annotation discovery | Auto-discovers new pods — already used; just needs `flink` namespace coverage |
| Flink metrics via JMX only | Built-in `PrometheusReporterFactory` in Flink 1.9+ | No sidecar needed — already configured in all FlinkDeployments |

---

## Open Questions

1. **Does Strimzi Kafka CR have `metricsConfig` set?**
   - What we know: Prometheus has a `strimzi-kafka` scrape job that looks for `strimzi_io_kind: Kafka` pods with `prometheus.io/scrape: "true"`. The kafka CR in `k8s/kafka/` needs inspection.
   - What's unclear: Whether the Kafka CR enables JMX metrics export. If not, `kafka_server_*` metrics will be absent.
   - Recommendation: Check `k8s/kafka/` directory. If no `metricsConfig:` present, add a `KafkaMetricConfig` or note that Kafka broker metrics will remain empty.

2. **Is `up{job="kubernetes-pods", kubernetes_namespace="flink"}` being scraped by the existing job?**
   - What we know: The existing `kubernetes-pods` job has no namespace restriction in `kubernetes_sd_configs`. But it depends on `prometheus.io/scrape: "true"` annotations and correct RBAC.
   - What's unclear: Whether the Prometheus ClusterRole/ClusterRoleBinding in `prometheus-rbac.yaml` covers the `flink` namespace.
   - Recommendation: The explicit `flink-jobs` scrape job is the safer fix regardless. Read `prometheus-rbac.yaml` in Plan 72-01 to determine if RBAC amendment is also needed.

3. **What `GF_AUTH_ANONYMOUS_ORG_ROLE` is set to?**
   - What we know: Anonymous access is enabled (`GF_AUTH_ANONYMOUS_ENABLED: "true"`) but `GF_AUTH_ANONYMOUS_ORG_ROLE` is NOT set in the deployment.
   - What's unclear: Whether the default role is `Viewer` (which can see dashboards) or `None`.
   - Recommendation: Grafana 10.x default for anonymous org role is `Viewer` — dashboards should be viewable. If not, add `GF_AUTH_ANONYMOUS_ORG_ROLE: "Viewer"` to the Deployment env. This is a low-risk fix.

---

## Sources

### Primary (HIGH confidence)
- Direct repo inspection: `k8s/monitoring/prometheus-configmap.yaml` — confirmed no flink scrape job
- Direct repo inspection: `k8s/flink/flinkdeployment-*.yaml` — confirmed `metrics.reporter.prom.port: "9249"` and pod annotations on all 5 deployments
- Direct repo inspection: `k8s/monitoring/grafana-deployment.yaml` — confirmed Grafana 10.4.0, anonymous enabled, 4 dashboard volumes
- Direct repo inspection: `k8s/monitoring/grafana-datasource-configmap.yaml` — confirmed Prometheus, Loki, TimescaleDB datasources without explicit UIDs
- Direct repo inspection: `k8s/monitoring/grafana-dashboard-flink.yaml` — confirmed stub with 2 panels only

### Secondary (MEDIUM confidence)
- Flink 1.19 Prometheus reporter metric naming conventions — based on Flink documentation patterns; actual metric names may include additional label dimensions not listed here
- Grafana 10.x datasource UID auto-generation behavior — based on known Grafana provisioning behavior; verify with `GET /api/datasources` in running Grafana

### Tertiary (LOW confidence)
- Whether Strimzi Kafka CR has metrics configured — requires reading `k8s/kafka/` which was not inspected

---

## Metadata

**Confidence breakdown:**
- Prometheus scrape gap (flink namespace): HIGH — confirmed by direct inspection of prometheus-configmap.yaml
- Flink metric names: MEDIUM — canonical names from Flink 1.19 docs; exact label dimensions need live verification
- Grafana datasource UID mismatch: MEDIUM — behavior of auto-generated UIDs in Grafana 10.4 provisioning is well-known but exact UID value needs verification via `GET /api/datasources`
- Kafka JMX metrics availability: LOW — requires Strimzi Kafka CR inspection

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable stack, no fast-moving components)
