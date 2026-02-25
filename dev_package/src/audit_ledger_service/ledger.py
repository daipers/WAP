"""
ledger.py
=========

This module implements a basic audit ledger.  Entries are appended
sequentially with a cryptographic hash chain to provide tamper
evidence.  For simplicity, we keep the ledger in memory.  In a real
system the ledger would be persisted to a database or external
append‑only log service.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
import hashlib
import json
import time

if TYPE_CHECKING:
    from audit_ledger_service.events import AuditEvent, EventType

# Import EventType for type hints - will be loaded lazily to avoid circular imports
EventType = None


def _get_event_type():
    """Lazy import of EventType to avoid circular imports."""
    global EventType
    if EventType is None:
        from audit_ledger_service.events import EventType
    return EventType


@dataclass
class LedgerEntry:
    event_id: int
    timestamp: float
    session_id: str
    candidate_id: str
    actor: str
    event_type: str
    action: str
    payload: Dict[str, Any]
    prev_hash: Optional[str]
    hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class AuditLedger:
    # Genesis hash - hardcoded initial hash for the chain
    _genesis_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self):
        self.entries: List[LedgerEntry] = []
        self._next_event_id = 1
        self._last_hash: Optional[str] = None

    def _compute_hash(self, data: str, include_genesis: bool = False) -> str:
        """Compute hash, optionally including genesis check."""
        if include_genesis and self._last_hash is None:
            # This would be the first entry - use genesis
            content = data + f",genesis:{self._genesis_hash}"
        else:
            content = data
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def record_event(
        self,
        session_id: str,
        actor: str,
        action: str,
        payload: Dict[str, Any],
        candidate_id: str = "unknown",
    ) -> LedgerEntry:
        """
        Legacy method for backward compatibility.
        Records an event with hash chain linking.
        """
        timestamp = time.time()
        prev_hash = (
            self._last_hash if self._last_hash is not None else self._genesis_hash
        )
        # Build a canonical string representation of the entry contents
        content = {
            "event_id": self._next_event_id,
            "timestamp": timestamp,
            "session_id": session_id,
            "candidate_id": candidate_id,
            "actor": actor,
            "event_type": action,
            "action": action,
            "payload": payload,
            "metadata": {},
            "prev_hash": prev_hash,
        }
        data_str = json.dumps(content, sort_keys=True)
        entry_hash = self._compute_hash(data_str)
        entry = LedgerEntry(
            event_id=self._next_event_id,
            timestamp=timestamp,
            session_id=session_id,
            candidate_id=candidate_id,
            actor=actor,
            event_type=action,
            action=action,
            payload=payload,
            metadata={},
            prev_hash=prev_hash,
            hash=entry_hash,
        )
        # Update ledger state
        self.entries.append(entry)
        self._last_hash = entry_hash
        self._next_event_id += 1
        return entry

    def record_audit_event(self, event: "AuditEvent") -> LedgerEntry:
        """
        Record an AuditEvent to the ledger with hash chain linking.

        Args:
            event: AuditEvent instance to record

        Returns:
            LedgerEntry created from the event
        """
        # Get event_type value (handles both Enum and string)
        event_type_val = (
            event.event_type.value
            if hasattr(event.event_type, "value")
            else str(event.event_type)
        )

        timestamp = event.timestamp
        prev_hash = (
            self._last_hash if self._last_hash is not None else self._genesis_hash
        )

        # Build canonical content for hashing
        content = {
            "event_id": self._next_event_id,
            "timestamp": timestamp,
            "session_id": event.session_id,
            "candidate_id": event.candidate_id,
            "actor": event.actor,
            "event_type": event_type_val,
            "action": event_type_val,
            "payload": event.payload,
            "metadata": event.metadata,
            "prev_hash": prev_hash,
        }
        data_str = json.dumps(content, sort_keys=True)
        entry_hash = self._compute_hash(data_str)

        entry = LedgerEntry(
            event_id=self._next_event_id,
            timestamp=timestamp,
            session_id=event.session_id,
            candidate_id=event.candidate_id,
            actor=event.actor,
            event_type=event.event_type.value
            if hasattr(event.event_type, "value")
            else str(event.event_type),
            action=event.event_type.value
            if hasattr(event.event_type, "value")
            else str(event.event_type),
            payload=event.payload,
            metadata=event.metadata,
            prev_hash=prev_hash,
            hash=entry_hash,
        )

        # Update ledger state
        self.entries.append(entry)
        self._last_hash = entry_hash
        self._next_event_id += 1
        return entry

    def get_events_by_session(self, session_id: str) -> List[LedgerEntry]:
        """Get all events for a specific session."""
        return [entry for entry in self.entries if entry.session_id == session_id]

    def get_events_by_candidate(self, candidate_id: str) -> List[LedgerEntry]:
        """Get all events for a specific candidate."""
        return [entry for entry in self.entries if entry.candidate_id == candidate_id]

    def get_events_by_type(self, event_type: Union[str, Any]) -> List[LedgerEntry]:
        """Get all events of a specific type."""
        type_str = getattr(event_type, "value", event_type)
        type_str = str(type_str)
        return [entry for entry in self.entries if entry.event_type == type_str]

    def get_session_attempt_events(
        self, session_id: str
    ) -> Dict[str, List[LedgerEntry]]:
        """
        Get all events for a session grouped by event type.

        Returns:
            Dict mapping event_type to list of LedgerEntry objects
        """
        session_events = self.get_events_by_session(session_id)
        grouped: Dict[str, List[LedgerEntry]] = {}
        for entry in session_events:
            if entry.event_type not in grouped:
                grouped[entry.event_type] = []
            grouped[entry.event_type].append(entry)
        return grouped

    def export_audit_log(self, output_path: str) -> None:
        """
        Export the audit log to JSON Lines format.

        Args:
            output_path: Path to write the JSON Lines file
        """
        with open(output_path, "w") as f:
            for entry in self.entries:
                f.write(json.dumps(entry.to_dict()) + "\n")

    def get_last_event_hash(self, session_id: str) -> Optional[str]:
        """Get the most recent hash for a specific session."""
        session_events = self.get_events_by_session(session_id)
        if not session_events:
            return None
        return session_events[-1].hash

    def verify_session_events(self, session_id: str) -> tuple[bool, List[LedgerEntry]]:
        """
        Verify the hash chain for events in a specific session.

        Returns:
            Tuple of (is_valid, list_of_invalid_entries)
        """
        session_events = self.get_events_by_session(session_id)
        if not session_events:
            return True, []

        invalid_entries = []

        # Build a map of event_id -> entry for quick lookup
        event_by_id = {entry.event_id: entry for entry in self.entries}

        # Track prev_hash per session - start with genesis
        session_prev_hash = self._genesis_hash

        # Go through ALL entries in order to maintain proper chain
        for entry in self.entries:
            if entry.session_id != session_id:
                # Update global tracking even if not this session
                session_prev_hash = entry.hash
                continue

            # Recreate the content that was hashed (must match record_audit_event exactly)
            content = {
                "event_id": entry.event_id,
                "timestamp": entry.timestamp,
                "session_id": entry.session_id,
                "candidate_id": entry.candidate_id,
                "actor": entry.actor,
                "event_type": entry.event_type,
                "action": entry.action,
                "payload": entry.payload,
                "metadata": entry.metadata,
                "prev_hash": session_prev_hash,
            }
            data_str = json.dumps(content, sort_keys=True)

            # Compute expected hash
            computed_hash = self._compute_hash(data_str)

            if computed_hash != entry.hash:
                invalid_entries.append(entry)

            # Update prev_hash for next event in this session
            session_prev_hash = entry.hash

        return len(invalid_entries) == 0, invalid_entries

    def export_for_attestation(self, session_id: str, output_path: str) -> None:
        """
        Export session events with signatures for third-party attestation.

        Args:
            session_id: The session to export
            output_path: Path to write the attestation file
        """
        session_events = self.get_events_by_session(session_id)
        attestation_data = {
            "session_id": session_id,
            "event_count": len(session_events),
            "first_event_timestamp": session_events[0].timestamp
            if session_events
            else None,
            "last_event_timestamp": session_events[-1].timestamp
            if session_events
            else None,
            "genesis_hash": self._genesis_hash,
            "final_hash": session_events[-1].hash
            if session_events
            else self._genesis_hash,
            "events": [entry.to_dict() for entry in session_events],
        }

        with open(output_path, "w") as f:
            json.dump(attestation_data, f, indent=2)

    def verify_chain(self) -> bool:
        """
        Verify the integrity of the hash chain.  Returns True if all hashes
        are valid and linked correctly.
        """
        prev_hash = self._genesis_hash
        for entry in self.entries:
            content = {
                "event_id": entry.event_id,
                "timestamp": entry.timestamp,
                "session_id": entry.session_id,
                "candidate_id": entry.candidate_id,
                "actor": entry.actor,
                "event_type": entry.event_type,
                "action": entry.action,
                "payload": entry.payload,
                "metadata": entry.metadata,
                "prev_hash": prev_hash,
            }
            data_str = json.dumps(content, sort_keys=True)
            if self._compute_hash(data_str) != entry.hash:
                return False
            prev_hash = entry.hash
        return True
