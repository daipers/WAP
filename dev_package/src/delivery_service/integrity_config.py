"""
integrity_config.py
===================

Lockdown configuration for assessment integrity controls.
Defines lockdown levels, configuration dataclass, and preset defaults.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class LockdownLevel(str, Enum):
    """Lockdown enforcement levels for assessments."""

    NONE = "NONE"  # No lockdown restrictions
    STANDARD = "STANDARD"  # Standard restrictions (default)
    STRICT = "STRICT"  # Maximum restrictions


@dataclass
class LockdownConfig:
    """
    Configuration for lockdown/integrity controls during assessment delivery.

    Attributes:
        require_fullscreen: Whether fullscreen mode is required
        block_copy_paste: Whether copy/paste is blocked
        block_keyboard_shortcuts: Whether keyboard shortcuts are blocked
        allow_text_selection: Whether text selection is allowed
        max_tab_switches: Maximum number of tab switches allowed (None = unlimited)
        log_all_events: Whether to log all integrity events
    """

    require_fullscreen: bool = False
    block_copy_paste: bool = False
    block_keyboard_shortcuts: bool = False
    allow_text_selection: bool = True
    max_tab_switches: Optional[int] = None
    log_all_events: bool = True

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_tab_switches is not None and self.max_tab_switches < 0:
            raise ValueError("max_tab_switches must be non-negative")

    def is_tab_switch_violation(self, tab_switch_count: int) -> bool:
        """Check if tab switch count exceeds the configured limit."""
        if self.max_tab_switches is None:
            return False
        return tab_switch_count > self.max_tab_switches

    def is_fullscreen_required(self) -> bool:
        """Check if fullscreen mode is required."""
        return self.require_fullscreen


def get_default_config(level: LockdownLevel = LockdownLevel.STANDARD) -> LockdownConfig:
    """
    Get preset lockdown configuration for a given level.

    Args:
        level: The lockdown level to get defaults for

    Returns:
        LockdownConfig with preset values for the specified level
    """
    presets = {
        LockdownLevel.NONE: LockdownConfig(
            require_fullscreen=False,
            block_copy_paste=False,
            block_keyboard_shortcuts=False,
            allow_text_selection=True,
            max_tab_switches=None,
            log_all_events=False,
        ),
        LockdownLevel.STANDARD: LockdownConfig(
            require_fullscreen=True,
            block_copy_paste=True,
            block_keyboard_shortcuts=False,
            allow_text_selection=False,
            max_tab_switches=3,
            log_all_events=True,
        ),
        LockdownLevel.STRICT: LockdownConfig(
            require_fullscreen=True,
            block_copy_paste=True,
            block_keyboard_shortcuts=True,
            allow_text_selection=False,
            max_tab_switches=0,  # Zero tolerance
            log_all_events=True,
        ),
    }
    return presets.get(level, presets[LockdownLevel.STANDARD])
