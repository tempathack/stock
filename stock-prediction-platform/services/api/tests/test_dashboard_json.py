"""Tests that Grafana dashboard JSON has correct threshold line and histogram sources.

These tests validate:
1. Panel 2 of the ML Performance dashboard has the 8s SLO threshold line configured.
2. All histogram_quantile expressions in both dashboards use real Prometheus _bucket series.
"""
import json
import pathlib

import pytest
import yaml

# Path resolution: this file lives at stock-prediction-platform/services/api/tests/
# k8s/monitoring is at stock-prediction-platform/k8s/monitoring/
# So we need 4 levels of .parent to reach stock-prediction-platform/
K8S_MONITORING = pathlib.Path(__file__).parent.parent.parent.parent / "k8s" / "monitoring"


def _load_dashboard(filename: str, json_key: str) -> dict:
    """Parse a Grafana ConfigMap YAML and return the embedded dashboard JSON as dict."""
    cm_path = K8S_MONITORING / filename
    with cm_path.open() as f:
        cm = yaml.safe_load(f)
    return json.loads(cm["data"][json_key])


def _get_panel(dashboard: dict, panel_id: int) -> dict:
    """Return the panel dict with the given id. Raises AssertionError if not found."""
    for panel in dashboard["panels"]:
        if panel.get("id") == panel_id:
            return panel
    raise AssertionError(f"Panel id={panel_id} not found in dashboard")


def _all_exprs(dashboard: dict) -> list:
    """Collect all PromQL expr strings from all panel targets."""
    exprs = []
    for panel in dashboard["panels"]:
        for target in panel.get("targets", []):
            if "expr" in target:
                exprs.append(target["expr"])
    return exprs


# ---------------------------------------------------------------------------
# ML Performance dashboard — panel 2 threshold line assertions
# ---------------------------------------------------------------------------

def test_ml_perf_panel2_thresholdsStyle_mode_is_line():
    """Panel 2 ('Prediction Latency by Model p95') must have thresholdsStyle.mode == 'line'.

    This is the Grafana v10 mechanism to render a dashed horizontal line at the
    threshold value on a timeseries panel. Without it, thresholds only change
    the series color but draw no visible line.
    """
    dashboard = _load_dashboard("grafana-dashboard-ml-perf.yaml", "ml-performance.json")
    panel = _get_panel(dashboard, panel_id=2)
    custom = panel["fieldConfig"]["defaults"]["custom"]
    assert "thresholdsStyle" in custom, (
        "Panel 2 fieldConfig.defaults.custom is missing 'thresholdsStyle'. "
        "Add thresholdsStyle: {mode: 'line'} to draw a dashed SLO reference line."
    )
    assert custom["thresholdsStyle"]["mode"] == "line", (
        f"Expected thresholdsStyle.mode == 'line', got {custom['thresholdsStyle']['mode']!r}"
    )


def test_ml_perf_panel2_has_threshold_line_at_8s():
    """Panel 2 thresholds steps must include a step at value=8 with color='red'.

    The 8-second value is the conservative SLO threshold for ML prediction p95 latency.
    """
    dashboard = _load_dashboard("grafana-dashboard-ml-perf.yaml", "ml-performance.json")
    panel = _get_panel(dashboard, panel_id=2)
    defaults = panel["fieldConfig"]["defaults"]
    assert "thresholds" in defaults, (
        "Panel 2 fieldConfig.defaults is missing 'thresholds'. "
        "Add thresholds with steps [{color: transparent, value: null}, {color: red, value: 8}]."
    )
    steps = defaults["thresholds"]["steps"]
    threshold_values = [step.get("value") for step in steps]
    assert 8 in threshold_values, (
        f"Panel 2 thresholds.steps does not contain a step at value=8. "
        f"Found values: {threshold_values}. Add {{color: 'red', value: 8}}."
    )
    red_step = next(s for s in steps if s.get("value") == 8)
    assert red_step["color"] == "red", (
        f"The threshold step at value=8 should have color='red', got {red_step['color']!r}"
    )


def test_ml_perf_panel2_thresholds_base_step_is_transparent():
    """Panel 2 thresholds must start with a base step at value=null with color='transparent'.

    Grafana requires the first threshold step to have value=null as the base.
    Without this, Grafana may color the entire series background red by default.
    """
    dashboard = _load_dashboard("grafana-dashboard-ml-perf.yaml", "ml-performance.json")
    panel = _get_panel(dashboard, panel_id=2)
    steps = panel["fieldConfig"]["defaults"]["thresholds"]["steps"]
    assert len(steps) >= 2, (
        f"Expected at least 2 threshold steps (base + SLO), found {len(steps)}"
    )
    base_step = steps[0]
    assert base_step.get("value") is None, (
        f"First threshold step must have value=null (JSON null), got {base_step.get('value')!r}"
    )
    assert base_step["color"] == "transparent", (
        f"First threshold step must have color='transparent', got {base_step['color']!r}"
    )


# ---------------------------------------------------------------------------
# Histogram source verification — both dashboards use real _bucket series
# ---------------------------------------------------------------------------

def test_histogram_quantile_uses_bucket_suffix_ml_perf():
    """All histogram_quantile() expressions in ml-performance.json must reference _bucket series.

    Using _bucket suffix means the expression operates on a genuine Prometheus
    Histogram, not a synthetic gauge or counter approximation.
    """
    dashboard = _load_dashboard("grafana-dashboard-ml-perf.yaml", "ml-performance.json")
    exprs = _all_exprs(dashboard)
    hq_exprs = [e for e in exprs if "histogram_quantile" in e]
    assert len(hq_exprs) > 0, (
        "No histogram_quantile expressions found in ml-performance.json. "
        "Expected at least panel 2 to use histogram_quantile(0.95, ..._bucket...)."
    )
    for expr in hq_exprs:
        assert "_bucket" in expr, (
            f"histogram_quantile expression does not use _bucket series:\n{expr}\n"
            "All histogram_quantile calls must operate on real Prometheus histogram buckets."
        )


def test_histogram_quantile_uses_bucket_suffix_api_health():
    """All histogram_quantile() expressions in api-health.json must reference _bucket series.

    Verifies that p50/p95/p99 panels in the API Health dashboard use genuine
    Prometheus Histogram metrics (http_request_duration_seconds_bucket,
    prediction_latency_seconds_bucket) rather than synthetic approximations.
    """
    dashboard = _load_dashboard("grafana-dashboard-api-health.yaml", "api-health.json")
    exprs = _all_exprs(dashboard)
    hq_exprs = [e for e in exprs if "histogram_quantile" in e]
    assert len(hq_exprs) > 0, (
        "No histogram_quantile expressions found in api-health.json. "
        "Expected p50/p95/p99 latency panels to use histogram_quantile(...)."
    )
    for expr in hq_exprs:
        assert "_bucket" in expr, (
            f"histogram_quantile expression does not use _bucket series:\n{expr}\n"
            "All histogram_quantile calls must operate on real Prometheus histogram buckets."
        )
