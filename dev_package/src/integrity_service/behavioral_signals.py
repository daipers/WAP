"""
behavioral_signals.py
======================

Behavioral signal aggregator for integrity monitoring.
Aggregates integrity events into signal categories for risk assessment.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

from audit_ledger_service.ledger import AuditLedger, LedgerEntry
from delivery_service.integrity_events import IntegrityEventType, IntegrityEventLogger


# Signal categories used in risk scoring
class SignalCategory(str, Enum):
    """Categories of behavioral signals for integrity analysis."""

    TAB_SWITCH_COUNT = "TAB_SWITCH_COUNT"
    COPY_PASTE_COUNT = "COPY_PASTE_COUNT"
    FULLSCREEN_VIOLATIONS = "FULLSCREEN_VIOLATIONS"
    IDLE_TIME = "IDLE_TIME"
    TOTAL_VIOLATIONS = "TOTAL_VIOLATIONS"
    VIOLATION_RATE = "VIOLATION_RATE"


@dataclass
class SignalSummary:
    """
    Aggregated signal data for a session.
    Contains both raw counts and derived metrics.
    """

    session_id: str
    candidate_id: str

    # Raw signal counts
    tab_switch_count: int = 0
    copy_attempt_count: int = 0
    paste_attempt_count: int = 0
    fullscreen_exit_count: int = 0
    keyboard_shortcut_count: int = 0
    network_disconnect_count: int = 0

    # Derived metrics
    total_violations: int = 0
    violation_rate: float = 0.0  # violations per minute

    # Session context
    session_duration_seconds: float = 0.0
    session_start_time: Optional[float] = None
    session_end_time: Optional[float] = None

    # Raw events (optional, for detailed analysis)
    raw_events: List[LedgerEntry] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "signals": {
                "tab_switch_count": self.tab_switch_count,
                "copy_attempt_count": self.copy_attempt_count,
                "paste_attempt_count": self.paste_attempt_count,
                "fullscreen_exit_count": self.fullscreen_exit_count,
                "keyboard_shortcut_count": self.keyboard_shortcut_count,
                "network_disconnect_count": self.network_disconnect_count,
                "total_violations": self.total_violations,
                "violation_rate": self.violation_rate,
            },
            "session_duration_seconds": self.session_duration_seconds,
            "session_start_time": self.session_start_time,
            "session_end_time": self.session_end_time,
        }


class BehavioralSignalAggregator:
    """
    Aggregates integrity events into behavioral signals for risk assessment.

    Queries the audit ledger for integrity events and computes signal
    categories including:
    - TAB_SWITCH_COUNT: Number of times the candidate switched tabs
    - COPY_PASTE_COUNT: Number of copy/paste attempts
    - FULLSCREEN_VIOLATIONS: Number of fullscreen exits
    - IDLE_TIME: Time spent away from the assessment (via tab hidden)
    - TOTAL_VIOLATIONS: Sum of all integrity violations
    - VIOLATION_RATE: Violations per minute of session time
    """

    def __init__(self, ledger: Optional[AuditLedger] = None):
        """
        Initialize the behavioral signal aggregator.

        Args:
            ledger: Optional AuditLedger instance. If None, creates a new one.
        """
        self._ledger = ledger if ledger is not None else AuditLedger()
        self._logger = IntegrityEventLogger(self._ledger)

    def aggregate_signals(
        self,
        session_id: str,
        candidate_id: str = "unknown",
    ) -> SignalSummary:
        """
        Aggregate all behavioral signals for a session.

        Args:
            session_id: The assessment session ID
            candidate_id: The candidate ID

        Returns:
            SignalSummary with all computed signal values
        """
        # Get all events for the session
        session_events = self._ledger.get_events_by_session(session_id)

        if not session_events:
            return SignalSummary(
                session_id=session_id,
                candidate_id=candidate_id,
            )

        # Calculate session timing
        session_start = min(e.timestamp for e in session_events)
        session_end = max(e.timestamp for e in session_events)
        session_duration = session_end - session_start

        # Count events by type
        tab_switch_count = 0
        copy_attempt_count = 0
        paste_attempt_count = 0
        fullscreen_exit_count = 0
        keyboard_shortcut_count = 0
        network_disconnect_count = 0

        integrity_event_types = {
            IntegrityEventType.TAB_HIDDEN.value,
            IntegrityEventType.TAB_VISIBLE.value,
            IntegrityEventType.COPY_ATTEMPT.value,
            IntegrityEventType.PASTE_ATTEMPT.value,
            IntegrityEventType.FULLSCREEN_EXIT.value,
            IntegrityEventType.KEYBOARD_SHORTCUT.value,
            IntegrityEventType.NETWORK_DISCONNECT.value,
        }

        for entry in session_events:
            event_type = entry.event_type
            if event_type == IntegrityEventType.TAB_HIDDEN.value:
                tab_switch_count += 1
            elif event_type == IntegrityEventType.COPY_ATTEMPT.value:
                copy_attempt_count += 1
            elif event_type == IntegrityEventType.PASTE_ATTEMPT.value:
                paste_attempt_count += 1
            elif event_type == IntegrityEventType.FULLSCREEN_EXIT.value:
                fullscreen_exit_count += 1
            elif event_type == IntegrityEventType.KEYBOARD_SHORTCUT.value:
                keyboard_shortcut_count += 1
            elif event_type == IntegrityEventType.NETWORK_DISCONNECT.value:
                network_disconnect_count += 1

        # Calculate totals
        copy_paste_count = copy_attempt_count + paste_attempt_count
        total_violations = (
            tab_switch_count
            + copy_paste_count
            + fullscreen_exit_count
            + keyboard_shortcut_count
        )

        # Calculate violation rate (per minute)
        session_duration_minutes = (
            session_duration / 60.0 if session_duration > 0 else 0
        )
        violation_rate = (
            total_violations / session_duration_minutes
            if session_duration_minutes > 0
            else 0
        )

        return SignalSummary(
            session_id=session_id,
            candidate_id=candidate_id,
            tab_switch_count=tab_switch_count,
            copy_attempt_count=copy_attempt_count,
            paste_attempt_count=paste_attempt_count,
            fullscreen_exit_count=fullscreen_exit_count,
            keyboard_shortcut_count=keyboard_shortcut_count,
            network_disconnect_count=network_disconnect_count,
            total_violations=total_violations,
            violation_rate=violation_rate,
            session_duration_seconds=session_duration,
            session_start_time=session_start,
            session_end_time=session_end,
            raw_events=session_events,
        )

    def get_session_events(self, session_id: str) -> List[LedgerEntry]:
        """
        Get all events for a session from the audit ledger.

        Args:
            session_id: The assessment session ID

        Returns:
            List of LedgerEntry objects
        """
        return self._ledger.get_events_by_session(session_id)
