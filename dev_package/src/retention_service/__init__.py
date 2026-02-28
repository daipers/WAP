"""
retention_service/__init__.py
=============================

FERPA-compliant data retention and disposal service.
"""

from retention_service.policies import (
    RetentionPolicy,
    RetentionManager,
    DataClassification,
)
from retention_service.disposal import DisposalService, DisposalRecord
from retention_service.classification import (
    DataClassification as ClassificationEnum,
    DataCategory,
    ClassificationEngine,
)
from retention_service.disclosure_log import (
    DisclosureLog,
    DisclosureRecord,
)

__all__ = [
    "RetentionPolicy",
    "RetentionManager",
    "DataClassification",
    "DisposalService",
    "DisposalRecord",
    "DataCategory",
    "ClassificationEngine",
    "DisclosureLog",
    "DisclosureRecord",
    "ClassificationEnum",
]
