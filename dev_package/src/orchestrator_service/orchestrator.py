"""
orchestrator.py
===============

Lightweight orchestration helpers for demo flows. The orchestrator drives
state machine transitions, optionally records audit events, and can
sequence scoring + reporting when injected with dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from audit_ledger_service.ledger import AuditLedger

if TYPE_CHECKING:
    from scoring_engine.score_runs import ScoreRunRepository
    from scoring_engine.scoring_service import ScoringService


class Orchestrator:
    def __init__(
        self,
        ledger: Optional[AuditLedger] = None,
        scoring_service: Optional["ScoringService"] = None,
    ) -> None:
        self._ledger = ledger
        self._scoring_service = scoring_service

    def trigger_event(
        self,
        session: Any,
        event_name: str,
        payload: Optional[Dict[str, Any]] = None,
        actor: str = "system",
    ) -> str:
        new_state = session.state_machine.trigger(event_name)
        if self._ledger is not None:
            self._ledger.record_event(
                session_id=session.session_id,
                actor=actor,
                action=event_name,
                payload=payload or {"state": new_state},
                candidate_id=getattr(session, "candidate_id", "unknown"),
            )
        return new_state

    def start_diagnostic(self, session: Any) -> str:
        return self.trigger_event(
            session, "on_diagnostic_start", payload={"phase": "diagnostic"}
        )

    def submit_diagnostic(self, session: Any) -> str:
        return self.trigger_event(session, "on_submit", payload={"phase": "diagnostic"})

    def schedule_interview(self, session: Any) -> str:
        return self.trigger_event(
            session, "on_schedule_interview", payload={"phase": "interview"}
        )

    def start_interview(self, session: Any) -> str:
        return self.trigger_event(
            session, "on_interview_start", payload={"phase": "interview"}
        )

    def submit_interview(self, session: Any) -> str:
        return self.trigger_event(session, "on_submit", payload={"phase": "interview"})

    def extract_features(self, session: Any) -> str:
        return self.trigger_event(session, "on_extract_features")

    def score(self, session: Any) -> str:
        return self.trigger_event(session, "on_scoring")

    def quality_gate(self, session: Any, passed: bool) -> str:
        event_name = "on_quality_gate_pass" if passed else "on_quality_gate_fail"
        return self.trigger_event(session, event_name, payload={"passed": passed})

    def publish(self, session: Any) -> str:
        return self.trigger_event(session, "on_publish")

    def void(self, session: Any, reason: str = "quality_gate_failed") -> str:
        return self.trigger_event(session, "on_void", payload={"reason": reason})

    def run_scoring_pipeline(
        self,
        session: Any,
        responses: Dict[str, Any],
        item_context: Dict[str, Any],
        reporting_service: Any,
        score_runs: Optional["ScoreRunRepository"] = None,
    ) -> Dict[str, Any]:
        if self._scoring_service is None:
            raise ValueError("ScoringService dependency not provided")

        score_run = self._scoring_service.score_session(
            session_id=session.session_id,
            candidate_id=session.candidate_id,
            responses=responses,
            item_context=item_context,
        )

        repository = score_runs or getattr(self._scoring_service, "_score_runs", None)
        if repository is None:
            raise ValueError("ScoreRunRepository is required to build a scorecard")

        response_snapshot = repository.get_snapshot_by_id(
            score_run.response_snapshot_id
        )
        if response_snapshot is None:
            raise ValueError("Response snapshot not found for score run")

        return reporting_service.generate_scorecard(
            session.candidate_id, score_run, response_snapshot
        )
