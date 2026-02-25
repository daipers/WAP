---
phase: 03-scoring-reporting
verified: 2026-02-25T07:22:16Z
status: human_needed
score: 8/8 must-haves verified
human_verification:
  - test: "LTI launch flow"
    expected: "Launch returns a valid context and audit entry"
    why_human: "Requires external LMS integration and real tokens"
  - test: "AGS grade passback"
    expected: "LMS records scoreGiven/scoreMaximum and reflects grade update"
    why_human: "Requires external LMS endpoints and OAuth token exchange"
---

# Phase 3: Scoring & Reporting Verification Report

**Phase Goal:** Produce trustworthy scorecards — the core value delivery with explainable, reproducible results
**Verified:** 2026-02-25T07:22:16Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | System automatically scores response-based items using configured rules | ✓ VERIFIED | ScoringEngine reads rubric and computes CPS/ASI from features in `dev_package/src/scoring_engine/scoring.py` | 
| 2 | System supports custom scoring rules defined per item or per test | ✓ VERIFIED | ScoringService resolves rubric per item_context and map in `dev_package/src/scoring_engine/scoring_service.py` | 
| 3 | Scores are versioned and reproducible — re-scoring produces identical results | ✓ VERIFIED | Hash inputs exclude timestamps in `dev_package/src/scoring_engine/score_runs.py` | 
| 4 | System generates candidate scorecard with detailed performance breakdown | ✓ VERIFIED | Scorecard includes CPS/ASI tiers and breakdowns in `dev_package/src/reporting_service/reporting.py` | 
| 5 | System exports results to CSV format for external analysis | ✓ VERIFIED | CSV export writes scorecard fields in `dev_package/src/reporting_service/csv_export.py` | 
| 6 | Scorecards link scores to evidence showing item responses | ✓ VERIFIED | Evidence map uses sorted item_id responses in `dev_package/src/reporting_service/reporting.py` | 
| 7 | System supports LTI 1.3 launch from LMS for seamless integration | ✓ VERIFIED | LTI routes and service validate launch in `dev_package/src/lti_service/lti_api.py` and `dev_package/src/lti_service/lti_service.py` | 
| 8 | System sends grade passback via LTI Outcomes to update LMS grades | ✓ VERIFIED | `publish_score` posts AGS payload via `AGSClient` in `dev_package/src/lti_service/lti_service.py` | 

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `dev_package/src/scoring_engine/scoring.py` | Scoring rules applied from rubric | ✓ VERIFIED | Uses rubric weights to compute CPS/ASI totals |
| `dev_package/src/scoring_engine/scoring_service.py` | Score run orchestration and audit logging | ✓ VERIFIED | Creates snapshots/runs, logs SCORING_RUN_CREATED |
| `dev_package/src/scoring_engine/score_runs.py` | Deterministic hashes for runs/snapshots | ✓ VERIFIED | Hashes exclude timestamps for reproducibility |
| `dev_package/src/reporting_service/reporting.py` | Scorecard + evidence links | ✓ VERIFIED | Evidence mapped by sorted item_id |
| `dev_package/src/reporting_service/csv_export.py` | Deterministic CSV export | ✓ VERIFIED | Writes rows sorted by item_id |
| `dev_package/src/reporting_service/ags_payload.py` | AGS payload builder | ✓ VERIFIED | scoreGiven/scoreMaximum with CPS/ASI fallback |
| `dev_package/src/lti_service/lti_service.py` | LTI launch + passback | ✓ VERIFIED | Validates launch and posts score |
| `dev_package/src/lti_service/lti_api.py` | LTI FastAPI routes | ✓ VERIFIED | /lti/login and /lti/launch routes |
| `dev_package/src/app.py` | API router wiring | ✓ VERIFIED | Includes delivery + LTI routers |
| `dev_package/configs/lti_config.yaml` | LTI config with issuer/client/deployment | ✓ VERIFIED | Required fields present |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `dev_package/src/scoring_engine/scoring_service.py` | `dev_package/src/scoring_engine/scoring.py` | `ScoringEngine.score` | WIRED | Score session uses rubric-based scoring |
| `dev_package/src/scoring_engine/scoring_service.py` | `dev_package/src/scoring_engine/score_runs.py` | `ResponseSnapshot`/`ScoreRun` | WIRED | Snapshot/run hashes persisted |
| `dev_package/src/reporting_service/reporting.py` | `dev_package/src/scoring_engine/score_runs.py` | evidence mapping | WIRED | Evidence uses response_snapshot.responses |
| `dev_package/src/reporting_service/csv_export.py` | scorecard evidence | sorted item_id | WIRED | Deterministic row ordering |
| `dev_package/src/lti_service/lti_api.py` | `dev_package/src/lti_service/lti_service.py` | validate_launch | WIRED | LTI routes call service |
| `dev_package/src/lti_service/lti_service.py` | `dev_package/src/lti_service/ags_client.py` | submit_score | WIRED | Passback uses AGS client |

### Requirements Coverage

| Requirement | Status | Blocking Issue |
| --- | --- | --- |
| SCR-01 | ✓ SATISFIED | - |
| SCR-02 | ✓ SATISFIED | - |
| SCR-03 | ✓ SATISFIED | - |
| REPT-01 | ✓ SATISFIED | - |
| REPT-02 | ✓ SATISFIED | - |
| REPT-03 | ✓ SATISFIED | - |
| INTG-03 | ✓ SATISFIED | - |
| INTG-04 | ✓ SATISFIED | - |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| - | - | - | - | None detected in scanned files |

### Human Verification Required

1. **LTI launch flow**

**Test:** Perform an actual LTI 1.3 launch against an LMS and complete the login/launch flow.
**Expected:** Launch returns a valid context and audit entry.
**Why human:** Requires external LMS integration and real tokens.

2. **AGS grade passback**

**Test:** Publish a score to a real LMS line item via AGS.
**Expected:** LMS records scoreGiven/scoreMaximum and reflects grade update.
**Why human:** Requires external LMS endpoints and OAuth token exchange.

---

_Verified: 2026-02-25T07:22:16Z_
_Verifier: Claude (gsd-verifier)_
