---
phase: 85-backtest-ux-polish-change-red-empty-state-message-to-neutral-label-orphaned-download-and-table-view-icon-buttons
plan: "01"
subsystem: ui
tags: [react, mui, backtest, export-buttons, empty-state]

requires: []
provides:
  - "Neutral empty state on Backtest page (grey SearchOffIcon + muted text instead of red ErrorFallback)"
  - "Labelled CSV and PDF export buttons on Backtest page using shared ExportButtons component"
affects: [backtest, frontend, ui-consistency]

tech-stack:
  added: []
  patterns:
    - "Use ExportButtons shared component for CSV/PDF export on all data pages"
    - "Use neutral Box with text.secondary color for no-data/error states instead of ErrorFallback"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/src/pages/Backtest.tsx

key-decisions:
  - "Replace ErrorFallback (red icon + text) with neutral Box matching idle-state style for non-alarming UX"
  - "Use shared ExportButtons component for consistency with Models and Forecasts pages"
  - "Remove ButtonGroup, Button, FileDownloadIcon, PictureAsPdfIcon imports — all handled by ExportButtons internally"

patterns-established:
  - "Pattern: All pages with data export use ExportButtons from @/components/ui"
  - "Pattern: No-data/error states use color:text.secondary + opacity:0.55 (neutral, not red)"

requirements-completed: []

duration: 3min
completed: 2026-04-03
---

# Phase 85 Plan 01: Backtest UX Polish Summary

**Neutral grey SearchOff empty state and shared ExportButtons (CSV/PDF labels) replace red error fallback and icon-only export controls on Backtest page**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-02T23:11:22Z
- **Completed:** 2026-04-02T23:13:44Z
- **Tasks:** 3 of 3
- **Files modified:** 1

## Accomplishments
- Error/no-data state replaced: red ErrorFallback removed, neutral Box with SearchOffIcon and muted grey text added
- Export buttons replaced: icon-only inline ButtonGroup removed, shared ExportButtons component added with "CSV" and "PDF" labels
- TypeScript compiles with zero errors after changes
- Imports cleaned up: removed ErrorFallback, ButtonGroup, Button, FileDownloadIcon, PictureAsPdfIcon

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace red ErrorFallback with neutral empty state** - `062154f` (feat)
2. **Task 2: Replace icon-only export ButtonGroup with shared ExportButtons** - `c134da7` (feat)
3. **Task 3: Human verify** - approved (Playwright MCP confirmed CSV/PDF labels and neutral grey empty state)

## Files Created/Modified
- `stock-prediction-platform/services/frontend/src/pages/Backtest.tsx` - Neutral empty state + ExportButtons component integration

## Decisions Made
- Used `SearchOffIcon` (not `ErrorOutlineIcon`) for the no-data state — more descriptive of "no results found" semantics vs "system error"
- Removed `Button` from MUI imports after confirming it was only used in the deleted ButtonGroup section (LoadingButton from @mui/lab handles the Run Backtest button)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Human visual verification completed (Task 3 approved): export buttons confirmed showing "CSV" and "PDF" labels; empty state confirmed showing grey SearchOffIcon + neutral text (no red)
- STATE.md and ROADMAP.md updated

---
*Phase: 85-backtest-ux-polish*
*Completed: 2026-04-02*
