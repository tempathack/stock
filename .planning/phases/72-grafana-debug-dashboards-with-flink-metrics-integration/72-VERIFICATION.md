---
phase: 72-grafana-debug-dashboards-with-flink-metrics-integration
verified: 2026-03-31T00:00:00Z
status: human_needed
score: 6/6 must-haves verified
re_verification: false
human_verification:
  - test: "Open the Flink Stream Processing dashboard in Grafana while at least one Flink job is running"
    expected: "All 10 data panels show populated time-series or stat values — no 'No data' or 'Datasource not found' errors"
    why_human: "Requires a live cluster with Flink pods annotated for scraping; cannot simulate metric ingestion programmatically"
  - test: "Open the API Health, ML Performance, and Kafka dashboards in Grafana"
    expected: "No panels show 'Datasource not found' — all panels resolve the 'prometheus' UID correctly"
    why_human: "Grafana UID resolution only happens at runtime; the YAML is correct but the runtime binding cannot be verified without the running stack"
  - test: "Check Prometheus targets page (Status > Targets) for the flink-jobs job"
    expected: "flink-jobs job appears in the list; any Flink pods that have prometheus.io/scrape=true are shown as UP"
    why_human: "Kubernetes service discovery and pod annotation scraping can only be confirmed against a live cluster"
---

# Phase 72: Grafana Debug Dashboards with Flink Metrics Integration — Verification Report

**Phase Goal:** Fix Grafana dashboards to show data — add Prometheus Flink scrape job and pin datasource UIDs, then build a comprehensive 10-panel Flink debug dashboard.
**Verified:** 2026-03-31
**Status:** human_needed — all automated checks passed; runtime dashboard rendering requires human confirmation
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Prometheus has a `flink-jobs` scrape job targeting the flink namespace on port 9249 | VERIFIED | `prometheus-configmap.yaml` lines 103-133: `job_name: flink-jobs` with `kubernetes_sd_configs role: pod, namespaces: [flink]` |
| 2 | Grafana Prometheus datasource has a pinned UID of `prometheus` (lowercase) | VERIFIED | `grafana-datasource-configmap.yaml` line 12: `uid: prometheus` |
| 3 | Flink dashboard has 10+ data panels covering job uptime, restarts, checkpoints, throughput, watermarks, and JVM heap | VERIFIED | 10 data panels confirmed by JSON parse: Job Uptime, Job Restart Count, Completed Checkpoints, Records In/Out Per Second, Last Checkpoint Duration, Failed Checkpoints, Input Watermark, JVM Heap Used, Last Checkpoint Size |
| 4 | No panel in any dashboard shows a 'Datasource not found' error (UID consistency) | VERIFIED | API Health: 25 occurrences of `"uid": "prometheus"`; ML Perf: 22; Kafka: 22; Flink: consistent `"uid": "prometheus"` on all 10 data panels and their targets |
| 5 | Flink dashboard PromQL references `flink_jobmanager_*` and `flink_taskmanager_*` metrics | VERIFIED | 6 occurrences of `flink_jobmanager` in flink dashboard YAML; also `flink_taskmanager_*` metrics present |
| 6 | Dashboard JSON is structurally valid with 10 data panels under 5 section rows | VERIFIED | JSON parsed cleanly; 15 total panels = 5 rows + 10 data panels across sections: Job Overview, Throughput, Checkpointing, Watermarks, JVM Resources |

**Score:** 6/6 truths verified (automated)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `k8s/monitoring/prometheus-configmap.yaml` | flink-jobs scrape config under scrape_configs | VERIFIED | Lines 103-133: full scrape job with namespace filter, annotation-based pod discovery, port rewriting, and `flink_job` relabel |
| `k8s/monitoring/grafana-datasource-configmap.yaml` | Prometheus datasource with pinned UID `prometheus` | VERIFIED | Line 12: `uid: prometheus` under the Prometheus datasource block |
| `k8s/monitoring/grafana-dashboard-flink.yaml` | Full Flink dashboard with 10+ panels | VERIFIED | 10 data panels confirmed; contains `flink_jobmanager_job_lastCheckpointDuration` (plan artifact check); `"uid": "flink-stream"` for dashboard identity |
| `k8s/monitoring/grafana-dashboard-api-health.yaml` | API Health dashboard with `"uid": "prometheus"` datasource refs | VERIFIED | 25 occurrences of `"uid": "prometheus"` |
| `k8s/monitoring/grafana-dashboard-ml-perf.yaml` | ML Performance dashboard with `"uid": "prometheus"` datasource refs | VERIFIED | 22 occurrences of `"uid": "prometheus"` |
| `k8s/monitoring/grafana-dashboard-kafka.yaml` | Kafka dashboard with `"uid": "prometheus"` datasource refs | VERIFIED | 22 occurrences of `"uid": "prometheus"` |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `prometheus-configmap.yaml` | flink namespace pods | `kubernetes_sd_configs role: pod, namespaces: [flink]` | WIRED | Pattern `namespaces:` at line 106, `- flink` at line 108; annotation filter `prometheus_io_scrape: true` kept |
| `grafana-datasource-configmap.yaml` | Dashboard JSON datasource refs | `uid: prometheus` matches `"uid": "prometheus"` in dashboard JSON | WIRED | Datasource YAML has `uid: prometheus`; all four dashboards use `"uid": "prometheus"` in panel datasource objects |
| `grafana-dashboard-flink.yaml` | Prometheus flink-jobs scrape output | PromQL `flink_jobmanager_*` and `flink_taskmanager_*` expressions | WIRED | 6 `flink_jobmanager` references + `flink_taskmanager_job_task_numRecordsInPerSecond`, `flink_taskmanager_job_task_numRecordsOutPerSecond`, `flink_taskmanager_Status_JVM_Memory_Heap_Used` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status |
|-------------|-------------|-------------|--------|
| MON-04 | 72-01 | Prometheus scrapes Flink pods | SATISFIED — `flink-jobs` scrape job added with correct namespace and annotation-based pod discovery |
| MON-05 | 72-01, 72-02 | Grafana datasource UID is pinned and consistent | SATISFIED — `uid: prometheus` in datasource configmap; all four dashboards reference it consistently |
| MON-06 | 72-01, 72-02 | Flink dashboard shows data panels | SATISFIED — 10 data panels with real PromQL expressions covering all required metric categories |
| MON-07 | 72-02 | Other dashboards fixed for datasource UID consistency | SATISFIED — API Health, ML Perf, Kafka dashboards all updated with consistent `"uid": "prometheus"` |

---

## Anti-Patterns Found

None. Scanned all six modified files for TODO/FIXME/XXX/HACK/placeholder comments, empty return statements, and console.log-only implementations. No issues found.

---

## Human Verification Required

### 1. Flink Dashboard Panels Populate with Live Data

**Test:** Navigate to the "Apache Flink — Stream Processing" dashboard in Grafana while at least one Flink job is running in the cluster.
**Expected:** All 10 data panels (Job Uptime, Job Restart Count, Completed Checkpoints, Records In Per Second, Records Out Per Second, Last Checkpoint Duration, Failed Checkpoints, Input Watermark, TaskManager JVM Heap Used, Last Checkpoint Size) display populated values. No panel shows "No data" or "Datasource not found".
**Why human:** Requires a live cluster with Flink pods annotated `prometheus.io/scrape=true` and Prometheus actively scraping the flink namespace. PromQL metric existence cannot be verified statically.

### 2. Datasource UID Resolves at Runtime in All Four Dashboards

**Test:** Open API Health, ML Performance, and Kafka dashboards in Grafana.
**Expected:** All panels load without "Datasource not found" errors. The Prometheus datasource is correctly identified as "Prometheus" in the panel datasource dropdowns.
**Why human:** Grafana UID-to-datasource binding happens at runtime. Even though YAML is correct, mismatches in provisioning order or Grafana version behavior can only be caught with the running stack.

### 3. Prometheus Flink Targets Are Discovered and Healthy

**Test:** In Prometheus UI go to Status > Targets and find the `flink-jobs` job.
**Expected:** The job appears in the targets list. Any Flink pods with `prometheus.io/scrape=true` annotation show state UP. No DNS resolution errors.
**Why human:** Kubernetes service discovery requires a running cluster. The ConfigMap YAML is correct but network reachability (port 9249 open on Flink pods) cannot be verified statically.

---

## Summary

All six must-have artifacts exist, are substantive (non-stub), and are properly wired:

- `prometheus-configmap.yaml` has a complete `flink-jobs` scrape job (lines 103-133) with flink namespace scoping, annotation-based filtering, port rewriting to 9249 (via annotation), and a `flink_job` relabel rule.
- `grafana-datasource-configmap.yaml` pins the Prometheus datasource UID to the lowercase string `prometheus`, resolving the root-cause UID mismatch.
- `grafana-dashboard-flink.yaml` delivers exactly 10 data panels (no rows counted) organized across 5 section rows, with real PromQL expressions covering all metric families called out in the plan: uptime, restarts, checkpoints (completed/failed/duration/size), record throughput (in/out), watermarks, and JVM heap.
- All three other dashboards (API Health, ML Perf, Kafka) have been updated with consistent `"uid": "prometheus"` datasource references throughout.

No stubs, placeholders, orphaned artifacts, or anti-patterns were found. The three human verification items are runtime checks that cannot be automated without a live cluster.

---

_Verified: 2026-03-31_
_Verifier: Claude (gsd-verifier)_
