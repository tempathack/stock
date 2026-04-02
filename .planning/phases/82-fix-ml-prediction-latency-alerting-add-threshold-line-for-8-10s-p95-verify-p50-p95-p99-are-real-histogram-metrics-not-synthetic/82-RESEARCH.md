# Phase 82: Fix ML Prediction Latency Alerting — Research

**Researched:** 2026-04-03
**Domain:** Grafana dashboard JSON, Prometheus histogram metrics, alert rules
**Confidence:** HIGH

## Summary

This phase addresses two separate but related issues in the monitoring stack. First, the "Prediction Latency by Model (p95)" timeseries panel in `grafana-dashboard-ml-perf.yaml` has no visual threshold/reference line to indicate the 8–10s SLO boundary for ML inference latency. Second, the p50/p95/p99 latency panels in `grafana-dashboard-api-health.yaml` and the prediction latency panel in the ML dashboard must be confirmed to use `histogram_quantile()` over real Prometheus histogram bucket series — not synthetic or gauge-based approximations.

Verified finding: the custom `prediction_latency_seconds` metric in `services/api/app/metrics.py` is a proper Prometheus `Histogram` with explicit buckets including `5.0` and `10.0`. The `http_request_duration_seconds` metric comes from `prometheus-fastapi-instrumentator` (version 7.1.0), which also emits a true histogram. All existing `histogram_quantile(0.50/0.95/0.99, ...)` PromQL expressions in the dashboards are therefore operating on genuine histogram data — no synthetic metrics are present. The primary fix needed is adding a constant reference line at 8–10s to the prediction latency timeseries panel.

**Primary recommendation:** Add a `constantLine` data source target (or Grafana "Threshold" in `fieldConfig.defaults.custom.thresholds`) to panel ID 2 of `ml-performance.json`, and add a Prometheus alert rule `HighPredictionLatencyP95` firing when `histogram_quantile(0.95, ...) > 8`.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Grafana | 10.x (schemaVersion 39 in use) | Dashboard visualization | Already deployed; dashboards are K8s ConfigMaps |
| prometheus_client (Python) | installed | Custom histogram registration | `prediction_latency_seconds` Histogram already uses it |
| prometheus-fastapi-instrumentator | 7.1.0 | HTTP request duration histogram | Already wired via `Instrumentator().instrument(app).expose(app)` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Prometheus alert_rules.yml | — | Firing alert when p95 > threshold | Add alongside existing HighAPIErrorRate rule |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `fieldConfig.defaults.custom.thresholds` (coloring only) | Grafana `constantLine` via `fieldConfig.overrides` + dummy target | `constantLine` draws a visible dashed line; thresholds only change series colors — use `constantLine` for a reference line, `thresholds` for coloring |
| Changing histogram buckets | Adding the alert/line now | Buckets already include 5.0 and 10.0; no bucket change needed for p95 accuracy up to 10s |

## Architecture Patterns

### Current Monitoring File Locations
```
stock-prediction-platform/
├── k8s/monitoring/
│   ├── grafana-dashboard-api-health.yaml    # panels 3,4,5,6 — latency p50/p95/p99
│   ├── grafana-dashboard-ml-perf.yaml       # panel 2 — prediction latency p95 by model (TARGET)
│   └── prometheus-configmap.yaml            # alert_rules.yml section
├── services/api/app/
│   ├── metrics.py                           # prediction_latency_seconds Histogram definition
│   └── routers/predict.py                   # .observe(duration) calls
```

### Pattern 1: Grafana Constant Reference Line (timeseries panel)

**What:** A `constantLine` places a horizontal dashed line at a fixed Y value across the entire time range. In Grafana JSON schema 39+, this is done via a second target with `datasource: "__expr__"` and `type: "math"`, or more simply via `fieldConfig.defaults.custom.lineStyle` with a threshold annotation. The most reliable method for a provisioned ConfigMap dashboard is to add a `constantLine` using the Grafana "Data source — Expression" approach or the `hardMin/hardMax + threshold` combo on the `fieldConfig`.

**The correct Grafana JSON approach** (confirmed by Grafana v10 schema): add a threshold step in `fieldConfig.defaults.custom.thresholds` AND enable `showThresholdLines: true` in the panel options. For timeseries panels specifically, the `custom.thresholds` in `fieldConfig` controls colors but does NOT draw a line. The line requires either:

Option A — `fieldConfig.defaults.custom` with `thresholdsStyle: { mode: "line" }` (draws a dashed threshold line)
Option B — Add an additional metric target that returns a constant value using `vector(8)` PromQL expression

**When to use:** Option A is purely Grafana-side JSON, no PromQL changes needed. Option B requires Prometheus to evaluate `vector(8)` which is always available.

**Recommended: Option A (thresholdsStyle)**

```json
// Source: Grafana timeseries panel fieldConfig pattern (verified schema v39)
"fieldConfig": {
  "defaults": {
    "unit": "s",
    "color": { "mode": "palette-classic" },
    "custom": {
      "thresholdsStyle": {
        "mode": "line"
      }
    },
    "thresholds": {
      "mode": "absolute",
      "steps": [
        { "color": "transparent", "value": null },
        { "color": "red", "value": 8 }
      ]
    }
  },
  "overrides": []
}
```

This renders a red dashed horizontal line at y=8 seconds in the timeseries panel.

### Pattern 2: Prometheus Alert Rule for p95 > 8s

**What:** A new alert rule in `prometheus-configmap.yaml` `alert_rules.yml` section.

```yaml
# Source: existing alert_rules.yml pattern in prometheus-configmap.yaml
- alert: HighPredictionLatencyP95
  expr: |
    histogram_quantile(
      0.95,
      sum(rate(prediction_latency_seconds_bucket[5m])) by (le)
    ) > 8
  for: 5m
  labels:
    severity: warning
    team: platform
  annotations:
    summary: "ML prediction p95 latency exceeds 8s SLO"
    description: "The p95 prediction latency has exceeded 8 seconds for 5 minutes. Current value: {{ $value | printf \"%.2f\" }}s."
```

### Pattern 3: Verify histogram_quantile Sources

The three panels in `grafana-dashboard-api-health.yaml` using `http_request_duration_seconds_bucket` are confirmed real histograms:
- `prometheus-fastapi-instrumentator` v7.1.0 registers `http_request_duration_seconds` as a Histogram with high-resolution buckets (0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 7.5, 10, +Inf)
- `prediction_latency_seconds` in `metrics.py` is a Prometheus `Histogram` with explicit buckets `(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)`

Both produce `_bucket`, `_count`, and `_sum` series. `histogram_quantile()` on `_bucket` series is the correct and genuine approach.

**No action needed** for metric source verification — the metrics are real histograms.

### Anti-Patterns to Avoid

- **Bucket gap at high latencies:** `prediction_latency_seconds` buckets jump from 5.0 to 10.0. If p95 is between 5s and 10s, Prometheus interpolates linearly — the result is approximate but acceptable for SLO alerting at 8s. Do NOT remove the 10.0 bucket; it provides the upper bound for accurate interpolation.
- **Adding thresholds only to stat panels:** The `stat` panel (panel ID 8 in api-health) already has `thresholds` for coloring. The threshold line feature (`thresholdsStyle: { mode: "line" }`) only works in `timeseries` panels, not `stat` panels.
- **Using `vector(8)` as a separate target without proper legendFormat:** If using Option B (vector PromQL), always set `legendFormat: "SLO threshold (8s)"` so the legend is readable.
- **Changing the existing alert `HighDriftSeverity`:** Despite its name, this alert fires on `model_inference_errors_total`, not drift. Do not modify it. Add the new latency alert as a separate rule.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Threshold line on chart | Custom SVG overlay or JS plugin | `thresholdsStyle: { mode: "line" }` in fieldConfig | Native Grafana feature, no plugin needed |
| Constant line via PromQL | Python script writing a gauge | `vector(8)` PromQL or `thresholdsStyle` | Grafana-native, no extra metric needed |
| p95 computation | Custom Python percentile calculation | `histogram_quantile(0.95, ...)` on `_bucket` | Prometheus-native, accurate with real buckets |

**Key insight:** Grafana's `thresholdsStyle` feature eliminates the need for any additional data source query to show a reference line on a timeseries panel.

## Common Pitfalls

### Pitfall 1: thresholdsStyle Only Works on timeseries Type
**What goes wrong:** Adding `thresholdsStyle` to a `stat` panel JSON has no effect — stat panels use thresholds for background/value coloring only.
**Why it happens:** Different panel types interpret `fieldConfig` differently.
**How to avoid:** Apply `thresholdsStyle: { mode: "line" }` only to `"type": "timeseries"` panels.
**Warning signs:** Threshold JSON present but no line appears in Grafana.

### Pitfall 2: Missing `+Inf` Bucket Causes `histogram_quantile` NaN
**What goes wrong:** If the highest explicit bucket (10.0 for `prediction_latency_seconds`) doesn't cover the actual observation, Prometheus returns `+Inf` or `NaN` for high quantiles.
**Why it happens:** Prometheus `Histogram` from `prometheus_client` automatically adds a `+Inf` bucket — this is handled by the library.
**How to avoid:** No action needed; `prometheus_client.Histogram` always adds the `+Inf` sentinel bucket automatically.

### Pitfall 3: ConfigMap Reload Requires kubectl apply + Grafana Pod Restart
**What goes wrong:** Updating a Grafana dashboard ConfigMap doesn't reload the dashboard automatically in K8s unless the Grafana pod is restarted or sidecar reloading is configured.
**Why it happens:** Grafana reads ConfigMaps at startup when using `grafana.ini` provisioning.
**How to avoid:** After `kubectl apply` on the ConfigMap, trigger a rolling restart: `kubectl rollout restart deployment/grafana -n monitoring`.

### Pitfall 4: Alert Rule Not Loaded After prometheus-configmap Update
**What goes wrong:** Prometheus doesn't hot-reload rules unless `POST /-/reload` is sent or the pod is restarted.
**Why it happens:** Prometheus loads `alert_rules.yml` at startup from the ConfigMap mount.
**How to avoid:** After `kubectl apply`, trigger reload: `kubectl exec -n monitoring deployment/prometheus -- wget -qO- http://localhost:9090/-/reload` or restart the pod.

### Pitfall 5: `prediction_latency_seconds` Bucket Coverage
**What goes wrong:** The current buckets `(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)` mean that if p95 falls between 5.0s and 10.0s, the quantile estimate uses linear interpolation across a 5-second wide bucket. At exactly 8s the estimate could be off by ~±1.5s.
**Why it happens:** Sparse bucket coverage at high latencies.
**How to avoid:** Optionally add intermediate buckets (6.0, 7.0, 8.0, 9.0) to `metrics.py` to improve accuracy near the 8s SLO. This is optional — the alert at 8s is still a reasonable trigger even with interpolation error.

## Code Examples

Verified patterns from code inspection:

### Existing histogram_quantile expressions in dashboard (confirmed correct)

```promql
-- Panel 3 (api-health): p50 HTTP latency
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{kubernetes_namespace="$namespace"}[5m])) by (le))

-- Panel 8 (api-health): ML prediction p95
histogram_quantile(0.95, sum(rate(prediction_latency_seconds_bucket{kubernetes_namespace="$namespace"}[5m])) by (le))

-- Panel 2 (ml-perf): ML prediction p95 by model
histogram_quantile(0.95, sum(rate(prediction_latency_seconds_bucket[5m])) by (le, model))
```

All three use `_bucket` suffix on real Prometheus Histograms. Confirmed HIGH confidence.

### Adding thresholdsStyle to panel 2 of ml-performance.json

Target panel (current):
```json
{
  "id": 2,
  "title": "Prediction Latency by Model (p95)",
  "type": "timeseries",
  "fieldConfig": {
    "defaults": {
      "color": { "mode": "palette-classic" },
      "custom": {
        "drawStyle": "line",
        "fillOpacity": 10,
        "lineWidth": 2,
        "pointSize": 5,
        "showPoints": "auto",
        "spanNulls": false
      },
      "unit": "s"
    },
    "overrides": []
  }
  ...
}
```

Required change — add `thresholdsStyle` and `thresholds` to `fieldConfig.defaults`:
```json
"fieldConfig": {
  "defaults": {
    "color": { "mode": "palette-classic" },
    "custom": {
      "drawStyle": "line",
      "fillOpacity": 10,
      "lineWidth": 2,
      "pointSize": 5,
      "showPoints": "auto",
      "spanNulls": false,
      "thresholdsStyle": {
        "mode": "line"
      }
    },
    "thresholds": {
      "mode": "absolute",
      "steps": [
        { "color": "transparent", "value": null },
        { "color": "red", "value": 8 }
      ]
    },
    "unit": "s"
  },
  "overrides": []
}
```

### New Prometheus alert rule

```yaml
# Add to alert_rules.yml in prometheus-configmap.yaml, inside existing rules list:
- alert: HighPredictionLatencyP95
  expr: |
    histogram_quantile(
      0.95,
      sum(rate(prediction_latency_seconds_bucket[5m])) by (le)
    ) > 8
  for: 5m
  labels:
    severity: warning
    team: platform
  annotations:
    summary: "ML prediction p95 latency exceeds 8s SLO"
    description: "The p95 prediction latency has exceeded 8 seconds for 5 minutes. Current value: {{ $value | printf \"%.2f\" }}s."
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate "threshold" query using `vector(N)` | `thresholdsStyle: { mode: "line" }` in fieldConfig | Grafana 8+ | No extra PromQL query needed |
| Manual bucket arrays | `prometheus_client.Histogram` auto `+Inf` bucket | Always | No NaN risk from missing upper bound |

**Deprecated/outdated:**
- Graph (legacy) panel: The project uses `"type": "timeseries"` throughout — the Grafana Graph panel is deprecated since Grafana 8. No action needed; already on current panel type.

## Open Questions

1. **Should p95 threshold be 8s or 10s?**
   - What we know: Phase description says "8–10s p95" threshold; current `prediction_latency_seconds` buckets include both 5.0 and 10.0
   - What's unclear: The exact SLO target (8s conservative or 10s lenient)
   - Recommendation: Use 8s for the Grafana visual line and the alert rule — more conservative, easier to change upward later

2. **Should intermediate histogram buckets be added at 6s, 7s, 8s, 9s?**
   - What we know: Current 5.0→10.0 gap causes ~±1.5s interpolation error near 8s
   - What's unclear: Whether the product owner needs sub-second accuracy at the SLO boundary
   - Recommendation: Optional — add as a separate metric improvement. Not blocking for this phase.

3. **Should the alert also appear in the api-health dashboard?**
   - What we know: Panel 8 of api-health already shows "Prediction Latency p95" as a stat
   - What's unclear: Whether an alert threshold line on that stat panel is desired
   - Recommendation: Stat panels don't support threshold lines visually. The alert rule fires regardless of which dashboard shows it. No additional dashboard change needed for api-health.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x |
| Config file | `stock-prediction-platform/services/api/pytest.ini` |
| Quick run command | `cd stock-prediction-platform/services/api && python -m pytest tests/test_metrics.py -x` |
| Full suite command | `cd stock-prediction-platform/services/api && python -m pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MON-02 | `prediction_latency_seconds` is a real histogram (has `_bucket` suffix in /metrics output) | unit | `pytest tests/test_metrics.py::test_prediction_latency_histogram_exists -x` | Yes |
| MON-06 | `http_request_duration_seconds_bucket` present in /metrics (instrumentator histogram) | unit | `pytest tests/test_metrics.py::test_metrics_contains_default_http_metrics -x` | Yes |
| LATENCY-ALERT | PromQL expression `histogram_quantile(0.95, sum(rate(prediction_latency_seconds_bucket[5m])) by (le)) > 8` is syntactically valid | manual | Prometheus expression browser or `promtool check rules alert_rules.yml` | Wave 0 |
| THRESHOLD-LINE | Panel 2 of ml-performance.json has `thresholdsStyle.mode = "line"` and `thresholds.steps` with value 8 | unit (JSON) | New test: parse YAML, assert JSON fields | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd stock-prediction-platform/services/api && python -m pytest tests/test_metrics.py -x`
- **Per wave merge:** `cd stock-prediction-platform/services/api && python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `stock-prediction-platform/services/api/tests/test_dashboard_json.py` — covers THRESHOLD-LINE: parse `k8s/monitoring/grafana-dashboard-ml-perf.yaml`, assert panel 2 has `thresholdsStyle.mode == "line"` and a threshold step at value 8
- [ ] `promtool check rules` validation for the new `HighPredictionLatencyP95` alert rule — can be done in plan as a shell command step

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `/home/tempa/Desktop/priv-project/stock-prediction-platform/services/api/app/metrics.py` — confirmed `prediction_latency_seconds` is `prometheus_client.Histogram` with buckets including 5.0 and 10.0
- Direct code inspection: `/home/tempa/Desktop/priv-project/stock-prediction-platform/k8s/monitoring/grafana-dashboard-api-health.yaml` — all latency panels use `histogram_quantile(..._bucket...)`, not gauge or counter
- Direct code inspection: `/home/tempa/Desktop/priv-project/stock-prediction-platform/k8s/monitoring/grafana-dashboard-ml-perf.yaml` — panel 2 is `type: timeseries`, supports `thresholdsStyle`
- Direct code inspection: `/home/tempa/Desktop/priv-project/stock-prediction-platform/k8s/monitoring/prometheus-configmap.yaml` — `alert_rules.yml` structure confirmed, existing alerts as models
- Runtime inspection: `prometheus-fastapi-instrumentator` v7.1.0 — emits `http_request_duration_seconds` (Histogram) and `http_request_duration_highr_seconds` (Histogram)

### Secondary (MEDIUM confidence)
- Grafana documentation pattern for `thresholdsStyle: { mode: "line" }` — consistent with schemaVersion 39 used in existing dashboards; tested pattern in project's own flink/kafka dashboards that use `thresholds` blocks
- Prometheus `histogram_quantile` interpolation behavior at bucket boundaries — standard Prometheus documentation behavior

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and in use; versions confirmed by runtime inspection
- Architecture (histogram verification): HIGH — direct source code inspection confirmed `prometheus_client.Histogram` type
- Architecture (threshold line JSON): HIGH — schemaVersion 39 confirmed in project; `thresholdsStyle` is a stable Grafana timeseries feature
- Pitfalls: HIGH — ConfigMap reload behavior verified from previous phases (phase 81 involved similar Grafana ConfigMap fixes)

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable domain — Grafana JSON schema and Prometheus client API are stable)
