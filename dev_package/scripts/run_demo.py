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
from feature_extractor.extractor import FeatureExtractor  # type: ignore
from scoring_engine.scoring import ScoringEngine  # type: ignore
from integrity_service.integrity_checker import IntegrityChecker  # type: ignore
from reporting_service.reporting import ReportingService  # type: ignore
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
    content_bank = ContentBankService(str(challenge_bank_path), str(injections_path), seed=42)
    interview_agent = InterviewAgent(content_bank=content_bank, orchestrator=orchestrator, ledger=ledger)
    feature_extractor = FeatureExtractor()
    scoring_engine = ScoringEngine(str(rubric_path))
    integrity_checker = IntegrityChecker()
    rubric = scoring_engine.rubric
    reporting_service = ReportingService(rubric)

    # Create candidate and start session
    candidate = identity_service.create_candidate(email="candidate@example.com", consent_version="1.0")
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
    features = feature_extractor.extract_features(session)

    # Integrity check
    integrity_flags = integrity_checker.check(session)
    features["values"].update({"integrity_flags.high_risk": integrity_flags.get("high_risk", False)})

    # Score
    orchestrator.score(session)
    scores = scoring_engine.score(features)
    # Quality gate: pass if not disqualified and scores above some minimal threshold
    passed_quality = scores.get("CPS", 0) > 20 and scores.get("ASI", 0) > 20 and not scores.get("disqualified")
    orchestrator.quality_gate(session, passed_quality)
    if passed_quality:
        orchestrator.publish(session)
    else:
        orchestrator.void(session)

    # Generate scorecard
    scorecard = reporting_service.generate_scorecard(candidate.candidate_id, scores)

    # Output results
    print("Scorecard:")
    for key, value in scorecard.items():
        print(f"{key}: {value}")
    print("\nLedger verified:", ledger.verify_chain())


if __name__ == "__main__":
    main()