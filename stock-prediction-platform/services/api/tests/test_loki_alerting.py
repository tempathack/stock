"""Tests for Phase 84 — Loki alerting datasource misconfiguration fixes.

Covers:
  LOKI-ALERT-01: Loki datasource has explicit uid: loki
  LOKI-ALERT-02: grafana-alerting-configmap.yaml exists with at least one rule group
  LOKI-ALERT-03: All alert rules referencing Loki use datasourceUid: loki
  LOKI-ALERT-04: Promtail __path__ replacement uses _ separator
  LOKI-ALERT-05: Grafana deployment mounts alerting ConfigMap at provisioning path
"""
import pathlib

import pytest
import yaml

# Path: tests/ is 4 parents below stock-prediction-platform/
# stock-prediction-platform/services/api/tests/  -> 4x .parent -> stock-prediction-platform/
K8S_MONITORING = (
    pathlib.Path(__file__).parent.parent.parent.parent / "k8s" / "monitoring"
)


def _load_yaml_file(filename: str) -> dict:
    """Load and parse a YAML file from K8S_MONITORING. Raises FileNotFoundError if missing."""
    path = K8S_MONITORING / filename
    with path.open() as f:
        return yaml.safe_load(f)


def _load_datasources() -> list:
    """Return the list of datasource dicts from grafana-datasource-configmap.yaml."""
    cm = _load_yaml_file("grafana-datasource-configmap.yaml")
    inner = yaml.safe_load(cm["data"]["datasources.yaml"])
    return inner["datasources"]


# ---------------------------------------------------------------------------
# LOKI-ALERT-01: Loki datasource must have explicit uid: loki
# ---------------------------------------------------------------------------

def test_loki_datasource_has_uid():
    """Loki datasource entry in grafana-datasource-configmap.yaml must have uid == 'loki'."""
    datasources = _load_datasources()
    loki_entries = [ds for ds in datasources if ds.get("name") == "Loki"]
    assert loki_entries, "No datasource named 'Loki' found in grafana-datasource-configmap.yaml"
    loki = loki_entries[0]
    assert "uid" in loki, (
        "Loki datasource is missing 'uid' field — add 'uid: loki' to pin the UID"
    )
    assert loki["uid"] == "loki", (
        f"Loki datasource uid must be 'loki', got: {loki['uid']!r}"
    )


# ---------------------------------------------------------------------------
# LOKI-ALERT-02: Alerting ConfigMap must exist with at least one rule group
# ---------------------------------------------------------------------------

def test_alerting_configmap_has_rules():
    """grafana-alerting-configmap.yaml must exist and contain at least one alert rule."""
    cm_path = K8S_MONITORING / "grafana-alerting-configmap.yaml"
    assert cm_path.exists(), (
        "grafana-alerting-configmap.yaml does not exist — create it with Grafana unified "
        "alerting provisioning schema (apiVersion: 1, groups)"
    )
    cm = yaml.safe_load(cm_path.read_text())
    assert "data" in cm, "ConfigMap missing 'data' key"
    yaml_keys = [k for k in cm["data"] if k.endswith(".yaml")]
    assert yaml_keys, "No .yaml data keys found in grafana-alerting-configmap.yaml data section"

    # Load the first inner YAML file and assert at least one rule exists
    inner_yaml_str = cm["data"][yaml_keys[0]]
    inner = yaml.safe_load(inner_yaml_str)
    assert "groups" in inner, "Inner alerting YAML missing 'groups' key"
    assert inner["groups"], "groups list is empty — add at least one alert rule group"
    assert inner["groups"][0].get("rules"), (
        "First group has no rules — add at least one alert rule"
    )


# ---------------------------------------------------------------------------
# LOKI-ALERT-03: All non-expression datasourceUid values must equal 'loki'
# ---------------------------------------------------------------------------

def test_alert_rules_use_stable_loki_uid():
    """Every alert rule data step that is not '__expr__' must reference datasourceUid: loki."""
    cm_path = K8S_MONITORING / "grafana-alerting-configmap.yaml"
    assert cm_path.exists(), "grafana-alerting-configmap.yaml does not exist"
    cm = yaml.safe_load(cm_path.read_text())
    yaml_keys = [k for k in cm["data"] if k.endswith(".yaml")]
    assert yaml_keys

    inner = yaml.safe_load(cm["data"][yaml_keys[0]])
    non_expr_uids = []
    for group in inner.get("groups", []):
        for rule in group.get("rules", []):
            for step in rule.get("data", []):
                uid = step.get("datasourceUid", "")
                if uid != "__expr__":
                    non_expr_uids.append(uid)

    assert non_expr_uids, (
        "No non-__expr__ datasourceUid values found — alert rules must reference the Loki datasource"
    )
    for uid in non_expr_uids:
        assert uid == "loki", (
            f"Alert rule datasourceUid must be 'loki' (stable), got: {uid!r}. "
            "Never reference auto-generated UIDs like 'P8E80F9AEF21F6940'."
        )


# ---------------------------------------------------------------------------
# LOKI-ALERT-04: Promtail __path__ relabel must use _ separator
# ---------------------------------------------------------------------------

def test_promtail_path_uses_underscore_separator():
    """Promtail __path__ relabel_config must use separator: _ and correct replacement glob."""
    cm = _load_yaml_file("promtail-configmap.yaml")
    inner = yaml.safe_load(cm["data"]["promtail.yaml"])

    scrape_configs = inner.get("scrape_configs", [])
    assert scrape_configs, "No scrape_configs found in promtail.yaml"

    relabel_configs = scrape_configs[0].get("relabel_configs", [])
    path_relabel = [
        r for r in relabel_configs if r.get("target_label") == "__path__"
    ]
    assert path_relabel, (
        "No relabel_config with target_label: __path__ found in Promtail scrape config"
    )
    cfg = path_relabel[0]

    assert cfg.get("separator") == "_", (
        f"Promtail __path__ relabel separator must be '_' (underscore), "
        f"got: {cfg.get('separator')!r}. "
        "Kubernetes pod log paths use {ns}_{pod}_{uid}/{container} — "
        "slash separator produces a glob that never matches."
    )
    assert cfg.get("replacement") == "/var/log/pods/*$1_$2_*/$3/*.log", (
        f"Promtail __path__ replacement must be '/var/log/pods/*$1_$2_*/$3/*.log', "
        f"got: {cfg.get('replacement')!r}"
    )


# ---------------------------------------------------------------------------
# LOKI-ALERT-05: Grafana deployment must mount alerting ConfigMap
# ---------------------------------------------------------------------------

def test_grafana_deployment_mounts_alerting_configmap():
    """grafana-deployment.yaml must mount grafana-alerting-rules ConfigMap at /etc/grafana/provisioning/alerting."""
    deployment = _load_yaml_file("grafana-deployment.yaml")

    containers = deployment["spec"]["template"]["spec"]["containers"]
    assert containers, "No containers in Grafana deployment"
    volume_mounts = containers[0].get("volumeMounts", [])

    alerting_mounts = [
        vm for vm in volume_mounts
        if vm.get("mountPath") == "/etc/grafana/provisioning/alerting"
    ]
    assert alerting_mounts, (
        "No volumeMount with mountPath '/etc/grafana/provisioning/alerting' found in "
        "Grafana deployment. Add: {name: grafana-alerting, mountPath: /etc/grafana/provisioning/alerting}"
    )

    volumes = deployment["spec"]["template"]["spec"].get("volumes", [])
    alerting_volumes = [
        v for v in volumes
        if v.get("configMap", {}).get("name") == "grafana-alerting-rules"
    ]
    assert alerting_volumes, (
        "No volume with configMap.name 'grafana-alerting-rules' found in Grafana deployment. "
        "Add: {name: grafana-alerting, configMap: {name: grafana-alerting-rules}}"
    )
