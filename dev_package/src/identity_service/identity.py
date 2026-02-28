"""
identity.py
===========

This module provides PostgreSQL-backed classes to manage candidates and
sessions. It uses SQLAlchemy for ORM and pgcrypto for PII encryption.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from utils.db import AsyncSessionLocal
from utils.state_machine import StateMachine
from identity_service.models import Candidate, Session


class IdentityService:
    """PostgreSQL-backed identity and session management."""

    def __init__(self, state_machine_path: str):
        self.state_machine_path = state_machine_path

    async def create_candidate(
        self, email: Optional[str] = None, consent_version: Optional[str] = None
    ) -> Candidate:
        """Create a new candidate in the database."""
        async with AsyncSessionLocal() as session:
            candidate = Candidate(email=email, consent_version=consent_version)
            session.add(candidate)
            await session.commit()
            await session.refresh(candidate)
            return candidate

    async def start_session(self, candidate_id: str) -> Session:
        """Start a new assessment session for a candidate."""
        async with AsyncSessionLocal() as session:
            # Check if candidate exists
            cid_uuid = (
                uuid.UUID(candidate_id)
                if isinstance(candidate_id, str)
                else candidate_id
            )
            result = await session.execute(
                select(Candidate).where(Candidate.candidate_id == cid_uuid)
            )
            candidate = result.scalar_one_or_none()
            if not candidate:
                raise ValueError(f"Unknown candidate {candidate_id}")

            # Increment attempt count
            candidate.attempt_count += 1

            # Create new session
            db_session = Session(
                candidate_id=candidate.candidate_id,
                state="INIT",
                consent_version=candidate.consent_version,
            )
            session.add(db_session)
            await session.commit()
            await session.refresh(db_session)

            return db_session

    async def record_consent(self, candidate_id: str, consent_version: str) -> None:
        """Record candidate consent version."""
        async with AsyncSessionLocal() as session:
            cid_uuid = (
                uuid.UUID(candidate_id)
                if isinstance(candidate_id, str)
                else candidate_id
            )
            result = await session.execute(
                select(Candidate).where(Candidate.candidate_id == cid_uuid)
            )
            candidate = result.scalar_one_or_none()
            if candidate:
                candidate.consent_version = consent_version
                await session.commit()
            else:
                raise ValueError(f"Candidate {candidate_id} not found")

    async def get_candidate(self, candidate_id: str) -> Candidate:
        """Retrieve a candidate by ID."""
        async with AsyncSessionLocal() as session:
            cid_uuid = (
                uuid.UUID(candidate_id)
                if isinstance(candidate_id, str)
                else candidate_id
            )
            result = await session.execute(
                select(Candidate).where(Candidate.candidate_id == cid_uuid)
            )
            candidate = result.scalar_one_or_none()
            if not candidate:
                raise KeyError(f"Candidate {candidate_id} not found")
            return candidate

    async def update_candidate(
        self,
        candidate_id: str,
        email: Optional[str] = None,
        consent_version: Optional[str] = None,
    ) -> Candidate:
        """Update candidate fields."""
        async with AsyncSessionLocal() as session:
            cid_uuid = (
                uuid.UUID(candidate_id)
                if isinstance(candidate_id, str)
                else candidate_id
            )
            result = await session.execute(
                select(Candidate).where(Candidate.candidate_id == cid_uuid)
            )
            candidate = result.scalar_one_or_none()
            if not candidate:
                raise KeyError(f"Candidate {candidate_id} not found")

            if email is not None:
                candidate.email = email
            if consent_version is not None:
                candidate.consent_version = consent_version

            await session.commit()
            await session.refresh(candidate)
            return candidate

    async def delete_candidate(self, candidate_id: str) -> None:
        """Soft delete a candidate."""
        async with AsyncSessionLocal() as session:
            cid_uuid = (
                uuid.UUID(candidate_id)
                if isinstance(candidate_id, str)
                else candidate_id
            )
            result = await session.execute(
                select(Candidate).where(Candidate.candidate_id == cid_uuid)
            )
            candidate = result.scalar_one_or_none()
            if not candidate:
                raise KeyError(f"Candidate {candidate_id} not found")
            candidate.is_active = False
            await session.commit()

    async def list_candidates(self) -> List[Candidate]:
        """List all active candidates."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Candidate).where(Candidate.is_active == True)
            )
            return list(result.scalars().all())

    async def get_session(self, session_id: str) -> Session:
        """Retrieve a session by ID."""
        async with AsyncSessionLocal() as session:
            sid_uuid = (
                uuid.UUID(session_id) if isinstance(session_id, str) else session_id
            )
            result = await session.execute(
                select(Session).where(Session.session_id == sid_uuid)
            )
            db_session = result.scalar_one_or_none()
            if not db_session:
                raise KeyError(f"Session {session_id} not found")
            return db_session

    async def save_session_state(self, session_id: str, state: str) -> None:
        """Save the current state of a session."""
        async with AsyncSessionLocal() as session:
            sid_uuid = (
                uuid.UUID(session_id) if isinstance(session_id, str) else session_id
            )
            result = await session.execute(
                select(Session).where(Session.session_id == sid_uuid)
            )
            db_session = result.scalar_one_or_none()
            if not db_session:
                raise KeyError(f"Session {session_id} not found")

            db_session.state = state
            await session.commit()

    async def get_session_by_candidate(self, candidate_id: str) -> Optional[Session]:
        """Find and return the most recent session for a candidate."""
        async with AsyncSessionLocal() as session:
            cid_uuid = (
                uuid.UUID(candidate_id)
                if isinstance(candidate_id, str)
                else candidate_id
            )
            result = await session.execute(
                select(Session)
                .where(Session.candidate_id == cid_uuid)
                .order_by(Session.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def cleanup_expired_sessions(self, max_age_days: int = 1) -> int:
        """Remove sessions older than max_age_days."""
        async with AsyncSessionLocal() as session:
            cutoff = datetime.utcnow() - timedelta(days=max_age_days)
            result = await session.execute(
                delete(Session).where(Session.created_at < cutoff)
            )
            await session.commit()
            return result.rowcount
