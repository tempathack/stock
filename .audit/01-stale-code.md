# Audit Section 1: Stale Code & Infrastructure Baseline

Status: IN PROGRESS

---

## K8s Pod Baseline

_Recorded: 2026-04-07_

| Namespace | Pod | Status |
|-----------|-----|--------|
| argocd | argocd-application-controller-0 | Running |
| argocd | argocd-applicationset-controller-f66c56b59-dzb9h | Running |
| argocd | argocd-dex-server-6d8548d96d-p57mq | Error |
| argocd | argocd-notifications-controller-65dbccbd4b-72xrd | Running |
| argocd | argocd-redis-6859df457f-clm9v | Running |
| argocd | argocd-repo-server-5f7f9c4dcb-xn28s | Completed |
| argocd | argocd-server-7cd9848b87-qmdvm | Running |
| cert-manager | cert-manager-767f578ff-c62zs | Running |
| cert-manager | cert-manager-cainjector-c7fdb4dbf-bwjnw | Running |
| cert-manager | cert-manager-webhook-768bf9d966-n64kk | Running |
| flink | feast-writer-654455db6d-df6wm | Running |
| flink | feast-writer-taskmanager-11-1 | Running |
| flink | flink-kubernetes-operator-7848cffc97-z9ffc | Running |
| flink | indicator-stream-58dcc69587-wrhtj | Running |
| flink | indicator-stream-taskmanager-10-1 | Running |
| flink | ohlcv-normalizer-6bc9464c66-zmjlz | Running |
| flink | ohlcv-normalizer-taskmanager-20-1 | Running |
| flink | sentiment-stream-7f7f565b7d-wfq8w | Running |
| flink | sentiment-stream-taskmanager-2-1 | Running |
| flink | sentiment-writer-744c697854-gswpk | Running |
| flink | sentiment-writer-taskmanager-3-1 | Running |
| frontend | frontend-7bdcb79c89-966q9 | Running |
| ingestion | intraday-ingestion-29587775-jnwfk | Completed |
| ingestion | intraday-ingestion-29587780-kxjnh | Completed |
| ingestion | intraday-ingestion-29587790-kz7tc | Completed |
| ingestion | reddit-producer-75dcc9fdb6-7jj6m | Running |
| ingestion | stock-api-8779d87f4-bgnmb | Running |
| ingress-nginx | ingress-nginx-controller-56d7c84fd4-n7x2r | Running |
| kserve | kserve-controller-manager-78bbf54fdb-lp52q | Running |
| kserve | kserve-localmodel-controller-manager-f5b5cd9cc-fhj5n | Running |
| kube-system | coredns-6b6cdb8cfd-rjps7 | Running |
| kube-system | etcd-minikube | Running |
| kube-system | kube-apiserver-minikube | Running |
| kube-system | kube-controller-manager-minikube | Running |
| kube-system | kube-proxy-hbv8x | Running |
| kube-system | kube-scheduler-minikube | Running |
| kube-system | metrics-server-7fbb699795-4g828 | Running |
| kube-system | storage-provisioner | Running |
| kubeflow | cache-deployer-deployment-6cd49db798-kjjrf | Running |
| kubeflow | cache-server-6669dd6674-msxjk | Running |
| kubeflow | metadata-envoy-deployment-677d8c6fb9-fhzr6 | Running |
| kubeflow | metadata-grpc-deployment-76d6fb49f8-kr7tl | Running |
| kubeflow | metadata-writer-685b9776db-77df6 | Running |
| kubeflow | minio-84b5cc74b5-b9mt2 | Running |
| kubeflow | ml-pipeline-64469779df-f5cjq | Running |
| kubeflow | ml-pipeline-persistenceagent-644484d7cd-qtzc6 | Running |
| kubeflow | ml-pipeline-scheduledworkflow-58b5f859c-zhbg6 | Running |
| kubeflow | ml-pipeline-ui-67df75b4cc-gzjcl | Running |
| kubeflow | ml-pipeline-viewer-crd-54d6b54bcb-6kjbc | Running |
| kubeflow | ml-pipeline-visualizationserver-6b6b7c7d6b-g9jhf | Running |
| kubeflow | mysql-767f4d9f9b-57flx | Running |
| kubeflow | smoke-daily-daily-closewvtrl-78-... | Init:ImagePullBackOff |
| kubeflow | smoke-intraday-intraday-r8st9d-... | Init:ErrImagePull |
| kubeflow | workflow-controller-6bc9b6d744-c2bxh | Running |
| kubernetes-dashboard | dashboard-metrics-scraper-5d59dccf9b-26pnw | Running |
| kubernetes-dashboard | kubernetes-dashboard-7779f9b69b-k4lq7 | Running |
| ml | aapl-retrain-v2-7df5v | Completed |
| ml | feast-feature-server-7f947d7777-xxgwm | Running |
| ml | manual-train-linear-rms9s | Completed |
| ml | stock-model-serving-canary-predictor-5f59f87547-6rh6v | Running |
| ml | stock-model-serving-predictor-cfbc44bd9-fv9rq | Running |
| monitoring | alertmanager-7d775494cb-lzf6c | Running |
| monitoring | grafana-c78fd8498-8lgm7 | Running |
| monitoring | loki-78d86995c4-tcdr2 | Running |
| monitoring | prometheus-769b456d4b-5pm92 | Running |
| monitoring | promtail-v949h | Running |
| processing | kafka-consumer-78875d9b96-t8m62 | Running |
| processing | kafka-consumer-78875d9b96-tbr7z | Running |
| storage | elasticsearch-0 | Running |
| storage | kafka-combined-0 | Running |
| storage | kafka-entity-operator-54c575b5b6-8bljs | Running |
| storage | kibana-5df4b8474c-8k9n5 | Running |
| storage | minio-76748b8597-d5nv5 | Running |
| storage | postgresql-5d7959b55-mx5qz | Running |
| storage | postgresql-backup-29587920-k9pmv | Completed |
| storage | redis-5d9fb5ffff-bqd5s | Running |
| storage | strimzi-cluster-operator-5444567598-db6xb | Running |

### Notable Issues (Pod Baseline)
- `argocd-dex-server`: Error (OAuth/SSO provider — non-critical for core function)
- `kubeflow smoke-daily / smoke-intraday`: Init:ImagePullBackOff / Init:ErrImagePull — pipeline smoke test pods stuck (image pull issue)

---

## Service Connectivity Baseline

_Recorded: 2026-04-07_

| Service | Endpoint | Status |
|---------|----------|--------|
| Stock API | http://localhost:8010/health | **UP** — `{"service":"stock-api","version":"1.0.0","status":"ok"}` |
| Prometheus | http://localhost:9090/-/ready | **UP** — `Prometheus Server is Ready.` |
| Grafana | http://localhost:3000/api/health | **UP** — `{"database":"ok","version":"10.4.0"}` |

### Port-Forward Commands Used
```bash
kubectl port-forward pod/stock-api-8779d87f4-bgnmb -n ingestion 8010:8000
kubectl port-forward svc/grafana -n monitoring 3000:3000
kubectl port-forward svc/prometheus -n monitoring 9090:9090
```

Note: API port-forward required pod-level forward (not svc-level) due to pod restart after minikube start.
