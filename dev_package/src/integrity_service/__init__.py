"""Integrity service package."""

from .integrity_checker import IntegrityChecker
from .behavioral_signals import BehavioralSignalAggregator, SignalSummary
from .risk_scorer import (
    RiskScorer,
    RiskLevel,
    RiskAssessment,
    RiskThresholds,
    get_risk_assessment,
)

__all__ = [
    "IntegrityChecker",
    "BehavioralSignalAggregator",
    "SignalSummary",
    "RiskScorer",
    "RiskLevel",
    "RiskAssessment",
    "RiskThresholds",
    "get_risk_assessment",
]


def get_risk_assessment(
    session_id: str, candidate_id: str = "unknown"
) -> RiskAssessment:
    """
    Convenience function to get a risk assessment for a session.

    Args:
        session_id: The assessment session ID
        candidate_id: The candidate ID

    Returns:
        RiskAssessment with score, level, and recommendations
    """
    scorer = RiskScorer()
    return scorer.assess_risk(session_id, candidate_id)
