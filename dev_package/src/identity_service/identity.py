"""
identity.py
===========

This module provides simple in‑memory classes to manage candidates and
sessions.  In a real system, this service would persist data to a
database, handle authentication via OAuth or similar, and enforce
rate limits and device heuristics.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional
import uuid
from datetime import datetime, timedelta

from utils.state_machine import StateMachine


@dataclass
class Candidate:
    candidate_id: str
    email: Optional[str] = None
    consent_version: Optional[str] = None
    attempt_count: int = 0
    risk_profile: Dict[str, int] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class Session:
    session_id: str
    candidate_id: str
    state_machine: StateMachine
    consent_version: Optional[str] = None
    assessment_version: Optional[str] = "1.0"
    selected_challenges: list = field(default_factory=list)
    selected_injections: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


class IdentityService:
    """In‑memory identity and session management."""

    def __init__(self, state_machine_path: str):
        self.candidates: Dict[str, Candidate] = {}
        self.sessions: Dict[str, Session] = {}
        self.state_machine_path = state_machine_path

    def create_candidate(
        self, email: Optional[str] = None, consent_version: Optional[str] = None
    ) -> Candidate:
        cid = str(uuid.uuid4())
        candidate = Candidate(
            candidate_id=cid, email=email, consent_version=consent_version
        )
        self.candidates[cid] = candidate
        return candidate

    def start_session(self, candidate_id: str) -> Session:
        if candidate_id not in self.candidates:
            raise ValueError(f"Unknown candidate {candidate_id}")
        candidate = self.candidates[candidate_id]
        candidate.attempt_count += 1
        session_id = str(uuid.uuid4())
        sm = StateMachine.from_yaml(self.state_machine_path, initial_state="INIT")
        session = Session(
            session_id=session_id,
            candidate_id=candidate_id,
            state_machine=sm,
            consent_version=candidate.consent_version,
        )
        self.sessions[session_id] = session
        return session

    def record_consent(self, candidate_id: str, consent_version: str) -> None:
        if candidate_id in self.candidates:
            self.candidates[candidate_id].consent_version = consent_version
        else:
            raise ValueError(f"Candidate {candidate_id} not found")

    def get_candidate(self, candidate_id: str) -> Candidate:
        """Retrieve a candidate by ID. Raises KeyError if not found."""
        if candidate_id not in self.candidates:
            raise KeyError(f"Candidate {candidate_id} not found")
        return self.candidates[candidate_id]

    def update_candidate(
        self,
        candidate_id: str,
        email: Optional[str] = None,
        consent_version: Optional[str] = None,
    ) -> Candidate:
        """Update candidate fields. Raises KeyError if not found."""
        if candidate_id not in self.candidates:
            raise KeyError(f"Candidate {candidate_id} not found")
        candidate = self.candidates[candidate_id]
        if email is not None:
            candidate.email = email
        if consent_version is not None:
            candidate.consent_version = consent_version
        return candidate

    def delete_candidate(self, candidate_id: str) -> None:
        """Soft delete a candidate (mark as inactive). Raises KeyError if not found."""
        if candidate_id not in self.candidates:
            raise KeyError(f"Candidate {candidate_id} not found")
        self.candidates[candidate_id].is_active = False

    def list_candidates(self) -> list:
        """List all active candidates."""
        return [c for c in self.candidates.values() if c.is_active]

    def get_session(self, session_id: str) -> Session:
        return self.sessions[session_id]

    def save_session(self, session_id: str) -> dict:
        """
        Serialize a session to a dict for persistence.

        Args:
            session_id: The session to serialize

        Returns:
            Dict containing all session data including state
        """
        session = self.sessions[session_id]
        # Get current state from state machine
        state = (
            session.state_machine.current_state
            if hasattr(session.state_machine, "current_state")
            else "INIT"
        )

        return {
            "session_id": session.session_id,
            "candidate_id": session.candidate_id,
            "state": state,
            "consent_version": session.consent_version,
            "assessment_version": session.assessment_version,
            "selected_challenges": session.selected_challenges,
            "selected_injections": session.selected_injections,
            "created_at": session.created_at.isoformat()
            if isinstance(session.created_at, datetime)
            else session.created_at,
        }

    def load_session(self, session_data: dict) -> Session:
        """
        Deserialize a session from a dict.

        Args:
            session_data: Dict containing session data

        Returns:
            Restored Session object
        """
        # Recreate state machine from saved state
        state = session_data.get("state", "INIT")
        sm = StateMachine.from_yaml(self.state_machine_path, initial_state=state)

        # Parse created_at timestamp
        created_at_str = session_data.get("created_at")
        if created_at_str:
            created_at = datetime.fromisoformat(created_at_str)
        else:
            created_at = datetime.utcnow()

        session = Session(
            session_id=session_data["session_id"],
            candidate_id=session_data["candidate_id"],
            state_machine=sm,
            consent_version=session_data.get("consent_version"),
            assessment_version=session_data.get("assessment_version", "1.0"),
            selected_challenges=session_data.get("selected_challenges", []),
            selected_injections=session_data.get("selected_injections", []),
            created_at=created_at,
        )
        self.sessions[session.session_id] = session
        return session

    def get_session_by_candidate(self, candidate_id: str) -> Optional[Session]:
        """
        Find and return the most recent active session for a candidate.

        Args:
            candidate_id: The candidate's ID

        Returns:
            Most recent Session for the candidate, or None if no active session
        """
        candidate_sessions = [
            s for s in self.sessions.values() if s.candidate_id == candidate_id
        ]
        if not candidate_sessions:
            return None
        # Return the most recently created session
        return max(candidate_sessions, key=lambda s: s.created_at)

    def cleanup_expired_sessions(self, max_age_days: int = 1) -> int:
        """
        Remove sessions older than max_age_days.

        Args:
            max_age_days: Maximum session age in days

        Returns:
            Number of sessions removed
        """
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        expired_ids = [
            sid for sid, session in self.sessions.items() if session.created_at < cutoff
        ]
        for sid in expired_ids:
            del self.sessions[sid]
        return len(expired_ids)
