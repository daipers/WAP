---
phase: 05-audit-compliance
plan: 01
subsystem: analytics_service
tags: [psychometrics, DIF, analytics, fairness]
dependency_graph:
  requires: []
  provides:
    - analytics_service.metrics
    - analytics_service.dif_detector
    - analytics_service.dashboard
  affects:
    - app.py
tech_stack:
  added:
    - Chart.js 4.x (visualization)
    - FastAPI (API)
    - Pydantic (validation)
  patterns:
    - Mantel-Haenszel chi-square for DIF
    - Logistic regression for DIF
    - Point-biserial correlation
    - Cronbach's alpha
key_files:
  created:
    - dev_package/src/analytics_service/__init__.py
    - dev_package/src/analytics_service/metrics.py
    - dev_package/src/analytics_service/dif_detector.py
    - dev_package/src/analytics_service/dashboard.py
    - dev_package/templates/analytics_dashboard.html
  modified:
    - dev_package/src/app.py
decisions:
  - "Used Wilson score interval for confidence intervals instead of normal approximation"
  - "ETS-style DIF classification thresholds (no_DIF, minor_DIF, moderate_DIF, severe_DIF)"
  - "Mock data for demo - production would query actual database"
---

# Phase 05 Plan 01: Analytics Dashboard with Psychometric Metrics Summary

## One-Liner
Analytics dashboard with psychometric metrics (difficulty, discrimination, Cronbach's alpha) and DIF detection using Mantel-Haenszel chi-square method.

## Objective
Build item performance analytics dashboard with psychometric metrics and DIF detection for fairness analysis.

## Tasks Completed

| Task | Name | Status | Commit |
|------|------|--------|--------|
| 1 | Create psychometric metrics module | DONE | eea700e |
| 2 | Create DIF detector module | DONE | 5fcb2c1 |
| 3 | Create analytics dashboard API | DONE | 623b840 |
| 4 | Create analytics dashboard UI | DONE | d5062c6 |

## Deviation Documentation

### Auto-Fixed Issues

**1. [Rule 3 - Blocking Issue] FastAPI not installed**
- **Found during:** Task 3 verification
- **Issue:** FastAPI module not available in environment
- **Fix:** Installed fastapi, pydantic, uvicorn via pip
- **Files modified:** System dependencies
- **Commit:** N/A (environment setup)

**2. [Rule 3 - Import Error] Circular import in __init__.py**
- **Found during:** Task 1 verification
- **Issue:** __init__.py imported dif_detector and dashboard which didn't exist yet
- **Fix:** Used lazy imports with get_dif_detector() and get_dashboard() functions
- **Files modified:** dev_package/src/analytics_service/__init__.py
- **Commit:** eea700e

### Auth Gates
None - no authentication required for this phase.

## Verification Results

1. `python3 -c "from dev_package.src.analytics_service.metrics import calculate_item_difficulty, calculate_discrimination_index, calculate_cronbach_alpha; print('OK')"` ✓
2. `python3 -c "from dev_package.src.analytics_service.dif_detector import detect_dif_chi_square, detect_dif_logistic; print('OK')"` ✓
3. `python3 -c "from dev_package.src.analytics_service.dashboard import router; print('OK')"` ✓
4. `ls dev_package/templates/analytics_dashboard.html` ✓

## Metrics

| Metric | Value |
|--------|-------|
| Duration | ~6 minutes |
| Tasks Completed | 4/4 |
| Files Created | 5 |
| Files Modified | 1 |
| Commits | 5 |

## Summary

Successfully implemented analytics dashboard with:

- **Psychometric Metrics Module** (`metrics.py`):
  - Item difficulty (p-value)
  - Discrimination index (point-biserial correlation)
  - Cronbach's alpha for internal consistency
  - Wilson score confidence intervals

- **DIF Detector Module** (`dif_detector.py`):
  - Mantel-Haenszel chi-square test
  - Logistic regression method
  - ETS-style classification (no_DIF, minor_DIF, moderate_DIF, severe_DIF)
  - Support for configurable group attributes

- **Dashboard API** (`dashboard.py`):
  - GET /api/analytics/item-performance
  - GET /api/analytics/fairness-report
  - GET /api/analytics/export

- **Dashboard UI** (`analytics_dashboard.html`):
  - Chart.js visualization
  - Item performance table
  - DIF results with badges
  - CSV export

---

## Self-Check: PASSED

All verification commands executed successfully:
- ✓ metrics.py exports required functions
- ✓ dif_detector.py exports chi-square and logistic methods
- ✓ dashboard.py exports router
- ✓ analytics_dashboard.html exists

All commits verified:
- ✓ eea700e: psychometric metrics
- ✓ 5fcb2c1: DIF detector
- ✓ 623b840: dashboard API
- ✓ d5062c6: dashboard UI
- ✓ cc14cf8: app.py integration
