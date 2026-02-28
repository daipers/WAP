"""
retention_service/disclosure_log.py
===================================

Disclosure logging and controls for FERPA compliance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class AuthorizationBasis(Enum):
    """Legal basis for disclosing education records."""

    CONSENT = "consent"  # Written consent from student/parent
    LEGITIMATE_EDUCATIONAL_INTEREST = "legitimate_educational_interest"
    JUDICIAL_ORDER = "judicial_order"  # Court order
    SUBPOENA = "subpoena"
    HEALTH_EMERGENCY = "health_emergency"
    LAW_ENFORCEMENT = "law_enforcement"
    DIRECTORY_INFO = "directory_info"  # Student did not opt out
    SCHOOL_OFFICIAL = "school_official"  # School official with legitimate interest
    OTHER_LEGAL = "other_legal"  # Other legally permitted disclosure


class DisclosurePurpose(Enum):
    """Purpose for disclosing education records."""

    EDUCATION = "education"  # Educational purposes
    HEALTH_SAFETY = "health_safety"  # Health or safety emergency
    JUDICIAL = "judicial"  # Legal proceedings
    RESEARCH = "research"  # Research (with IRB approval)
    ADMINISTRATION = "administration"  # Administrative purposes
    EMPLOYMENT = "employment"  # Employment decisions
    OTHER = "other"


class DisclosureStatus(Enum):
    """Status of disclosure."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    COMPLETED = "completed"
    REVOKED = "revoked"


@dataclass
class DisclosureRecord:
    """
    Record of a disclosure of education records.

    FERPA requires institutions to maintain a record of each request
    for access to and disclosure of personally identifiable information
    from education records.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    record_id: str = ""  # The education record ID
    disclosed_to: str = ""  # Recipient name/organization
    disclosed_to_type: str = ""  # e.g., "school_official", "parent", "researcher"
    purpose: DisclosurePurpose = DisclosurePurpose.EDUCATION
    authorization_basis: AuthorizationBasis = AuthorizationBasis.CONSENT
    disclosed_at: datetime = field(default_factory=datetime.utcnow)
    disclosed_by: str = ""  # Who made the disclosure
    authorized_by: str = ""  # Who authorized (if not the same as disclosed_by)
    consent_document_id: str = ""  # Reference to consent document
    expiration_date: Optional[datetime] = None  # For time-limited consent
    status: DisclosureStatus = DisclosureStatus.COMPLETED
    data_categories: list[str] = field(default_factory=list)  # Categories disclosed
    fields_disclosed: list[str] = field(default_factory=list)  # Specific fields
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "record_id": self.record_id,
            "disclosed_to": self.disclosed_to,
            "disclosed_to_type": self.disclosed_to_type,
            "purpose": self.purpose.value,
            "authorization_basis": self.authorization_basis.value,
            "disclosed_at": self.disclosed_at.isoformat(),
            "disclosed_by": self.disclosed_by,
            "authorized_by": self.authorized_by,
            "consent_document_id": self.consent_document_id,
            "expiration_date": self.expiration_date.isoformat()
            if self.expiration_date
            else None,
            "status": self.status.value,
            "data_categories": self.data_categories,
            "fields_disclosed": self.fields_disclosed,
            "notes": self.notes,
        }

    def is_expired(self) -> bool:
        """Check if consent/authorization has expired."""
        if self.expiration_date is None:
            return False
        return datetime.utcnow() > self.expiration_date

    def requires_authorization(self) -> bool:
        """Check if this disclosure requires explicit authorization."""
        return self.authorization_basis not in [
            AuthorizationBasis.DIRECTORY_INFO,
            AuthorizationBasis.LEGITIMATE_EDUCATIONAL_INTEREST,
            AuthorizationBasis.SCHOOL_OFFICIAL,
        ]


class DisclosureLog:
    """
    Service for logging and managing disclosures of education records.

    Maintains the required audit trail for FERPA compliance.
    """

    def __init__(self):
        self.disclosures: list[DisclosureRecord] = []
        self._setup_default_policies()

    def _setup_default_policies(self):
        """Setup default disclosure policies."""
        # Default: require consent for education records
        self.require_consent_for = [
            AuthorizationBasis.CONSENT,
        ]

        # Log all disclosures automatically
        self.auto_log = True

    def log_disclosure(
        self,
        record_id: str,
        disclosed_to: str,
        disclosed_to_type: str,
        purpose: DisclosurePurpose,
        authorization_basis: AuthorizationBasis,
        disclosed_by: str,
        authorized_by: str = "",
        consent_document_id: str = "",
        expiration_date: Optional[datetime] = None,
        data_categories: list[str] = None,
        fields_disclosed: list[str] = None,
        notes: str = "",
    ) -> DisclosureRecord:
        """
        Log a disclosure of education records.

        Returns the created disclosure record.
        """
        if data_categories is None:
            data_categories = []
        if fields_disclosed is None:
            fields_disclosed = []

        disclosure = DisclosureRecord(
            record_id=record_id,
            disclosed_to=disclosed_to,
            disclosed_to_type=disclosed_to_type,
            purpose=purpose,
            authorization_basis=authorization_basis,
            disclosed_by=disclosed_by,
            authorized_by=authorized_by,
            consent_document_id=consent_document_id,
            expiration_date=expiration_date,
            status=DisclosureStatus.COMPLETED,
            data_categories=data_categories,
            fields_disclosed=fields_disclosed,
            notes=notes,
        )

        self.disclosures.append(disclosure)
        return disclosure

    def get_disclosure(self, disclosure_id: str) -> Optional[DisclosureRecord]:
        """Get a specific disclosure by ID."""
        for disclosure in self.disclosures:
            if disclosure.id == disclosure_id:
                return disclosure
        return None

    def get_disclosures_for_record(self, record_id: str) -> list[dict]:
        """Get all disclosures for a specific record."""
        return [d.to_dict() for d in self.disclosures if d.record_id == record_id]

    def get_disclosures_by_recipient(self, disclosed_to: str) -> list[dict]:
        """Get all disclosures to a specific recipient."""
        return [
            d.to_dict()
            for d in self.disclosures
            if d.disclosed_to.lower() == disclosed_to.lower()
        ]

    def get_disclosures_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> list[dict]:
        """Get disclosures within a date range."""
        return [
            d.to_dict()
            for d in self.disclosures
            if start_date <= d.disclosed_at <= end_date
        ]

    def check_consent_required(
        self, record_id: str, disclosed_to: str, data_category: str
    ) -> dict:
        """
        Check if consent is required for a potential disclosure.

        Returns assessment of consent requirement.
        """
        # Get recent disclosures to this recipient
        recipient_disclosures = [
            d
            for d in self.disclosures
            if d.record_id == record_id and d.disclosed_to == disclosed_to
        ]

        if not recipient_disclosures:
            return {
                "consent_required": True,
                "reason": "No prior disclosures found",
                "valid_consent": False,
            }

        # Check for valid, non-expired consent
        latest = max(recipient_disclosures, key=lambda d: d.disclosed_at)

        if latest.is_expired():
            return {
                "consent_required": True,
                "reason": "Previous consent has expired",
                "valid_consent": False,
                "expiration_date": latest.expiration_date,
            }

        if latest.authorization_basis == AuthorizationBasis.CONSENT:
            return {
                "consent_required": False,
                "reason": "Valid consent on file",
                "valid_consent": True,
                "consent_id": latest.consent_document_id,
            }

        return {
            "consent_required": False,
            "reason": f"Authorized under {latest.authorization_basis.value}",
            "valid_consent": True,
        }

    def revoke_disclosure(
        self, disclosure_id: str, revoked_by: str, reason: str
    ) -> bool:
        """Revoke a previous disclosure."""
        disclosure = self.get_disclosure(disclosure_id)
        if disclosure is None:
            return False

        disclosure.status = DisclosureStatus.REVOKED
        disclosure.notes = f"Revoked by {revoked_by}: {reason}"
        return True

    def get_disclosure_summary(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> dict:
        """Get summary statistics of disclosures."""
        disclosures = self.disclosures

        if start_date:
            disclosures = [d for d in disclosures if d.disclosed_at >= start_date]
        if end_date:
            disclosures = [d for d in disclosures if d.disclosed_at <= end_date]

        # Count by authorization basis
        by_basis = {}
        for d in disclosures:
            basis = d.authorization_basis.value
            by_basis[basis] = by_basis.get(basis, 0) + 1

        # Count by purpose
        by_purpose = {}
        for d in disclosures:
            purpose = d.purpose.value
            by_purpose[purpose] = by_purpose.get(purpose, 0) + 1

        # Count by recipient type
        by_recipient_type = {}
        for d in disclosures:
            rtype = d.disclosed_to_type or "unknown"
            by_recipient_type[rtype] = by_recipient_type.get(rtype, 0) + 1

        return {
            "total_disclosures": len(disclosures),
            "by_authorization_basis": by_basis,
            "by_purpose": by_purpose,
            "by_recipient_type": by_recipient_type,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    def export_audit_log(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json",
    ) -> list[dict]:
        """
        Export disclosure audit log for compliance reporting.

        Args:
            start_date: Filter disclosures from this date
            end_date: Filter disclosures until this date
            format: Output format (json, csv)

        Returns:
            List of disclosure records
        """
        disclosures = self.disclosures

        if start_date:
            disclosures = [d for d in disclosures if d.disclosed_at >= start_date]
        if end_date:
            disclosures = [d for d in disclosures if d.disclosed_at <= end_date]

        # Sort by disclosure date
        disclosures.sort(key=lambda d: d.disclosed_at)

        return [d.to_dict() for d in disclosures]

    def validate_disclosure_request(
        self,
        record_id: str,
        disclosed_to: str,
        disclosed_to_type: str,
        data_categories: list[str],
    ) -> dict:
        """
        Validate a disclosure request before processing.

        Returns validation result with any issues.
        """
        issues = []
        warnings = []

        # Check for required fields
        if not record_id:
            issues.append("Record ID is required")

        if not disclosed_to:
            issues.append("Recipient is required")

        # Check for valid recipient type
        valid_types = [
            "school_official",
            "parent",
            "student",
            "researcher",
            "government",
            "employer",
            "other",
        ]
        if disclosed_to_type not in valid_types:
            warnings.append(f"Unknown recipient type: {disclosed_to_type}")

        # Check for sensitive data categories
        sensitive_categories = ["assessment_scores", "student_responses"]
        sensitive_requested = [c for c in data_categories if c in sensitive_categories]
        if sensitive_requested:
            warnings.append(f"Request includes sensitive data: {sensitive_requested}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }
