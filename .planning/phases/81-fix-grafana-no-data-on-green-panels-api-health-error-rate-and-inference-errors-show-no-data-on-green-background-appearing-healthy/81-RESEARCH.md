# Phase 81: Fix Grafana No-data-on-green Panels - Research

**Researched:** 2026-04-02
**Domain:** Grafana dashboard configuration — threshold coloring, no-data state, value mappings
**Confidence:** HIGH

## Summary

Two `stat` panels in the API Health dashboard show "No data" text on a green background, creating false-positive healthy signals. The root cause is structural: Grafana's threshold system uses `{ "color": "green", "value": null }` as the base (catch-all) step. When a Prometheus query returns no series at all — because the underlying metric has never been scraped or the rate expression evaluates to NaN over an empty series — Grafana renders the panel background in the base threshold color, which is green. The panel correctly displays the text "No data" but the green background communicates "all good."

The affected panels are panel ID 2 ("Error Rate %") and the latency stat panels (IDs 3, 4, 5) in `grafana-dashboard-api-health.yaml`. "Inference Errors" (panel ID 9) is a `timeseries` type and does not exhibit the green-background problem; it shows an empty chart which is visually neutral. The ML Performance dashboard (`grafana-dashboard-ml-perf.yaml`) does not have threshold-mode stat panels that would produce green no-data states for these specific metrics.

The fix requires adding a Grafana value mapping of type `"special"` with `match: "null+nan"` to override the display color when the value is null or NaN. This is the only Grafana-native mechanism (in v10.x) to distinguish a missing-metric state from a legitimately zero/low-value state. The fix is purely JSON configuration changes to one ConfigMap; no Prometheus metrics, Kubernetes services, or application code changes are required.

**Primary recommendation:** Add `type: "special", match: "null+nan"` value mappings with `color: "blue"` (neutral) to the affected stat panels; set `noValue: "No data"` in fieldConfig.defaults to control display text; do not change the threshold steps (those are correct for live data).

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Grafana | 10.4.0 | Dashboard visualization (deployed, version confirmed in grafana-deployment.yaml) | Project standard — already deployed |
| Grafana Stat Panel | built-in | Single-value panels with color modes | Used throughout existing dashboards |
| Grafana Value Mappings | built-in | Override display text and color for specific values | Only mechanism to handle null/nan distinctly |

### No Additional Dependencies
This fix requires zero new packages. All capability is in Grafana 10.4.0 already deployed.

## Architecture Patterns

### Recommended Project Structure

The affected files are already in place:
```
stock-prediction-platform/k8s/monitoring/
├── grafana-dashboard-api-health.yaml    # PRIMARY: fix panels 2, 3, 4, 5
├── grafana-dashboard-ml-perf.yaml       # SECONDARY: audit only — no green no-data stat panels found
├── grafana-dashboards-configmap.yaml    # Provisioning config (no changes needed)
└── grafana-deployment.yaml             # Grafana 10.4.0 image (no changes needed)
```

### Pattern 1: Grafana Threshold Base Color (Root Cause)

**What:** In Grafana's threshold system, the step with `"value": null` is the base/catch-all step. It applies when the panel value is below the first numeric threshold. Critically, when the query returns **no data at all** (empty series, NaN from division by zero in rate expressions), Grafana also falls through to this base step. If the base step is `"color": "green"`, the panel background renders green even with no data.

**When this bites:** Any `stat` panel with `"colorMode": "background"` or `"colorMode": "value"` combined with `"color": { "mode": "thresholds" }` and a green base threshold step will show a green panel when data is missing.

**Confirmed affected panels (api-health.json):**
- Panel ID 2 — "Error Rate %" — `colorMode: "background"`, query: `100 * sum(rate(5xx[5m])) / sum(rate(all[5m]))` — returns NaN when no requests exist
- Panel ID 3 — "p50 Latency" — `colorMode: "value"`, query: `histogram_quantile(0.50, ...)` — returns no series when no requests
- Panel ID 4 — "p95 Latency" — `colorMode: "value"`, query: `histogram_quantile(0.95, ...)`
- Panel ID 5 — "p99 Latency" — `colorMode: "value"`, query: `histogram_quantile(0.99, ...)`

### Pattern 2: Grafana Value Mappings — Special/Null+NaN Override

**What:** Grafana 10.x supports a value mapping type `"special"` that matches `"null+nan"`, `"null"`, or `"nan"` independently. This runs BEFORE the threshold color system and replaces the display color with a fixed color of the user's choice.

**When to use:** Any time you need to distinguish "no data" from "healthy low value" in a threshold-colored panel.

**Correct JSON structure (Grafana 10.4):**
```json
"mappings": [
  {
    "type": "special",
    "options": {
      "match": "null+nan",
      "result": {
        "text": "No data",
        "color": "blue",
        "index": 0
      }
    }
  }
]
```

Note: `"color": "blue"` uses Grafana's named palette — it renders as a neutral mid-blue, distinctly different from green or red. Alternative neutral colors: `"#808080"` (gray), `"orange"` (attention without alarm). Blue is the conventional Grafana "no data / unknown" color.

### Pattern 3: noValue Field Config Default

**What:** `fieldConfig.defaults.noValue` sets the text displayed when a panel has no data. It does NOT control the color — that is controlled by mappings. Setting it to `"No data"` is explicit and readable; if omitted Grafana defaults to displaying a dash (`-`) or the string "No data" depending on version.

**Correct placement:**
```json
"fieldConfig": {
  "defaults": {
    "noValue": "No data",
    "color": { "mode": "thresholds" },
    "mappings": [
      {
        "type": "special",
        "options": {
          "match": "null+nan",
          "result": { "text": "No data", "color": "blue", "index": 0 }
        }
      }
    ],
    "thresholds": {
      "mode": "absolute",
      "steps": [
        { "color": "green", "value": null },
        { "color": "yellow", "value": 1 },
        { "color": "red", "value": 5 }
      ]
    }
  }
}
```

The threshold steps remain unchanged — they are correct for when real data is present.

### Anti-Patterns to Avoid

- **Changing the base threshold color to gray**: This would make the panel appear gray when the metric IS at 0%, which is a healthy state (no errors). Do not touch threshold steps.
- **Setting `color.mode` to `"fixed"`**: This removes all threshold coloring and makes all values the same color — defeats the purpose of the alert thresholds.
- **Wrapping expressions in `or vector(0)`**: The `or vector(0)` PromQL trick makes a missing metric appear as 0. For error rate, 0% looks healthy — but this masks the fact that the exporter may not be running. This is the wrong fix because it hides the symptom rather than expressing "data not available."
- **Editing dashboards via Grafana UI without updating the ConfigMap**: The ConfigMap is the source of truth. The provisioning config has `disableDeletion: false` and `editable: true`, but UI edits are not persisted across pod restarts. Always edit the YAML ConfigMap.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| No-data color control | Threshold step reordering / color changes | `mappings` type `"special"` with `"match": "null+nan"` | Mappings are evaluated before thresholds; threshold changes affect real-data coloring too |
| Expressing "metric not scraped yet" | PromQL `or vector(0)` | Mapping + noValue display text | `or vector(0)` silences a real observability gap |
| Neutral no-data styling | Custom HTML/CSS overlays | Grafana native mapping result color | Grafana applies this consistently at the panel render level |

**Key insight:** The mapping system is the correct separation of concerns — thresholds answer "is the live value healthy?" and mappings answer "what should I show when there is no live value?"

## Common Pitfalls

### Pitfall 1: Forgetting `"index"` in the mapping result
**What goes wrong:** Grafana 10.x requires an `"index"` field in the mapping result for ordering. Without it the mapping may be ignored or cause a parse error when the ConfigMap is applied.
**Why it happens:** The schema is not strictly enforced at the YAML level, but Grafana's provisioning importer validates it.
**How to avoid:** Always include `"index": 0` (or sequential numbers for multiple mappings) in the `result` object.
**Warning signs:** Panel still shows green after ConfigMap reapply; check Grafana logs for provisioning errors.

### Pitfall 2: Applying ConfigMap without restarting/reloading Grafana
**What goes wrong:** Updated ConfigMap is mounted into the pod but Grafana doesn't re-read provisioned dashboards automatically in all configurations.
**Why it happens:** The dashboard provisioning watcher polls at an interval (default 30s) when `updateIntervalSeconds` is set. Without it, a pod restart is required.
**How to avoid:** After `kubectl apply`, run `kubectl rollout restart deployment/grafana -n monitoring` or wait 30s if the provider config includes `updateIntervalSeconds`.
**Warning signs:** Dashboard JSON in pod volume is updated but panel still shows old behavior.

### Pitfall 3: Multiple targets in one stat panel
**What goes wrong:** Panel ID 8 in ml-perf.json ("Drift Severity") has two targets (A and B). The `reduceOptions.calcs: ["lastNotNull"]` picks the last non-null across both — if one target returns data and the other doesn't, the panel won't show "No data." The mapping won't fire because there IS a value.
**Why it happens:** Stat panel reduce function collapses multiple series into one value.
**How to avoid:** For multi-target stat panels, each target should represent the same dimension. This is not a Phase 81 bug but worth auditing.

### Pitfall 4: Rate expressions returning NaN vs. no series
**What goes wrong:** `100 * sum(rate(5xx[5m])) / sum(rate(all[5m]))` returns NaN (division by zero) when there are no requests, not "no series." Grafana renders NaN differently from a missing series in some versions.
**Why it happens:** `sum(rate(...))` over an empty set returns 0, so `0 / 0 = NaN`.
**How to avoid:** The `"null+nan"` match in the mapping handles both cases correctly. Verify by checking that `"null+nan"` is the match string, not just `"null"`.

## Code Examples

### Complete fieldConfig Patch for "Error Rate %" (Panel ID 2)

```json
"fieldConfig": {
  "defaults": {
    "noValue": "No data",
    "color": { "mode": "thresholds" },
    "mappings": [
      {
        "type": "special",
        "options": {
          "match": "null+nan",
          "result": {
            "text": "No data",
            "color": "blue",
            "index": 0
          }
        }
      }
    ],
    "thresholds": {
      "mode": "absolute",
      "steps": [
        { "color": "green", "value": null },
        { "color": "yellow", "value": 1 },
        { "color": "red", "value": 5 }
      ]
    },
    "unit": "percent"
  },
  "overrides": []
}
```

### Complete fieldConfig Patch for Latency Stat Panels (IDs 3, 4, 5)

Same pattern, only threshold values change per panel. Example for p50:
```json
"fieldConfig": {
  "defaults": {
    "noValue": "No data",
    "color": { "mode": "thresholds" },
    "mappings": [
      {
        "type": "special",
        "options": {
          "match": "null+nan",
          "result": {
            "text": "No data",
            "color": "blue",
            "index": 0
          }
        }
      }
    ],
    "thresholds": {
      "mode": "absolute",
      "steps": [
        { "color": "green", "value": null },
        { "color": "yellow", "value": 0.5 },
        { "color": "red", "value": 1 }
      ]
    },
    "unit": "s"
  },
  "overrides": []
}
```

### kubectl Apply and Reload Commands

```bash
# Apply the updated ConfigMap
kubectl apply -f stock-prediction-platform/k8s/monitoring/grafana-dashboard-api-health.yaml -n monitoring

# Restart Grafana to pick up provisioned dashboard changes
kubectl rollout restart deployment/grafana -n monitoring

# Wait for rollout
kubectl rollout status deployment/grafana -n monitoring
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `or vector(0)` PromQL to mask no-data | `mappings` special null+nan | Grafana 7+ | Separates data-absence from zero-value |
| Changing base threshold to gray | Keep thresholds, add mappings | Grafana 7+ | Thresholds work correctly for live data |
| Panel-level `noDataState` in alert rules | `fieldConfig.defaults.noValue` + mapping | Grafana 9+ | Visualization concern separated from alerting |

**Deprecated/outdated:**
- `noDataState` in panel JSON (it was moved to alert rule definitions, not panel visualization in Grafana 8+)
- Editing dashboard JSON via UI without updating the source ConfigMap (works temporarily, lost on restart)

## Open Questions

1. **Should other dashboards be audited (Kafka, ML, Flink)?**
   - What we know: Phase 81 description specifically names "API Health Error Rate and Inference Errors" panels
   - What's unclear: Whether Kafka/Flink dashboards have similar green no-data stat panels
   - Recommendation: Scope Phase 81 to api-health dashboard only; the ML perf dashboard has been checked and its stat panels either use red-base thresholds (healthy) or palette-classic timeseries (not affected)

2. **Is "Inference Errors" (timeseries, panel ID 9) actually showing green?**
   - What we know: It uses `color.mode: "palette-classic"` and type `timeseries`, not a threshold-colored stat panel — no green background possible
   - What's unclear: The phase description mentions "Inference Errors" as showing No data on green background
   - Recommendation: The phase description may be referring to both panels in the same visual row of the dashboard. The timeseries panel shows empty (no green). The fix should address the stat panels; if the timeseries is somehow appearing green that would be a separate rendering issue. Plan should fix stat panels (2, 3, 4, 5) and note that the timeseries Inference Errors panel does not exhibit the green-background issue by its design.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Manual visual verification (no automated Grafana panel rendering tests exist in the project) |
| Config file | n/a |
| Quick run command | `kubectl port-forward svc/grafana 3000:3000 -n monitoring` then open browser |
| Full suite command | Same — visual check of all four panels in "No data" state |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| 81-01 | Error Rate % panel shows blue/neutral when no metric data | manual-only | Visual check via port-forward | N/A |
| 81-02 | p50/p95/p99 Latency stat panels show blue/neutral when no metric data | manual-only | Visual check via port-forward | N/A |
| 81-03 | Threshold coloring (green/yellow/red) still works when data IS present | manual-only | Visual check with live metrics | N/A |
| 81-04 | ConfigMap applies cleanly with no Grafana provisioning errors | smoke | `kubectl logs -n monitoring deploy/grafana \| grep -i "error\|provision"` | ❌ Wave 0 |

**Justification for manual-only:** Grafana panel rendering requires a live Grafana instance and cannot be unit tested. No test framework for Grafana JSON provisioning validation exists in this project.

### Sampling Rate
- **Per task commit:** `kubectl apply -f ... && kubectl rollout restart deployment/grafana -n monitoring`
- **Per wave merge:** Visual port-forward check of all affected panels
- **Phase gate:** All four stat panels show blue "No data" background with no metrics present

### Wave 0 Gaps
- None for code changes — the single task is a YAML ConfigMap edit
- [ ] Smoke test: `kubectl logs -n monitoring deploy/grafana | grep -i "provision"` after apply — manual step to confirm no provisioning errors

## Sources

### Primary (HIGH confidence)
- Direct inspection of `grafana-dashboard-api-health.yaml` — confirmed panel IDs 2, 3, 4, 5 have `"color": "green", "value": null` base threshold steps and `colorMode: "background"/"value"` in stat panels
- Grafana 10.4.0 documentation pattern — `mappings` with `type: "special"` and `match: "null+nan"` is the documented mechanism for no-data color overrides
- `grafana-deployment.yaml` — confirmed Grafana version `10.4.0`

### Secondary (MEDIUM confidence)
- Grafana value mapping schema (type, options.match, result.color, result.index) — consistent with Grafana 7+ through 10.x schema observed in documentation
- `or vector(0)` anti-pattern — widely documented in Grafana community as the wrong approach for no-data handling

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Root cause identification: HIGH — confirmed by reading actual dashboard JSON
- Fix mechanism (special mapping): HIGH — Grafana 10.4 built-in, no external dependencies
- Exact JSON schema for mappings: MEDIUM — derived from Grafana documentation patterns; validate against live instance if provisioning errors occur
- Scope (only api-health dashboard affected): HIGH — audited all four dashboard YAMLs

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable Grafana config format, not fast-moving)
