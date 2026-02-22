"""
integrity_events.py
===================

Integrity event logging for assessment delivery.
Logs events like fullscreen enter/exit, tab visibility, copy/paste attempts, etc.
Uses the existing audit ledger for storage.
"""

from enum import Enum
from typing import Dict, List, Optional, Any

from audit_ledger_service.ledger import AuditLedger, LedgerEntry
from audit_ledger_service.events import AuditEvent, EventType
import time


class IntegrityEventType(str, Enum):
    """Event types specific to integrity monitoring during assessment delivery."""

    FULLSCREEN_ENTER = "fullscreen_enter"
    FULLSCREEN_EXIT = "fullscreen_exit"
    TAB_VISIBLE = "tab_visible"
    TAB_HIDDEN = "tab_hidden"
    COPY_ATTEMPT = "copy_attempt"
    PASTE_ATTEMPT = "paste_attempt"
    KEYBOARD_SHORTCUT = "keyboard_shortcut"
    NETWORK_DISCONNECT = "network_disconnect"
    NETWORK_RECONNECT = "network_reconnect"


class IntegrityEventLogger:
    """
    Logger for integrity-specific events during assessment delivery.
    Wraps the AuditLedger to provide precise timestamps and event tracking.
    """

    def __init__(self, ledger: Optional[AuditLedger] = None):
        """
        Initialize the integrity event logger.

        Args:
            ledger: AuditLedger instance. If None, creates a new one.
        """
        self._ledger = ledger if ledger is not None else AuditLedger()

    @property
    def ledger(self) -> AuditLedger:
        """Get the underlying audit ledger."""
        return self._ledger

    def log_event(
        self,
        session_id: str,
        event_type: IntegrityEventType,
        metadata: Optional[Dict[str, Any]] = None,
        candidate_id: str = "unknown",
        actor: str = "system",
    ) -> LedgerEntry:
        """
        Log an integrity event to the audit ledger.

        Args:
            session_id: The assessment session ID
            event_type: The type of integrity event
            metadata: Additional event-specific metadata
            candidate_id: The candidate ID (defaults to "unknown")
            actor: Who triggered the event (system, candidate, browser, etc.)

        Returns:
            LedgerEntry that was recorded
        """
        timestamp = time.time()

        # Create payload with event type and metadata
        payload = {
            "event_type": event_type.value,
            "metadata": metadata or {},
        }

        # Record to the audit ledger
        entry = self._ledger.record_event(
            session_id=session_id,
            actor=actor,
            action=event_type.value,
            payload=payload,
            candidate_id=candidate_id,
        )

        return entry

    def get_session_events(self, session_id: str) -> List[LedgerEntry]:
        """
        Retrieve all integrity events for a specific session.

        Args:
            session_id: The assessment session ID

        Returns:
            List of LedgerEntry objects for the session
        """
        return self._ledger.get_events_by_session(session_id)

    def get_events_by_type(
        self, session_id: str, event_type: IntegrityEventType
    ) -> List[LedgerEntry]:
        """
        Get integrity events of a specific type for a session.

        Args:
            session_id: The assessment session ID
            event_type: The type of event to filter by

        Returns:
            List of matching LedgerEntry objects
        """
        session_events = self.get_session_events(session_id)
        return [
            entry for entry in session_events if entry.event_type == event_type.value
        ]

    def count_tab_switches(self, session_id: str) -> int:
        """
        Count the number of tab switches (TAB_HIDDEN events) for a session.

        Args:
            session_id: The assessment session ID

        Returns:
            Count of tab switch events
        """
        hidden_events = self.get_events_by_type(
            session_id, IntegrityEventType.TAB_HIDDEN
        )
        return len(hidden_events)

    def get_fullscreen_violations(self, session_id: str) -> List[LedgerEntry]:
        """
        Get all fullscreen exit events (potential violations).

        Args:
            session_id: The assessment session ID

        Returns:
            List of FULLSCREEN_EXIT LedgerEntry objects
        """
        return self.get_events_by_type(session_id, IntegrityEventType.FULLSCREEN_EXIT)

    def log_fullscreen_enter(
        self,
        session_id: str,
        candidate_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Log fullscreen mode entered."""
        return self.log_event(
            session_id=session_id,
            event_type=IntegrityEventType.FULLSCREEN_ENTER,
            metadata=metadata,
            candidate_id=candidate_id,
            actor="browser",
        )

    def log_fullscreen_exit(
        self,
        session_id: str,
        candidate_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Log fullscreen mode exited."""
        return self.log_event(
            session_id=session_id,
            event_type=IntegrityEventType.FULLSCREEN_EXIT,
            metadata=metadata,
            candidate_id=candidate_id,
            actor="browser",
        )

    def log_tab_visible(
        self,
        session_id: str,
        candidate_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Log tab became visible."""
        return self.log_event(
            session_id=session_id,
            event_type=IntegrityEventType.TAB_VISIBLE,
            metadata=metadata,
            candidate_id=candidate_id,
            actor="browser",
        )

    def log_tab_hidden(
        self,
        session_id: str,
        candidate_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Log tab became hidden (switched away)."""
        return self.log_event(
            session_id=session_id,
            event_type=IntegrityEventType.TAB_HIDDEN,
            metadata=metadata,
            candidate_id=candidate_id,
            actor="browser",
        )

    def log_copy_attempt(
        self,
        session_id: str,
        candidate_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Log copy attempt blocked."""
        return self.log_event(
            session_id=session_id,
            event_type=IntegrityEventType.COPY_ATTEMPT,
            metadata=metadata,
            candidate_id=candidate_id,
            actor="browser",
        )

    def log_paste_attempt(
        self,
        session_id: str,
        candidate_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Log paste attempt blocked."""
        return self.log_event(
            session_id=session_id,
            event_type=IntegrityEventType.PASTE_ATTEMPT,
            metadata=metadata,
            candidate_id=candidate_id,
            actor="browser",
        )

    def log_keyboard_shortcut(
        self,
        session_id: str,
        candidate_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Log keyboard shortcut attempted."""
        return self.log_event(
            session_id=session_id,
            event_type=IntegrityEventType.KEYBOARD_SHORTCUT,
            metadata=metadata,
            candidate_id=candidate_id,
            actor="browser",
        )

    def log_network_disconnect(
        self,
        session_id: str,
        candidate_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Log network disconnection."""
        return self.log_event(
            session_id=session_id,
            event_type=IntegrityEventType.NETWORK_DISCONNECT,
            metadata=metadata,
            candidate_id=candidate_id,
            actor="system",
        )

    def log_network_reconnect(
        self,
        session_id: str,
        candidate_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        """Log network reconnection."""
        return self.log_event(
            session_id=session_id,
            event_type=IntegrityEventType.NETWORK_RECONNECT,
            metadata=metadata,
            candidate_id=candidate_id,
            actor="system",
        )
