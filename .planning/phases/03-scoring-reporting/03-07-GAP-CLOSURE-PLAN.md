---
phase: 03-scoring-reporting
plan: 07
type: execute
wave: 1
depends_on: []
files_modified:
  - dev_package/src/scoring_engine/score_runs.py
autonomous: true
gap_closure: true
must_haves:
  truths:
    - "Re-scoring identical inputs produces identical input/output hashes"
    - "Score run verification is independent of created_at timestamps"
  artifacts:
    - path: "dev_package/src/scoring_engine/score_runs.py"
      provides: "Deterministic hash payloads for ResponseSnapshot and ScoreRun"
      contains: "compute_input_hash"
  key_links:
    - from: "dev_package/src/scoring_engine/scoring_service.py"
      to: "dev_package/src/scoring_engine/score_runs.py"
      via: "ResponseSnapshot/ScoreRun hash generation"
      pattern: "with_hash"
---

<objective>
Make score run hashes reproducible by removing time-dependent fields and clarifying the hash semantics.

Purpose: Ensure SCR-03 reproducibility by hashing only deterministic inputs and outputs.
Output: Updated hash payloads and documentation in score run models.
</objective>

<execution_context>
@./.opencode/get-shit-done/workflows/execute-plan.md
@./.opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/03-scoring-reporting/03-VERIFICATION.md
@.planning/phases/03-scoring-reporting/03-01-SUMMARY.md
@dev_package/src/scoring_engine/score_runs.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Remove created_at from hash payloads</name>
  <files>dev_package/src/scoring_engine/score_runs.py</files>
  <action>
    Update ResponseSnapshot.compute_input_hash and ScoreRun.compute_output_hash to hash only deterministic fields.
    - Remove created_at from the hash payloads.
    - Keep created_at as metadata on the models for audit usage, but ensure it does not affect hashes.
    - If you add helper functions for hash payloads, use them in both compute_* methods to prevent drift.
  </action>
  <verify>PYTHONPATH=dev_package/src python3 -c "from scoring_engine.score_runs import ResponseSnapshot, ScoreRun; s1=ResponseSnapshot(snapshot_id='s1', session_id='sess', candidate_id='c1', responses={'q1':'a'}, item_context={}, feature_values={}, feature_version='1', rubric_version='1', created_at=1.0).compute_input_hash(); s2=ResponseSnapshot(snapshot_id='s1', session_id='sess', candidate_id='c1', responses={'q1':'a'}, item_context={}, feature_values={}, feature_version='1', rubric_version='1', created_at=2.0).compute_input_hash(); r1=ScoreRun(score_run_id='r1', response_snapshot_id='s1', rubric_version='1', feature_version='1', score_output={'total': 5}, created_at=1.0).compute_output_hash(); r2=ScoreRun(score_run_id='r1', response_snapshot_id='s1', rubric_version='1', feature_version='1', score_output={'total': 5}, created_at=2.0).compute_output_hash(); assert s1==s2 and r1==r2; print('ok')"</verify>
  <done>Identical data with different created_at values produce identical input/output hashes.</done>
</task>

<task type="auto">
  <name>Task 2: Document reproducibility semantics for hashes</name>
  <files>dev_package/src/scoring_engine/score_runs.py</files>
  <action>
    Add concise documentation in the module or compute_* docstrings stating that hash inputs exclude created_at and other time-dependent metadata.
    Emphasize that hashes reflect deterministic inputs/outputs for reproducibility, while created_at remains for audit trail context.
  </action>
  <verify>Read dev_package/src/scoring_engine/score_runs.py to confirm the reproducibility note is present near the hash computation logic.</verify>
  <done>Hash semantics are explicitly documented and match the updated deterministic payloads.</done>
</task>

</tasks>

<verification>
- Hash computations ignore created_at and produce stable values for identical data.
</verification>

<success_criteria>
- SCR-03 truth passes: re-scoring identical inputs yields identical hashes.
</success_criteria>

<output>
After completion, create `.planning/phases/03-scoring-reporting/03-07-SUMMARY.md`
</output>
