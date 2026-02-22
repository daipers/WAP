"""
models.py
=========

Data models for the Delivery Service.
Provides assessment definitions, section configurations, and selection rules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from delivery_service.integrity_config import LockdownConfig


class NavigationMode(str, Enum):
    """Defines how test-takers can navigate through the assessment."""

    LINEAR = "LINEAR"  # Forward-only navigation
    NON_LINEAR = "NON_LINEAR"  # Free navigation (jump to any item)
    HYBRID = "HYBRID"  # Section-locked navigation within sections


class SelectionMode(str, Enum):
    """Defines how items are selected from the item pool."""

    RANDOM = "RANDOM"  # Random selection from pool
    FIXED = "FIXED"  # Fixed order as defined in pool
    ADAPTIVE = "ADAPTIVE"  # Adaptive selection based on performance


class OrderMode(str, Enum):
    """Defines how items are ordered within sections."""

    SEQUENTIAL = "SEQUENTIAL"  # Sequential order as defined
    RANDOM = "RANDOM"  # Random order
    SHUFFLE_SECTIONS = "SHUFFLE_SECTIONS"  # Shuffle section order


@dataclass
class SelectionRule:
    """
    Defines rules for selecting items from the item pool.
    """

    rule_type: SelectionMode  # random, fixed, adaptive
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.rule_type, str):
            self.rule_type = SelectionMode(self.rule_type)


@dataclass
class SectionConfig:
    """
    Configuration for a single section within an assessment.
    """

    section_id: str
    name: str
    item_pool_ids: List[str]  # List of item IDs available in this section
    selection_mode: SelectionMode = SelectionMode.RANDOM
    items_to_select: int = 0  # 0 means select all available
    order_mode: OrderMode = OrderMode.SEQUENTIAL
    time_limit_seconds: Optional[int] = None  # None means no time limit
    parameters: Dict[str, Any] = field(default_factory=dict)  # For adaptive rules

    def __post_init__(self):
        if isinstance(self.selection_mode, str):
            self.selection_mode = SelectionMode(self.selection_mode)
        if isinstance(self.order_mode, str):
            self.order_mode = OrderMode(self.order_mode)


@dataclass
class AssessmentDefinition:
    """
    Defines a complete assessment/test with sections, timing, and navigation rules.
    """

    assessment_id: str
    title: str
    sections: List[SectionConfig]
    time_limit_seconds: Optional[int] = None  # Overall time limit (None = no limit)
    attempt_limit: Optional[int] = None  # Max attempts (None = unlimited)
    navigation_mode: NavigationMode = NavigationMode.LINEAR
    lockdown: Optional[LockdownConfig] = None  # Lockdown/integrity settings
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if isinstance(self.navigation_mode, str):
            self.navigation_mode = NavigationMode(self.navigation_mode)
        # Ensure sections are SectionConfig objects
        self.sections = [
            s if isinstance(s, SectionConfig) else SectionConfig(**s)
            for s in self.sections
        ]

    def get_section(self, section_id: str) -> Optional[SectionConfig]:
        """Get a section by ID."""
        for section in self.sections:
            if section.section_id == section_id:
                return section
        return None


@dataclass
class AssessmentSession:
    """
    Represents an active assessment session.
    Tracks progress, responses, and timing.
    """

    session_id: str
    assessment_id: str
    test_taker_id: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    current_section_index: int = 0
    current_item_index: int = 0
    responses: Dict[str, Any] = field(default_factory=dict)
    flagged_items: List[str] = field(default_factory=list)
    time_remaining_seconds: Optional[int] = None
    is_completed: bool = False
    is_paused: bool = False

    def get_current_section(
        self, definition: AssessmentDefinition
    ) -> Optional[SectionConfig]:
        """Get the current section based on progress."""
        if 0 <= self.current_section_index < len(definition.sections):
            return definition.sections[self.current_section_index]
        return None

    def mark_completed(self) -> None:
        """Mark the session as completed."""
        self.completed_at = datetime.utcnow()
        self.is_completed = True

    def pause(self) -> None:
        """Pause the session."""
        self.is_paused = True

    def resume(self) -> None:
        """Resume the session."""
        self.is_paused = False
