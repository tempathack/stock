# Phase 59: Minikube E2E Validation — Research

**Researched:** 2026-03-24
**Domain:** Kubernetes / Minikube orchestration, KServe InferenceService, MinIO S3, end-to-end ML pipeline validation
**Confidence:** HIGH — all findings derived directly from reading the actual project source files

---

## Summary

Phase 59 closes the four human-verification items left open in Phase 57's VERIFICATION.md. The cluster is currently STOPPED (confirmed via `minikube status`). The full bootstrap sequence involves: start Minikube, run `setup-minikube.sh`, create secrets, run `deploy-all.sh`, build Docker images into Minikube's Docker daemon, then manually trigger the ingest and training CronJobs to produce a model artifact in MinIO so KServe can serve it.

The two secret files that `deploy-all.sh` requires (`k8s/storage/secrets.yaml` and `k8s/storage/minio-secrets.yaml`) do NOT exist on disk — only `.yaml.example` templates are present. These must be created with real credentials before the deploy script can proceed. The KServe S3 secret (`k8s/ml/kserve/kserve-s3-secret.yaml`) DOES already exist.

All five namespaces (`ingestion`, `processing`, `storage`, `ml`, `frontend`, `monitoring`) are defined in `k8s/namespaces.yaml`. The Strimzi Kafka operator is deployed by `setup-minikube.sh`; all workloads are deployed by `deploy-all.sh`. The `ingestion-config` ConfigMap already has `KSERVE_ENABLED: "true"` in `k8s/ingestion/configmap.yaml`, so the K8s API deployment is correctly wired for KServe from the start.

**Primary recommendation:** Run `setup-minikube.sh` → create missing secrets → run `deploy-all.sh` → build Docker images → `kubectl create job --from=cronjob/historical-ingestion` → `kubectl create job --from=cronjob/weekly-training` → verify MinIO artifact → confirm KServe InferenceService Ready → `curl /predict/AAPL`.

---

## Infrastructure Map

### Namespaces (from k8s/namespaces.yaml)
| Namespace | Purpose |
|-----------|---------|
| `ingestion` | FastAPI stock-api, ingest CronJobs |
| `processing` | Kafka consumer (batch DB writer) |
| `storage` | PostgreSQL/TimescaleDB, MinIO, Redis, Kafka |
| `ml` | Training CronJob, Drift CronJob, KServe InferenceService |
| `frontend` | React app |
| `monitoring` | Prometheus, Grafana, Loki, Promtail |

### Bootstrap Scripts
| Script | What it does | When to run |
|--------|-------------|-------------|
| `scripts/setup-minikube.sh` | Start Minikube (6 CPU, 12GB, `--addons=ingress,metrics-server,dashboard`), wait for node Ready, apply namespaces, create PostgreSQL secret (dev), apply Strimzi operator, wait 300s for Strimzi pod Ready | Step 1 — once per fresh cluster |
| `scripts/deploy-all.sh` | Applies every manifest in order: namespaces → secrets → PostgreSQL → RBAC → backup → MinIO → cert-manager → KServe → InferenceService → Phase 57 cleanup → Kafka → CronJobs (ingest) → Kafka consumer (build image) → ML pipeline (build image) → Frontend (build image) → Monitoring | Step 2 — after setup-minikube.sh |
| `scripts/seed-data.sh` | Direct psql to populate stocks, ohlcv_daily, ohlcv_intraday, model_registry, predictions, drift_logs | Optional — populates DB for frontend smoke testing WITHOUT needing a full train run |

---

## Critical Pre-conditions

### Secrets That Must Exist Before deploy-all.sh

`deploy-all.sh` exits with error (line 53 and line 98) if these files are absent:

| File | Template | Contents Needed |
|------|----------|-----------------|
| `k8s/storage/secrets.yaml` | `secrets.yaml.example` | `POSTGRES_PASSWORD`, `DATABASE_URL`, `DATABASE_URL_READONLY`, `DATABASE_URL_WRITER` (all base64) |
| `k8s/storage/minio-secrets.yaml` | `minio-secrets.yaml.example` | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` (base64) |

`k8s/ml/kserve/kserve-s3-secret.yaml` already exists (no need to create).

The KServe S3 secret annotations point to MinIO at `minio.storage.svc.cluster.local:9000` with `s3-usehttps: "0"` and `s3-verifyssl: "0"` — correct for in-cluster MinIO.

### Docker Images That Must Be Built Into Minikube Docker Daemon

All deployments use `imagePullPolicy: Never` — images must be built inside Minikube's Docker context:

| Image | Dockerfile Location | deploy-all.sh step |
|-------|--------------------|--------------------|
| `stock-kafka-consumer:latest` | `services/kafka-consumer/` | Phase 9 block |
| `stock-ml-pipeline:latest` | `ml/Dockerfile` (context: project root) | Phase 33 block |
| `stock-frontend:latest` | `services/frontend/` | Phase 25 block |
| `stock-api:latest` | Built separately — NOT in deploy-all.sh | Must be built manually before deploy |

`deploy-all.sh` runs `eval $(minikube docker-env)` before each build to switch Docker context. The `stock-api` image is used by `k8s/ingestion/fastapi-deployment.yaml` and `k8s/ingestion/cronjob-historical.yaml` but is NOT built in `deploy-all.sh` — this is a gap that the plan must address.

---

## Deployment Sequence (from deploy-all.sh analysis)

```
1.  setup-minikube.sh
      └─ minikube start (6cpu, 12GB, ingress + metrics-server + dashboard)
      └─ kubectl wait node Ready (120s)
      └─ kubectl apply namespaces.yaml
      └─ kubectl apply strimzi-operator.yaml (in storage ns)
      └─ kubectl wait strimzi pod Ready (300s)

2.  Create secrets (manual step — files don't exist yet):
      k8s/storage/secrets.yaml         (from secrets.yaml.example)
      k8s/storage/minio-secrets.yaml   (from minio-secrets.yaml.example)

3.  deploy-all.sh
      Phase 2:  namespaces
      Phase 3:  ingestion-config ConfigMap + stock-api Deployment + Service
      Phase 36: secrets → copy to ingestion/processing/ml namespaces
      Phase 4:  PostgreSQL PVC + Deployment → wait 120s → RBAC SQL
      Phase 41: backup PVC + CronJob
      Phase 51: minio-secrets + ConfigMap + PVC + Deployment → wait 120s
                minio-init-job (creates model-artifacts + drift-logs buckets) → wait 60s
                copy minio secret+config to ml namespace
      Phase 54: cert-manager (from internet) → wait 180s ×3 deployments
                KServe (from internet) → wait 180s
                kserve-cluster-resources (from internet)
                patch inferenceservice-config → RawDeployment
                kserve-s3-secret.yaml + kserve-s3-sa.yaml
                sklearn-serving-runtime.yaml
      Phase 55: kserve-inference-service.yaml
                kserve-inference-service-canary.yaml
                → kubectl wait InferenceService Ready (300s)  ← WILL FAIL without model in MinIO
      Phase 57: delete legacy model-serving deployment if exists
      Phase 5:  kafka-cluster.yaml + kafka-topics.yaml (Strimzi CRs)
      Phase 8:  ingest CronJobs (historical + intraday)
      Phase 9:  eval $(minikube docker-env) && docker build kafka-consumer
                kafka-consumer-deployment.yaml → rollout status 120s
      Phase 33: eval $(minikube docker-env) && docker build ml-pipeline
      Phase 34: model-pvc + ml configmap + cronjob-training + cronjob-drift + cronjob-feature-store
      Phase 25: eval $(minikube docker-env) && docker build frontend
                frontend deployment + service → rollout status 120s
      Phase 38: Prometheus + Grafana
      Phase 39: Loki + Promtail
```

### Known Timing Issue: KServe waits for model before training

At Phase 55, `deploy-all.sh` runs:
```bash
kubectl wait --for=condition=Ready inferenceservice/stock-model-serving -n ml --timeout=300s
```
KServe will NOT become Ready until `s3://model-artifacts/serving/active/` contains a valid `model-settings.json` and `model.joblib` (or equivalent sklearn artifact). On a fresh cluster with no model artifact in MinIO, this wait will time out.

**Options for the plan:**
1. Use `--ignore-not-found` approach: skip the wait in deploy-all.sh on first run, proceed without it, run ingest+train first, then apply InferenceService
2. OR: modify deploy-all.sh to not block on InferenceService Ready during initial deploy
3. OR: run seed-data.sh to populate DB → trigger training → wait for MinIO artifact → then re-apply/wait InferenceService

The plan should address this sequencing problem explicitly.

---

## Manual CronJob Triggering

The CronJob names and namespaces (verified from manifests):

| CronJob | Namespace | Schedule | Manual trigger command |
|---------|-----------|----------|----------------------|
| `historical-ingestion` | `ingestion` | `0 2 * * 0` | `kubectl create job --from=cronjob/historical-ingestion manual-ingest-59 -n ingestion` |
| `intraday-ingestion` | `ingestion` | (separate) | `kubectl create job --from=cronjob/intraday-ingestion manual-intraday-59 -n ingestion` |
| `weekly-training` | `ml` | `0 3 * * 0` | `kubectl create job --from=cronjob/weekly-training manual-train-59 -n ml` |
| `daily-drift` | `ml` | `0 22 * * 1-5` | `kubectl create job --from=cronjob/daily-drift manual-drift-59 -n ml` |
| `feature-store` | `ml` | daily | `kubectl create job --from=cronjob/feature-store manual-fs-59 -n ml` |

Wait for completion:
```bash
kubectl wait --for=condition=complete job/manual-train-59 -n ml --timeout=600s
```

---

## E2E Flow Sequence (from Phase 57 VERIFICATION.md human_verification items)

```
1. Seed DB (optional shortcut) OR ingest real data:
   kubectl create job --from=cronjob/historical-ingestion manual-ingest-59 -n ingestion
   kubectl wait --for=condition=complete job/manual-ingest-59 -n ingestion --timeout=600s

2. Trigger training:
   kubectl create job --from=cronjob/weekly-training manual-train-59 -n ml
   kubectl wait --for=condition=complete job/manual-train-59 -n ml --timeout=600s

3. Verify MinIO artifact:
   MINIO_POD=$(kubectl get pod -n storage -l app=minio -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n storage $MINIO_POD -- mc ls local/model-artifacts/serving/active/
   # Must see model-settings.json and model.joblib

4. Verify KServe InferenceService Ready:
   kubectl get inferenceservice stock-model-serving -n ml
   # READY = True, URL populated

5. Test predict endpoint:
   API_IP=$(kubectl get svc stock-api -n ingestion -o jsonpath='{.spec.clusterIP}')
   curl http://$API_IP:8000/predict/AAPL
   # Expected: {"predicted_price": <float>, "ticker": "AAPL", ...}

6. Drift path:
   kubectl create job --from=cronjob/daily-drift manual-drift-59 -n ml
   kubectl wait --for=condition=complete job/manual-drift-59 -n ml --timeout=300s
   # Check drift_logs table and frontend /drift page
```

---

## KServe Architecture Details

### InferenceService Configuration (from kserve-inference-service.yaml)
- **Name:** `stock-model-serving`, namespace `ml`
- **Runtime:** `stock-sklearn-mlserver` (ClusterServingRuntime using `seldonio/mlserver:1.6.1-slim`)
- **Protocol:** V2 (Open Inference Protocol)
- **StorageUri:** `s3://model-artifacts/serving/active`
- **ServiceAccount:** `kserve-s3-sa` (annotated with `serving.kserve.io/s3-secret: kserve-s3-credentials`)
- **Mode:** RawDeployment (no Istio, sidecar injection disabled)
- **Internal DNS:** `stock-model-serving-predictor.ml.svc.cluster.local:80`

### V2 Inference Protocol Endpoints
```
POST /v2/models/stock-model-serving/infer   — prediction
GET  /v2/models/stock-model-serving/ready   — readiness
GET  /v2/models/stock-model-serving         — model metadata
GET  /v2/health/ready                        — server health
```

### KServe V2 Request Format (from kserve_client.py)
```python
payload = {
    "inputs": [{
        "name": "predict",
        "shape": [n_rows, n_features],
        "datatype": "FP64",
        "data": flat_data,  # row-major flattened
    }],
}
```
Response parsed via `response["outputs"][0]["data"][0]` (first scalar).

### S3/MinIO Wiring
- MinIO endpoint in KServe S3 secret annotations: `minio.storage.svc.cluster.local:9000`
- `s3-usehttps: "0"` and `s3-verifyssl: "0"` (plain HTTP to MinIO)
- MinIO configmap in `ml` namespace is copied from `storage` namespace in deploy-all.sh Phase 51 block

---

## API KServe Wiring (KSERVE_ENABLED)

**Critical:** `app/config.py` has `KSERVE_ENABLED: bool = False` as the Python default. BUT `k8s/ingestion/configmap.yaml` has `KSERVE_ENABLED: "true"` — so the K8s deployment WILL use KServe. The docker-compose environment uses the Python default (`false`). This asymmetry is by design.

The `ingestion-config` ConfigMap (`k8s/ingestion/configmap.yaml`) also contains:
- `KSERVE_INFERENCE_URL: "http://stock-model-serving-predictor.ml.svc.cluster.local:80"`
- `KSERVE_MODEL_NAME: "stock-model-serving"`
- `KSERVE_TIMEOUT_SECONDS: "30"`

---

## MinIO Model Artifact Structure

The training pipeline writes to `s3://model-artifacts/serving/active/`. For KServe MLServer sklearn runtime, the bucket path must contain:
- `model-settings.json` — MLServer model configuration (model name, implementation, parameters)
- `model.joblib` (or `model.pkl`) — the serialized sklearn Pipeline

The `ml-pipeline-config` ConfigMap specifies:
- `SERVING_DIR: "serving/active"` — relative path within the `model-artifacts` bucket
- `STORAGE_BACKEND: "s3"` — confirms S3 path (set in CronJob env too)

---

## Frontend Verification

After KServe serving is active, frontend pages to validate:
- `/forecasts` — should display AAPL row with `predicted_price` from KServe
- `/drift` — should show drift events from `drift_logs` table after running drift CronJob

Frontend is deployed in `frontend` namespace. Access via `kubectl port-forward` or `minikube service`:
```bash
kubectl port-forward svc/frontend -n frontend 3000:80
# OR
minikube service frontend -n frontend --url
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Manual job from CronJob | Custom K8s Job YAML | `kubectl create job --from=cronjob/<name>` |
| Checking InferenceService readiness | Custom polling script | `kubectl wait --for=condition=Ready inferenceservice/<name>` |
| Listing MinIO objects | Custom S3 client script | `kubectl exec minio-pod -- mc ls local/bucket/prefix/` |
| Port forwarding for access | Ingress config changes | `kubectl port-forward` or `minikube service --url` |
| Accessing DB from host | Deploying a DB client pod | `kubectl port-forward svc/postgresql -n storage 5432:5432` |

---

## Common Pitfalls

### Pitfall 1: KServe InferenceService wait blocks deploy-all.sh on fresh cluster
**What goes wrong:** `kubectl wait --for=condition=Ready inferenceservice/stock-model-serving -n ml --timeout=300s` times out because no model artifact exists in MinIO yet.
**Root cause:** `deploy-all.sh` applies InferenceService and immediately waits for Ready status. KServe polls `s3://model-artifacts/serving/active/` for a model — if the bucket is empty, it enters a CrashLoopBackOff cycle.
**How to avoid:** The plan must either (a) patch deploy-all.sh to skip the InferenceService Ready wait on first run, or (b) split deploy into two stages: deploy infra first, then train, then deploy InferenceService.
**Warning signs:** `kubectl describe inferenceservice stock-model-serving -n ml` shows `FailedMount` or `ModelNotFound` conditions.

### Pitfall 2: stock-api Docker image not built in deploy-all.sh
**What goes wrong:** `k8s/ingestion/fastapi-deployment.yaml` uses `stock-api:latest` with `imagePullPolicy: Never` — but `deploy-all.sh` only builds `stock-kafka-consumer`, `stock-ml-pipeline`, and `stock-frontend`.
**Root cause:** The API image build was omitted from the deploy script.
**How to avoid:** The plan must include a step to `eval $(minikube docker-env) && docker build -t stock-api:latest services/api/` before or within deploy-all.sh.
**Warning signs:** `ErrImageNeverPull` on `stock-api` pod.

### Pitfall 3: Missing secrets.yaml and minio-secrets.yaml
**What goes wrong:** `deploy-all.sh` exits at line 53 (`exit 1`) if `k8s/storage/secrets.yaml` is absent.
**Root cause:** Secret files are gitignored (only `.yaml.example` templates are committed).
**How to avoid:** Plan must include a step to create both files from their `.example` templates with dev credentials before running deploy-all.sh.

### Pitfall 4: Strimzi Kafka not ready before Kafka CRs applied
**What goes wrong:** `deploy-all.sh` applies `kafka-cluster.yaml` (a Strimzi Kafka CR) but Strimzi operator may still be initializing if `setup-minikube.sh` was just run.
**Root cause:** setup-minikube.sh waits 300s for Strimzi pod, but the operator's webhooks may take additional seconds to become available.
**How to avoid:** Add a brief kubectl wait for Strimzi's admission webhook before applying Kafka CRs, or add a retry loop.

### Pitfall 5: cert-manager and KServe fetched from internet during deploy-all.sh
**What goes wrong:** `deploy-all.sh` fetches cert-manager and KServe YAML from `github.com` at runtime. Network failures will break the deploy.
**Root cause:** URLs are hardcoded: `cert-manager v1.16.2`, `kserve v0.14.1`.
**How to avoid:** Ensure internet connectivity before running. These files could be pre-downloaded to the repo (as Strimzi was), but currently are not.

### Pitfall 6: Training CronJob requires historical data in DB
**What goes wrong:** `python -m ml.pipelines.training_pipeline` will fail or produce no model if `ohlcv_daily` table is empty.
**Root cause:** Training requires historical OHLCV data as input features.
**How to avoid:** Run `scripts/seed-data.sh` (populates ~90 days × 20 tickers) OR run the historical ingestion job first. The seed script is faster and more reliable for E2E testing.

### Pitfall 7: Redis deployment present but no Redis secret
**What goes wrong:** `k8s/storage/redis-deployment.yaml` exists but there is no `redis-secrets.yaml` or apply step in `deploy-all.sh`. If any service depends on Redis being up, it may fail silently.
**Root cause:** Redis was added in Phase 47 but deploy-all.sh may not include a Redis apply step.
**How to avoid:** Verify Redis section in deploy-all.sh; add apply step if missing.

---

## Code Examples

### Manually trigger ingest + training + verify
```bash
# Source Minikube Docker env first (for builds)
eval $(minikube docker-env)

# Trigger historical ingest
kubectl create job --from=cronjob/historical-ingestion manual-ingest-59 -n ingestion
kubectl wait --for=condition=complete job/manual-ingest-59 -n ingestion --timeout=600s
kubectl logs job/manual-ingest-59 -n ingestion

# Trigger training
kubectl create job --from=cronjob/weekly-training manual-train-59 -n ml
kubectl wait --for=condition=complete job/manual-train-59 -n ml --timeout=600s
kubectl logs job/manual-train-59 -n ml

# Verify MinIO artifact
MINIO_POD=$(kubectl get pod -n storage -l app=minio -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n storage "$MINIO_POD" -- mc ls local/model-artifacts/serving/active/

# Force KServe to reconcile (if InferenceService was applied before model existed)
kubectl rollout restart deployment -n ml -l serving.kserve.io/inferenceservice=stock-model-serving

# Verify InferenceService Ready
kubectl wait --for=condition=Ready inferenceservice/stock-model-serving -n ml --timeout=300s
kubectl get inferenceservice -n ml

# Test predict via API
API_IP=$(kubectl get svc stock-api -n ingestion -o jsonpath='{.spec.clusterIP}')
curl -s http://$API_IP:8000/predict/AAPL | python3 -m json.tool
```

### Trigger drift detection
```bash
kubectl create job --from=cronjob/daily-drift manual-drift-59 -n ml
kubectl wait --for=condition=complete job/manual-drift-59 -n ml --timeout=300s
kubectl logs job/manual-drift-59 -n ml

# Check drift_logs in DB
PG_POD=$(kubectl get pod -n storage -l app=postgresql -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n storage "$PG_POD" -- \
  psql -U stockuser -d stockdb -c "SELECT drift_type, severity, detected_at FROM drift_logs ORDER BY detected_at DESC LIMIT 5;"
```

### Check KServe InferenceService status
```bash
# Full status conditions
kubectl get inferenceservice stock-model-serving -n ml \
  -o jsonpath='{.status.conditions}' | python3 -m json.tool

# Predictor pod state
kubectl get pods -n ml -l serving.kserve.io/inferenceservice=stock-model-serving

# Direct V2 readiness check (from within cluster or after port-forward)
KSERVE_IP=$(kubectl get svc stock-model-serving-predictor -n ml -o jsonpath='{.spec.clusterIP}')
curl http://$KSERVE_IP:80/v2/health/ready
```

### Access frontend
```bash
# Port-forward approach
kubectl port-forward svc/frontend -n frontend 3000:80 &
# Then open browser: http://localhost:3000/forecasts
# Then open browser: http://localhost:3000/drift
```

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (integration tests) |
| Config file | `tests/integration/conftest.py` |
| Quick run command | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow -x -v` |
| Full suite command | `pytest tests/integration/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| KSERV-15-A | KServe InferenceService Ready | integration | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow::test_kserve_inference_service_exists -x` | Yes (`test_pipeline_to_serving.py` line 232) |
| KSERV-15-B | KServe predictor pod Running | integration | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow::test_kserve_predictor_pod_running -x` | Yes (line 243) |
| KSERV-15-C | model-settings.json in MinIO serving/active/ | integration | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow::test_model_artifact_in_minio -x` | Yes (line 255) |
| KSERV-15-D | GET /predict/AAPL returns predicted_price > 0 via KServe | integration | `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow::test_predict_endpoint_uses_kserve -x` | Yes (line 303) |
| KSERV-15-E | Drift CronJob produces drift_logs entries | integration | `pytest tests/integration/test_drift_cycle.py -x` | Yes |
| KSERV-15-F | Frontend /forecasts shows AAPL prediction | manual | Navigate `http://localhost:3000/forecasts` | N/A — visual |
| KSERV-15-G | Frontend /drift shows events + retrain logs | manual | Navigate `http://localhost:3000/drift` | N/A — visual |

### Sampling Rate
- **Per task commit:** `kubectl get inferenceservice -n ml` (cluster health check)
- **Per wave merge:** `pytest tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow -v`
- **Phase gate:** Full integration suite green + manual frontend visual check before `/gsd:verify-work`

### Wave 0 Gaps
- None — all integration tests exist at `tests/integration/test_pipeline_to_serving.py::TestKServeServingFlow`. Tests require a running Minikube cluster with KServe active; they skip gracefully without one.

---

## Phases this closes

| Phase 57 Human-Verification Item | Closed by |
|----------------------------------|-----------|
| Full E2E: POST /ingest/historical → training CronJob → MinIO artifact → GET /predict/AAPL via KServe V2 | Tasks: ingest job + training job + MinIO verify + API curl |
| Drift detection → retrain → KServe rolling update | Tasks: drift job + drift_logs verify + re-check InferenceService |
| Frontend /forecasts shows AAPL prediction from KServe | Task: port-forward + browser navigate + screenshot |
| Frontend /drift shows drift events and retrain logs | Task: port-forward + browser navigate + screenshot |

---

## Open Questions

1. **Redis apply step in deploy-all.sh**
   - What we know: `k8s/storage/redis-deployment.yaml` exists; Phase 47 added Redis.
   - What's unclear: Whether `deploy-all.sh` was updated to apply Redis manifests in Phase 47 (the current deploy-all.sh content does not show a Redis apply block).
   - Recommendation: The plan should verify and add a Redis apply block if missing, to ensure Phase 47 services (caching) work in the cluster.

2. **KServe InferenceService canary model artifact**
   - What we know: `kserve-inference-service-canary.yaml` is also applied in Phase 55 block. It presumably points to `s3://model-artifacts/serving/canary`.
   - What's unclear: Whether a separate canary artifact needs to be placed in MinIO, or if the canary can remain NotReady without blocking the primary flow.
   - Recommendation: If canary fails to start, confirm it doesn't block the primary flow. The plan can defer canary validation.

3. **mc (MinIO Client) availability in MinIO pod**
   - What we know: The Phase 57 VERIFICATION.md shows `mc ls local/model-artifacts/...` for verification.
   - What's unclear: Whether the `mc` binary is available inside the MinIO pod image used.
   - Recommendation: Use `kubectl exec minio-pod -- mc` OR use `kubectl port-forward svc/minio -n storage 9000:9000` and access via boto3/curl with S3 API.

---

## Sources

### Primary (HIGH confidence)
- `stock-prediction-platform/scripts/deploy-all.sh` — full deployment sequence, all phases, secret gate, image builds
- `stock-prediction-platform/scripts/setup-minikube.sh` — cluster start parameters, Strimzi install, addon list
- `stock-prediction-platform/scripts/seed-data.sh` — DB population approach, table coverage
- `stock-prediction-platform/k8s/ml/kserve/kserve-inference-service.yaml` — InferenceService spec, storageUri, runtime, SA
- `stock-prediction-platform/k8s/ml/kserve/sklearn-serving-runtime.yaml` — MLServer image, V2 protocol config
- `stock-prediction-platform/k8s/ml/kserve/kserve-s3-secret.yaml.example` — MinIO endpoint annotations
- `stock-prediction-platform/k8s/ml/cronjob-training.yaml` — CronJob name, image, command, env
- `stock-prediction-platform/k8s/ml/cronjob-drift.yaml` — CronJob name, image, command, env
- `stock-prediction-platform/k8s/ingestion/configmap.yaml` — KSERVE_ENABLED=true, KServe URLs
- `stock-prediction-platform/k8s/ingestion/cronjob-historical.yaml` — CronJob name + trigger mechanism
- `stock-prediction-platform/k8s/storage/secrets.yaml.example` — secret keys required
- `stock-prediction-platform/k8s/storage/minio-secrets.yaml.example` — MinIO secret keys
- `stock-prediction-platform/services/api/app/services/kserve_client.py` — V2 request format, parse logic
- `stock-prediction-platform/services/api/app/config.py` — KSERVE_ENABLED default=False (Python) vs. K8s override
- `.planning/phases/57/57-VERIFICATION.md` — exact human verification steps, expected outputs, Phase 57 gaps

### Secondary (MEDIUM confidence)
- `.planning/STATE.md` — phase history, decisions log confirming migration design
- `.planning/ROADMAP.md` — phase sequence, requirement IDs

---

## Metadata

**Confidence breakdown:**
- Cluster bootstrap sequence: HIGH — read directly from setup-minikube.sh and deploy-all.sh
- Secret pre-conditions: HIGH — verified by checking file existence on disk
- KServe wiring and V2 protocol: HIGH — read from actual manifest and kserve_client.py
- Training → MinIO → KServe flow timing: HIGH — read from all manifest files, issue identified from deploy-all.sh wait logic
- stock-api image build gap: HIGH — verified absence in deploy-all.sh
- Redis gap: MEDIUM — inferred from absence in deploy-all.sh; actual redis-deployment.yaml not fully read

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable infrastructure; Minikube/KServe versions locked in manifests)
