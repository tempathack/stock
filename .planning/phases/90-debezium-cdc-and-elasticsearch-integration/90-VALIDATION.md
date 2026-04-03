---
phase: 90
slug: debezium-cdc-and-elasticsearch-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-03
---

# Phase 90 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing, services/api/tests/) |
| **Config file** | `stock-prediction-platform/services/api/pytest.ini` or `pyproject.toml` |
| **Quick run command** | `cd stock-prediction-platform/services/api && pytest tests/test_search_router.py tests/test_elasticsearch_service.py -x` |
| **Full suite command** | `cd stock-prediction-platform/services/api && pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_search_router.py tests/test_elasticsearch_service.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green + Playwright browser verification
- **Max feedback latency:** ~15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 90-01-01 | 01 | 0 | PostgreSQL WAL | unit/manual | `kubectl apply --dry-run=client -f k8s/storage/postgresql-deployment.yaml` | ✅ | ⬜ pending |
| 90-02-01 | 02 | 0 | Wave 0 tests | unit | `pytest tests/test_search_router.py tests/test_elasticsearch_service.py -x` | ❌ W0 | ⬜ pending |
| 90-03-01 | 03 | 1 | ES StatefulSet | manual | `kubectl apply --dry-run=client -f k8s/storage/elasticsearch-statefulset.yaml` | ❌ W0 | ⬜ pending |
| 90-03-02 | 03 | 1 | Kibana Deployment | manual | `kubectl apply --dry-run=client -f k8s/storage/kibana-deployment.yaml` | ❌ W0 | ⬜ pending |
| 90-04-01 | 04 | 1 | KafkaConnect CR | manual | `kubectl get kafkaconnect -n processing` | ❌ W0 | ⬜ pending |
| 90-04-02 | 04 | 1 | KafkaConnector CRs | manual | `kubectl get kafkaconnector -n processing` | ❌ W0 | ⬜ pending |
| 90-05-01 | 05 | 2 | elasticsearch_service | unit | `pytest tests/test_elasticsearch_service.py -x` | ❌ W0 | ⬜ pending |
| 90-06-01 | 06 | 2 | /search/predictions | unit | `pytest tests/test_search_router.py::test_search_predictions -x` | ❌ W0 | ⬜ pending |
| 90-06-02 | 06 | 2 | /search/models | unit | `pytest tests/test_search_router.py::test_search_models -x` | ❌ W0 | ⬜ pending |
| 90-06-03 | 06 | 2 | /search/drift-events | unit | `pytest tests/test_search_router.py::test_search_drift_events -x` | ❌ W0 | ⬜ pending |
| 90-06-04 | 06 | 2 | /search/stocks | unit | `pytest tests/test_search_router.py::test_search_stocks -x` | ❌ W0 | ⬜ pending |
| 90-07-01 | 07 | 3 | Search.tsx page | Playwright | Playwright MCP browser_navigate + snapshot | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_search_router.py` — stubs for all four /search/* endpoints with mocked AsyncElasticsearch
- [ ] `tests/test_elasticsearch_service.py` — query builder unit tests with asserted ES query shapes
- [ ] `tests/conftest.py` update — add `mock_es_client` fixture using `AsyncMock`

*Existing infrastructure covers the test runner; only new test files are needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CDC topics created with correct config | Kafka CDC pipeline | Requires live Minikube cluster | `kubectl get kafkatopic -n storage \| grep debezium` |
| KafkaConnector shows RUNNING state | Debezium connector | Requires live cluster + running PG WAL | `kubectl get kafkaconnector -n processing` |
| ES index receives CDC documents | End-to-end CDC flow | Requires live Debezium + ES | Kibana DevTools: `GET debezium.public.predictions/_count` |
| PostgreSQL WAL level set correctly | Debezium source | Requires live PG pod | `kubectl exec -n storage <pg-pod> -- psql -U postgres -c "SHOW wal_level;"` |
| vm.max_map_count set on Minikube | ES startup | Requires live Minikube node | `minikube ssh "sysctl vm.max_map_count"` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
