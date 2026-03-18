# Phase 1: Repo & Folder Scaffold - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Create the full production project skeleton: folder tree from §15 of Project_scope.md, docker-compose.yml with all service stubs, and a shared structured JSON logging utility (utils/logging.py). Git is already initialized. No service logic is implemented in this phase.

</domain>

<decisions>
## Implementation Decisions

### Folder Structure
- Follow §15 of Project_scope.md **exactly** — no additions or omissions
- Every Python file should be a module skeleton: minimal `__init__.py` or stub with docstring — importable but no logic
- Do NOT add .env.example, Makefile, or other extras beyond §15

### Docker Compose
- docker-compose.yml contains **stubs only**: all services listed with image placeholders and exposed ports — no volumes, no env_file, no depends_on wiring (that happens in later phases when each service is built)
- All services must appear at scaffold stage: `api`, `kafka-consumer`, `postgres`, `kafka`, `zookeeper`, `frontend`

### Logging Utility
- Use **structlog** for the shared JSON logging utility
- Default log record fields: `timestamp`, `level`, `service`, `message`, `request_id`, `trace_id`
- `service` injected via environment variable (e.g., `SERVICE_NAME`)
- `request_id` and `trace_id` included as structlog context vars (can be empty string if not set)
- The utility must be importable from `services/api/app/utils/logging.py` and reusable across all services

### Claude's Discretion
- Exact structlog processor chain configuration (JSON renderer, timestamp format, log level filtering)
- Whether to expose a `get_logger(name)` helper or use `structlog.get_logger()` directly
- README.md structure and content

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope
- `Project_scope.md` §15 — Definitive folder structure. Every directory and file in the scaffold must match this section.
- `Project_scope.md` §13 — Technical requirements: structured JSON logging, environment variables for config, type hints, docstrings.

### Planning
- `.planning/REQUIREMENTS.md` — INFRA-03 (folder structure), INFRA-06 (docker-compose), INFRA-09 (structured logging)
- `.planning/PROJECT.md` — Constraints: no hardcoded secrets, production-ready code only

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None yet — this is the first phase, greenfield

### Established Patterns
- None established yet — this phase sets the patterns for all subsequent phases

### Integration Points
- `services/api/app/utils/logging.py` — the logging utility created here will be imported by all other services
- `docker-compose.yml` — service stubs here will be fleshed out in phases 3–9

</code_context>

<specifics>
## Specific Ideas

- Full observability logging fields (request_id, trace_id) chosen proactively — will be important for distributed tracing across Kafka, FastAPI, and Kubeflow later

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-repo-folder-scaffold*
*Context gathered: 2026-03-18*
