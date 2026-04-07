"""
accommodations.py
==================

Accessibility accommodation service for assessment delivery.
Provides time multipliers, format support, and accommodation profile management.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List


class AccommodationType(str, Enum):
    """Types of accessibility accommodations supported."""

    EXTRA_TIME = "EXTRA_TIME"
    LARGE_FONT = "LARGE_FONT"
    COLOR_CONTRAST = "COLOR_CONTRAST"
    SCREEN_READER = "SCREEN_READER"
    BRAILLE = "BRAILLE"


# Default time multiplier for extra time accommodation
DEFAULT_EXTRA_TIME_MULTIPLIER = 1.5

# Time multipliers for different accommodation levels
TIME_MULTIPLIERS = {
    AccommodationType.EXTRA_TIME: 1.0,  # Base - will be applied as multiplier
}

# Format mappings for different accommodation types
FORMAT_MAPPINGS = {
    AccommodationType.LARGE_FONT: "large_font",
    AccommodationType.COLOR_CONTRAST: "high_contrast",
    AccommodationType.SCREEN_READER: "screen_reader_optimized",
    AccommodationType.BRAILLE: "braille",
}


@dataclass
class AccommodationProfile:
    """
    Complete accommodation profile for a candidate.

    Contains all accommodations to be applied during assessment delivery.
    """

    candidate_id: str
    accommodations: Dict[AccommodationType, Any] = field(default_factory=dict)

    # Session-specific overrides
    session_overrides: Dict[str, Dict[AccommodationType, Any]] = field(
        default_factory=dict
    )

    def get_accommodation(self, acc_type: AccommodationType) -> Optional[Any]:
        """Get an accommodation value by type."""
        return self.accommodations.get(acc_type)

    def has_accommodation(self, acc_type: AccommodationType) -> bool:
        """Check if a specific accommodation is enabled."""
        return acc_type in self.accommodations

    def set_accommodation(self, acc_type: AccommodationType, value: Any) -> None:
        """Set an accommodation value."""
        self.accommodations[acc_type] = value

    def get_session_override(
        self, session_id: str, acc_type: AccommodationType
    ) -> Optional[Any]:
        """Get a session-specific accommodation override."""
        session_overrides = self.session_overrides.get(session_id, {})
        return session_overrides.get(acc_type)

    def set_session_override(
        self, session_id: str, acc_type: AccommodationType, value: Any
    ) -> None:
        """Set a session-specific accommodation override."""
        if session_id not in self.session_overrides:
            self.session_overrides[session_id] = {}
        self.session_overrides[session_id][acc_type] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "candidate_id": self.candidate_id,
            "accommodations": {k.value: v for k, v in self.accommodations.items()},
            "session_overrides": {
                sid: {k.value: v for k, v in overrides.items()}
                for sid, overrides in self.session_overrides.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AccommodationProfile":
        """Create from dictionary."""
        accommodations = {
            AccommodationType(k): v for k, v in data.get("accommodations", {}).items()
        }
        session_overrides = {
            sid: {AccommodationType(k): v for k, v in overrides.items()}
            for sid, overrides in data.get("session_overrides", {}).items()
        }
        return cls(
            candidate_id=data["candidate_id"],
            accommodations=accommodations,
            session_overrides=session_overrides,
        )


class AccommodationConflictError(Exception):
    """Raised when accommodations conflict with each other."""

    pass


class AccommodationService:
    """
    Service for managing accessibility accommodations.

    Provides:
    - Time limit adjustments based on EXTRA_TIME accommodation
    - Format selection based on visual/reading accommodations
    - Conflict validation for conflicting accommodation types
    """

    # Class constants for multipliers
    DEFAULT_EXTRA_TIME_MULTIPLIER = 1.5

    # Conflicting accommodation pairs
    CONFLICTING_PAIRS: List[tuple[AccommodationType, AccommodationType]] = [
        (AccommodationType.LARGE_FONT, AccommodationType.SCREEN_READER),
    ]

    def __init__(
        self,
        default_time_multiplier: float = DEFAULT_EXTRA_TIME_MULTIPLIER,
    ):
        """
        Initialize the accommodation service.

        Args:
            default_time_multiplier: Default multiplier for EXTRA_TIME (default 1.5x)
        """
        self._default_time_multiplier = default_time_multiplier

    @property
    def default_time_multiplier(self) -> float:
        """Get the default time multiplier."""
        return self._default_time_multiplier

    def get_adjusted_time_limit(
        self,
        base_minutes: int,
        profile: AccommodationProfile,
        session_id: Optional[str] = None,
    ) -> int:
        """
        Calculate adjusted time limit based on accommodation profile.

        Applies EXTRA_TIME multiplier if enabled. The multiplier is applied
        to the base time limit.

        Args:
            base_minutes: Base time limit in minutes
            profile: Accommodation profile
            session_id: Optional session ID for session-specific overrides

        Returns:
            Adjusted time limit in minutes
        """
        multiplier = 1.0

        # Check for EXTRA_TIME accommodation
        # Priority: session override > profile accommodation > default
        extra_time = None

        if session_id:
            extra_time = profile.get_session_override(
                session_id, AccommodationType.EXTRA_TIME
            )

        if extra_time is None:
            extra_time = profile.get_accommodation(AccommodationType.EXTRA_TIME)

        if extra_time is not None:
            # Extra time can be specified as:
            # - A multiplier (float like 1.5)
            # - Additional minutes (int like 30)
            if isinstance(extra_time, float):
                multiplier = extra_time
            elif isinstance(extra_time, int):
                # Additional minutes - convert to multiplier
                additional_fraction = (
                    extra_time / base_minutes if base_minutes > 0 else 0
                )
                multiplier = 1.0 + additional_fraction

        adjusted = int(base_minutes * multiplier)
        return max(adjusted, base_minutes)  # Never less than base

    def get_format_for_item(
        self,
        item_id: str,
        profile: AccommodationProfile,
    ) -> str:
        """
        Get the appropriate format for an item based on accommodation profile.

        Returns the format identifier that should be used to render the item
        for this candidate.

        Args:
            item_id: The item ID
            profile: Accommodation profile

        Returns:
            Format identifier (e.g., "default", "large_font", "high_contrast")
        """
        # Check for visual/reading accommodations
        if profile.has_accommodation(AccommodationType.LARGE_FONT):
            return FORMAT_MAPPINGS[AccommodationType.LARGE_FONT]

        if profile.has_accommodation(AccommodationType.COLOR_CONTRAST):
            return FORMAT_MAPPINGS[AccommodationType.COLOR_CONTRAST]

        if profile.has_accommodation(AccommodationType.SCREEN_READER):
            return FORMAT_MAPPINGS[AccommodationType.SCREEN_READER]

        if profile.has_accommodation(AccommodationType.BRAILLE):
            return FORMAT_MAPPINGS[AccommodationType.BRAILLE]

        return "default"

    def validate_accommodations(
        self,
        profile: AccommodationProfile,
    ) -> List[str]:
        """
        Validate accommodation profile for conflicts.

        Checks for:
        - Conflicting accommodation pairs
        - Invalid value types

        Args:
            profile: Accommodation profile to validate

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []
        accommodation_keys = list(profile.accommodations.keys())

        # Check for conflicting pairs
        for acc1, acc2 in self.CONFLICTING_PAIRS:
            if acc1 in profile.accommodations and acc2 in profile.accommodations:
                warnings.append(f"Conflict: {acc1.value} and {acc2.value} may conflict")

        # Validate EXTRA_TIME value
        extra_time = profile.get_accommodation(AccommodationType.EXTRA_TIME)
        if extra_time is not None:
            if isinstance(extra_time, (int, float)):
                if extra_time < 1.0:
                    warnings.append("EXTRA_TIME multiplier should be >= 1.0")
            else:
                warnings.append(
                    "EXTRA_TIME must be a number (multiplier or additional minutes)"
                )

        return warnings

    def check_conflicts(
        self,
        profile: AccommodationProfile,
    ) -> bool:
        """
        Check if there are any conflicting accommodations.

        Args:
            profile: Accommodation profile

        Returns:
            True if there are conflicts, False otherwise
        """
        return len(self.validate_accommodations(profile)) > 0

    def create_profile(
        self,
        candidate_id: str,
        extra_time: Optional[float] = None,
        large_font: bool = False,
        color_contrast: bool = False,
        screen_reader: bool = False,
        braille: bool = False,
    ) -> AccommodationProfile:
        """
        Convenience method to create an accommodation profile.

        Args:
            candidate_id: The candidate ID
            extra_time: Optional extra time multiplier or additional minutes
            large_font: Enable large font accommodation
            color_contrast: Enable high contrast accommodation
            screen_reader: Enable screen reader optimization
            braille: Enable braille format

        Returns:
            New AccommodationProfile
        """
        profile = AccommodationProfile(candidate_id=candidate_id)

        if extra_time is not None:
            profile.set_accommodation(AccommodationType.EXTRA_TIME, extra_time)

        if large_font:
            profile.set_accommodation(AccommodationType.LARGE_FONT, True)

        if color_contrast:
            profile.set_accommodation(AccommodationType.COLOR_CONTRAST, True)

        if screen_reader:
            profile.set_accommodation(AccommodationType.SCREEN_READER, True)

        if braille:
            profile.set_accommodation(AccommodationType.BRAILLE, True)

        return profile
