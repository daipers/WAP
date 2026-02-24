"""
scoring_service.py
==================

ScoringService orchestrates feature extraction, rubric selection, scoring,
score run persistence, and audit logging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional
import time
import uuid

try:
    from audit_ledger_service.events import EventType, create_event
    from audit_ledger_service.ledger import AuditLedger
except ModuleNotFoundError:
    from ..audit_ledger_service.events import EventType, create_event
    from ..audit_ledger_service.ledger import AuditLedger

from .score_runs import ResponseSnapshot, ScoreRun, ScoreRunRepository
from .scoring import ScoringEngine


@dataclass
class RubricSelection:
    rubric_path: str
    rubric_version: str


class ScoringService:
    def __init__(
        self,
        scoring_engine: ScoringEngine,
        audit_ledger: AuditLedger,
        score_runs: ScoreRunRepository,
        feature_extractor: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        rubric_map: Optional[Dict[str, Dict[str, str]]] = None,
        default_rubric_path: Optional[str] = None,
        default_rubric_version: str = "unknown",
    ) -> None:
        self._base_scoring_engine = scoring_engine
        self._audit_ledger = audit_ledger
        self._score_runs = score_runs
        self._feature_extractor = feature_extractor or self._extract_features
        self._rubric_map = rubric_map or {}
        self._default_rubric_path = default_rubric_path
        self._default_rubric_version = default_rubric_version

    @staticmethod
    def _normalized(value: float, max_value: float) -> float:
        if max_value <= 0:
            return 0.0
        return max(0.0, min(1.0, value / max_value))

    @staticmethod
    def _detect_high_risk(responses: Dict[str, Any]) -> bool:
        for response in responses.values():
            if isinstance(response, dict):
                flags = response.get("integrity_flags") or {}
                if isinstance(flags, dict) and flags.get("high_risk"):
                    return True
        return False

    def _extract_features(self, response_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        responses = response_snapshot.get("responses") or {}
        item_ids = sorted(responses.keys())
        item_count = len(item_ids)
        answer_lengths = []

        for item_id in item_ids:
            response = responses.get(item_id, {})
            if isinstance(response, dict):
                answer = response.get("answer", "")
            else:
                answer = response
            answer_lengths.append(len(str(answer)))

        total_length = float(sum(answer_lengths))
        avg_length = total_length / item_count if item_count else 0.0
        high_risk = self._detect_high_risk(responses)

        values: Dict[str, Any] = {
            "structure.plan_quality": self._normalized(item_count, 5),
            "structure.decomposition_depth": self._normalized(item_count, 8),
            "structure.logical_consistency": 0.8 if item_count else 0.0,
            "structure.correctness_rate": self._normalized(total_length, 800),
            "structure.constraint_compliance": 1.0 if not high_risk else 0.2,
            "tooling_instincts.tool_selection_score": self._normalized(avg_length, 400),
            "tooling_instincts.verification_rate": 0.6 if item_count else 0.0,
            "structure.output_clarity": self._normalized(avg_length, 300),
            "structure.succinctness": max(0.0, 1.0 - self._normalized(avg_length, 600)),
            "evaluation_discipline.self_check_rate": 0.5 if item_count else 0.0,
            "evaluation_discipline.test_count": float(item_count),
            "adaptation.response_latency": self._normalized(item_count, 10),
            "adaptation.revision_count": 0.0,
            "failure_recovery.ack_latency": self._normalized(item_count, 10),
            "failure_recovery.correction_success": 0.7 if item_count else 0.0,
            "meta_cognition.uncertainty_statements": self._normalized(
                total_length, 1000
            ),
            "meta_cognition.assumption_calls": self._normalized(item_count, 6),
            "risk_anticipation.checklist_quality": self._normalized(item_count, 6),
            "risk_anticipation.contingency_plans": self._normalized(item_count, 6),
            "composure.prioritization_score": 0.8 if item_count else 0.0,
            "improvement_instinct.refinement_cycles": self._normalized(item_count, 4),
            "integrity_flags.high_risk": high_risk,
        }

        return {
            "version": "1.0",
            "values": values,
            "summary": {
                "item_count": item_count,
                "response_length": total_length,
            },
        }

    def _resolve_rubric(self, item_context: Dict[str, Any]) -> RubricSelection:
        rubric_path = item_context.get("rubric_path")
        rubric_version = item_context.get("rubric_version")

        if not rubric_path:
            item_id = item_context.get("item_id")
            mapping = self._rubric_map.get(item_id) if item_id else None
            if mapping:
                rubric_path = mapping.get("rubric_path")
                rubric_version = rubric_version or mapping.get("rubric_version")

        if not rubric_path and self._default_rubric_path:
            rubric_path = self._default_rubric_path

        if not rubric_path:
            raise ValueError("No rubric_path available for scoring request")

        return RubricSelection(
            rubric_path=rubric_path,
            rubric_version=rubric_version or self._default_rubric_version,
        )

    def _scoring_engine_for_rubric(self, rubric_path: str) -> ScoringEngine:
        base_cls = self._base_scoring_engine.__class__
        return base_cls(rubric_path)

    def get_score_run(self, score_run_id: str) -> Optional[ScoreRun]:
        return self._score_runs.get_score_run_by_id(score_run_id)

    def get_response_snapshot(self, snapshot_id: str) -> Optional[ResponseSnapshot]:
        return self._score_runs.get_snapshot_by_id(snapshot_id)

    def get_rubric(self) -> Dict[str, Any]:
        return getattr(self._base_scoring_engine, "rubric", {})

    def score_session(
        self,
        session_id: str,
        candidate_id: str,
        responses: Dict[str, Any],
        item_context: Dict[str, Any],
    ) -> ScoreRun:
        feature_set = self._feature_extractor(
            {
                "session_id": session_id,
                "candidate_id": candidate_id,
                "responses": responses,
                "item_context": item_context,
            }
        )

        rubric = self._resolve_rubric(item_context)
        scoring_engine = self._scoring_engine_for_rubric(rubric.rubric_path)
        score_output = scoring_engine.score(feature_set)

        snapshot = ResponseSnapshot(
            snapshot_id=str(uuid.uuid4()),
            session_id=session_id,
            candidate_id=candidate_id,
            responses=responses,
            item_context=item_context,
            feature_values=feature_set.get("values", {}),
            feature_version=feature_set.get("version", "unknown"),
            rubric_version=rubric.rubric_version,
            created_at=time.time(),
        ).with_hash()
        self._score_runs.add_snapshot(snapshot)

        score_run = ScoreRun(
            score_run_id=str(uuid.uuid4()),
            response_snapshot_id=snapshot.snapshot_id,
            rubric_version=rubric.rubric_version,
            feature_version=snapshot.feature_version,
            score_output=score_output,
            created_at=time.time(),
        ).with_hash()
        self._score_runs.add_score_run(score_run)

        event = create_event(
            event_type=EventType.SCORING_RUN_CREATED,
            session_id=session_id,
            candidate_id=candidate_id,
            actor="system",
            payload={
                "score_run_id": score_run.score_run_id,
                "response_snapshot_id": snapshot.snapshot_id,
                "rubric_version": score_run.rubric_version,
                "feature_version": score_run.feature_version,
                "input_hash": snapshot.input_hash,
                "output_hash": score_run.output_hash,
            },
            metadata={"rubric_path": rubric.rubric_path},
            timestamp=time.time(),
        )
        self._audit_ledger.record_audit_event(event)

        return score_run
