---
status: complete
phase: 04-integrity-identity
source: 04-01-SUMMARY.md, 04-02-SUMMARY.md
started: 2026-02-27T00:00:00Z
updated: 2026-02-27T00:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 6
name: Session timing respects accommodation profile
expected: When session created with EXTRA_TIME accommodation, time_limit_seconds = base * 1.5
result: pass
awaiting: next test

## Tests

### 1. Import integrity service modules
expected: All integrity modules (behavioral_signals, risk_scorer) import without errors
result: pass
reported: "All integrity modules import successfully"
severity: none

### 2. Behavioral signal aggregation
expected: BehavioralSignalAggregator correctly counts integrity events by type (tab_switch, copy, fullscreen)
result: pass
reported: "1 tab_switch, 1 copy_attempt, 1 fullscreen_exit, 3 total violations"
severity: none

### 3. Risk scoring computes levels
expected: RiskScorer correctly computes risk score and level from aggregated signals
result: pass
reported: "Score 80 (3xTAB_SWITCH=30 + COPY=20 + FULLSCREEN=30) → HIGH risk"
severity: none

### 4. Risk thresholds and weights configuration
expected: RiskScorer allows custom thresholds (LOW=0-30, MEDIUM=31-60, HIGH=61-100) and custom signal weights
result: pass
reported: "Custom thresholds and weights correctly affect risk level calculation"
severity: none

### 5. Accommodation service time multiplier
expected: AccommodationService applies 1.5x multiplier for EXTRA_TIME, supports additional minutes, session overrides
result: pass
reported: "1.5x multiplier: 60min→90min; Additional 30min: 60min→90min; Session override 2.0x: 60min→120min"
severity: none

### 6. Session timing respects accommodation profile
expected: Time limit adjusted when EXTRA_TIME accommodation present in profile
result: pass
reported: "Base 3600s (60min) + 1.5x accommodation = 5400s (90min)"
severity: none

### 7. Format selection based on accommodation
expected: get_format_for_item returns correct format mapping (LARGE_FONT→large_font, etc)
result: pass
reported: "All 5 accommodation types map to correct format strings"
severity: none

### 8. LTI PNP parameter mapping
expected: PNP_PARAM_MAPPING correctly maps launch params to AccommodationType (launch_extra_time→EXTRA_TIME, etc)
result: pass
reported: "4 PNP params mapped: launch_extra_time, launch_font_size, launch_color_contrast, launch_screen_reader"
severity: none

### 9. PNP extraction from LTI launch
expected: LTI service extracts PNP from launch params (multiplier, additional minutes, boolean flags)
result: pass
reported: "EXTRA_TIME parsed as float multiplier (1.5), int minutes (30), boolean flags parsed correctly"
severity: none

### 10. Accommodation conflict detection
expected: validate_accommodations detects conflicts (LARGE_FONT + SCREEN_READER)
result: pass
reported: "Conflict detected: LARGE_FONT and SCREEN_READER may conflict"
severity: none

### 11. End-to-end integration test
expected: Complete workflow from integrity events → risk scoring → accommodations works together
result: pass
reported: "Session with 4 violations → HIGH risk (70), 1.5x accommodation → 90min"
severity: none

### 12. Module-level convenience functions
expected: get_risk_assessment() and AccommodationService.create_profile() work correctly
result: pass
reported: "Module-level functions available and work correctly"
severity: none

## Summary

total: 12
passed: 12
issues: 0
pending: 0
skipped: 0

## Gaps

None - all tests passed.

## Diagnosis

None required - no issues found.

## Fix Plan

None required - no issues found.