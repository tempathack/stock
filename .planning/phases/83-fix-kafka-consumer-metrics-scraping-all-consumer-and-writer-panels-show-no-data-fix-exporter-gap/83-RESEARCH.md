# Phase 83: Fix Kafka Consumer Metrics Scraping - Research

**Researched:** 2026-04-03
**Domain:** Prometheus scraping configuration — Kubernetes pod annotations, Service discovery, port alignment
**Confidence:** HIGH

## Summary

All panels in the Grafana "Kafka & Infrastructure" dashboard show "No data." The root cause is a chain of three concrete gaps that together prevent any consumer metrics from reaching Prometheus.

**Gap 1 — Port mismatch in docker-compose prometheus.yml.** `monitoring/prometheus.yml` (used by docker-compose) has a static scrape target `kafka-consumer:8001`, but the consumer starts its metrics HTTP server on port 9090 (hardcoded in `consumer/main.py` and `consumer/metrics.py`). Prometheus can never reach the consumer on port 8001.

**Gap 2 — No K8s Service for kafka-consumer.** The `k8s/processing/` directory contains only `kafka-consumer-deployment.yaml` and `configmap.yaml`. There is no Service manifest. The pod has annotations `prometheus.io/scrape: "true"`, `prometheus.io/port: "9090"`, `prometheus.io/path: "/metrics"` which enables the `kubernetes-pods` scrape job in `prometheus-configmap.yaml`. However, without a Service, cross-namespace network routing and DNS (`kafka-consumer.processing.svc.cluster.local`) do not exist. The pod-based scrape discovery should work IF Prometheus RBAC covers the `processing` namespace — but it was scoped to infer pods only in namespaces where it can list pods. This needs verification against the RBAC rules.

**Gap 3 — INTRADAY_TOPIC blank in processing ConfigMap.** `k8s/processing/configmap.yaml` has `INTRADAY_TOPIC: ""` (empty string). The consumer subscribes to both topics. An empty topic name will cause `confluent_kafka` to raise an error or silently subscribe to nothing, preventing the consumer pod from running at all — which means no metrics are emitted.

The dashboard panels query metrics from three sources: `messages_consumed_total` (custom, from consumer), `batch_write_duration_seconds` (custom, from consumer), and `consumer_lag` (custom, from consumer). If the consumer pod either crashes on startup (due to empty topic) or is unreachable to Prometheus (port mismatch, no Service), all three metric families return no data.

**Primary recommendation:** Fix in this order: (1) set `INTRADAY_TOPIC: "intraday-data"` in the processing ConfigMap so the consumer starts, (2) fix `monitoring/prometheus.yml` static target to port 9090, (3) add a K8s Service for kafka-consumer exposing port 9090, (4) verify Prometheus RBAC includes the `processing` namespace. No dashboard JSON changes are needed — the queries in `grafana-dashboard-kafka.yaml` are correct once metrics are actually scraped.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| prometheus_client | 0.20.x (in requirements.txt) | Python metrics server via `start_http_server` | Already in use in consumer service |
| Kubernetes pod annotations | native | `prometheus.io/scrape`, `prometheus.io/port`, `prometheus.io/path` | The `kubernetes-pods` job in prometheus-configmap.yaml uses these annotations — already configured |
| Prometheus kubernetes_sd_configs | built-in | Pod-based scrape discovery | Already configured in prometheus-configmap.yaml for kubernetes-pods job |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| K8s ClusterRole/RoleBinding | native | Allow Prometheus to list/watch pods in processing namespace | Required for kubernetes_sd_configs pod role to discover kafka-consumer pods |

### No New Libraries Required
All fixes are configuration changes — YAML manifests and one prometheus.yml edit.

**Installation:** No new packages.

## Architecture Patterns

### How Prometheus Scrapes kafka-consumer Pods

The `kubernetes-pods` job in `prometheus-configmap.yaml` works as follows:
1. Prometheus queries the K8s API for all pods across all namespaces (via `kubernetes_sd_configs.role: pod`)
2. For each pod, it reads the annotation `prometheus.io/scrape: "true"` — keep only these pods
3. It reads `prometheus.io/port` and replaces the pod's address port with that value
4. It reads `prometheus.io/path` and uses that as the metrics path
5. It scrapes `<pod_ip>:<port><path>`

The kafka-consumer Deployment already has all three annotations set correctly for port 9090. This means the K8s-based scrape path is **correct by design** and will work once the consumer pod is actually running (gap 3 fix) and Prometheus has RBAC to discover pods in the `processing` namespace.

### Recommended File Changes

```
stock-prediction-platform/
├── monitoring/prometheus.yml                          # Fix: kafka-consumer target port 8001 -> 9090
├── k8s/processing/
│   ├── configmap.yaml                                 # Fix: INTRADAY_TOPIC: "" -> "intraday-data"
│   └── kafka-consumer-service.yaml                   # New: K8s Service exposing port 9090
└── k8s/monitoring/
    └── prometheus-rbac.yaml                          # Audit: confirm processing namespace in ClusterRole
```

### Pattern 1: K8s Service for Pod-with-Metrics

**What:** A headless or standard ClusterIP Service targeting kafka-consumer pods by label `app: kafka-consumer`, exposing port 9090 named `metrics`. The Service is not strictly required for the pod-annotation scrape path (which scrapes by pod IP directly), but it provides: stable DNS for health probes, enables future ServiceMonitor-style scraping, and makes the liveness/readiness probes more robust.

**When to use:** Any pod that exposes a metrics port should have a corresponding Service for DNS resolution and network policy purposes.

**Example:**
```yaml
# k8s/processing/kafka-consumer-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: kafka-consumer
  namespace: processing
  labels:
    app: kafka-consumer
spec:
  selector:
    app: kafka-consumer
  ports:
    - name: metrics
      port: 9090
      targetPort: 9090
      protocol: TCP
  type: ClusterIP
```

### Pattern 2: Prometheus RBAC for Cross-Namespace Pod Discovery

**What:** The `kubernetes-pods` job needs `list`, `watch` on `pods` resource in the `processing` namespace. This is granted via a ClusterRole or Role + binding.

**When to use:** Any time a new namespace is added that Prometheus needs to scrape.

Check `k8s/monitoring/prometheus-rbac.yaml` — if it uses a ClusterRole with `["", "pods"]` resources at cluster scope, the `processing` namespace is already covered. If it uses namespace-scoped Roles, a new binding is needed for `processing`.

### Pattern 3: Fixing docker-compose prometheus.yml

**What:** The static config in `monitoring/prometheus.yml` has `targets: ["kafka-consumer:8001"]`. The consumer's metrics server starts on 9090. Change to `targets: ["kafka-consumer:9090"]`.

**Note:** In docker-compose, `kafka-consumer` service does not expose port 9090 explicitly (no `ports:` mapping in docker-compose.yml for that service). The internal network allows `kafka-consumer:9090` to resolve because Docker Compose networking connects services by name on the internal network — no external port mapping needed.

### Anti-Patterns to Avoid

- **Changing metrics server port in Python code**: Do not change `start_metrics_server(9090)` — the K8s deployment annotation already says `prometheus.io/port: "9090"` and the deployment's `containerPort: 9090` matches. Fix the prometheus.yml to match the code, not vice versa.
- **Fixing dashboard JSON instead of metrics source**: The Grafana dashboard queries (`messages_consumed_total`, `consumer_lag`, `batch_write_duration_seconds`) are correct. Do not add `or vector(0)` or similar workarounds to the PromQL — fix the scrape path.
- **Adding a new prometheus scrape job for kafka-consumer**: The `kubernetes-pods` generic job already handles it via annotations. A dedicated `kafka-consumer` job is not needed for K8s mode and would duplicate discovery.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Per-service Prometheus job | Dedicated `job_name: kafka-consumer` static job | Pod annotation-based discovery via `kubernetes-pods` job | Already configured; annotation pattern is established in codebase |
| Metrics forwarding proxy | Nginx sidecar or annotation rewrite | Direct pod IP scraping via pod annotations | Prometheus kubernetes_sd already handles this natively |
| Custom health endpoint for metrics liveness | New HTTP endpoint | Reuse `/metrics` endpoint for liveness probe | Already done in kafka-consumer-deployment.yaml |

**Key insight:** The kubernetes-pods job pattern is already correctly configured for the whole cluster. The consumer just needs to: (a) start up (fix INTRADAY_TOPIC), (b) be on the right port (fix prometheus.yml for docker-compose), and (c) be discoverable (Prometheus RBAC).

## Common Pitfalls

### Pitfall 1: Empty INTRADAY_TOPIC causes silent consumer crash
**What goes wrong:** `confluent_kafka.Consumer.subscribe([..., ""])` with an empty string topic either raises an error on subscribe or connects to a non-existent topic, causing the consumer to crash or idle. No metrics are emitted.
**Why it happens:** The configmap.yaml was left with `INTRADAY_TOPIC: ""` — likely a copy-paste omission.
**How to avoid:** Set `INTRADAY_TOPIC: "intraday-data"` in `k8s/processing/configmap.yaml`.
**Warning signs:** `kubectl get pods -n processing` shows the kafka-consumer pod in `CrashLoopBackOff` or `Error` state; `kubectl logs` will show a confluent_kafka error about topic subscription.

### Pitfall 2: Port 8001 in docker-compose prometheus.yml was never corrected
**What goes wrong:** `monitoring/prometheus.yml` targets `kafka-consumer:8001`. The consumer only listens on 9090. Prometheus will log `context deadline exceeded` or `connection refused` for the kafka-consumer job. All consumer metrics show "No data" in docker-compose mode.
**Why it happens:** The prometheus.yml appears to have been written with an assumed port that doesn't match the actual implementation.
**How to avoid:** Change target to `kafka-consumer:9090` in `monitoring/prometheus.yml`.
**Warning signs:** Prometheus Targets page shows kafka-consumer as DOWN with connection refused.

### Pitfall 3: Prometheus RBAC may not cover the processing namespace
**What goes wrong:** If the ClusterRole or Role for Prometheus only covers specific namespaces (not `processing`), the `kubernetes-pods` job cannot discover kafka-consumer pods. Prometheus logs will show RBAC permission denied errors.
**Why it happens:** The processing namespace is not in the monitoring namespace — cross-namespace access requires explicit RBAC.
**How to avoid:** Audit `k8s/monitoring/prometheus-rbac.yaml`. If it uses a ClusterRole with namespace-agnostic rules, processing is already covered. If namespace-scoped, add a RoleBinding in `processing`.
**Warning signs:** `kubectl logs -n monitoring deploy/prometheus | grep "permission denied\|403"` shows RBAC errors for the processing namespace.

### Pitfall 4: kafka-consumer-deployment.yaml has no Service — liveness probes may fail in some network modes
**What goes wrong:** Liveness and readiness probes use `httpGet.port: 9090` on the pod directly (no service needed for probes). However, if any cross-pod routing assumes a Service DNS name, requests will fail.
**Why it happens:** The Service was never created.
**How to avoid:** Create `kafka-consumer-service.yaml`. This is lower priority than the port fix and INTRADAY_TOPIC fix but should be added for completeness.
**Warning signs:** No immediate failure — probes work on pod IP directly. But Prometheus cannot use a stable Service DNS target.

## Code Examples

### Fix 1: docker-compose prometheus.yml (port 8001 -> 9090)

```yaml
# monitoring/prometheus.yml — change this entry:
  - job_name: kafka-consumer
    static_configs:
      - targets: ["kafka-consumer:9090"]   # was 8001 — matches consumer/main.py start_metrics_server(9090)
    metrics_path: /metrics
```

### Fix 2: processing ConfigMap — INTRADAY_TOPIC

```yaml
# k8s/processing/configmap.yaml
data:
  KAFKA_BOOTSTRAP_SERVERS: "kafka-kafka-bootstrap.storage.svc.cluster.local:9092"
  KAFKA_GROUP_ID: "stock-consumer-group"
  INTRADAY_TOPIC: "intraday-data"      # was "" (empty) — fixes consumer startup
  HISTORICAL_TOPIC: "historical-data"
  BATCH_SIZE: "100"
  BATCH_TIMEOUT_MS: "5000"
  LOG_LEVEL: "INFO"
```

### Fix 3: New kafka-consumer K8s Service

```yaml
# k8s/processing/kafka-consumer-service.yaml (new file)
apiVersion: v1
kind: Service
metadata:
  name: kafka-consumer
  namespace: processing
  labels:
    app: kafka-consumer
spec:
  selector:
    app: kafka-consumer
  ports:
    - name: metrics
      port: 9090
      targetPort: 9090
      protocol: TCP
  type: ClusterIP
```

### Verification Commands

```bash
# Check consumer pods are running
kubectl get pods -n processing -l app=kafka-consumer

# Check consumer logs for subscribe errors
kubectl logs -n processing -l app=kafka-consumer --tail=50

# Check Prometheus can reach consumer (pod IP scrape)
kubectl port-forward -n monitoring deploy/prometheus 9090:9090
# Then visit http://localhost:9090/targets and look for kafka-consumer

# Verify metrics are present
kubectl port-forward -n processing <pod-name> 9090:9090
curl http://localhost:9090/metrics | grep -E "messages_consumed_total|consumer_lag|batch_write"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static scrape targets per service | Pod annotation-based discovery | Prometheus 2.x + K8s SD | Already implemented in this project; only docker-compose uses static config |
| Separate metrics port per service | Shared annotation-driven port on each pod | Prometheus k8s-sd | The project already follows this — kafka-consumer just has wrong port in prometheus.yml |

**No deprecated approaches need removal.** The annotation-based pod discovery pattern is current and correct.

## Open Questions

1. **Does Prometheus RBAC ClusterRole cover `processing` namespace?**
   - What we know: `prometheus-rbac.yaml` exists but was not fully read — it uses a ClusterRole pattern based on the job configs being cluster-wide
   - What's unclear: Whether the ClusterRole uses `namespace: ""` (cluster-scoped) or is namespace-scoped
   - Recommendation: Read `prometheus-rbac.yaml` in the plan and add a processing-namespace RoleBinding if needed; if ClusterRole is cluster-scoped, no change needed

2. **Is the consumer pod currently in CrashLoopBackOff due to empty INTRADAY_TOPIC?**
   - What we know: `INTRADAY_TOPIC: ""` in configmap; confluent_kafka will likely fail on empty topic subscription
   - What's unclear: Whether the consumer code gracefully handles empty topic (filtering out blank strings before subscribe call)
   - Recommendation: Check `consumer/main.py` — topics are built from settings directly. A plan task should verify pod state before and after the fix.

3. **Should the `kubernetes-pods` scrape job be restricted to specific namespaces?**
   - What we know: The current config discovers pods in ALL namespaces matching the annotation
   - What's unclear: Whether this causes noise from non-app pods (kube-system, etc.) that happen to have the annotation
   - Recommendation: Out of scope for this phase — the current cluster-wide approach is fine and established.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual verification + pytest (consumer service has tests in `services/kafka-consumer/tests/`) |
| Config file | `services/kafka-consumer/pytest.ini` |
| Quick run command | `cd stock-prediction-platform/services/kafka-consumer && python -m pytest tests/ -x -q` |
| Full suite command | `cd stock-prediction-platform/services/kafka-consumer && python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MON-03 | Consumer metrics endpoint reachable by Prometheus on port 9090 | smoke | `kubectl port-forward -n processing <pod> 9090:9090 & curl -s http://localhost:9090/metrics` | manual |
| MON-03 | `messages_consumed_total`, `consumer_lag`, `batch_write_duration_seconds` present | smoke | `curl -s http://localhost:9090/metrics | grep -c "messages_consumed_total\|consumer_lag\|batch_write"` | manual |
| INFRA | Prometheus targets page shows kafka-consumer as UP | smoke | Prometheus /targets UI via port-forward | manual |
| INFRA | Grafana Kafka dashboard panels show data (not "No data") | manual-only | Visual check via Grafana port-forward | manual |

**Justification for manual-only:** The broken state is a K8s+Prometheus integration — cannot be unit tested. Existing `test_metrics.py` confirms the Python metrics objects work. The fixes are to YAML config files, verified by live cluster state.

### Sampling Rate
- **Per task commit:** Apply ConfigMap/manifest change, check pod status
- **Per wave merge:** `kubectl port-forward` verification of Prometheus targets + Grafana panels
- **Phase gate:** Grafana "Kafka & Infrastructure" dashboard shows live data in Consumer Metrics and Database Writer sections

### Wave 0 Gaps
None — existing test infrastructure covers the Python metrics code. The fixes are YAML-only and require live cluster verification, not new test files.

## Sources

### Primary (HIGH confidence)
- Direct inspection of `monitoring/prometheus.yml` — confirmed `kafka-consumer:8001` target (wrong port)
- Direct inspection of `services/kafka-consumer/consumer/main.py` and `metrics.py` — confirmed `start_metrics_server(9090)` (correct port)
- Direct inspection of `k8s/processing/kafka-consumer-deployment.yaml` — confirmed `prometheus.io/port: "9090"` annotation and `containerPort: 9090`
- Direct inspection of `k8s/processing/configmap.yaml` — confirmed `INTRADAY_TOPIC: ""` (empty)
- Direct inspection of `k8s/processing/` directory — confirmed no Service manifest exists
- Direct inspection of `k8s/monitoring/prometheus-configmap.yaml` — confirmed `kubernetes-pods` job uses annotation-based discovery (no dedicated kafka-consumer job)
- Direct inspection of `k8s/monitoring/grafana-dashboard-kafka.yaml` — confirmed all panels query custom consumer metrics (`messages_consumed_total`, `consumer_lag`, `batch_write_duration_seconds`) which are correct once scraped

### Secondary (MEDIUM confidence)
- Prometheus kubernetes_sd_configs pod role behavior — annotation-driven scrape is a well-established Prometheus pattern; requires RBAC to list pods in target namespace

### Tertiary (LOW confidence)
- confluent_kafka behavior with empty topic string in `subscribe([..., ""])` — likely raises an error but not verified by reading confluent_kafka source; may need empirical check against live consumer logs

## Metadata

**Confidence breakdown:**
- Root cause (port mismatch, INTRADAY_TOPIC blank, missing Service): HIGH — directly observed in source files
- Fix approach (YAML changes only, no Python changes): HIGH — all three gaps are config/manifest issues
- RBAC coverage of processing namespace: MEDIUM — not read in detail, needs plan-time verification
- Consumer behavior with empty topic: MEDIUM — inferred from confluent_kafka conventions

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (K8s manifest patterns are stable; no fast-moving dependencies)
