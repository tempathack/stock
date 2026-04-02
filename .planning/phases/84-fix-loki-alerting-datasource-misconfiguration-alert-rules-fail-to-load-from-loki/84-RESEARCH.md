# Phase 84: Fix Loki Alerting Datasource Misconfiguration — Research

**Researched:** 2026-04-03
**Domain:** Grafana unified alerting, Loki datasource provisioning, Promtail log scraping
**Confidence:** HIGH

## Summary

Live cluster inspection (Grafana 10.4.0, Loki 2.9.6) reveals three distinct but related problems that together prevent Loki-backed alert rules from working.

**Problem 1 — No Grafana unified alert rules exist at all.** Grafana unified alerting is enabled (`unifiedAlertingEnabled: true`), but the provisioning directory `/etc/grafana/provisioning/alerting/` is empty. No alerting ConfigMap is mounted to the Grafana deployment. The existing alert rules (HighDriftSeverity, HighAPIErrorRate, HighConsumerLag, HighPredictionLatencyP95) live in `prometheus-configmap.yaml` as Prometheus-native rules, not in Grafana unified alerting. There are zero Grafana-managed alert rules for Loki log queries.

**Problem 2 — Loki datasource has no explicit UID in provisioning.** The `grafana-datasource-configmap.yaml` provisions Prometheus with `uid: prometheus` (explicit, stable) but provisions Loki with no `uid` field at all. Grafana auto-generates `P8E80F9AEF21F6940` for Loki. Any Grafana alert rule referencing the Loki datasource by UID will break on pod restart when a new UID is generated. This is the root cause of "alert rules fail to load from Loki."

**Problem 3 — Promtail has 0/0 active targets; Loki has no ingested logs.** The Promtail scrape config uses a path replacement pattern with `/` separators between namespace, pod, and container components (`/var/log/pods/*$1/$2/$3/*.log`). The actual Kubernetes pod log directory layout uses `_` as separator: `/var/log/pods/{namespace}_{pod-name}_{uid}/{container}/N.log`. No log entries are reaching Loki (confirmed: `{namespace="monitoring"}` returns 0 streams). This means any Loki-based alert rule would return "no data" even after datasource is fixed.

**Primary recommendation:** Fix all three gaps in a single plan: (1) add `uid: loki` to Loki datasource provisioning, (2) create `grafana-alerting-configmap.yaml` with at least one meaningful Loki-backed alert rule mounted to `/etc/grafana/provisioning/alerting/`, (3) fix Promtail path replacement so logs flow into Loki.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Grafana | 10.4.0 (already deployed) | Unified alerting with Loki datasource | Already in cluster; provisioning via K8s ConfigMap is the established pattern |
| Loki | 2.9.6 (already deployed) | Log storage queried by Grafana alerts | Already running; `ready` endpoint returns 200 |
| Promtail | 2.9.6 (already deployed) | DaemonSet log collector pushing to Loki | Already deployed; only config fix needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Grafana provisioning alerting YAML | schema v1 | Declare alert rules as code in K8s ConfigMap | Preferred over UI-created rules for GitOps reproducibility |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Grafana unified alerting for Loki rules | Loki ruler + Cortex ruler | Loki 2.9.6 has no `ruler` section configured; enabling it requires additional storage and ring config — overkill for this fix |
| Fixing Promtail path pattern | Re-deploying Promtail with Helm chart | Config-only change is simpler, no new tooling needed |

**Installation:** No new packages — all changes are K8s ConfigMap YAML edits.

## Architecture Patterns

### Current Monitoring File Locations
```
stock-prediction-platform/
└── k8s/monitoring/
    ├── grafana-datasource-configmap.yaml     # ADD uid: loki to Loki datasource
    ├── grafana-deployment.yaml               # ADD alerting volume mount
    ├── grafana-alerting-configmap.yaml       # CREATE: Grafana unified alert rules
    └── promtail-configmap.yaml               # FIX: __path__ replacement pattern
```

### Pattern 1: Grafana Unified Alerting Provisioning via ConfigMap

**What:** Grafana 10.x reads `*.yaml` files from `/etc/grafana/provisioning/alerting/` on startup. Files follow the `apiVersion: 1` schema with `groups` containing `orgId`, `name`, `folder`, and `rules`. Each rule specifies a `datasource_uid` to identify which datasource evaluates the query.

**When to use:** Any time alert rules need to survive pod restarts — provisioned rules are immutable from the UI by default (`editable: false` equivalent comes from `provenance: file`).

**Example (Grafana unified alerting provisioning format):**
```yaml
# Source: Grafana 10 provisioning docs — /etc/grafana/provisioning/alerting/rules.yaml
apiVersion: 1
groups:
  - orgId: 1
    name: loki-log-alerts
    folder: Alerting
    interval: 1m
    rules:
      - uid: loki-high-error-log-rate
        title: "High Error Log Rate"
        condition: C
        data:
          - refId: A
            datasourceUid: loki
            model:
              expr: 'sum(rate({namespace=~".+"} |= "ERROR" [5m])) > 1'
              queryType: range
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions:
                - evaluator:
                    params: [1]
                    type: gt
                  query:
                    params: [A]
        noDataState: NoData
        execErrState: Error
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error log rate detected across namespaces"
```

**Key constraint:** `datasourceUid` in alert rules MUST match the `uid` field in the datasource provisioning. Since the Loki datasource currently has no explicit `uid`, this value is auto-generated and unstable.

### Pattern 2: Loki Datasource UID Pinning

**What:** Add `uid: loki` to the Loki datasource entry in `grafana-datasource-configmap.yaml` to make the UID stable and predictable across pod restarts.

**Example:**
```yaml
# In grafana-datasource-configmap.yaml datasources.yaml section
- name: Loki
  type: loki
  uid: loki
  access: proxy
  url: http://loki.monitoring.svc.cluster.local:3100
  isDefault: false
  editable: false
```

**Why critical:** Prometheus datasource already uses `uid: prometheus` (line 12 of current config). Loki is the only datasource missing this. Alert rules referencing `datasourceUid: loki` will resolve correctly after this fix, and survive pod restarts.

### Pattern 3: Promtail Path Fix for Kubernetes Pod Logs

**What:** The standard Kubernetes pod log path is `/var/log/pods/{namespace}_{pod-name}_{uid}/{container-name}/{num}.log`. The current Promtail `__path__` relabel uses `/` separator producing `/var/log/pods/*{namespace}/{pod}/{container}/*.log` — this glob never matches.

**Confirmed:** The actual path `/var/log/pods/monitoring_grafana-56f48999f4-4bj82_a937d507-9fe9-43f0-bb30-6c27bd9c25c2/grafana/0.log` exists and the glob pattern `*monitoring/grafana-*` cannot match `monitoring_grafana-*_{uid}`.

**Fix — replace the path relabel block with the correct glob:**
```yaml
# In promtail-configmap.yaml scrape_configs[0].relabel_configs
# REPLACE the __path__ target block with:
- source_labels:
    - __meta_kubernetes_namespace
    - __meta_kubernetes_pod_name
    - __meta_kubernetes_pod_container_name
  separator: _
  target_label: __path__
  replacement: /var/log/pods/*$1_$2_*/$3/*.log
```

**Why:** The `_` separator plus the `*` wildcard before and after the pod name handles the UID component without needing to capture it separately.

### Pattern 4: Mounting Alerting ConfigMap in Grafana Deployment

**What:** Add a new volume and volumeMount to `grafana-deployment.yaml` to expose the alerting provisioning ConfigMap at `/etc/grafana/provisioning/alerting/`.

```yaml
# Add to volumes:
- name: grafana-alerting
  configMap:
    name: grafana-alerting-rules

# Add to volumeMounts:
- name: grafana-alerting
  mountPath: /etc/grafana/provisioning/alerting
```

### Anti-Patterns to Avoid
- **Loki ruler without storage config:** Adding a `ruler:` section to Loki config without a dedicated ruler storage backend causes startup failure. Grafana unified alerting is the correct approach here — don't configure Loki ruler.
- **Auto-generated UID references:** Never reference `P8E80F9AEF21F6940` (the auto-generated Loki UID) in alert rule YAML. Always reference the stable string UID `loki` after pinning it.
- **Log query without active ingestion:** Even with correct datasource config, Loki alert rules evaluating LogQL over empty streams will fire `NoData`. Fix Promtail first so logs flow before testing alert rule evaluation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Alert rule delivery | Custom webhook receiver | Grafana built-in contact points (already configured: email receiver) | Grafana unified alerting handles routing, silencing, grouping |
| Log path discovery | Shell script to find log paths | Standard Promtail `*` glob with `_` separator | Kubernetes guarantees the `{ns}_{pod}_{uid}/{container}/*.log` layout |
| Datasource UID tracking | External registry | Explicit `uid:` field in provisioning YAML | Grafana honors it on first provisioning and never changes it |

**Key insight:** All three fixes are ConfigMap YAML edits. No new services, no new images, no schema migrations.

## Common Pitfalls

### Pitfall 1: Grafana Does Not Reload Provisioning at Runtime
**What goes wrong:** Editing a ConfigMap does not automatically reload Grafana provisioning. The pod must be restarted (or the provisioning API called) for changes to take effect.
**Why it happens:** Grafana reads provisioning files only at startup unless file watching is explicitly enabled.
**How to avoid:** After applying ConfigMap changes, run `kubectl rollout restart deployment/grafana -n monitoring`.
**Warning signs:** Alert rules don't appear in Grafana UI even after ConfigMap apply.

### Pitfall 2: Alert Rule UID Must Be Globally Unique
**What goes wrong:** Two alert rules with the same `uid` field cause the second to silently overwrite the first on startup.
**Why it happens:** Grafana uses the `uid` as the primary key for stored alert rules.
**How to avoid:** Use descriptive, namespaced UIDs like `loki-high-error-rate` or `loki-error-logs-5m`.
**Warning signs:** One of two rules disappears after pod restart.

### Pitfall 3: Promtail Path Glob Must Match Real UID Directory
**What goes wrong:** A glob pattern like `*$1/$2_$3_*` would fail if the separator encoding is wrong.
**Why it happens:** Kubernetes uses `{namespace}_{pod}_{uid}` as directory name — underscore-separated, not slash-separated.
**How to avoid:** Verify glob with `kubectl exec promtail -- sh -c 'ls /var/log/pods/monitoring_grafana*/'` after applying fix.
**Warning signs:** Promtail targets page still shows "0/0 ready" after config update.

### Pitfall 4: Grafana Alerting Provisioning Folder Must Exist
**What goes wrong:** If the `folder:` specified in the alerting YAML (e.g., `Alerting`) does not exist in Grafana, rule provisioning fails silently or creates it with default permissions depending on version.
**Why it happens:** Grafana 10.4 auto-creates alert folders from provisioning files, but some patch versions have bugs.
**How to avoid:** Use `folder: ""` (default General folder) or verify folder existence before referencing.

### Pitfall 5: LogQL in Alert Rules Requires Metric Query Type
**What goes wrong:** A LogQL stream selector `{namespace="monitoring"}` returns log lines, not a numeric value. Alert conditions need a numeric result.
**Why it happens:** Grafana unified alerting requires the query to produce a number for threshold comparison. Raw log queries produce streams.
**How to avoid:** Use `sum(rate({...}[5m]))` or `count_over_time({...}[5m])` — metric expressions that produce a number. The `condition` refId must reference a threshold expression (`__expr__` datasource) that evaluates the numeric result.

## Code Examples

### Complete Alert Rule ConfigMap (Loki datasource)
```yaml
# Source: Grafana 10 unified alerting provisioning schema
# File: k8s/monitoring/grafana-alerting-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-alerting-rules
  namespace: monitoring
data:
  loki-alerts.yaml: |
    apiVersion: 1
    groups:
      - orgId: 1
        name: loki-log-alerts
        folder: Alerting
        interval: 1m
        rules:
          - uid: loki-high-error-log-rate
            title: "High Error Log Rate (Loki)"
            condition: C
            data:
              - refId: A
                queryType: range
                relativeTimeRange:
                  from: 300
                  to: 0
                datasourceUid: loki
                model:
                  expr: 'sum(rate({namespace=~".+"} |= "ERROR" [5m]))'
                  queryType: range
              - refId: C
                datasourceUid: __expr__
                model:
                  type: threshold
                  conditions:
                    - evaluator:
                        params: [1]
                        type: gt
                      query:
                        params: [A]
            noDataState: NoData
            execErrState: Error
            for: 5m
            labels:
              severity: warning
              team: platform
            annotations:
              summary: "High ERROR log rate across namespaces"
              description: "Error log rate has exceeded 1 line/s for 5 minutes."
```

### Loki Datasource with Pinned UID
```yaml
# In grafana-datasource-configmap.yaml — add uid field to Loki entry
- name: Loki
  type: loki
  uid: loki
  access: proxy
  url: http://loki.monitoring.svc.cluster.local:3100
  isDefault: false
  editable: false
```

### Promtail Path Fix
```yaml
# In promtail-configmap.yaml — replace __path__ relabel block
- source_labels:
    - __meta_kubernetes_namespace
    - __meta_kubernetes_pod_name
    - __meta_kubernetes_pod_container_name
  separator: _
  target_label: __path__
  replacement: /var/log/pods/*$1_$2_*/$3/*.log
```

### Grafana Deployment Alerting Volume Mount Addition
```yaml
# Add to grafana-deployment.yaml volumeMounts:
- name: grafana-alerting
  mountPath: /etc/grafana/provisioning/alerting

# Add to grafana-deployment.yaml volumes:
- name: grafana-alerting
  configMap:
    name: grafana-alerting-rules
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Grafana legacy alerting (dashboard-level) | Grafana unified alerting (`ngalert`) | Grafana 9.0 (2022), mandatory in 10.x | Alert rules are now folder-based, provisioned separately from dashboards |
| Prometheus rules for all alerting | Grafana can evaluate Loki/Prometheus/PostgreSQL rules natively | Grafana 9.0+ | Log-based alert rules no longer need Loki ruler or Prometheus recording rules |
| Manual UID for datasources | Auto-generated UID when `uid:` missing | Always existed | Must explicitly set `uid:` in provisioning to get stable, referenceable UIDs |

**Deprecated/outdated:**
- `GF_ALERTING_ENABLED=true` env var: This controls the old legacy alerting (panel-level). Setting `GF_UNIFIED_ALERTING_ENABLED=true` is what controls the modern system — but in Grafana 10.4, unified alerting is on by default and cannot be disabled.

## Open Questions

1. **Alert rule content — what specific Loki queries are wanted?**
   - What we know: The phase title says "alert rules fail to load from Loki" implying rules should exist but don't
   - What's unclear: Which specific behaviors should be alerted (error rate threshold? specific log patterns?)
   - Recommendation: Create one representative alert rule (high error log rate via `count_over_time`) as proof-of-concept that the datasource and provisioning work end-to-end. The content is less important than proving the plumbing works.

2. **Should Promtail fix be in this phase or a separate phase?**
   - What we know: Without Promtail sending logs, any Loki alert rule will evaluate against empty streams (NoData state)
   - What's unclear: The phase title mentions "alert rules fail to load" — "fail to load" is a datasource/provisioning problem, not a data problem
   - Recommendation: Fix Promtail in this same phase since it's a single-line config change and without it the alert rule fix cannot be verified end-to-end.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.3 |
| Config file | `stock-prediction-platform/services/api/pytest.ini` |
| Quick run command | `cd stock-prediction-platform/services/api && python -m pytest tests/test_dashboard_json.py -x -q` |
| Full suite command | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LOKI-ALERT-01 | Loki datasource has explicit `uid: loki` in provisioning YAML | unit | `pytest tests/test_loki_alerting.py::test_loki_datasource_has_uid -x` | Wave 0 |
| LOKI-ALERT-02 | Grafana alerting ConfigMap exists and contains at least one rule group | unit | `pytest tests/test_loki_alerting.py::test_alerting_configmap_has_rules -x` | Wave 0 |
| LOKI-ALERT-03 | All alert rules referencing Loki use `datasourceUid: loki` | unit | `pytest tests/test_loki_alerting.py::test_alert_rules_use_stable_loki_uid -x` | Wave 0 |
| LOKI-ALERT-04 | Promtail __path__ replacement uses underscore separator (not slash) | unit | `pytest tests/test_loki_alerting.py::test_promtail_path_uses_underscore_separator -x` | Wave 0 |
| LOKI-ALERT-05 | Grafana deployment mounts alerting ConfigMap at provisioning path | unit | `pytest tests/test_loki_alerting.py::test_grafana_deployment_mounts_alerting_configmap -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform/services/api && python -m pytest tests/test_loki_alerting.py -x -q`
- **Per wave merge:** `cd stock-prediction-platform/services/api && python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `stock-prediction-platform/services/api/tests/test_loki_alerting.py` — covers LOKI-ALERT-01 through 05 (YAML structure tests, no cluster needed)

## Sources

### Primary (HIGH confidence)
- Live cluster: `kubectl exec grafana -- ls /etc/grafana/provisioning/alerting/` — confirmed empty directory
- Live cluster: `curl /api/datasources` on Grafana 10.4.0 — confirmed Loki UID is auto-generated `P8E80F9AEF21F6940`, Prometheus has stable `prometheus`
- Live cluster: `curl /api/v1/provisioning/alert-rules` on Grafana — confirmed `[]` (zero rules)
- Live cluster: `curl http://localhost:9080/targets` on Promtail — confirmed `0/0 ready`
- Live cluster: `kubectl exec promtail -- sh -c 'ls /var/log/pods/monitoring_grafana*/'` — confirmed real path uses `_` separator with UID suffix
- `stock-prediction-platform/k8s/monitoring/loki-configmap.yaml` — confirmed no `ruler:` section
- `stock-prediction-platform/k8s/monitoring/grafana-datasource-configmap.yaml` — confirmed Loki missing `uid:` field

### Secondary (MEDIUM confidence)
- Grafana 10.x provisioning documentation: alerting YAML schema with `apiVersion: 1`, `groups`, `rules`, `datasourceUid`
- Promtail Kubernetes service discovery documentation: standard `__path__` replacement pattern for `{namespace}_{pod}_{uid}/{container}/*.log`

### Tertiary (LOW confidence)
- None — all critical claims verified against live cluster or project YAML files

## Metadata

**Confidence breakdown:**
- Root cause analysis: HIGH — verified against live cluster (empty alerting dir, auto-generated UID, 0/0 promtail targets, broken path glob)
- Fix patterns: HIGH — Grafana provisioning schema is stable and documented; path glob fix is verified against actual filesystem layout
- Alert rule content: MEDIUM — the specific LogQL thresholds are examples; exact values depend on desired alert semantics

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (Grafana 10.4 provisioning schema stable; Loki 2.9.6 API stable)

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LOKI-ALERT-01 | Loki datasource has explicit stable `uid: loki` in grafana-datasource-configmap.yaml | Verified missing via live cluster API call; fix pattern documented |
| LOKI-ALERT-02 | grafana-alerting-configmap.yaml exists with at least one Loki-backed alert rule group | Confirmed no alerting ConfigMap exists; creation pattern documented with complete YAML |
| LOKI-ALERT-03 | Grafana deployment mounts alerting ConfigMap at /etc/grafana/provisioning/alerting | Confirmed provisioning dir is empty; volume mount pattern from existing dashboard mounts |
| LOKI-ALERT-04 | Promtail __path__ replacement uses correct `_` separator matching K8s pod log layout | Confirmed path bug via live filesystem inspection; correct glob pattern documented |
| LOKI-ALERT-05 | Grafana unified alerting UI shows the provisioned Loki rule in active/pending/firing state | Verified zero rules in Grafana API; achievable after all above fixes + pod restart |
</phase_requirements>
