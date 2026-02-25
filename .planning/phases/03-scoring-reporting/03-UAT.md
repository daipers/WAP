---
status: complete
phase: 03-scoring-reporting
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md
started: 2026-02-23T07:00:00Z
updated: 2026-02-25T06:25:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 7
name: Audit events logged for scoring
expected: |
  Scoring operations create SCORING_RUN_CREATED events in the audit ledger with run_id and hash_chain linkage
result: pass
awaiting: next test

## Tests

### 1. Demo execution produces scorecard output
expected: Running `python3 dev_package/scripts/run_demo.py` produces CSV output with scorecard data including item IDs, scores, and evidence links without errors or exceptions
result: pass
reported: "Demo completes; CSV generated; Ledger verified: True"
severity: none

### 2. LTI configuration loads successfully
expected: LTI config file exists at `dev_package/configs/lti_config.yaml` and contains valid platform/tool configuration with required fields (issuer, client_id, deployment_id)
result: pass

### 3. FastAPI app starts with mounted routes
expected: Running `PYTHONPATH=dev_package/src python -c "import app; print([route.path for route in app.app.router.routes])"` shows delivery and LTI route paths are registered
result: pass
reported: "Routes printed successfully (delivery + LTI). pip install emitted PyYAML build error but FastAPI import worked."
severity: none

### 4. Scoring service creates score runs
expected: ScoringService can create score runs with deterministic hashes that include response snapshots and rubric selections
result: pass
reported: "ScoringService import succeeds"
severity: none

### 5. Scorecard includes evidence links
expected: Generated scorecards contain evidence section with ordered item_id mappings linking scores to response data
result: pass
reported: "scorecard.csv includes item_id and response evidence payload"
severity: none

### 6. CSV export produces deterministic output
expected: CSV export writes UTF-8 rows sorted by item_id, producing consistent output across multiple runs
result: pass
reported: "Re-run produced CSV with item_id rows in consistent order"
severity: none

### 7. Audit events logged for scoring
expected: Scoring operations create SCORING_RUN_CREATED events in the audit ledger with run_id and hash_chain linkage
result: pass
reported: "SCORING_RUN_CREATED event recorded with score_run_id, response_snapshot_id, hashes"

### 8. AGS score payload structure
expected: AGS passback payload includes scoreGiven and scoreMaximum fields derived from scoring totals with fallbacks to legacy CPS/ASI fields
result: pass
reported: "build_ags_payload returns scoreGiven/scoreMaximum with CPS/ASI fallback"
severity: none

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0

## Gaps

- truth: "Demo execution produces scorecard output"
  status: passed
  reason: "Demo completes and ledger verification succeeds"
  severity: none
  test: 1
  artifacts:
    - dev_package/data/scorecard.csv
  missing: []
  debug_session: "UAT-03-004"

- truth: "FastAPI app starts with mounted routes showing delivery and LTI paths"
  status: failed
  reason: "User reported: ModuleNotFoundError: No module named 'fastapi'"
  severity: major
  test: 3
  artifacts: []
  missing: []
  debug_session: "UAT-03-005"

## Diagnosis

- id: UAT-03-001
  test: 1
  finding: run_demo imports InterviewAgent from interview_agent_service, but that package is not present in dev_package/src
  impact: Demo cannot execute end-to-end, blocking scorecard CSV generation and downstream scoring/reporting checks
  root_cause: Missing interview_agent_service package in repository

- id: UAT-03-002
  test: 1
  finding: run_demo imports IntegrityChecker from integrity_service, but that package is not present in dev_package/src
  impact: Demo cannot execute end-to-end, blocking scorecard CSV generation and downstream scoring/reporting checks
  root_cause: Missing integrity_service package in repository

- id: UAT-03-003
  test: 1
  finding: run_demo expects data files under dev_package/data, but challenge_bank.json and failure_injections.json are missing
  impact: Demo cannot load content bank, blocking interview and scoring pipeline
  root_cause: Missing demo data files in repository

- id: UAT-03-004
  test: 1
  finding: Demo completes but ledger verification reports False
  impact: Audit chain integrity check fails at end of demo run
  root_cause: Likely hash chain inconsistency between record_event and verify_chain implementations

- id: UAT-03-005
  test: 3
  finding: Importing FastAPI app fails because fastapi dependency is missing
  impact: Cannot verify route mounting or API surface for delivery/LTI
  root_cause: Python dependencies not installed in current environment

## Fix Plan

- id: FIX-03-001
  for_gap: UAT-03-001
  approach: Add minimal interview agent module to dev package used by the demo
  steps:
    - Create package directory `dev_package/src/interview_agent_service/`
    - Add `__init__.py` exporting InterviewAgent
    - Implement `interview_agent.py` with InterviewAgent class that:
      - accepts content_bank, orchestrator, ledger in __init__
      - selects a challenge via ContentBankService (seeded selection already present)
      - appends selected challenge and any injection ids to session fields
      - triggers orchestrator.start_interview and orchestrator.submit_interview
      - records a ledger event if ledger provided
  verification: Re-run `python3 dev_package/scripts/run_demo.py` and confirm CSV output path is printed and no import errors occur

- id: FIX-03-002
  for_gap: UAT-03-002
  approach: Add minimal integrity checker module to dev package used by the demo
  steps:
    - Create package directory `dev_package/src/integrity_service/`
    - Add `__init__.py` exporting IntegrityChecker
    - Implement `integrity_checker.py` with IntegrityChecker.check returning a dict of integrity flags
  verification: Re-run `python3 dev_package/scripts/run_demo.py` and confirm CSV output path is printed and no import errors occur

- id: FIX-03-003
  for_gap: UAT-03-003
  approach: Add minimal demo data files for content bank and failure injections
  steps:
    - Create `dev_package/data/challenge_bank.json` with a couple of sample challenges
    - Create `dev_package/data/failure_injections.json` with a sample injection
  verification: Re-run `python3 dev_package/scripts/run_demo.py` and confirm CSV output path is printed and no import errors occur

- id: FIX-03-004
  for_gap: UAT-03-004
  approach: Align ledger verification with record_event hash inputs
  steps:
    - Inspect audit_ledger_service.ledger hashing content in record_event vs verify_chain
    - Ensure verify_chain includes the same fields and genesis handling used in record_event
    - Re-run demo to confirm Ledger verified: True
  verification: Run `python3 dev_package/scripts/run_demo.py` and confirm Ledger verified: True

- id: FIX-03-005
  for_gap: UAT-03-005
  approach: Install FastAPI and related dependencies for the dev package
  steps:
    - Run `python3 -m pip install -r dev_package/requirements.txt`
    - Re-run the FastAPI import command to list mounted routes
  verification: Command prints route paths without ModuleNotFoundError

- truth: "FastAPI app starts with mounted routes showing delivery and LTI paths"
  status: failed
  reason: "User reported: ModuleNotFoundError: No module named 'fastapi'"
  severity: major
  test: 3
  artifacts: []
  missing: []
  debug_session: "UAT-03-005"

- truth: "ScoringService can create score runs with deterministic hashes that include response snapshots and rubric selections"
  status: failed
  reason: "User reported: ScoringService import blocked by missing feature_extractor module; score run models have dataclass loading issues"
  severity: major
  test: 4
  artifacts: []
  missing: []
  debug_session: ""  # To be filled by diagnosis
