---
phase: 03-scoring-reporting
plan: 04
subsystem: api
tags: [lti, fastapi, scoring, ags]

# Dependency graph
requires:
  - phase: 03-scoring-reporting
    provides: LTI launch routes and AGS passback foundations
  - phase: 03-scoring-reporting
    provides: scoring engine outputs and score run primitives
provides:
  - FastAPI app entrypoint mounting delivery and LTI routers
  - AGS-ready score totals mapped into passback payloads
affects: [lms-integrations, reporting, delivery-api]

# Tech tracking
tech-stack:
  added: []
  patterns: ["App entrypoint mounts service routers", "Score totals mapped to AGS scoreGiven/scoreMaximum"]

key-files:
  created:
    - dev_package/src/app.py
  modified:
    - dev_package/src/delivery_service/delivery_api.py
    - dev_package/src/delivery_service/session_manager.py
    - dev_package/src/delivery_service/test_assembly.py
    - dev_package/src/scoring_engine/scoring.py
    - dev_package/src/lti_service/lti_service.py

key-decisions:
  - "None - followed plan as specified"

patterns-established:
  - "Service routers registered at the FastAPI app level"
  - "Score payload derives totals with fallbacks to legacy CPS/ASI fields"

# Metrics
duration: 3 min
completed: 2026-02-23
---

# Phase 03 Plan 04: LTI Routing + AGS Totals Summary

**FastAPI app entrypoint with LTI routing plus scoring totals mapped to AGS passback fields.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-23T06:16:14Z
- **Completed:** 2026-02-23T06:19:29Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added a FastAPI app entrypoint mounting delivery and LTI routers for LTI reachability
- Exposed total_score/max_score with CPS/ASI totals in scoring output for AGS passback
- Ensured AGS payload falls back to legacy CPS/ASI fields when totals are missing

## Task Commits

Each task was committed atomically:

1. **Task 1: Add FastAPI app entrypoint and mount LTI routes** - `0f00eba` (feat)
2. **Task 2: Align score output totals with AGS passback payload** - `08237f3` (feat)

**Plan metadata:** _pending_

## Files Created/Modified
- `dev_package/src/app.py` - FastAPI app entrypoint mounting delivery and LTI routers
- `dev_package/src/delivery_service/delivery_api.py` - Absolute imports to allow app startup under PYTHONPATH
- `dev_package/src/delivery_service/session_manager.py` - Absolute imports for identity service dependency
- `dev_package/src/delivery_service/test_assembly.py` - Absolute imports for content bank dependency
- `dev_package/src/scoring_engine/scoring.py` - Added CPS/ASI totals plus total_score/max_score output
- `dev_package/src/lti_service/lti_service.py` - Populated AGS scoreGiven/scoreMaximum with fallbacks

## Decisions Made
None - followed plan as specified.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed delivery_service relative imports to allow app import**
- **Found during:** Task 1 (Add FastAPI app entrypoint and mount LTI routes)
- **Issue:** Relative imports in delivery_service modules failed under PYTHONPATH, preventing app import for verification.
- **Fix:** Switched to absolute imports for content_bank_service and identity_service dependencies.
- **Files modified:** dev_package/src/delivery_service/test_assembly.py, dev_package/src/delivery_service/session_manager.py, dev_package/src/delivery_service/delivery_api.py
- **Verification:** `PYTHONPATH=dev_package/src .venv/bin/python -c "import app; print([route.path for route in app.app.router.routes])"`
- **Committed in:** 0f00eba (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Unblocked verification without changing intended behavior.

## Issues Encountered
- System Python was externally managed (PEP 668), so verification used a local `.venv` with FastAPI/PyYAML/requests installed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 03 scoring/reporting LTI gaps are closed; ready to move to Phase 04 planning.

---
*Phase: 03-scoring-reporting*
*Completed: 2026-02-23*

## Self-Check: PASSED
