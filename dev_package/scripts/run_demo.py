#!/usr/bin/env python3
"""
run_demo.py
===========

This script demonstrates a minimal end‑to‑end flow through the WAA‑ADS
pipeline using the skeleton services provided in this package.  It
creates a candidate, starts a session, runs a diagnostic and live
interview (simulated), extracts features, scores the session, checks
integrity, and generates a simple scorecard.

Run this script from the repository root with:

    python3 scripts/run_demo.py

Note: This demo is highly simplified and meant for learning purposes.
"""

import os
import sys
from pathlib import Path

# Adjust sys.path so that the 'src' package can be imported when this script
# is executed as a standalone file.  This allows relative imports to work
# without installing the package.
BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
sys.path.append(str(SRC_DIR))

from identity_service.identity import IdentityService  # type: ignore
from orchestrator_service.orchestrator import Orchestrator  # type: ignore
from content_bank_service.content_bank import ContentBankService  # type: ignore
from interview_agent_service.interview_agent import InterviewAgent  # type: ignore
from scoring_engine.scoring import ScoringEngine  # type: ignore
from scoring_engine.score_runs import ScoreRunRepository  # type: ignore
from scoring_engine.scoring_service import ScoringService  # type: ignore
from integrity_service.integrity_checker import IntegrityChecker  # type: ignore
from reporting_service.reporting import ReportingService  # type: ignore
from reporting_service.csv_export import export_scorecard_csv  # type: ignore
from audit_ledger_service.ledger import AuditLedger  # type: ignore


def main():
    base_path = BASE_DIR
    state_machine_path = base_path / "configs" / "state_machine.yaml"
    rubric_path = base_path / "configs" / "rubric.yaml"
    challenge_bank_path = base_path / "data" / "challenge_bank.json"
    injections_path = base_path / "data" / "failure_injections.json"

    # Initialise core services
    ledger = AuditLedger()
    identity_service = IdentityService(str(state_machine_path))
    orchestrator = Orchestrator(ledger=ledger)
    content_bank = ContentBankService(
        str(challenge_bank_path), str(injections_path), seed=42
    )
    interview_agent = InterviewAgent(
        content_bank=content_bank, orchestrator=orchestrator, ledger=ledger
    )
    scoring_engine = ScoringEngine(str(rubric_path))
    score_runs = ScoreRunRepository()
    scoring_service = ScoringService(
        scoring_engine=scoring_engine,
        audit_ledger=ledger,
        score_runs=score_runs,
    )
    integrity_checker = IntegrityChecker()
    rubric = scoring_engine.rubric
    reporting_service = ReportingService(rubric)

    # Create candidate and start session
    candidate = identity_service.create_candidate(
        email="candidate@example.com", consent_version="1.0"
    )
    session = identity_service.start_session(candidate.candidate_id)
    # Record consent; update state
    identity_service.record_consent(candidate.candidate_id, "1.0")
    orchestrator.trigger_event(session, "on_consent_received")

    # Start and submit diagnostic (simplified)
    orchestrator.start_diagnostic(session)
    # Candidate completes diagnostic tasks here (omitted)
    orchestrator.submit_diagnostic(session)

    # Schedule and run interview
    orchestrator.schedule_interview(session)
    interview_agent.run_interview(session)

    # Extract features
    orchestrator.extract_features(session)

    # Integrity check
    integrity_flags = integrity_checker.check(session)

    # Score
    orchestrator.score(session)
    item_id = (
        session.selected_challenges[0] if session.selected_challenges else "demo-item"
    )
    responses = {
        item_id: {
            "answer": "<candidate response>",
            "integrity_flags": integrity_flags,
        }
    }
    item_context = {
        "item_id": item_id,
        "rubric_path": str(rubric_path),
        "rubric_version": rubric.get("version", "unknown"),
    }
    score_run = scoring_service.score_session(
        session_id=session.session_id,
        candidate_id=candidate.candidate_id,
        responses=responses,
        item_context=item_context,
    )
    scores = score_run.score_output
    # Quality gate: pass if not disqualified and scores above some minimal threshold
    passed_quality = (
        scores.get("CPS", 0) > 20
        and scores.get("ASI", 0) > 20
        and not scores.get("disqualified")
    )
    orchestrator.quality_gate(session, passed_quality)
    if passed_quality:
        orchestrator.publish(session)
    else:
        orchestrator.void(session)

    # Generate scorecard
    response_snapshot = score_runs.get_snapshot_by_id(score_run.response_snapshot_id)
    if response_snapshot is None:
        raise ValueError("Response snapshot not found for score run")
    scorecard = reporting_service.generate_scorecard(
        candidate.candidate_id, score_run, response_snapshot
    )
    csv_path = export_scorecard_csv(
        scorecard, str(base_path / "data" / "scorecard.csv")
    )

    # Output results
    print(f"Score run id: {score_run.score_run_id}")
    print(f"Scorecard CSV: {csv_path}")
    print("Scorecard summary:")
    for key in ("candidate_id", "CPS", "ASI", "credential_level"):
        print(f"{key}: {scorecard.get(key)}")
    print("Evidence items:", len(scorecard.get("evidence", {})))
    print("\nLedger verified:", ledger.verify_chain())


if __name__ == "__main__":
    main()
