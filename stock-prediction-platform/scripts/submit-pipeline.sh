#!/usr/bin/env bash
# =============================================================================
# submit-pipeline.sh — Upload a compiled KFP pipeline YAML and create a run
# =============================================================================
#
# Prerequisites
# -------------
#   1. Kubeflow Pipelines installed in the 'kubeflow' namespace.
#      See k8s/ml/kubeflow/kfp-standalone.yaml for install instructions:
#
#        export PIPELINE_VERSION=2.3.0
#        kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
#        kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
#        kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic?ref=$PIPELINE_VERSION"
#
#   2. Port-forward the KFP UI/API to localhost:8888 (run in another terminal,
#      or keep the port-forward started by deploy-all.sh running):
#
#        kubectl port-forward svc/ml-pipeline-ui 8888:80 -n kubeflow
#
#   3. kfp Python SDK >= 2.0 installed in your local environment:
#
#        pip install "kfp>=2.0,<3"
#
#   4. A compiled pipeline YAML at $PIPELINE_YAML.  Two ways to produce it:
#
#      a) Via in-cluster compile Job (recommended — matches the deployed image):
#
#           kubectl delete job compile-kfp-pipeline -n ml --ignore-not-found
#           kubectl apply  -f k8s/ml/kubeflow/compile-pipeline-job.yaml
#           kubectl wait   --for=condition=complete job/compile-kfp-pipeline \
#                          -n ml --timeout=120s
#           POD=$(kubectl get pod -l job-name=compile-kfp-pipeline -n ml \
#                     -o jsonpath='{.items[0].metadata.name}')
#           kubectl cp ml/${POD}:/pipelines/training_pipeline.yaml \
#                      /tmp/training_pipeline.yaml
#
#      b) Locally (requires kfp SDK in your local virtualenv):
#
#           cd stock-prediction-platform
#           python3 -c "
#           from ml.pipelines.drift_pipeline import compile_kfp_pipeline
#           compile_kfp_pipeline('/tmp/training_pipeline.yaml')
#           "
#
# Usage
# -----
#   # One-shot run with defaults:
#   ./scripts/submit-pipeline.sh
#
#   # Custom overrides:
#   KFP_HOST=http://localhost:8888 \
#   PIPELINE_YAML=/tmp/training_pipeline.yaml \
#   EXPERIMENT_NAME=stock-prediction \
#   RUN_NAME=training-$(date +%Y%m%d) \
#   ./scripts/submit-pipeline.sh
#
#   # Recurring run every day at 02:00 UTC:
#   RECURRING=true CRON="0 2 * * *" ./scripts/submit-pipeline.sh
#
# Environment variables
# ---------------------
#   KFP_HOST        KFP API/UI base URL         default: http://localhost:8888
#   PIPELINE_YAML   Path to compiled YAML       default: /tmp/training_pipeline.yaml
#   EXPERIMENT_NAME KFP experiment name         default: stock-prediction
#   RUN_NAME        Name for this run           default: training-<timestamp>
#   RECURRING       'true' for a recurring run  default: false
#   CRON            Cron schedule for recurring default: "0 2 * * *"  (02:00 UTC)
#   TICKERS         Comma-separated tickers     default: pipeline default (AAPL,MSFT,GOOGL)
#   REGISTRY_DIR    Model registry path         default: pipeline default (model_registry)
#   SERVING_DIR     Model serving path          default: pipeline default (/models/active)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---------------------------------------------------------------------------
# Configuration (all overridable via environment variables)
# ---------------------------------------------------------------------------
KFP_HOST="${KFP_HOST:-http://localhost:8888}"
PIPELINE_YAML="${PIPELINE_YAML:-/tmp/training_pipeline.yaml}"
EXPERIMENT_NAME="${EXPERIMENT_NAME:-stock-prediction}"
RUN_NAME="${RUN_NAME:-training-$(date +%Y%m%d-%H%M%S)}"
RECURRING="${RECURRING:-false}"
CRON="${CRON:-0 2 * * *}"
TICKERS="${TICKERS:-}"
REGISTRY_DIR="${REGISTRY_DIR:-}"
SERVING_DIR="${SERVING_DIR:-}"

echo "=== KFP Pipeline Submission ==="
echo "  KFP host        : $KFP_HOST"
echo "  Pipeline YAML   : $PIPELINE_YAML"
echo "  Experiment      : $EXPERIMENT_NAME"
echo "  Run name        : $RUN_NAME"
echo "  Recurring       : $RECURRING"
if [ "$RECURRING" = "true" ]; then
  echo "  Cron            : $CRON"
fi
echo ""

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is required but not found on PATH" >&2
  exit 1
fi

if ! python3 -c "import kfp" 2>/dev/null; then
  echo "ERROR: kfp Python SDK not found. Install with:" >&2
  echo "       pip install 'kfp>=2.0,<3'" >&2
  exit 1
fi

if [ ! -f "$PIPELINE_YAML" ]; then
  echo "ERROR: Pipeline YAML not found at: $PIPELINE_YAML" >&2
  echo "" >&2
  echo "Compile it first (choose one method):" >&2
  echo "" >&2
  echo "  Method A — in-cluster compile Job:" >&2
  echo "    kubectl delete job compile-kfp-pipeline -n ml --ignore-not-found" >&2
  echo "    kubectl apply  -f $PROJECT_ROOT/k8s/ml/kubeflow/compile-pipeline-job.yaml" >&2
  echo "    kubectl wait   --for=condition=complete job/compile-kfp-pipeline -n ml --timeout=120s" >&2
  echo "    POD=\$(kubectl get pod -l job-name=compile-kfp-pipeline -n ml -o jsonpath='{.items[0].metadata.name}')" >&2
  echo "    kubectl cp ml/\${POD}:/pipelines/training_pipeline.yaml $PIPELINE_YAML" >&2
  echo "" >&2
  echo "  Method B — local compile (needs kfp SDK in your env):" >&2
  echo "    cd $PROJECT_ROOT" >&2
  echo "    python3 -c \"from ml.pipelines.drift_pipeline import compile_kfp_pipeline; compile_kfp_pipeline('$PIPELINE_YAML')\"" >&2
  exit 1
fi

# Warn (do not fail) if the KFP API is not yet reachable
if ! curl -sf --max-time 3 "${KFP_HOST}/apis/v2beta1/healthz" >/dev/null 2>&1; then
  echo "WARNING: KFP API healthz check failed at $KFP_HOST" >&2
  echo "         Ensure port-forward is active:" >&2
  echo "           kubectl port-forward svc/ml-pipeline-ui 8888:80 -n kubeflow" >&2
  echo ""
fi

# ---------------------------------------------------------------------------
# Submit (or create recurring run) via KFP Python SDK
# ---------------------------------------------------------------------------
export _KFP_HOST="$KFP_HOST"
export _PIPELINE_YAML="$PIPELINE_YAML"
export _EXPERIMENT_NAME="$EXPERIMENT_NAME"
export _RUN_NAME="$RUN_NAME"
export _RECURRING="$RECURRING"
export _CRON="$CRON"
export _TICKERS="$TICKERS"
export _REGISTRY_DIR="$REGISTRY_DIR"
export _SERVING_DIR="$SERVING_DIR"

python3 <<'PYEOF'
import sys
import os

try:
    import kfp
except ImportError:
    print("ERROR: kfp SDK not importable", file=sys.stderr)
    sys.exit(1)

host            = os.environ["_KFP_HOST"]
pipeline_yaml   = os.environ["_PIPELINE_YAML"]
experiment_name = os.environ["_EXPERIMENT_NAME"]
run_name        = os.environ["_RUN_NAME"]
recurring       = os.environ["_RECURRING"].lower() == "true"
cron            = os.environ["_CRON"]
tickers         = os.environ.get("_TICKERS", "") or None
registry_dir    = os.environ.get("_REGISTRY_DIR", "") or None
serving_dir     = os.environ.get("_SERVING_DIR", "") or None

print(f"Connecting to KFP at {host} ...")
client = kfp.Client(host=host)

# Build optional pipeline parameter overrides
params = {}
if tickers:
    params["tickers"] = tickers
if registry_dir:
    params["registry_dir"] = registry_dir
if serving_dir:
    params["serving_dir"] = serving_dir

print(f"Creating/fetching experiment: {experiment_name}")
try:
    experiment = client.create_experiment(name=experiment_name)
    experiment_id = experiment.experiment_id
except Exception:
    # Experiment may already exist
    experiment = client.get_experiment(experiment_name=experiment_name)
    experiment_id = experiment.experiment_id

print(f"Experiment ID: {experiment_id}")

if not recurring:
    print(f"Submitting one-shot run: {run_name}")
    run = client.run_pipeline(
        experiment_id=experiment_id,
        job_name=run_name,
        pipeline_package_path=pipeline_yaml,
        params=params if params else None,
    )
    print("Run submitted successfully.")
    print(f"  Run ID   : {run.run_id}")
    print(f"  Run name : {run_name}")
    print(f"  View at  : {host}/#/runs/details/{run.run_id}")
else:
    print(f"Creating recurring run: {run_name}  [cron: {cron}]")
    recurring_run = client.create_recurring_run(
        experiment_id=experiment_id,
        job_name=run_name,
        pipeline_package_path=pipeline_yaml,
        params=params if params else None,
        cron_expression=cron,
        enabled=True,
    )
    print("Recurring run created successfully.")
    print(f"  Job ID   : {recurring_run.recurring_run_id}")
    print(f"  Cron     : {cron}")
    print(f"  View at  : {host}/#/recurringruns/details/{recurring_run.recurring_run_id}")
PYEOF
