"""
interview_agent.py
==================

Minimal interview agent used by the demo flow. It selects a challenge,
attaches it to the session, triggers interview state transitions, and
optionally records an audit event.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class InterviewAgent:
    def __init__(
        self, content_bank: Any, orchestrator: Any, ledger: Any = None
    ) -> None:
        self._content_bank = content_bank
        self._orchestrator = orchestrator
        self._ledger = ledger

    def run_interview(self, session: Any) -> Dict[str, Any]:
        challenge = self._content_bank.select_random_challenge()
        challenge_id = challenge.get("id", "demo-item")

        if challenge_id not in session.selected_challenges:
            session.selected_challenges.append(challenge_id)

        injection_ids = self._collect_injection_ids(challenge)
        for injection_id in injection_ids:
            if injection_id not in session.selected_injections:
                session.selected_injections.append(injection_id)

        self._orchestrator.start_interview(session)
        self._orchestrator.submit_interview(session)

        if self._ledger is not None:
            self._ledger.record_event(
                session_id=session.session_id,
                actor="system",
                action="interview_completed",
                payload={
                    "challenge_id": challenge_id,
                    "injection_ids": injection_ids,
                },
                candidate_id=session.candidate_id,
            )

        return {
            "challenge_id": challenge_id,
            "injection_ids": injection_ids,
        }

    @staticmethod
    def _collect_injection_ids(challenge: Dict[str, Any]) -> List[str]:
        injection_ids: List[str] = []

        if "injection_id" in challenge and challenge["injection_id"]:
            injection_ids.append(str(challenge["injection_id"]))

        if "injection" in challenge and challenge["injection"]:
            injection_ids.append(str(challenge["injection"]))

        if "injection_ids" in challenge and challenge["injection_ids"]:
            for injection_id in challenge["injection_ids"]:
                injection_ids.append(str(injection_id))

        return injection_ids
