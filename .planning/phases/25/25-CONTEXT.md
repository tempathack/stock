# Phase 25 — React App Bootstrap & Navigation

## What This Phase Delivers

A fully scaffolded React 18 + Vite application with Bloomberg Terminal dark theme, client-side routing for 4 pages, an API client layer (React Query), and containerized K8s deployment — the shell in which Phases 26–29 will build the actual page contents.

## Requirements Covered

| ID | Requirement | Deliverable |
|----|-------------|-------------|
| FE-01 | React app bootstrapped (Vite) with Tailwind CSS | Vite + React 18 + TypeScript project scaffold |
| FE-02 | Dark theme (Bloomberg Terminal aesthetic) | Tailwind dark theme config, global styles, CSS variables |
| FE-03 | Sidebar or top navigation linking all 4 pages | Sidebar layout component with NavLinks |
| FE-04 | Responsive layout | Mobile-first Tailwind utilities, collapsible sidebar |
| FE-05 | API client layer (React Query) connected to FastAPI | Axios instance + React Query provider, /health smoke test |
| FE-06 | Dockerfile + K8s Deployment/Service for frontend | Multi-stage Dockerfile (build + Nginx), update existing K8s manifests |

## Pre-existing Scaffolding

Phase 1 created placeholder files. These exist and need to be replaced:

| File | Current | Phase 25 Action |
|------|---------|-----------------|
| `services/frontend/Dockerfile` | Single-line placeholder | Replace with multi-stage Vite + Nginx |
| `services/frontend/package.json` | Minimal stub (name + version) | Replace with full Vite project deps |
| `services/frontend/src/App.jsx` | Single-line placeholder | Replace with Router + Layout |
| `services/frontend/src/pages/MarketDashboard.jsx` | Placeholder | Replace with skeleton page component |
| `services/frontend/src/pages/ModelComparison.jsx` | Placeholder | Replace with skeleton page component |
| `services/frontend/src/pages/StockForecasts.jsx` | Placeholder | Replace with skeleton page component |
| `services/frontend/src/pages/DriftMonitoring.jsx` | Placeholder | Replace with skeleton page component |
| `services/frontend/src/styles/.gitkeep` | Empty | Add `globals.css` + Tailwind directives |
| `services/frontend/src/api/.gitkeep` | Empty | Add `client.ts` (Axios + React Query) |
| `services/frontend/src/hooks/.gitkeep` | Empty | Add custom hooks (useApi, etc.) |
| `services/frontend/src/components/.gitkeep` (subfolders) | Empty gitkeeps | Add Layout, Sidebar, PageHeader components |
| `k8s/frontend/deployment.yaml` | Complete (port 80, VITE_API_URL env) | No changes needed |
| `k8s/frontend/service.yaml` | Complete (NodePort 30080) | No changes needed |

## API Endpoints Available (from Phases 23-24)

The API client must be able to reach:

| Method | Path | Purpose | Phase |
|--------|------|---------|-------|
| GET | `/health` | API health check (smoke test) | 3 |
| GET | `/predict/{ticker}` | 7-day forecast for one ticker | 23 |
| GET | `/predict/bulk` | Forecasts for all S&P 500 | 23 |
| GET | `/models/comparison` | Ranked model metrics table | 23 |
| GET | `/models/drift` | Drift detection status | 23 |
| GET | `/market/overview` | Treemap data (all tickers) | 24 |
| GET | `/market/indicators/{ticker}` | Technical indicators | 24 |

## Technology Stack Decisions

| Choice | Rationale |
|--------|-----------|
| Vite 6 | Fast HMR, native ES module dev server, production-optimized builds |
| React 18 | Current stable, concurrent features for responsive UI |
| TypeScript | Type safety for API response shapes, component props |
| Tailwind CSS 4 | Utility-first, easy dark theme, responsive breakpoints |
| React Router 7 | SPA client-side routing, layout routes |
| TanStack React Query 5 | Server state management, caching, refetch intervals |
| Axios | HTTP client with interceptors, base URL config |
| Nginx (Alpine) | Production static serving, minimal image size |

## K8s Integration

- **Deployment** already exists: `k8s/frontend/deployment.yaml` — serves on port 80, image `stock-frontend:latest`, `imagePullPolicy: Never` (Minikube), `VITE_API_URL` env var
- **Service** already exists: `k8s/frontend/service.yaml` — NodePort on 30080
- Dockerfile must produce a Nginx-based image tagged `stock-frontend:latest`
- `VITE_API_URL` is baked at build time (Vite replaces `import.meta.env.VITE_API_URL`)
- docker-compose maps port 3000 (dev) — Vite dev server port match

## Theme Specification (Bloomberg Terminal)

| Element | Value |
|---------|-------|
| Background (primary) | `#1a1a2e` (deep navy) |
| Background (surface) | `#16213e` (panel navy) |
| Background (card) | `#0f3460` (elevated card) |
| Text (primary) | `#e0e0e0` |
| Text (secondary) | `#a0a0a0` |
| Accent (primary) | `#e94560` (Bloomberg red) |
| Accent (green) | `#00d4aa` (profit green) |
| Accent (amber) | `#ffa726` (warning) |
| Border | `#2a2a4a` |
| Font | `Inter`, system sans-serif stack |
| Monospace | `JetBrains Mono`, `Fira Code`, monospace |
