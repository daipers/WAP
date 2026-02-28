"""
retention_service/policies.py
=============================

FERPA-compliant retention policies and management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class DataClassification(Enum):
    """FERPA data classification levels."""

    EDUCATION_RECORD = "education_record"  # Protected under FERPA
    DIRECTORY_INFO = "directory_info"  # May be disclosed
    PERSONAL_NOTE = "personal_note"  # Not an education record
    AGGREGATED = "aggregated"  # De-identified data


@dataclass
class RetentionPolicy:
    """Retention policy for a data category."""

    name: str
    classification: DataClassification
    retention_years: Optional[int]  # None = indefinite retention
    review_required: bool
    secure_deletion: bool
    description: str = ""

    def calculate_disposal_date(self, created_at: datetime) -> Optional[datetime]:
        """Calculate the disposal date based on creation date."""
        if self.retention_years is None:
            return None  # No automatic disposal
        return created_at + timedelta(days=self.retention_years * 365)

    @property
    def retention_days(self) -> Optional[int]:
        """Get retention period in days."""
        if self.retention_years is None:
            return None
        return self.retention_years * 365


# Standard retention policies for educational records
class StandardPolicies:
    """Pre-defined retention policies for common data categories."""

    ASSESSMENT_SCORES = RetentionPolicy(
        name="Assessment Scores",
        classification=DataClassification.EDUCATION_RECORD,
        retention_years=3,  # Varies by state (1-7 years typical)
        review_required=True,
        secure_deletion=True,
        description="Student assessment scores and results",
    )

    SESSION_LOGS = RetentionPolicy(
        name="Session Logs",
        classification=DataClassification.EDUCATION_RECORD,
        retention_years=3,
        review_required=False,
        secure_deletion=True,
        description="Assessment session activity logs",
    )

    ASSESSMENT_CONTENT = RetentionPolicy(
        name="Assessment Content",
        classification=DataClassification.EDUCATION_RECORD,
        retention_years=5,
        review_required=True,
        secure_deletion=True,
        description="Assessment items and content",
    )

    STUDENT_RESPONSES = RetentionPolicy(
        name="Student Responses",
        classification=DataClassification.EDUCATION_RECORD,
        retention_years=3,
        review_required=True,
        secure_deletion=True,
        description="Student response data",
    )

    AGGREGATED_ANALYTICS = RetentionPolicy(
        name="Aggregated Analytics",
        classification=DataClassification.AGGREGATED,
        retention_years=None,  # No limit - de-identified
        review_required=False,
        secure_deletion=False,
        description="De-identified aggregated analytics",
    )

    DIRECTORY_INFO = RetentionPolicy(
        name="Directory Information",
        classification=DataClassification.DIRECTORY_INFO,
        retention_years=None,  # Maintained while student enrolled
        review_required=False,
        secure_deletion=False,
        description="Student directory information",
    )

    PERSONAL_NOTES = RetentionPolicy(
        name="Personal Notes",
        classification=DataClassification.PERSONAL_NOTE,
        retention_years=None,  # Not education records
        review_required=False,
        secure_deletion=True,
        description="Instructor personal notes (not education records)",
    )


class RetentionManager:
    """Manage data retention and schedule disposal."""

    def __init__(self):
        self.policies: dict[str, RetentionPolicy] = {}
        self._register_default_policies()

    def _register_default_policies(self):
        """Register standard retention policies."""
        self.policies["assessment_scores"] = StandardPolicies.ASSESSMENT_SCORES
        self.policies["session_logs"] = StandardPolicies.SESSION_LOGS
        self.policies["assessment_content"] = StandardPolicies.ASSESSMENT_CONTENT
        self.policies["student_responses"] = StandardPolicies.STUDENT_RESPONSES
        self.policies["aggregated_analytics"] = StandardPolicies.AGGREGATED_ANALYTICS
        self.policies["directory_info"] = StandardPolicies.DIRECTORY_INFO
        self.policies["personal_notes"] = StandardPolicies.PERSONAL_NOTES

    def register_policy(self, category: str, policy: RetentionPolicy):
        """Register a custom retention policy."""
        self.policies[category] = policy

    def get_policy(self, category: str) -> Optional[RetentionPolicy]:
        """Get retention policy for a category."""
        return self.policies.get(category)

    def calculate_disposal_date(
        self, data_category: str, created_at: datetime
    ) -> Optional[datetime]:
        """Calculate when data should be disposed."""
        policy = self.policies.get(data_category)
        if policy is None or policy.retention_years is None:
            return None  # No automatic disposal

        return policy.calculate_disposal_date(created_at)

    def is_eligible_for_disposal(
        self, data_category: str, created_at: datetime, as_of: Optional[datetime] = None
    ) -> bool:
        """Check if data is eligible for disposal."""
        if as_of is None:
            as_of = datetime.utcnow()

        disposal_date = self.calculate_disposal_date(data_category, created_at)
        if disposal_date is None:
            return False

        return as_of >= disposal_date

    def get_data_for_disposal(
        self, data_category: str, as_of: Optional[datetime] = None
    ) -> list[str]:
        """
        Get list of record IDs eligible for disposal.

        This is a placeholder - actual implementation would query database.
        """
        if as_of is None:
            as_of = datetime.utcnow()

        policy = self.policies.get(data_category)
        if policy is None or policy.retention_years is None:
            return []

        # Query would filter by created_at < disposal_date
        # and not already disposed
        return []

    def dispose_records(
        self, data_category: str, record_ids: list[str], method: str = "secure_delete"
    ) -> dict:
        """Dispose records according to policy."""
        policy = self.policies.get(data_category)
        if policy is None:
            raise ValueError(f"Unknown category: {data_category}")

        if not policy.secure_deletion and method == "secure_delete":
            raise ValueError(f"Secure deletion not required for {data_category}")

        # Return disposal summary
        return {
            "disposed_count": len(record_ids),
            "method": method,
            "policy": policy.name,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def list_policies(self) -> list[dict]:
        """List all registered retention policies."""
        return [
            {
                "category": category,
                "name": policy.name,
                "classification": policy.classification.value,
                "retention_years": policy.retention_years,
                "review_required": policy.review_required,
                "secure_deletion": policy.secure_deletion,
                "description": policy.description,
            }
            for category, policy in self.policies.items()
        ]

    def get_policy_summary(self, data_category: str) -> Optional[dict]:
        """Get summary of retention policy for a category."""
        policy = self.policies.get(data_category)
        if policy is None:
            return None

        return {
            "category": data_category,
            "policy_name": policy.name,
            "classification": policy.classification.value,
            "retention_years": policy.retention_years,
            "retention_days": policy.retention_days,
            "review_required": policy.review_required,
            "secure_deletion": policy.secure_deletion,
        }
