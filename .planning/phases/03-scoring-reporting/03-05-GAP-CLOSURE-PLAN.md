---
phase: 03-scoring-reporting
plan: 05
type: execute
wave: 1
depends_on: ["03-01", "03-02", "03-03", "03-04"]
files_modified: ["dev_package/src/orchestrator_service/__init__.py", "dev_package/src/orchestrator_service/orchestrator.py", "dev_package/src/scoring_engine/feature_extractor.py", "dev_package/src/scoring_engine/scoring_service.py", "dev_package/src/scoring_engine/score_runs.py"]
autonomous: true
gap_closure: true
must_haves:
  truths:
    - "Demo execution produces scorecard output"
    - "FastAPI app starts with mounted routes showing delivery and LTI paths"
    - "ScoringService can create score runs with deterministic hashes that include response snapshots and rubric selections"
  artifacts:
    - path: "dev_package/src/orchestrator_service/__init__.py"
      provides: "Orchestrator service package exports"
      min_lines: 10
    - path: "dev_package/src/orchestrator_service/orchestrator.py"
      provides: "Orchestrator service implementation used by demo"
      min_lines: 60
    - path: "dev_package/src/scoring_engine/feature_extractor.py"
      provides: "Feature extraction helpers for scoring service"
      min_lines: 40
    - path: "dev_package/src/scoring_engine/scoring_service.py"
      provides: "Scoring service with resolved imports"
      min_lines: 100
    - path: "dev_package/src/scoring_engine/score_runs.py"
      provides: "Score run models load without dataclass import errors"
      min_lines: 80
  key_links:
    - from: "dev_package/scripts/run_demo.py"
      to: "dev_package/src/orchestrator_service/orchestrator.py"
      via: "import statement"
      pattern: "from orchestrator_service"
    - from: "dev_package/src/scoring_engine/scoring_service.py"
      to: "dev_package/src/scoring_engine/feature_extractor.py"
      via: "import statement"
      pattern: "from .feature_extractor import"
    - from: "dev_package/src/scoring_engine/scoring_service.py"
      to: "dev_package/src/scoring_engine/score_runs.py"
      via: "import statement"
      pattern: "from .score_runs import"
---

<objective>
Resolve missing orchestrator_service and feature_extractor dependencies blocking demo execution, FastAPI startup, and scoring service functionality.

Purpose: Fix ModuleNotFoundError exceptions and dataclass import issues so scoring can run end-to-end.
Output: Working demo script, functional FastAPI app import, and operational ScoringService.
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
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add orchestrator service scaffolding for demo flow</name>
  <files>dev_package/src/orchestrator_service/__init__.py, dev_package/src/orchestrator_service/orchestrator.py</files>
  <action>
    Implement a minimal orchestrator_service package to satisfy demo imports:
    - Create Orchestrator class with methods used by run_demo (use names matching existing demo calls)
    - Accept dependencies via constructor (scoring service, audit ledger) to avoid hard-coded imports
    - Provide a single orchestration method that sequences: load responses -> run scoring -> return scorecard
    - Keep logic lightweight; delegate scoring to ScoringService and reporting helpers
    - Export Orchestrator from __init__.py
  </action>
  <verify>PYTHONPATH=dev_package/src python3 -c "from orchestrator_service import Orchestrator; print('ok')"</verify>
  <done>Orchestrator imports succeed and demo module dependencies are satisfied</done>
</task>

<task type="auto">
  <name>Task 2: Implement feature extraction module and fix score run model imports</name>
  <files>dev_package/src/scoring_engine/feature_extractor.py, dev_package/src/scoring_engine/score_runs.py</files>
  <action>
    Add a feature_extractor module used by ScoringService:
    - Implement extract_features(response_snapshot) -> dict with stable, deterministic fields
    - Keep feature extraction isolated from scoring_service to avoid circular imports
    - Use only types from score_runs or shared models (no scoring_service imports)
    - Update score_runs.py if needed to resolve dataclass loading issues (import order, forward refs)
  </action>
  <verify>PYTHONPATH=dev_package/src python3 -c "from scoring_engine.feature_extractor import extract_features; print('ok')"</verify>
  <done>Feature extractor imports cleanly and score run models load without dataclass errors</done>
</task>

<task type="auto">
  <name>Task 3: Wire ScoringService to feature extractor and score runs</name>
  <files>dev_package/src/scoring_engine/scoring_service.py</files>
  <action>
    Update ScoringService to use the new feature_extractor module:
    - Import extract_features from scoring_engine.feature_extractor
    - Ensure ScoringService can create score runs without circular imports
    - Confirm deterministic hashing still uses ResponseSnapshot/ScoreRun helpers
    - Keep public API stable for reporting and LTI integrations
  </action>
  <verify>PYTHONPATH=dev_package/src python3 -c "from scoring_engine.scoring_service import ScoringService; print('ok')"</verify>
  <done>ScoringService imports cleanly and can create score runs with deterministic hashes</done>
</task>

</tasks>

<verification>
- [ ] Demo script imports orchestrator_service without ModuleNotFoundError
- [ ] FastAPI app imports without missing feature_extractor errors
- [ ] ScoringService can instantiate and create score runs without dataclass load issues
</verification>

<success_criteria>
Phase 03 scoring/reporting gap closure is achieved when:
- Demo execution runs without missing orchestrator_service imports
- FastAPI app starts with mounted routes and no feature_extractor import failures
- ScoringService creates score runs with deterministic hashes and response snapshots
</success_criteria>

<output>
After completion, create `.planning/phases/03-scoring-reporting/03-05-SUMMARY.md`
</output>
