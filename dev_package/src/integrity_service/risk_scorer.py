"""
risk_scorer.py
===============

Risk scoring service for integrity assessment.
Computes risk scores from behavioral signals with configurable thresholds.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set, TYPE_CHECKING

from .behavioral_signals import BehavioralSignalAggregator, SignalSummary


class RiskLevel(str, Enum):
    """Risk level categories for integrity assessment."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @classmethod
    def from_score(cls, score: float, thresholds: "RiskThresholds") -> "RiskLevel":
        """
        Determine risk level from a score based on thresholds.

        Args:
            score: The computed risk score (0-100)
            thresholds: Risk threshold configuration

        Returns:
            RiskLevel enum value
        """
        if score <= thresholds.low_max:
            return cls.LOW
        elif score <= thresholds.medium_max:
            return cls.MEDIUM
        else:
            return cls.HIGH


@dataclass
class RiskThresholds:
    """
    Configurable thresholds for risk level categorization.

    Default values:
    - LOW: 0-30
    - MEDIUM: 31-60
    - HIGH: 61-100
    """

    low_max: float = 30.0
    medium_max: float = 60.0
    # High is anything above medium_max (up to 100)

    def __post_init__(self):
        """Validate threshold values."""
        if self.low_max < 0 or self.low_max > 100:
            raise ValueError("low_max must be between 0 and 100")
        if self.medium_max < 0 or self.medium_max > 100:
            raise ValueError("medium_max must be between 0 and 100")
        if self.low_max >= self.medium_max:
            raise ValueError("low_max must be less than medium_max")


# Default signal weights for risk calculation
DEFAULT_SIGNAL_WEIGHTS = {
    "TAB_SWITCH": 10.0,
    "COPY_PASTE": 20.0,
    "FULLSCREEN": 30.0,
    "KEYBOARD_SHORTCUT": 15.0,
    "NETWORK_DISCONNECT": 5.0,
}


@dataclass
class SignalContribution:
    """
    Represents a signal's contribution to the overall risk score.
    """

    signal_name: str
    count: int
    weight: float
    contribution: float


@dataclass
class RiskAssessment:
    """
    Complete risk assessment result.

    Contains the computed risk score, level, contributing signals,
    and recommendations for manual review.
    """

    session_id: str
    candidate_id: str
    risk_score: float  # 0-100 scale
    risk_level: RiskLevel
    contributing_signals: List[SignalContribution] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Signal summary reference
    signal_summary: Optional[SignalSummary] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value,
            "contributing_signals": [
                {
                    "signal_name": s.signal_name,
                    "count": s.count,
                    "weight": s.weight,
                    "contribution": s.contribution,
                }
                for s in self.contributing_signals
            ],
            "recommendations": self.recommendations,
        }


class RiskScorer:
    """
    Computes risk scores from behavioral signals.

    Applies configurable weights to signal categories and produces
    a risk score on a 0-100 scale with level categorization.

    Default weights:
    - TAB_SWITCH: 10 points per occurrence
    - COPY_PASTE: 20 points per occurrence
    - FULLSCREEN: 30 points per occurrence
    - KEYBOARD_SHORTCUT: 15 points per occurrence
    - NETWORK_DISCONNECT: 5 points per occurrence
    """

    def __init__(
        self,
        signal_weights: Optional[Dict[str, float]] = None,
        thresholds: Optional[RiskThresholds] = None,
    ):
        """
        Initialize the risk scorer.

        Args:
            signal_weights: Optional custom weights for signal categories.
                          If None, uses DEFAULT_SIGNAL_WEIGHTS.
            thresholds: Optional custom risk thresholds.
                       If None, uses default thresholds (LOW: 0-30, MEDIUM: 31-60).
        """
        self._signal_weights = signal_weights or DEFAULT_SIGNAL_WEIGHTS.copy()
        self._thresholds = thresholds or RiskThresholds()
        self._aggregator = BehavioralSignalAggregator()

    @property
    def signal_weights(self) -> Dict[str, float]:
        """Get the current signal weights."""
        return self._signal_weights.copy()

    @property
    def thresholds(self) -> RiskThresholds:
        """Get the current risk thresholds."""
        return self._thresholds

    def set_signal_weight(self, signal_name: str, weight: float) -> None:
        """
        Update the weight for a specific signal type.

        Args:
            signal_name: The signal type name (e.g., "TAB_SWITCH")
            weight: The new weight value
        """
        if weight < 0:
            raise ValueError("Weight must be non-negative")
        self._signal_weights[signal_name] = weight

    def set_thresholds(self, thresholds: RiskThresholds) -> None:
        """
        Set custom risk thresholds.

        Args:
            thresholds: RiskThresholds configuration
        """
        self._thresholds = thresholds

    def compute_risk_score(self, signal_summary: SignalSummary) -> float:
        """
        Compute the risk score from a signal summary.

        The score is calculated as a weighted sum of signal counts,
        capped at 100.

        Args:
            signal_summary: Aggregated signal data

        Returns:
            Risk score on a 0-100 scale
        """
        score = 0.0

        # TAB_SWITCH contribution
        tab_contribution = signal_summary.tab_switch_count * self._signal_weights.get(
            "TAB_SWITCH", 0
        )
        score += tab_contribution

        # COPY_PASTE contribution (combined copy + paste attempts)
        copy_paste_count = (
            signal_summary.copy_attempt_count + signal_summary.paste_attempt_count
        )
        copy_paste_contribution = copy_paste_count * self._signal_weights.get(
            "COPY_PASTE", 0
        )
        score += copy_paste_contribution

        # FULLSCREEN contribution
        fullscreen_contribution = (
            signal_summary.fullscreen_exit_count
            * self._signal_weights.get("FULLSCREEN", 0)
        )
        score += fullscreen_contribution

        # KEYBOARD_SHORTCUT contribution
        keyboard_contribution = (
            signal_summary.keyboard_shortcut_count
            * self._signal_weights.get("KEYBOARD_SHORTCUT", 0)
        )
        score += keyboard_contribution

        # NETWORK_DISCONNECT contribution
        network_contribution = (
            signal_summary.network_disconnect_count
            * self._signal_weights.get("NETWORK_DISCONNECT", 0)
        )
        score += network_contribution

        # Cap at 100
        return min(score, 100.0)

    def _generate_contributing_signals(
        self, signal_summary: SignalSummary
    ) -> List[SignalContribution]:
        """
        Generate detailed signal contributions for the assessment.

        Args:
            signal_summary: Aggregated signal data

        Returns:
            List of SignalContribution objects
        """
        contributions = []

        # Tab switches
        if signal_summary.tab_switch_count > 0:
            weight = self._signal_weights.get("TAB_SWITCH", 0)
            contributions.append(
                SignalContribution(
                    signal_name="TAB_SWITCH",
                    count=signal_summary.tab_switch_count,
                    weight=weight,
                    contribution=signal_summary.tab_switch_count * weight,
                )
            )

        # Copy attempts
        if signal_summary.copy_attempt_count > 0:
            weight = self._signal_weights.get("COPY_PASTE", 0)
            contributions.append(
                SignalContribution(
                    signal_name="COPY_ATTEMPT",
                    count=signal_summary.copy_attempt_count,
                    weight=weight,
                    contribution=signal_summary.copy_attempt_count * weight,
                )
            )

        # Paste attempts
        if signal_summary.paste_attempt_count > 0:
            weight = self._signal_weights.get("COPY_PASTE", 0)
            contributions.append(
                SignalContribution(
                    signal_name="PASTE_ATTEMPT",
                    count=signal_summary.paste_attempt_count,
                    weight=weight,
                    contribution=signal_summary.paste_attempt_count * weight,
                )
            )

        # Fullscreen exits
        if signal_summary.fullscreen_exit_count > 0:
            weight = self._signal_weights.get("FULLSCREEN", 0)
            contributions.append(
                SignalContribution(
                    signal_name="FULLSCREEN_EXIT",
                    count=signal_summary.fullscreen_exit_count,
                    weight=weight,
                    contribution=signal_summary.fullscreen_exit_count * weight,
                )
            )

        # Keyboard shortcuts
        if signal_summary.keyboard_shortcut_count > 0:
            weight = self._signal_weights.get("KEYBOARD_SHORTCUT", 0)
            contributions.append(
                SignalContribution(
                    signal_name="KEYBOARD_SHORTCUT",
                    count=signal_summary.keyboard_shortcut_count,
                    weight=weight,
                    contribution=signal_summary.keyboard_shortcut_count * weight,
                )
            )

        # Network disconnects
        if signal_summary.network_disconnect_count > 0:
            weight = self._signal_weights.get("NETWORK_DISCONNECT", 0)
            contributions.append(
                SignalContribution(
                    signal_name="NETWORK_DISCONNECT",
                    count=signal_summary.network_disconnect_count,
                    weight=weight,
                    contribution=signal_summary.network_disconnect_count * weight,
                )
            )

        return contributions

    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        signal_summary: SignalSummary,
        contributions: List[SignalContribution],
    ) -> List[str]:
        """
        Generate recommendations based on risk assessment.

        Args:
            risk_level: The computed risk level
            signal_summary: The signal summary data
            contributions: Signal contributions

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if risk_level == RiskLevel.HIGH:
            recommendations.append("Flag for manual integrity review")
            recommendations.append("Review raw integrity events for patterns")

            # Add specific high-risk signal recommendations
            if signal_summary.fullscreen_exit_count > 0:
                recommendations.append(
                    f"Investigate {signal_summary.fullscreen_exit_count} fullscreen exit(s)"
                )
            if (
                signal_summary.copy_attempt_count > 0
                or signal_summary.paste_attempt_count > 0
            ):
                recommendations.append(
                    f"Review {signal_summary.copy_attempt_count + signal_summary.paste_attempt_count} "
                    "copy/paste attempt(s)"
                )

        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("Monitor closely for additional violations")

            if signal_summary.tab_switch_count > 5:
                recommendations.append("Review tab switch patterns")

        else:  # LOW
            recommendations.append("No action required")

        # Always include session duration info
        if signal_summary.session_duration_seconds > 0:
            duration_min = signal_summary.session_duration_seconds / 60
            recommendations.append(f"Session duration: {duration_min:.1f} minutes")

        return recommendations

    def assess_risk(
        self,
        session_id: str,
        candidate_id: str = "unknown",
    ) -> RiskAssessment:
        """
        Perform a complete risk assessment for a session.

        Args:
            session_id: The assessment session ID
            candidate_id: The candidate ID

        Returns:
            RiskAssessment with score, level, and recommendations
        """
        # Aggregate signals
        signal_summary = self._aggregator.aggregate_signals(session_id, candidate_id)

        # Compute risk score
        risk_score = self.compute_risk_score(signal_summary)

        # Determine risk level
        risk_level = RiskLevel.from_score(risk_score, self._thresholds)

        # Get contributing signals
        contributions = self._generate_contributing_signals(signal_summary)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_level, signal_summary, contributions
        )

        return RiskAssessment(
            session_id=session_id,
            candidate_id=candidate_id,
            risk_score=risk_score,
            risk_level=risk_level,
            contributing_signals=contributions,
            recommendations=recommendations,
            signal_summary=signal_summary,
        )

    def get_signal_summary(
        self,
        session_id: str,
        candidate_id: str = "unknown",
    ) -> SignalSummary:
        """
        Get the aggregated signal summary for a session.

        Args:
            session_id: The assessment session ID
            candidate_id: The candidate ID

        Returns:
            SignalSummary with aggregated signals
        """
        return self._aggregator.aggregate_signals(session_id, candidate_id)


# Module-level convenience function
_default_scorer: Optional[RiskScorer] = None


def get_risk_assessment(
    session_id: str,
    candidate_id: str = "unknown",
) -> RiskAssessment:
    """
    Convenience function to get a risk assessment for a session.

    Uses a module-level RiskScorer instance with default configuration.

    Args:
        session_id: The assessment session ID
        candidate_id: The candidate ID

    Returns:
        RiskAssessment with score, level, and recommendations
    """
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = RiskScorer()
    return _default_scorer.assess_risk(session_id, candidate_id)
