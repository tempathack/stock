---
phase: 38-grafana-dashboards-alerting
plan: 01
subsystem: infra
tags: [prometheus, grafana, kubernetes, monitoring, rbac, configmap, deployment]

requires:
  - phase: 37-prometheus-metrics-instrumentation
    provides: metrics endpoints on api:8000/metrics and kafka-consumer:8001/metrics with pod annotations

provides:
  - Kubernetes monitoring namespace with label app.kubernetes.io/part-of: stock-prediction-platform
  - Prometheus RBAC (ServiceAccount, ClusterRole, ClusterRoleBinding) for cross-namespace pod scraping
  - Prometheus ConfigMap with 15s scrape interval, kubernetes-pods annotation-based discovery, alert_rules.yml placeholder
  - Prometheus Deployment (prom/prometheus:v2.51.0) with TSDB retention 15d, probes, 250m/256Mi requests
  - Prometheus ClusterIP Service on port 9090
  - Grafana datasources ConfigMap pointing to http://prometheus.monitoring.svc.cluster.local:9090
  - Grafana dashboard provider ConfigMap (file-based at /var/lib/grafana/dashboards)
  - Grafana Deployment (grafana/grafana:10.4.0) with provisioning mounts and dashboard JSON volume mounts
  - Grafana NodePort Service on port 30300
  - monitoring namespace added to k8s/namespaces.yaml
  - Phase 38 section in deploy-all.sh (apply monitoring stack, wait for rollouts)
  - Prometheus + Grafana services in docker-compose.yml for local dev

affects: [39-structured-logging, phase-62-infra-e2e-tests]

tech-stack:
  added: [prom/prometheus:v2.51.0, grafana/grafana:10.4.0]
  patterns:
    - annotation-based pod discovery (prometheus.io/scrape=true)
    - file-based Grafana dashboard provisioning via ConfigMap
    - separate monitoring namespace with RBAC for cross-namespace scraping

key-files:
  created:
    - stock-prediction-platform/k8s/monitoring/namespace.yaml
    - stock-prediction-platform/k8s/monitoring/prometheus-rbac.yaml
    - stock-prediction-platform/k8s/monitoring/prometheus-configmap.yaml
    - stock-prediction-platform/k8s/monitoring/prometheus-deployment.yaml
    - stock-prediction-platform/k8s/monitoring/prometheus-service.yaml
    - stock-prediction-platform/k8s/monitoring/grafana-datasource-configmap.yaml
    - stock-prediction-platform/k8s/monitoring/grafana-dashboards-configmap.yaml
    - stock-prediction-platform/k8s/monitoring/grafana-deployment.yaml
    - stock-prediction-platform/k8s/monitoring/grafana-service.yaml
  modified:
    - stock-prediction-platform/k8s/namespaces.yaml
    - stock-prediction-platform/scripts/deploy-all.sh
    - stock-prediction-platform/docker-compose.yml

key-decisions:
  - "Grafana port 3001:3000 in docker-compose to avoid conflict with frontend (port 3000 used by Loki grafana later changed to 3003)"
  - "annotation-based kubernetes-pods discovery instead of static_configs for zero-config scraping of any annotated pod"
  - "emptyDir for Prometheus TSDB (not PVC) — dev/local env, data loss acceptable on pod restart"
  - "GF_AUTH_ANONYMOUS_ENABLED=true for dev convenience, no auth needed in local Minikube"
  - "alert_rules.yml added as placeholder in Plan 01, populated with real rules in Plan 03"

requirements-completed: [MON-04, MON-05]

duration: 35min
completed: 2026-03-23
---

# Phase 38 Plan 01: Monitoring Namespace, Prometheus & Grafana Infrastructure Summary

**Kubernetes monitoring namespace with Prometheus annotation-based scraping and Grafana provisioning via ConfigMaps — zero-config dashboard loading on startup**

## Performance

- **Duration:** 35 min
- **Started:** 2026-03-23T10:00:00Z
- **Completed:** 2026-03-23T10:35:00Z
- **Tasks:** 11
- **Files modified:** 12

## Accomplishments
- Created monitoring namespace with RBAC allowing Prometheus to scrape pods across all namespaces
- Configured Prometheus annotation-based discovery (kubernetes-pods job) so any pod with `prometheus.io/scrape: "true"` is automatically scraped
- Grafana deployed with file-based provisioning — dashboards from Plan 02 load automatically on startup
- Both services added to deploy-all.sh and docker-compose.yml for K8s and local dev environments

## Task Commits

All tasks committed as part of the large batch commit:

1. **Task 1: namespace.yaml** — k8s/monitoring/namespace.yaml
2. **Task 2: prometheus-rbac.yaml** — ServiceAccount + ClusterRole + ClusterRoleBinding
3. **Task 3: prometheus-configmap.yaml** — prometheus.yml + alert_rules.yml placeholder
4. **Task 4: prometheus-deployment.yaml** — prom/prometheus:v2.51.0 with probes
5. **Task 5: prometheus-service.yaml** — ClusterIP on 9090
6. **Task 6: Grafana provisioning ConfigMaps** — datasource + dashboard provider
7. **Task 7: grafana-deployment.yaml** — grafana/grafana:10.4.0 with volume mounts
8. **Task 8: grafana-service.yaml** — NodePort 30300
9. **Task 9: namespaces.yaml** — added monitoring namespace block
10. **Task 10: deploy-all.sh** — Phase 38 section added
11. **Task 11: docker-compose.yml** — prometheus + grafana services

**Plan metadata:** `fdbe69c` (Phase 31-57 batch commit)

## Files Created/Modified
- `k8s/monitoring/namespace.yaml` — monitoring namespace with platform label
- `k8s/monitoring/prometheus-rbac.yaml` — ServiceAccount/ClusterRole/ClusterRoleBinding
- `k8s/monitoring/prometheus-configmap.yaml` — prometheus.yml with annotation-based discovery
- `k8s/monitoring/prometheus-deployment.yaml` — prom/prometheus:v2.51.0, 250m/256Mi
- `k8s/monitoring/prometheus-service.yaml` — ClusterIP port 9090
- `k8s/monitoring/grafana-datasource-configmap.yaml` — Prometheus datasource config
- `k8s/monitoring/grafana-dashboards-configmap.yaml` — file-based dashboard provider
- `k8s/monitoring/grafana-deployment.yaml` — grafana/grafana:10.4.0 with provisioning
- `k8s/monitoring/grafana-service.yaml` — NodePort 30300
- `k8s/namespaces.yaml` — added monitoring namespace after frontend
- `scripts/deploy-all.sh` — Phase 38 deployment section
- `docker-compose.yml` — prometheus + grafana services

## Decisions Made
- Used annotation-based Kubernetes pod discovery instead of static job configs — works for any future pod with `prometheus.io/scrape: "true"` without config changes
- emptyDir for Prometheus data storage (not PVC) — acceptable in Minikube dev environment
- Grafana anonymous access enabled for local dev convenience
- alert_rules.yml initially empty placeholder, populated by Plan 03

## Deviations from Plan
None — plan executed exactly as written.

## Issues Encountered
None.

## Next Phase Readiness
- Prometheus scrapes all annotated pods — Phase 37 API and Kafka consumer metrics are being collected
- Grafana auto-loads dashboards from /var/lib/grafana/dashboards via file provider
- Plan 02 (dashboard JSONs) can be applied immediately — Grafana provisioning picks them up on restart

---
*Phase: 38-grafana-dashboards-alerting*
*Completed: 2026-03-23*
