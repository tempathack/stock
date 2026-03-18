# Phase 1: Repo & Folder Scaffold — Research

**Written:** 2026-03-18
**Status:** Complete

---

## 1. structlog Setup — Best Practice Configuration

### Why structlog over stdlib logging

structlog provides a processor-chain architecture that is fundamentally better suited to JSON microservice logging than the stdlib `logging` module. It separates event capture from rendering, which means the same log call can emit human-readable output in development and machine-parseable JSON in production based purely on configuration — no code changes required.

### Recommended Processor Chain

The processor chain is ordered and executed left-to-right before final rendering. For this platform, the recommended production chain is:

```
structlog.contextvars.merge_contextvars          # Pulls in request_id, trace_id from context
structlog.stdlib.add_log_level                   # Adds "level" key
structlog.stdlib.add_logger_name                 # Adds "logger" key (optional, adds source module)
structlog.processors.TimeStamper(fmt="iso")      # Adds "timestamp" in ISO 8601
structlog.processors.StackInfoRenderer()         # Handles stack_info kwarg
structlog.processors.format_exc_info             # Formats exception tracebacks into "exception" key
structlog.processors.UnicodeDecoder()            # Ensures all strings are unicode
structlog.processors.JSONRenderer()              # Final: renders entire event dict as JSON
```

For development (human-readable), swap the last processor to `structlog.dev.ConsoleRenderer()`.

### Context Variables for request_id and trace_id

structlog 21.1+ ships `structlog.contextvars` which integrates with Python's `contextvars.ContextVar`. The pattern is:

1. At the start of each FastAPI request (via middleware), call `structlog.contextvars.bind_contextvars(request_id=..., trace_id=...)`.
2. At the end of the request, call `structlog.contextvars.clear_contextvars()`.
3. `merge_contextvars` processor (first in chain) automatically merges these into every log event within that request's async context.

When no request context exists (startup, background tasks), the keys will be absent unless explicitly bound. For this platform, the decision in CONTEXT.md is to emit empty strings — this can be achieved by calling `structlog.contextvars.bind_contextvars(request_id="", trace_id="")` once at module level in the logging utility, so the keys always appear in output.

### SERVICE_NAME Injection

The `service` field is injected by adding a custom processor that reads `os.environ.get("SERVICE_NAME", "unknown")` at log time and adds it to the event dict. This processor should be placed immediately after `merge_contextvars` so it is available for filtering but before rendering.

Example processor:

```python
import os, structlog

def add_service_name(logger, method, event_dict):
    event_dict["service"] = os.environ.get("SERVICE_NAME", "unknown")
    return event_dict
```

### structlog.configure() Call

`structlog.configure()` must be called exactly once at import time in `utils/logging.py`. It is global state. Subsequent imports of the module are no-ops (Python module caching). The configure call should set:

- `processors` — the chain described above
- `wrapper_class=structlog.stdlib.BoundLogger` — ensures the public API matches stdlib signatures (`.info()`, `.warning()`, etc.)
- `context_class=dict` — thread-safe default
- `logger_factory=structlog.PrintLoggerFactory()` — writes to stdout, appropriate for containerized services where Docker/K8s captures stdout

### get_logger Helper

CONTEXT.md leaves the choice to Claude's discretion. The recommended pattern is to expose a `get_logger(name: str | None = None)` helper that wraps `structlog.get_logger(name)`. This:

- Provides a stable import path: `from app.utils.logging import get_logger`
- Allows all services to use the same import regardless of structlog internals
- Makes future changes (adding default bindings per service) transparent to callers

### Log Level Filtering

Add `structlog.stdlib.filter_by_level` as the second processor (after `merge_contextvars`) to honor the `LOG_LEVEL` environment variable. Configure via:

```python
import logging
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
```

structlog defers to stdlib's root logger level when `filter_by_level` is in the chain.

### Final Output Format (Required Fields)

Each emitted JSON line must contain these keys, per CONTEXT.md:

| Key | Source |
|-----|--------|
| `timestamp` | `TimeStamper(fmt="iso")` |
| `level` | `add_log_level` |
| `service` | `add_service_name` custom processor |
| `message` | The `event=` argument passed to the logger call |
| `request_id` | `merge_contextvars` from context var |
| `trace_id` | `merge_contextvars` from context var |

Additional keys (exception info, extra kwargs) are appended automatically by structlog.

---

## 2. docker-compose Stub Patterns

### Purpose of Stubs in This Phase

The docker-compose.yml created in Phase 1 is intentionally incomplete. Its role is:
1. Enumerate all six services so later phases can flesh them out incrementally.
2. Define stable service names that other phases will reference.
3. Expose ports as documentation of the final intended topology.

No volumes, env_file references, depends_on wiring, healthchecks, or restart policies are added in this phase. Those are added when each service is actually built.

### Service Inventory

Per CONTEXT.md and Project_scope.md §15, the six services are:

| Service Name | Image Placeholder | Exposed Port(s) | Notes |
|---|---|---|---|
| `api` | `stock-prediction-api:latest` | `8000:8000` | FastAPI backend |
| `kafka-consumer` | `stock-prediction-consumer:latest` | (none, internal) | Batch processor |
| `postgres` | `timescale/timescaledb:latest-pg15` | `5432:5432` | Real image known |
| `kafka` | `confluentinc/cp-kafka:7.5.0` | `9092:9092` | Real image known |
| `zookeeper` | `confluentinc/cp-zookeeper:7.5.0` | `2181:2181` | Required by Kafka |
| `frontend` | `stock-prediction-frontend:latest` | `3000:3000` | React app |

For custom-built services (`api`, `kafka-consumer`, `frontend`), use a `build: .` context pointing to the service directory. Since no Dockerfile exists yet in this phase, use a placeholder image name instead. The pattern of using `image:` with a placeholder tag is cleaner at scaffold time than `build:` which would fail without a Dockerfile.

### Stub YAML Pattern

The minimal valid stub for a custom service:

```yaml
services:
  api:
    image: stock-prediction-api:latest
    ports:
      - "8000:8000"
```

The minimal valid stub for an infrastructure service with a real image:

```yaml
  postgres:
    image: timescale/timescaledb:latest-pg15
    ports:
      - "5432:5432"
```

### What NOT to Include in Phase 1

- `volumes:` — no database persistence wiring yet
- `environment:` — no env vars (Phase 3+ wires these)
- `env_file:` — no .env files exist yet
- `depends_on:` — no service ordering yet
- `networks:` — default bridge network is sufficient for stubs
- `restart:` — not needed for stubs
- `healthcheck:` — not needed for stubs

### docker-compose Version

Use `version: "3.8"` (or omit `version` entirely for Compose V2+ compatibility). The Compose spec no longer requires the `version` key in Docker Compose V2. Omitting it is the current best practice and avoids deprecation warnings.

---

## 3. Python Module Skeleton Conventions

### What "Importable Stub" Means

A stub module is a Python file that:
1. Has a module-level docstring explaining what the module will do.
2. Is syntactically valid and importable without errors.
3. Contains no business logic — either empty or with `pass`/`...` stubs for functions that will be implemented later.
4. Has type hints on all function signatures (even if the body is `...`).

### `__init__.py` Pattern

For a package like `services/api/app/routers/`, the `__init__.py` should be minimal:

```python
"""Routers package for the stock prediction API."""
```

Do not import submodules in `__init__.py` unless explicitly needed for a public API. Auto-importing causes import-time side effects and makes circular imports more likely. An empty or docstring-only `__init__.py` is correct for this project.

### Stub Module Pattern

For a module like `services/api/app/routers/health.py`:

```python
"""Health check router for the stock prediction API."""

from __future__ import annotations
```

For modules that will contain functions/classes, add forward declarations as stubs:

```python
"""Yahoo Finance data fetching service."""

from __future__ import annotations
from typing import Any


def fetch_intraday(ticker: str) -> list[dict[str, Any]]:
    """Fetch minute-level OHLCV data for a single ticker.

    Args:
        ticker: The stock ticker symbol.

    Returns:
        List of OHLCV records.
    """
    ...
```

Using `...` (Ellipsis) as the body is preferable to `pass` for stubs because it signals "not yet implemented" more clearly and is idiomatic in type stubs (`.pyi` files).

### Files That Are NOT Pure Stubs

Some files in the scaffold are deliverables in their own right in Phase 1:

- `services/api/app/utils/logging.py` — must be fully implemented (see Section 1)
- `docker-compose.yml` — must be fully present with all service stubs
- `README.md` — should have at minimum the project name and architecture summary

All other `.py` files in the scaffold are minimal importable stubs.

### Non-Python Files

For non-Python scaffold files that are not yet implemented:

- **YAML manifests** (e.g., `k8s/ingestion/cronjob-intraday.yaml`): create as empty files or with a single comment `# Placeholder — implemented in Phase N`.
- **Shell scripts** (e.g., `scripts/setup-minikube.sh`): create with shebang line and a comment: `#!/usr/bin/env bash\n# Implemented in Phase 2`.
- **SQL files** (`db/init.sql`): create with a comment placeholder.
- **Frontend files** (`src/App.jsx`, `package.json`): create as minimal stubs.
- **`requirements.txt`** files: create empty files — populated in the phase that implements the service.

### `from __future__ import annotations`

Include this import in all Python stub files. It enables PEP 563 postponed evaluation of annotations, which is important when forward-referencing types. It is harmless when not needed and consistent across the codebase.

---

## 4. Validation Architecture

### How to Validate Phase 1 Success

The three success criteria from ROADMAP.md map to three distinct validation strategies:

#### Criterion 1: Full folder tree exists with placeholder files

**Validation method: file existence checks via shell**

A validation script (or CI step) should enumerate every expected path from §15 and assert it exists:

```bash
# Example checks
test -f stock-prediction-platform/docker-compose.yml
test -d stock-prediction-platform/services/api/app/utils
test -f stock-prediction-platform/services/api/app/utils/logging.py
test -f stock-prediction-platform/ml/pipelines/training_pipeline.py
# ... one line per required path
```

The complete list of paths to check must be derived directly from Project_scope.md §15.

For directories, use `test -d`. For files, use `test -f`. A missing file causes the script to exit non-zero.

#### Criterion 2: docker-compose.yml with all service stubs

**Validation method: grep checks for service names**

```bash
grep -q "^  api:" docker-compose.yml
grep -q "^  kafka-consumer:" docker-compose.yml
grep -q "^  postgres:" docker-compose.yml
grep -q "^  kafka:" docker-compose.yml
grep -q "^  zookeeper:" docker-compose.yml
grep -q "^  frontend:" docker-compose.yml
```

Additionally, `docker compose config` (Compose V2) can be used to validate the YAML syntax:

```bash
docker compose -f docker-compose.yml config --quiet
```

This will error on invalid YAML or Compose spec violations without starting any containers.

#### Criterion 3: Structured JSON logging utility implemented and importable

**Validation method: Python import test**

```bash
cd stock-prediction-platform
python -c "from services.api.app.utils.logging import get_logger; logger = get_logger('test'); logger.info('scaffold validation', phase=1)"
```

This test:
1. Verifies the module is importable (no import errors).
2. Verifies `get_logger` is exported.
3. Verifies a `.info()` call executes without error.
4. Emits a JSON line to stdout that can be inspected for required fields.

For field presence verification:

```bash
cd stock-prediction-platform
python -c "
from services.api.app.utils.logging import get_logger
import json, sys
logger = get_logger('validation')
# Capture output by redirecting — or inspect manually
logger.info('test event', request_id='', trace_id='')
" 2>&1 | python -c "
import json, sys
line = sys.stdin.read().strip()
record = json.loads(line)
required = ['timestamp', 'level', 'service', 'event', 'request_id', 'trace_id']
missing = [k for k in required if k not in record]
if missing:
    print(f'FAIL: missing keys {missing}')
    sys.exit(1)
print('PASS: all required log fields present')
"
```

Note: structlog uses `event` as the key name for the log message (not `message`). CONTEXT.md specifies the field as `message`. This is a naming discrepancy to resolve in planning: either rename the field by adding a processor that renames `event` → `message`, or accept `event` as the field name. The rename approach is clean:

```python
def rename_event_key(logger, method, event_dict):
    event_dict["message"] = event_dict.pop("event")
    return event_dict
```

This processor must be placed last in the chain, immediately before `JSONRenderer()`.

### Summary of Validation Checks

| Check | Tool | Failure Mode |
|---|---|---|
| All paths exist | `test -f / test -d` shell script | Missing file/directory |
| docker-compose.yml has all 6 services | `grep -q` | Service name absent |
| docker-compose.yml is valid YAML | `docker compose config` | Parse error |
| logging.py is importable | `python -c "import ..."` | ImportError |
| `get_logger` is exported | `python -c "from ... import get_logger"` | ImportError or AttributeError |
| Logger emits valid JSON | `python -c ... \| python -c "json.loads(...)"` | JSONDecodeError |
| All required fields present | Field presence check in Python | Missing key |

---

## Key Decisions to Make During Planning

1. **`event` vs `message` field name** — structlog uses `event`; CONTEXT.md specifies `message`. Decide whether to add a rename processor.

2. **`get_logger` location** — The logging utility lives at `services/api/app/utils/logging.py`. CONTEXT.md says it must be reusable across all services. Since it is in the `api` service directory, other services either need to copy it or it should be factored into a shared location. However, CONTEXT.md explicitly states the path is `services/api/app/utils/logging.py` and that it is reusable. The simplest resolution for Phase 1 is to place it there as specified and document that other services will either copy or symlink it; a shared library refactor is a v2 concern.

3. **Placeholder image names** — Custom service images (`stock-prediction-api:latest`, etc.) do not exist yet. The docker-compose.yml will fail `docker compose up` until Dockerfiles are built. This is expected and intentional for Phase 1.

4. **`from __future__ import annotations`** — Include in all Python files for consistency. No downside.

5. **README.md content** — CONTEXT.md defers this to Claude's discretion. Recommended: project name, one-line mission, link to Project_scope.md, and the architecture diagram from §2 of Project_scope.md. Keep it brief.

---

*Phase: 01-repo-folder-scaffold*
*Research written: 2026-03-18*
