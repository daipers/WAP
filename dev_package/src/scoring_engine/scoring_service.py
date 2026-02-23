"""
scoring_service.py
==================

ScoringService orchestrates feature extraction, rubric selection, scoring,
score run persistence, and audit logging.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import time
import uuid

from audit_ledger_service.events import EventType, create_event
from audit_ledger_service.ledger import AuditLedger
from feature_extractor.extractor import FeatureExtractor
from scoring_engine.score_runs import ResponseSnapshot, ScoreRun, ScoreRunRepository
from scoring_engine.scoring import ScoringEngine


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
        feature_extractor: Optional[FeatureExtractor] = None,
        rubric_map: Optional[Dict[str, Dict[str, str]]] = None,
        default_rubric_path: Optional[str] = None,
        default_rubric_version: str = "unknown",
    ) -> None:
        self._base_scoring_engine = scoring_engine
        self._audit_ledger = audit_ledger
        self._score_runs = score_runs
        self._feature_extractor = feature_extractor or FeatureExtractor()
        self._rubric_map = rubric_map or {}
        self._default_rubric_path = default_rubric_path
        self._default_rubric_version = default_rubric_version

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

    def score_session(
        self,
        session_id: str,
        candidate_id: str,
        responses: Dict[str, Any],
        item_context: Dict[str, Any],
    ) -> ScoreRun:
        feature_set = self._feature_extractor.extract_features(
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
