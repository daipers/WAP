"""
lockdown.py
===========

Lockdown enforcement helpers for assessment delivery.
Provides violation detection and enforcement rule generation.
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from delivery_service.integrity_config import LockdownConfig, LockdownLevel
    from delivery_service.models import AssessmentSession, AssessmentDefinition
    from delivery_service.integrity_events import (
        IntegrityEventType,
        IntegrityEventLogger,
    )


class LockdownEnforcer:
    """
    Enforces lockdown rules based on configuration and session events.
    Detects violations and generates enforcement rules for frontend.
    """

    def __init__(
        self,
        config: "LockdownConfig",
        session: "AssessmentSession",
    ):
        """
        Initialize the lockdown enforcer.

        Args:
            config: The lockdown configuration to enforce
            session: The assessment session to monitor
        """
        self.config = config
        self.session = session

    def check_violation(
        self,
        event_type: "IntegrityEventType",
        count: int = 1,
    ) -> bool:
        """
        Check if an event constitutes a violation based on the lockdown config.

        Args:
            event_type: The type of integrity event
            count: The count of events (for tab switches, etc.)

        Returns:
            True if the event is a violation, False otherwise
        """
        # For STANDARD level: >3 tab switches = violation
        if event_type.value == "tab_hidden":
            if self.config.max_tab_switches is not None:
                return count > self.config.max_tab_switches

        # For STRICT level: any fullscreen exit = violation
        if event_type.value == "fullscreen_exit":
            if self.config.require_fullscreen:
                # In strict mode, any exit is a violation
                return count > 0

        return False

    def check_tab_switch_violation(self, tab_switch_count: int) -> bool:
        """
        Check if tab switch count violates the configuration.

        Args:
            tab_switch_count: Current number of tab switches

        Returns:
            True if violates, False otherwise
        """
        return self.config.is_tab_switch_violation(tab_switch_count)

    def check_fullscreen_violation(self, fullscreen_exit_count: int) -> bool:
        """
        Check if fullscreen exits violate the configuration.

        Args:
            fullscreen_exit_count: Number of fullscreen exits

        Returns:
            True if violates, False otherwise
        """
        # If fullscreen is required, check the mode
        if not self.config.require_fullscreen:
            return False

        # In STANDARD: allow some exits (we track violations elsewhere)
        # In STRICT: any exit is a violation
        # We check this based on max_tab_switches being 0 (strict mode)
        if (
            self.config.max_tab_switches is not None
            and self.config.max_tab_switches == 0
        ):
            return fullscreen_exit_count > 0

        return False

    def get_enforcement_rules(self) -> str:
        """
        Generate JavaScript snippet for frontend enforcement.

        Returns:
            JavaScript code string that can be injected into the frontend
        """
        rules = []

        if self.config.require_fullscreen:
            rules.append("""
    // Require fullscreen mode
    document.addEventListener('fullscreenchange', function() {
        if (!document.fullscreenElement) {
            integrityLogger.log('fullscreen_exit', { timestamp: Date.now() });
        }
    });
    document.addEventListener('mozfullscreenchange', function() {
        if (!document.mozFullScreenElement) {
            integrityLogger.log('fullscreen_exit', { timestamp: Date.now() });
        }
    });
    document.addEventListener('webkitfullscreenchange', function() {
        if (!document.webkitFullscreenElement) {
            integrityLogger.log('fullscreen_exit', { timestamp: Date.now() });
        }
    });
    document.addEventListener('MSFullscreenChange', function() {
        if (!document.msFullscreenElement) {
            integrityLogger.log('fullscreen_exit', { timestamp: Date.now() });
        }
    });
""")

        if self.config.block_copy_paste:
            rules.append("""
    // Block copy/paste
    document.addEventListener('copy', function(e) {
        e.preventDefault();
        integrityLogger.log('copy_attempt', { timestamp: Date.now() });
        return false;
    });
    document.addEventListener('cut', function(e) {
        e.preventDefault();
        integrityLogger.log('copy_attempt', { timestamp: Date.now() });
        return false;
    });
    document.addEventListener('paste', function(e) {
        e.preventDefault();
        integrityLogger.log('paste_attempt', { timestamp: Date.now() });
        return false;
    });
""")

        if self.config.block_keyboard_shortcuts:
            rules.append("""
    // Block keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Block Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+U, Ctrl+I, Ctrl+Shift+I, F12
        if ((e.ctrlKey || e.metaKey) && 
            ['c', 'v', 'x', 'u', 'i'].includes(e.key.toLowerCase())) {
            e.preventDefault();
            integrityLogger.log('keyboard_shortcut', { 
                key: e.key, 
                timestamp: Date.now() 
            });
            return false;
        }
        // Block F12
        if (e.key === 'F12') {
            e.preventDefault();
            integrityLogger.log('keyboard_shortcut', { 
                key: 'F12', 
                timestamp: Date.now() 
            });
            return false;
        }
    });
""")

        if not self.config.allow_text_selection:
            rules.append("""
    // Disable text selection
    document.addEventListener('selectstart', function(e) {
        e.preventDefault();
        return false;
    });
    document.addEventListener('mousedown', function(e) {
        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
        }
    });
""")

        # Tab visibility tracking
        max_switches = self.config.max_tab_switches
        if max_switches is not None:
            rules.append(f"""
    // Track tab visibility
    let tabSwitchCount = 0;
    document.addEventListener('visibilitychange', function() {{
        if (document.hidden) {{
            tabSwitchCount++;
            integrityLogger.log('tab_hidden', {{ 
                count: tabSwitchCount, 
                timestamp: Date.now() 
            }});
            if (tabSwitchCount > {max_switches}) {{
                // Trigger violation handler
                if (typeof onIntegrityViolation === 'function') {{
                    onIntegrityViolation('tab_switch_limit_exceeded');
                }}
            }}
        }} else {{
            integrityLogger.log('tab_visible', {{ timestamp: Date.now() }});
        }}
    }});
""")

        return "\n".join(rules)

    def get_violation_message(self, event_type: "IntegrityEventType") -> str:
        """
        Get a user-friendly violation message for an event type.

        Args:
            event_type: The type of event that caused the violation

        Returns:
            Violation message string
        """
        messages = {
            "tab_hidden": f"Tab switch limit exceeded. Maximum allowed: {self.config.max_tab_switches}",
            "fullscreen_exit": "Fullscreen mode exit detected. Please remain in fullscreen for the duration of the assessment.",
            "copy_attempt": "Copy operation blocked for assessment integrity.",
            "paste_attempt": "Paste operation blocked for assessment integrity.",
            "keyboard_shortcut": "Keyboard shortcut blocked for assessment integrity.",
        }
        return messages.get(event_type.value, "Integrity violation detected.")


def apply_lockdown_rules(
    config: "LockdownConfig",
    session: "AssessmentSession",
    event_type: "IntegrityEventType",
    event_counts: Dict[str, int],
) -> tuple[bool, Optional[str]]:
    """
    Apply lockdown rules and check for violations.

    Args:
        config: The lockdown configuration
        session: The assessment session
        event_type: The type of event to check
        event_counts: Dictionary of event type counts

    Returns:
        Tuple of (is_violation, message)
    """
    enforcer = LockdownEnforcer(config, session)

    # Get count for this event type
    count = event_counts.get(event_type.value, 0)

    # Check for violation
    is_violation = enforcer.check_violation(event_type, count)

    if is_violation:
        message = enforcer.get_violation_message(event_type)
        return True, message

    return False, None


def create_enforcer_from_definition(
    definition: "AssessmentDefinition",
    session: "AssessmentSession",
) -> Optional[LockdownEnforcer]:
    """
    Create a LockdownEnforcer from an assessment definition.

    Args:
        definition: The assessment definition (with lockdown config)
        session: The assessment session

    Returns:
        LockdownEnforcer instance, or None if no lockdown config
    """
    from delivery_service.models import AssessmentDefinition

    if isinstance(definition, AssessmentDefinition) and definition.lockdown:
        return LockdownEnforcer(definition.lockdown, session)
    return None
