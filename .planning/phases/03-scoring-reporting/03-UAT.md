---
status: complete
phase: 03-scoring-reporting
source: 03-01-SUMMARY.md, 03-02-SUMMARY.md, 03-03-SUMMARY.md, 03-04-SUMMARY.md
started: 2026-02-23T07:00:00Z
updated: 2026-02-23T07:06:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

number: 4
name: Scoring service creates score runs
expected: |
  ScoringService can create score runs with deterministic hashes that include response snapshots and rubric selections
result: [pending]
awaiting: user response

## Tests

### 1. Demo execution produces scorecard output
expected: Running `python3 dev_package/scripts/run_demo.py` produces CSV output with scorecard data including item IDs, scores, and evidence links without errors or exceptions
result: issue
reported: "Demo script fails with ModuleNotFoundError: No module named 'orchestrator_service' and multiple missing dependencies"
severity: major

### 2. LTI configuration loads successfully
expected: LTI config file exists at `dev_package/configs/lti_config.yaml` and contains valid platform/tool configuration with required fields (issuer, client_id, deployment_id)
result: pass

### 3. FastAPI app starts with mounted routes
expected: Running `PYTHONPATH=dev_package/src python -c "import app; print([route.path for route in app.app.router.routes])"` shows delivery and LTI route paths are registered
result: issue
reported: "Import fails with ModuleNotFoundError: No module named 'feature_extractor' in scoring_service.py"
severity: major

### 4. Scoring service creates score runs
expected: ScoringService can create score runs with deterministic hashes that include response snapshots and rubric selections
result: issue
reported: "ScoringService import blocked by missing feature_extractor module; score run models have dataclass loading issues"
severity: major

### 5. Scorecard includes evidence links
expected: Generated scorecards contain evidence section with ordered item_id mappings linking scores to response data
result: issue
reported: "Scorecard generation blocked by circular dependency through scoring_engine package init importing ScoringService with missing feature_extractor"
severity: major

### 6. CSV export produces deterministic output
expected: CSV export writes UTF-8 rows sorted by item_id, producing consistent output across multiple runs
result: issue
reported: "CSV export blocked by circular dependency through scoring_engine package init importing ScoringService with missing feature_extractor"
severity: major

### 7. Audit events logged for scoring
expected: Scoring operations create SCORING_RUN_CREATED events in the audit ledger with run_id and hash_chain linkage
result: pass

### 8. AGS score payload structure
expected: AGS passback payload includes scoreGiven and scoreMaximum fields derived from scoring totals with fallbacks to legacy CPS/ASI fields
result: issue
reported: "AGS payload structure cannot be verified due to blocked scoring service from missing feature_extractor dependency"
severity: major

## Summary

total: 8
passed: 2
issues: 6
pending: 0
skipped: 0

## Gaps

- truth: "Demo execution produces scorecard output"
  status: failed
  reason: "User reported: Demo script fails with ModuleNotFoundError: No module named 'orchestrator_service' and multiple missing dependencies"
  severity: major
  test: 1
  artifacts: []
  missing: []
  debug_session: ""  # To be filled by diagnosis

- truth: "FastAPI app starts with mounted routes showing delivery and LTI paths"
  status: failed
  reason: "User reported: Import fails with ModuleNotFoundError: No module named 'feature_extractor' in scoring_service.py"
  severity: major
  test: 3
  artifacts: []
  missing: []
  debug_session: ""  # To be filled by diagnosis

- truth: "ScoringService can create score runs with deterministic hashes that include response snapshots and rubric selections"
  status: failed
  reason: "User reported: ScoringService import blocked by missing feature_extractor module; score run models have dataclass loading issues"
  severity: major
  test: 4
  artifacts: []
  missing: []
  debug_session: ""  # To be filled by diagnosis
