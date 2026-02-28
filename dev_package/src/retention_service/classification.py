"""
retention_service/classification.py
=====================================

Data classification framework for FERPA compliance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class DataClassification(Enum):
    """
    FERPA data classification levels.

    - EDUCATION_RECORD: Protected under FERPA, requires consent for disclosure
    - DIRECTORY_INFO: May be disclosed unless student opts out
    - PERSONAL_NOTE: Not an education record, not protected
    - AGGREGATED: De-identified, no restriction
    """

    EDUCATION_RECORD = "education_record"
    DIRECTORY_INFO = "directory_info"
    PERSONAL_NOTE = "personal_note"
    AGGREGATED = "aggregated"


class ClassificationRuleType(Enum):
    """Types of classification rules."""

    FIELD_PATTERN = "field_pattern"
    TABLE_NAME = "table_name"
    DATA_TYPE = "data_type"
    EXPLICIT_TAG = "explicit_tag"


@dataclass
class DataCategory:
    """Definition of a data category."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    classification: DataClassification = DataClassification.EDUCATION_RECORD
    requires_consent: bool = True
    can_disclose: bool = False
    retention_category: str = ""
    sensitivity_level: int = 1  # 1-5 scale

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "classification": self.classification.value,
            "requires_consent": self.requires_consent,
            "can_disclose": self.can_disclose,
            "retention_category": self.retention_category,
            "sensitivity_level": self.sensitivity_level,
        }


@dataclass
class ClassificationRule:
    """Rule for automatic data classification."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    rule_type: ClassificationRuleType = ClassificationRuleType.EXPLICIT_TAG
    pattern: str = ""  # Regex or table/field name
    classification: DataClassification = DataClassification.EDUCATION_RECORD
    category_name: str = ""
    enabled: bool = True

    def matches(
        self, table_name: str = "", field_name: str = "", tag: str = ""
    ) -> bool:
        """Check if this rule matches the given data."""
        if not self.enabled:
            return False

        if self.rule_type == ClassificationRuleType.TABLE_NAME:
            import re

            return bool(re.match(self.pattern, table_name, re.IGNORECASE))

        elif self.rule_type == ClassificationRuleType.FIELD_PATTERN:
            import re

            return bool(re.match(self.pattern, field_name, re.IGNORECASE))

        elif self.rule_type == ClassificationRuleType.EXPLICIT_TAG:
            return self.pattern.lower() == tag.lower()

        return False


class DefaultCategories:
    """Pre-defined data categories."""

    STUDENT_PROFILE = DataCategory(
        name="student_profile",
        description="Student personal information",
        classification=DataClassification.EDUCATION_RECORD,
        requires_consent=True,
        can_disclose=False,
        retention_category="student_responses",
        sensitivity_level=5,
    )

    ASSESSMENT_SCORE = DataCategory(
        name="assessment_score",
        description="Student assessment scores and results",
        classification=DataClassification.EDUCATION_RECORD,
        requires_consent=True,
        can_disclose=False,
        retention_category="assessment_scores",
        sensitivity_level=4,
    )

    STUDENT_RESPONSE = DataCategory(
        name="student_response",
        description="Student answers to assessment items",
        classification=DataClassification.EDUCATION_RECORD,
        requires_consent=True,
        can_disclose=False,
        retention_category="student_responses",
        sensitivity_level=4,
    )

    SESSION_LOG = DataCategory(
        name="session_log",
        description="Assessment session activity logs",
        classification=DataClassification.EDUCATION_RECORD,
        requires_consent=True,
        can_disclose=False,
        retention_category="session_logs",
        sensitivity_level=2,
    )

    STUDENT_NAME = DataCategory(
        name="student_name",
        description="Student name (directory information)",
        classification=DataClassification.DIRECTORY_INFO,
        requires_consent=False,
        can_disclose=True,
        retention_category="directory_info",
        sensitivity_level=1,
    )

    AGGREGATED_STATS = DataCategory(
        name="aggregated_stats",
        description="De-identified aggregated statistics",
        classification=DataClassification.AGGREGATED,
        requires_consent=False,
        can_disclose=True,
        retention_category="aggregated_analytics",
        sensitivity_level=1,
    )

    INSTRUCTOR_NOTES = DataCategory(
        name="instructor_notes",
        description="Instructor personal notes about students",
        classification=DataClassification.PERSONAL_NOTE,
        requires_consent=False,
        can_disclose=False,
        retention_category="personal_notes",
        sensitivity_level=3,
    )


class DefaultRules:
    """Pre-defined classification rules."""

    RULES = [
        # Student data - Education Record
        ClassificationRule(
            name="Student table",
            rule_type=ClassificationRuleType.TABLE_NAME,
            pattern=r"^student[s]?$",
            classification=DataClassification.EDUCATION_RECORD,
            category_name="student_profile",
        ),
        ClassificationRule(
            name="Score table",
            rule_type=ClassificationRuleType.TABLE_NAME,
            pattern=r"^score[s]?$",
            classification=DataClassification.EDUCATION_RECORD,
            category_name="assessment_score",
        ),
        ClassificationRule(
            name="Response table",
            rule_type=ClassificationRuleType.TABLE_NAME,
            pattern=r"^response[s]?$",
            classification=DataClassification.EDUCATION_RECORD,
            category_name="student_response",
        ),
        # Field patterns
        ClassificationRule(
            name="SSN field",
            rule_type=ClassificationRuleType.FIELD_PATTERN,
            pattern=r"(ssn|social.?security)",
            classification=DataClassification.EDUCATION_RECORD,
            category_name="student_profile",
        ),
        ClassificationRule(
            name="Score field",
            rule_type=ClassificationRuleType.FIELD_PATTERN,
            pattern=r"(score|result|grade)",
            classification=DataClassification.EDUCATION_RECORD,
            category_name="assessment_score",
        ),
        # Aggregated data
        ClassificationRule(
            name="Aggregated table",
            rule_type=ClassificationRuleType.TABLE_NAME,
            pattern=r"^aggregated",
            classification=DataClassification.AGGREGATED,
            category_name="aggregated_stats",
        ),
        # Directory info
        ClassificationRule(
            name="Directory info",
            rule_type=ClassificationRuleType.TABLE_NAME,
            pattern=r"^directory",
            classification=DataClassification.DIRECTORY_INFO,
            category_name="student_name",
        ),
    ]


class ClassificationEngine:
    """Engine for classifying data based on FERPA requirements."""

    def __init__(self):
        self.categories: dict[str, DataCategory] = {}
        self.rules: list[ClassificationRule] = []
        self._register_defaults()

    def _register_defaults(self):
        """Register default categories and rules."""
        # Register categories
        self.categories["student_profile"] = DefaultCategories.STUDENT_PROFILE
        self.categories["assessment_score"] = DefaultCategories.ASSESSMENT_SCORE
        self.categories["student_response"] = DefaultCategories.STUDENT_RESPONSE
        self.categories["session_log"] = DefaultCategories.SESSION_LOG
        self.categories["student_name"] = DefaultCategories.STUDENT_NAME
        self.categories["aggregated_stats"] = DefaultCategories.AGGREGATED_STATS
        self.categories["instructor_notes"] = DefaultCategories.INSTRUCTOR_NOTES

        # Register rules
        self.rules = list(DefaultRules.RULES)

    def classify(
        self, table_name: str = "", field_name: str = "", tag: str = ""
    ) -> DataClassification:
        """Classify data based on table, field, or tag."""
        # Check rules in order
        for rule in self.rules:
            if rule.matches(table_name, field_name, tag):
                return rule.classification

        # Default to education record (most protective)
        return DataClassification.EDUCATION_RECORD

    def get_category(self, category_name: str) -> Optional[DataCategory]:
        """Get category by name."""
        return self.categories.get(category_name)

    def add_category(self, category: DataCategory):
        """Add a custom category."""
        self.categories[category.name] = category

    def add_rule(self, rule: ClassificationRule):
        """Add a custom classification rule."""
        self.rules.append(rule)

    def can_disclose(self, category_name: str) -> bool:
        """Check if a category can be disclosed."""
        category = self.categories.get(category_name)
        if category is None:
            return False
        return category.can_disclose

    def requires_consent(self, category_name: str) -> bool:
        """Check if a category requires consent for disclosure."""
        category = self.categories.get(category_name)
        if category is None:
            return True  # Default to requiring consent
        return category.requires_consent

    def get_disclosure_requirements(self, category_name: str) -> dict:
        """Get disclosure requirements for a category."""
        category = self.categories.get(category_name)
        if category is None:
            return {
                "requires_consent": True,
                "can_disclose": False,
                "sensitivity_level": 1,
            }

        return {
            "requires_consent": category.requires_consent,
            "can_disclose": category.can_disclose,
            "sensitivity_level": category.sensitivity_level,
            "classification": category.classification.value,
        }

    def list_categories(self) -> list[dict]:
        """List all registered categories."""
        return [cat.to_dict() for cat in self.categories.values()]

    def list_rules(self) -> list[dict]:
        """List all classification rules."""
        return [
            {
                "id": rule.id,
                "name": rule.name,
                "rule_type": rule.rule_type.value,
                "pattern": rule.pattern,
                "classification": rule.classification.value,
                "category_name": rule.category_name,
                "enabled": rule.enabled,
            }
            for rule in self.rules
        ]

    def classify_record(self, metadata: dict) -> dict:
        """
        Classify a record based on its metadata.

        Args:
            metadata: Dictionary with table_name, field_name, tags, etc.

        Returns:
            Classification result with category and requirements.
        """
        table_name = metadata.get("table_name", "")
        field_name = metadata.get("field_name", "")
        tags = metadata.get("tags", [])

        # Try to match a rule
        classification = self.classify(table_name, field_name)

        # Find matching rule for category
        category_name = ""
        for rule in self.rules:
            if rule.matches(table_name, field_name):
                category_name = rule.category_name
                break

        # Get requirements
        requirements = self.get_disclosure_requirements(category_name)

        return {
            "classification": classification.value,
            "category": category_name,
            "requires_consent": requirements.get("requires_consent", True),
            "can_disclose": requirements.get("can_disclose", False),
            "sensitivity_level": requirements.get("sensitivity_level", 1),
        }
