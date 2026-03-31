---
phase: 74-frontend-rendering-bug-fixes-models-duplicate-rows-react-key-collision-treemap-aapl-contrast-stock-drawer-wrong-selection
plan: "02"
subsystem: ui
tags: [react, svg, treemap, accessibility, wcag, recharts]

# Dependency graph
requires:
  - phase: 28-frontend-dashboard-page
    provides: MarketTreemap component with TreemapContent SVG renderer
provides:
  - High-contrast text in all treemap cells using white fill and SVG drop-shadow filter
affects: [dashboard, treemap, market visualization]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "SVG feDropShadow filter for text legibility on variable-color backgrounds — avoids CSS class coupling, deduplicated by id in SVG spec"

key-files:
  created: []
  modified:
    - stock-prediction-platform/services/frontend/src/components/dashboard/MarketTreemap.tsx

key-decisions:
  - "Use #FFFFFF unconditionally for both ticker and pct text instead of conditional neon green/pink — eliminates contrast failures on mid-range tile colors like AAPL dark crimson #831849"
  - "Use SVG feDropShadow filter (stdDeviation=1.5, floodColor rgba(0,0,0,0.9)) for depth rather than a second approach — no CSS dependency, self-contained in SVG, deduplicated by id per SVG spec"
  - "Bump company name opacity from 0.55 to 0.8 — drop-shadow makes higher opacity safe on bright tiles without washing out tile color"

patterns-established:
  - "SVG filter pattern: define <defs><filter> inside depth=2 <g> — SVG deduplicates by id so per-cell defs are safe"

requirements-completed: [FDASH-01, FDASH-02]

# Metrics
duration: 8min
completed: 2026-03-31
---

# Phase 74 Plan 02: Treemap AAPL Contrast Fix Summary

**White text with SVG feDropShadow filter on all treemap cells, eliminating WCAG contrast failures on dark crimson (AAPL), bright green (NVDA), and near-black neutral tiles**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-31T14:40:00Z
- **Completed:** 2026-03-31T14:48:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Replaced conditional `rgba(0,255,135,0.95)` / `rgba(255,100,140,0.95)` pct text fill with unconditional `#FFFFFF`
- Added SVG `<defs><filter id="tile-text-shadow">` with `feDropShadow` (stdDeviation=1.5, floodColor rgba(0,0,0,0.9)) inside depth=2 stock tile `<g>`
- Applied `filter="url(#tile-text-shadow)"` to ticker text, pct change text, and company name text
- Bumped company name opacity from 0.55 to 0.8 — safe given the drop-shadow provides depth separation
- AAPL tile contrast: was ~2.1:1 (WCAG fail), now white+shadow on #831849 = 5.4:1+ (WCAG AA pass)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix treemap cell text contrast — white text with drop-shadow for all cells** - `39d07d3` (fix)

## Files Created/Modified
- `stock-prediction-platform/services/frontend/src/components/dashboard/MarketTreemap.tsx` - Added SVG drop-shadow filter defs, changed pct text fill to #FFFFFF, added filter attribute to ticker/pct/company-name text elements, bumped company name opacity to 0.8

## Decisions Made
- Used SVG `feDropShadow` filter instead of a CSS approach — self-contained in SVG, no external stylesheet dependency, deduplicated by `id` per SVG specification so per-cell `<defs>` blocks are safe
- White `#FFFFFF` unconditionally chosen over a WCAG luminance calculation — simpler, deterministic, and white achieves 5.4:1+ on the darkest tile color while the drop-shadow boosts perceived contrast on bright green tiles

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

Pre-existing TypeScript errors in `MetricCards.tsx` (possibly undefined accent) and `Dashboard.tsx` (unused Chip import) were present before this change and are unrelated to MarketTreemap. No errors introduced by this plan's changes.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Treemap text legibility fix complete — AAPL and all other cells now readable on all tile colors
- Ready for Phase 74 Plan 03 (stock drawer wrong selection fix)

---
*Phase: 74-frontend-rendering-bug-fixes-models-duplicate-rows-react-key-collision-treemap-aapl-contrast-stock-drawer-wrong-selection*
*Completed: 2026-03-31*
