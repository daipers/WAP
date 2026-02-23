---
phase: 03-scoring-reporting
plan: 02
subsystem: reporting
tags: [scorecards, csv, celery, scoring-service]

# Dependency graph
requires:
  - phase: 03-scoring-reporting
    provides: score run primitives and scoring pipeline
provides:
  - Evidence-linked scorecard generation
  - Deterministic CSV exports for scorecards
  - Celery task wrappers for reporting outputs
affects: [03-scoring-reporting, reporting, scoring]

# Tech tracking
tech-stack:
  added: []
  patterns: [evidence ordering by sorted item_id, deterministic CSV export]

key-files:
  created:
    - dev_package/src/reporting_service/csv_export.py
    - dev_package/src/reporting_service/tasks.py
  modified:
    - dev_package/src/reporting_service/reporting.py
    - dev_package/src/reporting_service/__init__.py
    - dev_package/scripts/run_demo.py

key-decisions:
  - "Guard reporting task imports so demo runs without optional Celery dependency"

patterns-established:
  - "Scorecard evidence stored in deterministic item_id order"
  - "CSV export writes UTF-8 rows sorted by item_id"

# Metrics
duration: 0 min
completed: 2026-02-23
---

# Phase 3 Plan 2: Scorecards and Reporting Artifacts Summary

**Evidence-linked scorecards with deterministic CSV exports and Celery task wrappers for reporting workflows.**

## Performance

- **Duration:** 0 min
- **Started:** 2026-02-23T00:44:43Z
- **Completed:** 2026-02-23T00:44:56Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Added scorecard generation that links score runs to response evidence with ordered item mappings
- Implemented CSV export utility for scorecards with deterministic row ordering
- Added reporting Celery tasks and updated the demo to emit CSV output

## Task Commits

Each task was committed atomically:

1. **Task 1: Extend scorecard generation with evidence links** - `d63f415` (feat)
2. **Task 2: Add CSV export for scorecards and evidence** - `fb4d81b` (feat)
3. **Task 3: Add reporting Celery tasks and update demo flow** - `4282bee` (feat)

**Additional fix:** `076a407` (fix)

## Files Created/Modified
- `dev_package/src/reporting_service/reporting.py` - Generate scorecards from score runs with evidence and metadata
- `dev_package/src/reporting_service/csv_export.py` - Export scorecards and evidence to CSV
- `dev_package/src/reporting_service/tasks.py` - Celery task wrappers for reporting outputs
- `dev_package/src/reporting_service/__init__.py` - Package exports with optional task imports
- `dev_package/scripts/run_demo.py` - Demo flow using ScoringService with CSV output

## Decisions Made
- Guarded reporting task imports to allow demo execution without Celery installed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Guarded optional Celery imports in reporting package**
- **Found during:** Task 3 (Add reporting Celery tasks and update demo flow)
- **Issue:** Demo execution failed with `ModuleNotFoundError: No module named 'celery'` due to package-level task imports
- **Fix:** Wrapped task imports in `try/except` and exposed `None` when Celery isn't installed
- **Files modified:** dev_package/src/reporting_service/__init__.py
- **Verification:** `python3 dev_package/scripts/run_demo.py`
- **Committed in:** 076a407

---

**Total deviations:** 1 auto-fixed (Rule 3)
**Impact on plan:** Blocking import resolved without changing intended reporting behavior.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Reporting artifacts ready for LTI integration work in Plan 03-03
- Demo produces evidence-linked scorecards and CSV export for validation

---
*Phase: 03-scoring-reporting*
*Completed: 2026-02-23*

## Self-Check: PASSED
