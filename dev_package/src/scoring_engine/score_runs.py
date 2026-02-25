"""
score_runs.py
=============

Immutable scoring run models and in-memory repository for deterministic
hashing of inputs and outputs (timestamps excluded from hashes).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import hashlib
import json
import time


def _stable_hash(payload: Dict[str, Any]) -> str:
    """Compute a deterministic SHA-256 hash for payload."""
    serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


@dataclass(frozen=True)
class ResponseSnapshot:
    snapshot_id: str
    session_id: str
    candidate_id: str
    responses: Dict[str, Any]
    item_context: Dict[str, Any]
    feature_values: Dict[str, Any]
    feature_version: str
    rubric_version: str
    created_at: float = field(default_factory=lambda: time.time())
    input_hash: Optional[str] = None

    def compute_input_hash(self) -> str:
        payload = {
            "snapshot_id": self.snapshot_id,
            "session_id": self.session_id,
            "candidate_id": self.candidate_id,
            "responses": self.responses,
            "item_context": self.item_context,
            "feature_values": self.feature_values,
            "feature_version": self.feature_version,
            "rubric_version": self.rubric_version,
        }
        return _stable_hash(payload)

    def with_hash(self) -> "ResponseSnapshot":
        if self.input_hash:
            return self
        return ResponseSnapshot(
            snapshot_id=self.snapshot_id,
            session_id=self.session_id,
            candidate_id=self.candidate_id,
            responses=self.responses,
            item_context=self.item_context,
            feature_values=self.feature_values,
            feature_version=self.feature_version,
            rubric_version=self.rubric_version,
            created_at=self.created_at,
            input_hash=self.compute_input_hash(),
        )


@dataclass(frozen=True)
class ScoreRun:
    score_run_id: str
    response_snapshot_id: str
    rubric_version: str
    feature_version: str
    score_output: Dict[str, Any]
    created_at: float = field(default_factory=lambda: time.time())
    output_hash: Optional[str] = None

    def compute_output_hash(self) -> str:
        payload = {
            "score_run_id": self.score_run_id,
            "response_snapshot_id": self.response_snapshot_id,
            "rubric_version": self.rubric_version,
            "feature_version": self.feature_version,
            "score_output": self.score_output,
        }
        return _stable_hash(payload)

    def with_hash(self) -> "ScoreRun":
        if self.output_hash:
            return self
        return ScoreRun(
            score_run_id=self.score_run_id,
            response_snapshot_id=self.response_snapshot_id,
            rubric_version=self.rubric_version,
            feature_version=self.feature_version,
            score_output=self.score_output,
            created_at=self.created_at,
            output_hash=self.compute_output_hash(),
        )


class ScoreRunRepository:
    def __init__(self) -> None:
        self._snapshots_by_id: Dict[str, ResponseSnapshot] = {}
        self._snapshots_by_hash: Dict[str, ResponseSnapshot] = {}
        self._score_runs_by_id: Dict[str, ScoreRun] = {}
        self._score_runs_by_hash: Dict[str, ScoreRun] = {}

    def add_snapshot(self, snapshot: ResponseSnapshot) -> ResponseSnapshot:
        snapshot_with_hash = snapshot.with_hash()
        self._snapshots_by_id[snapshot_with_hash.snapshot_id] = snapshot_with_hash
        if snapshot_with_hash.input_hash:
            self._snapshots_by_hash[snapshot_with_hash.input_hash] = snapshot_with_hash
        return snapshot_with_hash

    def add_score_run(self, score_run: ScoreRun) -> ScoreRun:
        score_run_with_hash = score_run.with_hash()
        self._score_runs_by_id[score_run_with_hash.score_run_id] = score_run_with_hash
        if score_run_with_hash.output_hash:
            self._score_runs_by_hash[score_run_with_hash.output_hash] = (
                score_run_with_hash
            )
        return score_run_with_hash

    def get_snapshot_by_id(self, snapshot_id: str) -> Optional[ResponseSnapshot]:
        return self._snapshots_by_id.get(snapshot_id)

    def get_snapshot_by_hash(self, input_hash: str) -> Optional[ResponseSnapshot]:
        return self._snapshots_by_hash.get(input_hash)

    def get_score_run_by_id(self, score_run_id: str) -> Optional[ScoreRun]:
        return self._score_runs_by_id.get(score_run_id)

    def get_score_run_by_hash(self, output_hash: str) -> Optional[ScoreRun]:
        return self._score_runs_by_hash.get(output_hash)

    def verify_score_run(self, score_run_id: str) -> bool:
        score_run = self._score_runs_by_id.get(score_run_id)
        if not score_run:
            return False
        expected_hash = score_run.compute_output_hash()
        return score_run.output_hash == expected_hash
