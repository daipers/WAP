"""
session_manager.py
=================

Manages assessment sessions with state machine patterns.
Provides AssessmentSession model and SessionManager for lifecycle management.

State transitions:
- not_started -> in_progress (on start)
- in_progress -> paused (on pause)
- paused -> in_progress (on resume)
- in_progress -> completed (on submit)
- in_progress -> expired (on time expiry)
- in_progress -> terminated (on terminate)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid

from .models import AssessmentDefinition, AssessmentSession as ModelAssessmentSession
from identity_service.identity import IdentityService


class SessionState(str, Enum):
    """Assessment session states."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    TERMINATED = "terminated"


# Valid state transitions
STATE_TRANSITIONS = {
    SessionState.NOT_STARTED: {SessionState.IN_PROGRESS},
    SessionState.IN_PROGRESS: {
        SessionState.PAUSED,
        SessionState.COMPLETED,
        SessionState.EXPIRED,
        SessionState.TERMINATED,
    },
    SessionState.PAUSED: {SessionState.IN_PROGRESS, SessionState.TERMINATED},
    SessionState.COMPLETED: set(),
    SessionState.EXPIRED: set(),
    SessionState.TERMINATED: set(),
}


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    pass


@dataclass
class AssessmentItemData:
    """Simplified item data for session delivery."""

    item_id: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionSection:
    """A section within an assembled assessment."""

    section_id: str
    name: str
    items: List[AssessmentItemData]
    time_limit_seconds: Optional[int] = None

    @property
    def item_count(self) -> int:
        return len(self.items)


@dataclass
class AssessmentSession:
    """
    Represents an active assessment session with full state tracking.
    Tracks progress, responses, timing, and state transitions.
    """

    session_id: str
    assessment_id: str
    test_taker_id: str
    candidate_id: str
    title: str
    state: SessionState = SessionState.NOT_STARTED
    current_section_index: int = 0
    current_item_index: int = 0
    responses: Dict[str, Any] = field(default_factory=dict)  # item_id -> response
    flagged_items: List[str] = field(default_factory=list)
    time_limit_seconds: Optional[int] = None
    time_remaining_seconds: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    sections: List[SessionSection] = field(default_factory=list)
    navigation_mode: str = "LINEAR"

    def _get_all_items(self) -> List[AssessmentItemData]:
        """Get all items across all sections as a flat list."""
        all_items = []
        for section in self.sections:
            all_items.extend(section.items)
        return all_items

    @property
    def items(self) -> List[AssessmentItemData]:
        """Get all items in the session."""
        return self._get_all_items()

    @property
    def total_items(self) -> int:
        """Total number of items in the assessment."""
        return sum(s.item_count for s in self.sections)

    @property
    def current_item(self) -> Optional[AssessmentItemData]:
        """Get the current item based on position."""
        all_items = self._get_all_items()
        if 0 <= self.current_item_index < len(all_items):
            return all_items[self.current_item_index]
        return None

    @property
    def current_section(self) -> Optional[SessionSection]:
        """Get the current section."""
        if 0 <= self.current_section_index < len(self.sections):
            return self.sections[self.current_section_index]
        return None

    def _can_transition_to(self, new_state: SessionState) -> bool:
        """Check if transition to new state is valid."""
        return new_state in STATE_TRANSITIONS.get(self.state, set())

    def transition_to(self, new_state: SessionState) -> None:
        """
        Transition to a new state if the transition is valid.

        Raises:
            InvalidStateTransitionError: If the transition is not allowed.
        """
        if not self._can_transition_to(new_state):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self.state.value} to {new_state.value}"
            )
        self.state = new_state

        if new_state == SessionState.COMPLETED:
            self.completed_at = datetime.utcnow()

    def get_response(self, item_id: str) -> Optional[Any]:
        """Get the response for a specific item."""
        return self.responses.get(item_id)

    def set_response(self, item_id: str, response: Any) -> None:
        """Set the response for a specific item."""
        self.responses[item_id] = response

    def flag_item(self, item_id: str) -> None:
        """Flag an item for review."""
        if item_id not in self.flagged_items:
            self.flagged_items.append(item_id)

    def unflag_item(self, item_id: str) -> None:
        """Unflag an item."""
        if item_id in self.flagged_items:
            self.flagged_items.remove(item_id)

    def is_item_flagged(self, item_id: str) -> bool:
        """Check if an item is flagged."""
        return item_id in self.flagged_items

    def get_item_at_index(self, index: int) -> Optional[AssessmentItemData]:
        """Get item at a specific index in the flat items list."""
        all_items = self._get_all_items()
        if 0 <= index < len(all_items):
            return all_items[index]
        return None

    def get_index_for_item(self, item_id: str) -> Optional[int]:
        """Get the flat index for an item by ID."""
        all_items = self._get_all_items()
        for idx, item in enumerate(all_items):
            if item.item_id == item_id:
                return idx
        return None

    def calculate_time_remaining(self) -> Optional[int]:
        """
        Calculate remaining time based on start time and time limit.
        Returns None if no time limit.
        """
        if self.time_limit_seconds is None:
            return None

        if self.started_at is None:
            return self.time_limit_seconds

        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        remaining = int(self.time_limit_seconds - elapsed)

        # Don't let it go below zero
        return max(0, remaining)

    def is_time_expired(self) -> bool:
        """Check if the session time has expired."""
        if self.time_limit_seconds is None:
            return False
        remaining = self.calculate_time_remaining()
        return remaining is not None and remaining <= 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session to dictionary for persistence."""
        return {
            "session_id": self.session_id,
            "assessment_id": self.assessment_id,
            "test_taker_id": self.test_taker_id,
            "candidate_id": self.candidate_id,
            "title": self.title,
            "state": self.state.value,
            "current_section_index": self.current_section_index,
            "current_item_index": self.current_item_index,
            "responses": self.responses,
            "flagged_items": self.flagged_items,
            "time_limit_seconds": self.time_limit_seconds,
            "time_remaining_seconds": self.calculate_time_remaining(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "sections": [
                {
                    "section_id": s.section_id,
                    "name": s.name,
                    "items": [
                        {
                            "item_id": i.item_id,
                            "content": i.content,
                            "metadata": i.metadata,
                        }
                        for i in s.items
                    ],
                    "time_limit_seconds": s.time_limit_seconds,
                }
                for s in self.sections
            ],
            "navigation_mode": self.navigation_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssessmentSession":
        """Deserialize session from dictionary."""
        # Convert sections
        sections = []
        for s_data in data.get("sections", []):
            items = [
                AssessmentItemData(
                    item_id=i["item_id"],
                    content=i["content"],
                    metadata=i.get("metadata", {}),
                )
                for i in s_data.get("items", [])
            ]
            sections.append(
                SessionSection(
                    section_id=s_data["section_id"],
                    name=s_data["name"],
                    items=items,
                    time_limit_seconds=s_data.get("time_limit_seconds"),
                )
            )

        # Parse timestamps
        started_at = None
        if data.get("started_at"):
            started_at = datetime.fromisoformat(data["started_at"])

        completed_at = None
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        return cls(
            session_id=data["session_id"],
            assessment_id=data["assessment_id"],
            test_taker_id=data["test_taker_id"],
            candidate_id=data["candidate_id"],
            title=data["title"],
            state=SessionState(data.get("state", SessionState.NOT_STARTED.value)),
            current_section_index=data.get("current_section_index", 0),
            current_item_index=data.get("current_item_index", 0),
            responses=data.get("responses", {}),
            flagged_items=data.get("flagged_items", []),
            time_limit_seconds=data.get("time_limit_seconds"),
            time_remaining_seconds=data.get("time_remaining_seconds"),
            started_at=started_at,
            completed_at=completed_at,
            sections=sections,
            navigation_mode=data.get("navigation_mode", "LINEAR"),
        )


class SessionManager:
    """
    Manages assessment sessions throughout their lifecycle.
    Handles creation, retrieval, state transitions, and persistence.
    """

    def __init__(self, identity_service: Optional[IdentityService] = None):
        """
        Initialize the session manager.

        Args:
            identity_service: Optional IdentityService for candidate validation.
        """
        self._sessions: Dict[str, AssessmentSession] = {}
        self._identity_service = identity_service

    def set_identity_service(self, identity_service: IdentityService) -> None:
        """Set or update the identity service."""
        self._identity_service = identity_service

    def _validate_candidate(self, candidate_id: str) -> None:
        """Validate that a candidate exists and is active."""
        if self._identity_service:
            candidate = self._identity_service.get_candidate(candidate_id)
            if not candidate.is_active:
                raise ValueError(f"Candidate {candidate_id} is not active")

    def create_session(
        self,
        assessment_definition: AssessmentDefinition,
        candidate_id: str,
        test_taker_id: str,
        assembled_test: Dict[str, Any],
    ) -> AssessmentSession:
        """
        Create a new assessment session.

        Args:
            assessment_definition: The assessment definition
            candidate_id: The candidate's ID
            test_taker_id: The test taker's ID
            assembled_test: The pre-assembled test from TestAssemblyService

        Returns:
            New AssessmentSession
        """
        # Validate candidate
        self._validate_candidate(candidate_id)

        session_id = str(uuid.uuid4())

        # Convert assembled test to session sections
        sections = []
        for section_data in assembled_test.get("sections", []):
            items = [
                AssessmentItemData(
                    item_id=item.item_id if hasattr(item, "item_id") else item.item_id,
                    content=item.content if hasattr(item, "content") else {},
                    metadata=item.metadata if hasattr(item, "metadata") else {},
                )
                for item in section_data.get("items", [])
            ]
            sections.append(
                SessionSection(
                    section_id=section_data["section_id"],
                    name=section_data["name"],
                    items=items,
                    time_limit_seconds=section_data.get("time_limit_seconds"),
                )
            )

        # Create session
        session = AssessmentSession(
            session_id=session_id,
            assessment_id=assessment_definition.assessment_id,
            test_taker_id=test_taker_id,
            candidate_id=candidate_id,
            title=assessment_definition.title,
            state=SessionState.NOT_STARTED,
            time_limit_seconds=assessment_definition.time_limit_seconds,
            sections=sections,
            navigation_mode=assessment_definition.navigation_mode.value,
        )

        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> AssessmentSession:
        """
        Retrieve a session by ID.

        Args:
            session_id: The session ID

        Returns:
            The AssessmentSession

        Raises:
            KeyError: If session not found
        """
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")
        return self._sessions[session_id]

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return session_id in self._sessions

    def start_session(self, session_id: str) -> AssessmentSession:
        """
        Start an assessment session.

        Transitions from NOT_STARTED to IN_PROGRESS and sets start time.

        Args:
            session_id: The session ID

        Returns:
            The updated session

        Raises:
            KeyError: If session not found
            InvalidStateTransitionError: If session cannot be started
        """
        session = self.get_session(session_id)

        if session.state == SessionState.NOT_STARTED:
            session.transition_to(SessionState.IN_PROGRESS)
            session.started_at = datetime.utcnow()
            session.time_remaining_seconds = session.time_limit_seconds

        return session

    def save_progress(self, session_id: str) -> Dict[str, Any]:
        """
        Save session progress.

        Returns the serialized session state for persistence.

        Args:
            session_id: The session ID

        Returns:
            Serialized session data
        """
        session = self.get_session(session_id)
        # Update time remaining before saving
        session.time_remaining_seconds = session.calculate_time_remaining()
        return session.to_dict()

    def restore_session(self, session_data: Dict[str, Any]) -> AssessmentSession:
        """
        Restore a session from saved data.

        Args:
            session_data: Serialized session data

        Returns:
            Restored AssessmentSession
        """
        session = AssessmentSession.from_dict(session_data)
        self._sessions[session.session_id] = session
        return session

    def get_time_remaining(self, session_id: str) -> Optional[int]:
        """
        Get the remaining time for a session.

        Args:
            session_id: The session ID

        Returns:
            Remaining seconds, or None if no time limit
        """
        session = self.get_session(session_id)
        return session.calculate_time_remaining()

    def update_state(
        self, session_id: str, new_state: SessionState
    ) -> AssessmentSession:
        """
        Update the session state.

        Args:
            session_id: The session ID
            new_state: The new state

        Returns:
            The updated session

        Raises:
            KeyError: If session not found
            InvalidStateTransitionError: If transition is invalid
        """
        session = self.get_session(session_id)
        session.transition_to(new_state)

        # Check for time expiry on every state update
        if session.is_time_expired() and session.state == SessionState.IN_PROGRESS:
            session.transition_to(SessionState.EXPIRED)

        return session

    def submit_answer(
        self, session_id: str, item_id: str, response: Any
    ) -> AssessmentSession:
        """
        Submit an answer for an item.

        Args:
            session_id: The session ID
            item_id: The item ID
            response: The response data

        Returns:
            The updated session
        """
        session = self.get_session(session_id)
        session.set_response(item_id, response)
        return session

    def navigate(
        self,
        session_id: str,
        direction: str = "next",
        target_index: Optional[int] = None,
    ) -> AssessmentSession:
        """
        Navigate to a different item.

        Args:
            session_id: The session ID
            direction: "next", "previous", or "specific"
            target_index: Required if direction is "specific"

        Returns:
            The updated session

        Raises:
            KeyError: If session not found
            ValueError: If navigation is invalid
        """
        session = self.get_session(session_id)

        # Check time expiry before allowing navigation
        if session.is_time_expired():
            session.transition_to(SessionState.EXPIRED)
            return session

        total_items = session.total_items

        if direction == "next":
            new_index = session.current_item_index + 1
            if new_index >= total_items:
                raise ValueError("Cannot navigate past the last item")
            session.current_item_index = new_index

        elif direction == "previous":
            new_index = session.current_item_index - 1
            if new_index < 0:
                raise ValueError("Cannot navigate before the first item")
            session.current_item_index = new_index

        elif direction == "specific":
            if target_index is None:
                raise ValueError("target_index required for specific navigation")
            if target_index < 0 or target_index >= total_items:
                raise ValueError(f"Invalid target index: {target_index}")

            # Check navigation mode
            if session.navigation_mode == "LINEAR":
                # Only allow forward progression
                if target_index <= session.current_item_index:
                    raise ValueError("LINEAR mode: can only navigate forward")

            session.current_item_index = target_index

        else:
            raise ValueError(f"Invalid direction: {direction}")

        return session

    def pause_session(self, session_id: str) -> AssessmentSession:
        """
        Pause a session.

        Args:
            session_id: The session ID

        Returns:
            The updated session
        """
        session = self.get_session(session_id)
        session.transition_to(SessionState.PAUSED)
        return session

    def resume_session(self, session_id: str) -> AssessmentSession:
        """
        Resume a paused session.

        Args:
            session_id: The session ID

        Returns:
            The updated session
        """
        session = self.get_session(session_id)
        session.transition_to(SessionState.IN_PROGRESS)
        return session

    def submit_assessment(self, session_id: str) -> AssessmentSession:
        """
        Submit/complete an assessment.

        Args:
            session_id: The session ID

        Returns:
            The updated session
        """
        session = self.get_session(session_id)
        session.transition_to(SessionState.COMPLETED)
        return session

    def terminate_session(self, session_id: str) -> AssessmentSession:
        """
        Terminate a session (e.g., by administrator).

        Args:
            session_id: The session ID

        Returns:
            The updated session
        """
        session = self.get_session(session_id)
        session.transition_to(SessionState.TERMINATED)
        return session

    def list_active_sessions(self) -> List[AssessmentSession]:
        """List all active (in_progress or paused) sessions."""
        return [
            s
            for s in self._sessions.values()
            if s.state in (SessionState.IN_PROGRESS, SessionState.PAUSED)
        ]

    def delete_session(self, session_id: str) -> None:
        """Delete a session (soft delete - just removes from memory)."""
        if session_id in self._sessions:
            del self._sessions[session_id]
