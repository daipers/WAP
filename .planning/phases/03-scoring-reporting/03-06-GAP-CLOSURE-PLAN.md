---
phase: 03-scoring-reporting
plan: 06
type: execute
wave: 1
depends_on: ["03-01", "03-02", "03-03", "03-04", "03-05"]
files_modified: ["dev_package/src/scoring_engine/__init__.py", "dev_package/src/scoring_engine/scoring_service.py", "dev_package/src/scoring_engine/feature_extractor.py", "dev_package/src/scoring_engine/score_runs.py", "dev_package/src/reporting_service/reporting.py"]
autonomous: true
gap_closure: true
must_haves:
  truths:
    - "Scorecard includes evidence links"
    - "CSV export produces deterministic output"
    - "AGS score payload structure can be verified"
  artifacts:
    - path: "dev_package/src/scoring_engine/__init__.py"
      provides: "Clean scoring engine package exports without circular imports"
      min_lines: 20
    - path: "dev_package/src/scoring_engine/scoring_service.py"
      provides: "Scoring service with resolved circular dependencies"
      min_lines: 100
    - path: "dev_package/src/scoring_engine/feature_extractor.py"
      provides: "Feature extractor with independent functionality"
      min_lines: 40
    - path: "dev_package/src/reporting_service/reporting.py"
      provides: "Scorecard generation with evidence links"
      min_lines: 80
  key_links:
    - from: "dev_package/src/scoring_engine/__init__.py"
      to: "dev_package/src/scoring_engine/scoring_service.py"
      via: "package exports"
      pattern: "from .scoring_service import"
    - from: "dev_package/src/scoring_engine/scoring_service.py"
      to: "dev_package/src/scoring_engine/feature_extractor.py"
      via: "import statement"
      pattern: "from .feature_extractor import"
    - from: "dev_package/src/reporting_service/reporting.py"
      to: "dev_package/src/scoring_engine/scoring_service.py"
      via: "import statement"
      pattern: "from scoring_engine import ScoringService"
---

<objective>
Resolve circular import dependencies blocking scorecard generation, CSV export, and AGS payload verification.

Purpose: Fix package structure issues preventing evidence links in scorecards, deterministic CSV output, and AGS payload verification.
Output: Working scoring pipeline with clean imports and verifiable AGS payload structure.
</objective>

<execution_context>
@./.opencode/get-shit-done/workflows/execute-plan.md
@./.opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md

@./.planning/phases/03-scoring-reporting/03-01-SUMMARY.md
@./.planning/phases/03-scoring-reporting/03-02-SUMMARY.md
@./.planning/phases/03-scoring-reporting/03-03-SUMMARY.md
@./.planning/phases/03-scoring-reporting/03-04-SUMMARY.md
@./.planning/phases/03-scoring-reporting/03-05-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix circular import in scoring engine package structure</name>
  <files>dev_package/src/scoring_engine/__init__.py, dev_package/src/scoring_engine/scoring_service.py, dev_package/src/scoring_engine/feature_extractor.py</files>
  <action>
    Resolve circular dependencies by:
    - Remove direct imports from scoring_service.py to feature_extractor.py
    - Move feature extraction logic into scoring_service as internal methods
    - Update __init__.py to export only public API without creating import cycles
    - Ensure scoring_service can be imported independently
    
    Reference existing working patterns from audit_ledger_service package structure.
    
    Current circular dependency pattern:
    - scoring_service imports feature_extractor
    - feature_extractor imports models that depend on scoring_service
    - __init__.py creates additional import cycles
  </action>
  <verify>python3 -c "from dev_package.src.scoring_engine.scoring_service import ScoringService; print('ScoringService import works')"</verify>
  <done>Scoring engine package imports work without circular dependencies</done>
</task>

<task type="auto">
  <name>Task 2: Restore scorecard evidence link generation</name>
  <files>dev_package/src/reporting_service/reporting.py, dev_package/src/scoring_engine/scoring_service.py</files>
  <action>
    Re-implement scorecard generation with evidence links:
    - Create generate_scorecard_with_evidence(score_run_id: str) -> Scorecard
    - Link score runs to response evidence using item_id ordering
    - Include evidence section in scorecard output
    - Ensure deterministic ordering by sorted item_id
    
    Use scoring_service to:
    - Retrieve score run data
    - Get response snapshots with evidence
    - Map scores to evidence items
    - Generate complete scorecard structure
    
    Reference 03-02-SUMMARY.md patterns for evidence ordering and CSV export.
  </action>
  <verify>python3 -c "from dev_package.src.reporting_service.reporting import generate_scorecard_with_evidence; print('Scorecard generation works')"</verify>
  <done>Scorecards include evidence section with ordered item_id mappings linking scores to response data</done>
</task>

<task type="auto">
  <name>Task 3: Fix CSV export for deterministic output</name>
  <files>dev_package/src/reporting_service/csv_export.py, dev_package/src/reporting_service/reporting.py</files>
  <action>
    Ensure CSV export produces deterministic output:
    - Sort rows by item_id before writing
    - Use consistent UTF-8 encoding
    - Write header row with consistent field order
    - Ensure same input produces identical output across runs
    
    Update export_scorecard_to_csv(scorecard: Scorecard, file_path: str) to:
    - Sort evidence items by item_id
    - Write consistent field order
    - Handle UTF-8 encoding properly
    - Include all required scorecard fields
    
    Test with sample data to verify deterministic output.
  </action>
  <verify>python3 -c "from dev_package.src.reporting_service.csv_export import export_scorecard_to_csv; print('CSV export works')"</verify>
  <done>CSV export writes UTF-8 rows sorted by item_id, producing consistent output across multiple runs</done>
</task>

<task type="auto">
  <name>Task 4: Implement AGS score payload structure</name>
  <files>dev_package/src/reporting_service/ags_payload.py, dev_package/src/reporting_service/reporting.py</files>
  <action>
    Create AGS payload generation for LTI passback:
    - Implement build_ags_payload(scorecard: Scorecard) -> dict
    - Include scoreGiven and scoreMaximum fields
    - Include fallback to legacy CPS/ASI fields if needed
    - Structure payload according to AGS specification
    
    Payload structure should include:
    - scoreGiven: calculated score
    - scoreMaximum: maximum possible score
    - comment: scorecard summary
    - timestamp: ISO 8601 format
    - fallback fields for legacy systems
    
    Verify payload structure matches AGS requirements.
  </action>
  <verify>python3 -c "from dev_package.src.reporting_service.ags_payload import build_ags_payload; print('AGS payload works')"</verify>
  <done>AGS passback payload includes scoreGiven and scoreMaximum fields derived from scoring totals with fallbacks to legacy CPS/ASI fields</done>
</task>

</tasks>

<verification>
- [ ] All 4 gaps resolved (scorecard evidence, CSV export, AGS payload, circular dependencies)
- [ ] No circular import errors in scoring engine package
- [ ] Scorecards include evidence section with ordered item_id mappings
- [ ] CSV export produces deterministic UTF-8 output sorted by item_id
- [ ] AGS payload structure verified and contains required fields
- [ ] All imports work without ModuleNotFoundError exceptions
</verification>

<success_criteria>
Phase 03 scoring/reporting gaps are closed when:
- Scorecards include evidence links with ordered item_id mappings
- CSV export produces deterministic output across multiple runs
- AGS score payload structure can be verified with required fields
- Circular import dependencies are resolved
- User can proceed with complete UAT verification
</success_criteria>

<output>
After completion, create `.planning/phases/03-scoring-reporting/03-06-SUMMARY.md`
</output>