import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.db import Base, PGcryptoString


class Candidate(Base):
    """Candidate model with encrypted PII."""

    __tablename__ = "candidates"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[Optional[str]] = mapped_column(
        PGcryptoString, unique=True, nullable=True
    )
    consent_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    risk_profile: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sessions = relationship("Session", back_populates="candidate")


class Session(Base):
    """Assessment session model for candidates."""

    __tablename__ = "sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("candidates.candidate_id"), nullable=False
    )
    state: Mapped[str] = mapped_column(String, default="INIT")
    consent_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assessment_version: Mapped[str] = mapped_column(String, default="1.0")
    selected_challenges: Mapped[List[str]] = mapped_column(JSON, default=list)
    selected_injections: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    candidate = relationship("Candidate", back_populates="sessions")
