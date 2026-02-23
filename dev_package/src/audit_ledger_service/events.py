"""
events.py
=========

Audit event types and schemas for the WAA-ADS assessment delivery system.
Defines event types for all delivery events and the AuditEvent dataclass.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional


class EventType(Enum):
    """All audit event types for assessment delivery."""

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    CONSENT_RECORDED = "consent_recorded"
    DIAGNOSTIC_START = "diagnostic_start"
    DIAGNOSTIC_SUBMIT = "diagnostic_submit"
    INTERVIEW_START = "interview_start"
    INTERVIEW_SUBMIT = "interview_submit"
    ANSWER_SUBMITTED = "answer_submitted"
    ITEM_VIEWED = "item_viewed"
    TERMINATE = "terminate"
    TIMEOUT = "timeout"
    SCORING_RUN_CREATED = "scoring_run_created"
    SCORING_RESCORE = "scoring_rescore"


# Payload schemas for each event type
# Defines required and optional fields for each event type
PAYLOAD_SCHEMAS: Dict[EventType, Dict[str, Any]] = {
    EventType.SESSION_START: {
        "required": ["ip_address", "user_agent"],
        "optional": ["browser_fingerprint", "platform"],
    },
    EventType.SESSION_END: {
        "required": ["reason"],
        "optional": ["duration_seconds", "events_completed"],
    },
    EventType.CONSENT_RECORDED: {
        "required": ["consent_version", "consent_given"],
        "optional": ["ip_address"],
    },
    EventType.DIAGNOSTIC_START: {
        "required": ["item_count"],
        "optional": ["time_limit"],
    },
    EventType.DIAGNOSTIC_SUBMIT: {
        "required": ["items_attempted", "items_correct"],
        "optional": ["time_taken_seconds"],
    },
    EventType.INTERVIEW_START: {
        "required": ["challenge_ids"],
        "optional": ["time_limit"],
    },
    EventType.INTERVIEW_SUBMIT: {
        "required": ["responses_recorded"],
        "optional": ["duration_seconds"],
    },
    EventType.ANSWER_SUBMITTED: {
        "required": ["item_id", "response"],
        "optional": ["time_taken_seconds", "flagged"],
    },
    EventType.ITEM_VIEWED: {
        "required": ["item_id"],
        "optional": ["view_duration_seconds"],
    },
    EventType.TERMINATE: {"required": ["reason"], "optional": ["actor", "notes"]},
    EventType.TIMEOUT: {
        "required": ["session_duration"],
        "optional": ["last_activity"],
    },
    EventType.SCORING_RUN_CREATED: {
        "required": [
            "score_run_id",
            "response_snapshot_id",
            "rubric_version",
            "input_hash",
            "output_hash",
        ],
        "optional": ["feature_version"],
    },
    EventType.SCORING_RESCORE: {
        "required": [
            "score_run_id",
            "response_snapshot_id",
            "rubric_version",
            "input_hash",
            "output_hash",
        ],
        "optional": ["feature_version", "reason"],
    },
}


@dataclass
class AuditEvent:
    """Represents a single audit event in the assessment system."""

    event_type: EventType
    session_id: str
    candidate_id: str
    timestamp: float
    actor: str
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate_payload(self) -> bool:
        """Validate that the payload contains required fields for this event type."""
        schema = PAYLOAD_SCHEMAS.get(self.event_type, {})
        required_fields = schema.get("required", [])

        for field_name in required_fields:
            if field_name not in self.payload:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "payload": self.payload,
            "metadata": self.metadata,
        }


def create_event(
    event_type: EventType,
    session_id: str,
    candidate_id: str,
    actor: str,
    payload: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[float] = None,
) -> AuditEvent:
    """
    Factory function to create an AuditEvent with defaults.

    Args:
        event_type: The type of event
        session_id: The assessment session ID
        candidate_id: The candidate ID
        actor: Who triggered the event (system, candidate, proctor, etc.)
        payload: Event-specific data (optional, defaults to empty dict)
        metadata: Additional metadata (optional, defaults to empty dict)
        timestamp: Event timestamp (optional, defaults to current time)

    Returns:
        AuditEvent instance
    """
    import time

    return AuditEvent(
        event_type=event_type,
        session_id=session_id,
        candidate_id=candidate_id,
        timestamp=timestamp or time.time(),
        actor=actor,
        payload=payload or {},
        metadata=metadata or {},
    )
