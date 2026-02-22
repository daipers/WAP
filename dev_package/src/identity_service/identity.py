"""
identity.py
===========

This module provides simple in‑memory classes to manage candidates and
sessions.  In a real system, this service would persist data to a
database, handle authentication via OAuth or similar, and enforce
rate limits and device heuristics.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import uuid

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
