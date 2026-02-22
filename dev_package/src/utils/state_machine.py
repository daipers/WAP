"""
state_machine.py
=================

This module defines a simple deterministic state machine base class.  The
orchestrator service uses this to manage assessment session states.

State machines are defined externally in YAML.  Each state has a set of
transitions keyed by event names.  An event triggers a transition to the
target state.  Invalid transitions raise errors.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import yaml


@dataclass
class StateMachine:
    """A deterministic state machine defined by a transition map."""

    transitions: Dict[str, Dict[str, str]]
    current_state: str = field(default="INIT")

    @classmethod
    def from_yaml(cls, yaml_path: str, initial_state: str = "INIT") -> "StateMachine":
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(transitions=data, current_state=initial_state)

    def trigger(self, event: str) -> str:
        """
        Trigger an event and transition to a new state.

        :param event: The event name.
        :return: The new state name.
        :raises: KeyError if the event is invalid for the current state.
        """
        if self.current_state not in self.transitions:
            raise KeyError(f"Unknown state {self.current_state}")
        state_map = self.transitions[self.current_state] or {}
        if event not in state_map:
            raise KeyError(
                f"Invalid event '{event}' for state '{self.current_state}'. Valid events: {list(state_map.keys())}"
            )
        new_state = state_map[event]
        self.current_state = new_state
        return new_state

    def allowed_events(self) -> Dict[str, str]:
        """Return a mapping of allowed events from the current state to next states."""
        return self.transitions.get(self.current_state, {}) or {}
