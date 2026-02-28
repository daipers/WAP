"""
retention_service/disposal.py
=============================

Automated disposal scheduling and secure deletion service.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import uuid


class DisposalMethod(Enum):
    """Methods for secure data disposal."""

    SECURE_DELETE = "secure_delete"  # Overwrite and delete
    STANDARD_DELETE = "standard_delete"  # Regular deletion
    CRYPTOGRAPHIC_ERASE = "cryptographic_erase"  # Encryption key destruction
    PHYSICAL_DESTRUCTION = "physical_destruction"  # Physical media destruction


class DisposalStatus(Enum):
    """Status of disposal operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


@dataclass
class DisposalRecord:
    """Record of a disposal operation."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    record_id: str = ""  # The data record being disposed
    data_category: str = ""
    disposal_method: DisposalMethod = DisposalMethod.SECURE_DELETE
    status: DisposalStatus = DisposalStatus.PENDING
    scheduled_at: Optional[datetime] = None
    disposed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    disposed_by: str = ""
    verification_hash: str = ""  # Hash to verify deletion
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "record_id": self.record_id,
            "data_category": self.data_category,
            "disposal_method": self.disposal_method.value,
            "status": self.status.value,
            "scheduled_at": self.scheduled_at.isoformat()
            if self.scheduled_at
            else None,
            "disposed_at": self.disposed_at.isoformat() if self.disposed_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "disposed_by": self.disposed_by,
            "verification_hash": self.verification_hash,
            "notes": self.notes,
        }


class DisposalSchedule:
    """Schedule for automated disposal."""

    def __init__(
        self,
        data_category: str,
        retention_days: int,
        batch_size: int = 100,
        enabled: bool = True,
    ):
        self.data_category = data_category
        self.retention_days = retention_days
        self.batch_size = batch_size
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None

    def calculate_next_run(self, from_time: Optional[datetime] = None) -> datetime:
        """Calculate next scheduled run."""
        if from_time is None:
            from_time = datetime.utcnow()

        # Run daily at midnight
        next_run = from_time + timedelta(days=1)
        next_run = next_run.replace(hour=0, minute=0, second=0, microsecond=0)
        self.next_run = next_run
        return next_run

    def get_cutoff_date(self, as_of: Optional[datetime] = None) -> datetime:
        """Get the cutoff date for eligible records."""
        if as_of is None:
            as_of = datetime.utcnow()
        return as_of - timedelta(days=self.retention_days)


class DisposalService:
    """Service for managing data disposal operations."""

    def __init__(self):
        self.schedules: dict[str, DisposalSchedule] = {}
        self.disposal_records: list[DisposalRecord] = []
        self._register_default_schedules()

    def _register_default_schedules(self):
        """Register default disposal schedules."""
        # Assessment scores - 3 years
        self.schedules["assessment_scores"] = DisposalSchedule(
            data_category="assessment_scores", retention_days=3 * 365, batch_size=100
        )

        # Session logs - 3 years
        self.schedules["session_logs"] = DisposalSchedule(
            data_category="session_logs", retention_days=3 * 365, batch_size=500
        )

        # Assessment content - 5 years
        self.schedules["assessment_content"] = DisposalSchedule(
            data_category="assessment_content", retention_days=5 * 365, batch_size=50
        )

        # Student responses - 3 years
        self.schedules["student_responses"] = DisposalSchedule(
            data_category="student_responses", retention_days=3 * 365, batch_size=100
        )

    def register_schedule(self, schedule: DisposalSchedule):
        """Register a custom disposal schedule."""
        self.schedules[schedule.data_category] = schedule

    def get_eligible_records(
        self, data_category: str, as_of: Optional[datetime] = None
    ) -> list[str]:
        """
        Get records eligible for disposal.

        Returns list of record IDs that have passed their retention period.
        """
        if as_of is None:
            as_of = datetime.utcnow()

        schedule = self.schedules.get(data_category)
        if schedule is None or not schedule.enabled:
            return []

        cutoff_date = schedule.get_cutoff_date(as_of)

        # In a real implementation, this would query the database
        # filtering by: created_at < cutoff_date AND disposed = false
        # Returns list of record IDs
        return []

    def schedule_disposal(
        self,
        record_id: str,
        data_category: str,
        scheduled_at: Optional[datetime] = None,
        disposal_method: DisposalMethod = DisposalMethod.SECURE_DELETE,
        disposed_by: str = "",
    ) -> DisposalRecord:
        """Schedule a record for disposal."""
        if scheduled_at is None:
            scheduled_at = datetime.utcnow()

        record = DisposalRecord(
            record_id=record_id,
            data_category=data_category,
            disposal_method=disposal_method,
            scheduled_at=scheduled_at,
            disposed_by=disposed_by,
            status=DisposalStatus.PENDING,
        )

        self.disposal_records.append(record)
        return record

    def execute_disposal(
        self,
        record_ids: list[str],
        data_category: str,
        method: DisposalMethod = DisposalMethod.SECURE_DELETE,
        disposed_by: str = "",
    ) -> dict:
        """
        Execute disposal for records.

        Returns summary of disposal operation.
        """
        now = datetime.utcnow()

        # Find and update pending records
        updated_records = []
        for record in self.disposal_records:
            if record.record_id in record_ids and record.data_category == data_category:
                record.status = DisposalStatus.IN_PROGRESS
                record.disposed_at = now
                record.disposed_by = disposed_by
                updated_records.append(record)

        # Generate verification hash
        verification_hash = self._generate_verification_hash(record_ids)

        for record in updated_records:
            record.status = DisposalStatus.COMPLETED
            record.verification_hash = verification_hash

        return {
            "disposed_count": len(updated_records),
            "method": method.value,
            "data_category": data_category,
            "timestamp": now.isoformat(),
            "verification_hash": verification_hash,
            "status": DisposalStatus.COMPLETED.value,
        }

    def verify_disposal(self, record_id: str, expected_hash: str) -> bool:
        """Verify that a record was properly disposed."""
        for record in self.disposal_records:
            if record.record_id == record_id:
                if record.verification_hash == expected_hash:
                    record.status = DisposalStatus.VERIFIED
                    record.verified_at = datetime.utcnow()
                    return True
                return False
        return False

    def _generate_verification_hash(self, record_ids: list[str]) -> str:
        """Generate a hash to verify disposal."""
        import hashlib

        combined = ",".join(sorted(record_ids))
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def get_disposal_history(
        self,
        data_category: Optional[str] = None,
        status: Optional[DisposalStatus] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get disposal history with optional filters."""
        records = self.disposal_records

        if data_category:
            records = [r for r in records if r.data_category == data_category]

        if status:
            records = [r for r in records if r.status == status]

        # Sort by disposed_at descending
        records.sort(key=lambda r: r.disposed_at or datetime.min, reverse=True)

        return [r.to_dict() for r in records[:limit]]

    def get_disposal_summary(self, data_category: str) -> dict:
        """Get summary of disposal operations for a category."""
        records = [r for r in self.disposal_records if r.data_category == data_category]

        return {
            "data_category": data_category,
            "total_records": len(records),
            "pending": sum(1 for r in records if r.status == DisposalStatus.PENDING),
            "completed": sum(
                1 for r in records if r.status == DisposalStatus.COMPLETED
            ),
            "verified": sum(1 for r in records if r.status == DisposalStatus.VERIFIED),
            "failed": sum(1 for r in records if r.status == DisposalStatus.FAILED),
        }

    def run_scheduled_disposal(
        self, data_category: str, disposed_by: str = "system"
    ) -> dict:
        """Run scheduled disposal for a category."""
        schedule = self.schedules.get(data_category)
        if schedule is None or not schedule.enabled:
            return {"error": f"No schedule for {data_category}"}

        eligible_ids = self.get_eligible_records(data_category)

        if not eligible_ids:
            return {
                "data_category": data_category,
                "eligible_count": 0,
                "message": "No records eligible for disposal",
            }

        # Process in batches
        batch = eligible_ids[: schedule.batch_size]
        result = self.execute_disposal(batch, data_category, disposed_by=disposed_by)

        schedule.last_run = datetime.utcnow()
        schedule.calculate_next_run()

        return result
