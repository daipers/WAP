"""
integrity_checker.py
====================

Minimal integrity checker for the demo flow.
"""

from __future__ import annotations

from typing import Any, Dict


class IntegrityChecker:
    def __init__(self, high_risk: bool = False) -> None:
        self._high_risk = high_risk

    def check(self, session: Any) -> Dict[str, Any]:
        return {
            "high_risk": self._high_risk,
            "session_id": getattr(session, "session_id", None),
        }
