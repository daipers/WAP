"""
verification.py
===============

Enhanced hash chain verification for audit logs.
Provides tamper detection and chain integrity verification.

Reference: Plan 05-03-PLAN.md - Enhanced hash chain verification
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from audit_ledger_service.ledger import AuditLedger, LedgerEntry


@dataclass
class VerificationResult:
    """Result of audit log verification."""

    is_valid: bool
    session_id: str
    checked_at: str
    event_count: int
    first_event_timestamp: Optional[float] = None
    last_event_timestamp: Optional[float] = None
    invalid_entries: List[Dict[str, Any]] = field(default_factory=list)
    chain_valid: bool = True
    merkle_root_valid: bool = True
    anchor_valid: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "session_id": self.session_id,
            "checked_at": self.checked_at,
            "event_count": self.event_count,
            "first_event_timestamp": self.first_event_timestamp,
            "last_event_timestamp": self.last_event_timestamp,
            "invalid_entries": self.invalid_entries,
            "chain_valid": self.chain_valid,
            "merkle_root_valid": self.merkle_root_valid,
            "anchor_valid": self.anchor_valid,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass
class ChainIntegrityReport:
    """Comprehensive integrity report for audit chain."""

    session_id: str
    genesis_hash: str
    final_hash: str
    event_count: int
    chain_intact: bool
    generated_at: str
    merkle_root: Optional[str] = None
    anchor_date: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "genesis_hash": self.genesis_hash,
            "final_hash": self.final_hash,
            "event_count": self.event_count,
            "chain_intact": self.chain_intact,
            "generated_at": self.generated_at,
            "merkle_root": self.merkle_root,
            "anchor_date": self.anchor_date,
            "warnings": self.warnings,
        }


class AuditVerifier:
    """
    Enhanced hash chain verification for audit logs.

    Provides:
    - Automatic verification on read
    - Verification result logging
    - Tamper detection alerts
    - Chain integrity reports
    """

    # Genesis hash from ledger
    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, ledger: Optional[AuditLedger] = None):
        """
        Initialize verifier.

        Args:
            ledger: AuditLedger instance to verify
        """
        self.ledger = ledger
        self.verification_history: List[VerificationResult] = []

    def set_ledger(self, ledger: AuditLedger):
        """Set the ledger to verify."""
        self.ledger = ledger

    def verify_session(self, session_id: str) -> VerificationResult:
        """
        Verify hash chain for a specific session.

        Args:
            session_id: Session to verify

        Returns:
            VerificationResult with detailed status
        """
        if not self.ledger:
            return VerificationResult(
                is_valid=False,
                session_id=session_id,
                checked_at=datetime.now(timezone.utc).isoformat(),
                event_count=0,
                errors=["No ledger configured"],
            )

        session_events = self.ledger.get_events_by_session(session_id)

        if not session_events:
            return VerificationResult(
                is_valid=True,  # No events is valid
                session_id=session_id,
                checked_at=datetime.now(timezone.utc).isoformat(),
                event_count=0,
                warnings=["No events found for session"],
            )

        # Verify hash chain
        chain_valid, invalid_entries = self.ledger.verify_session_events(session_id)

        # Build result
        result = VerificationResult(
            is_valid=chain_valid and len(invalid_entries) == 0,
            session_id=session_id,
            checked_at=datetime.now(timezone.utc).isoformat(),
            event_count=len(session_events),
            first_event_timestamp=session_events[0].timestamp,
            last_event_timestamp=session_events[-1].timestamp,
            chain_valid=chain_valid,
        )

        # Add invalid entries details
        for entry in invalid_entries:
            result.invalid_entries.append(
                {
                    "event_id": entry.event_id,
                    "timestamp": entry.timestamp,
                    "hash": entry.hash,
                    "prev_hash": entry.prev_hash,
                }
            )
            result.errors.append(f"Invalid hash at event {entry.event_id}")

        # Log verification
        self.verification_history.append(result)

        return result

    def verify_all_sessions(self) -> List[VerificationResult]:
        """
        Verify all sessions in the ledger.

        Returns:
            List of VerificationResult for each session
        """
        if not self.ledger:
            return []

        # Get unique session IDs
        session_ids = set(entry.session_id for entry in self.ledger.entries)

        results = []
        for session_id in session_ids:
            result = self.verify_session(session_id)
            results.append(result)

        return results

    def generate_integrity_report(self, session_id: str) -> ChainIntegrityReport:
        """
        Generate comprehensive integrity report for a session.

        Args:
            session_id: Session to report on

        Returns:
            ChainIntegrityReport with full details
        """
        if not self.ledger:
            return ChainIntegrityReport(
                session_id=session_id,
                genesis_hash=self.GENESIS_HASH,
                final_hash="",
                event_count=0,
                chain_intact=False,
                generated_at=datetime.now(timezone.utc).isoformat(),
                warnings=["No ledger configured"],
            )

        session_events = self.ledger.get_events_by_session(session_id)

        if not session_events:
            return ChainIntegrityReport(
                session_id=session_id,
                genesis_hash=self.GENESIS_HASH,
                final_hash=self.GENESIS_HASH,
                event_count=0,
                chain_intact=True,
                generated_at=datetime.now(timezone.utc).isoformat(),
                warnings=["No events in session"],
            )

        # Verify chain
        chain_valid, _ = self.ledger.verify_session_events(session_id)

        return ChainIntegrityReport(
            session_id=session_id,
            genesis_hash=self.GENESIS_HASH,
            final_hash=session_events[-1].hash,
            event_count=len(session_events),
            chain_intact=chain_valid,
            generated_at=datetime.now(timezone.utc).isoformat(),
            warnings=[] if chain_valid else ["Chain integrity compromised"],
        )

    def get_verification_summary(self) -> Dict[str, Any]:
        """
        Get summary of all verifications performed.

        Returns:
            Summary dictionary
        """
        if not self.verification_history:
            return {
                "total_verifications": 0,
                "passed": 0,
                "failed": 0,
                "sessions_checked": 0,
            }

        passed = sum(1 for r in self.verification_history if r.is_valid)
        failed = len(self.verification_history) - passed
        sessions = len(set(r.session_id for r in self.verification_history))

        return {
            "total_verifications": len(self.verification_history),
            "passed": passed,
            "failed": failed,
            "sessions_checked": sessions,
        }

    def detect_tampering(self, session_id: str) -> Tuple[bool, List[str]]:
        """
        Detect tampering in session audit log.

        Args:
            session_id: Session to check

        Returns:
            Tuple of (tampered, list_of_issues)
        """
        issues = []

        if not self.ledger:
            return True, ["No ledger configured"]

        session_events = self.ledger.get_events_by_session(session_id)

        if not session_events:
            return False, []

        # Check for gaps in event sequence
        event_ids = [e.event_id for e in session_events]
        expected = list(range(min(event_ids), max(event_ids) + 1))
        missing = set(expected) - set(event_ids)

        if missing:
            issues.append(f"Missing event IDs: {sorted(missing)}")

        # Verify each entry's hash
        for entry in session_events:
            if not self._verify_entry_hash(entry):
                issues.append(f"Hash mismatch at event {entry.event_id}")

        # Check prev_hash chain
        for i, entry in enumerate(session_events):
            if i == 0:
                if entry.prev_hash != self.GENESIS_HASH:
                    issues.append(
                        f"First event has wrong prev_hash at event {entry.event_id}"
                    )
            else:
                expected_prev = session_events[i - 1].hash
                if entry.prev_hash != expected_prev:
                    issues.append(f"Broken chain at event {entry.event_id}")

        return len(issues) > 0, issues

    def _verify_entry_hash(self, entry: LedgerEntry) -> bool:
        """Verify a single entry's hash is correct."""
        # Recreate the content that was hashed
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
            "prev_hash": entry.prev_hash,
        }
        data_str = json.dumps(content, sort_keys=True)

        # Compute expected hash
        import hashlib

        computed_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()

        return computed_hash == entry.hash
