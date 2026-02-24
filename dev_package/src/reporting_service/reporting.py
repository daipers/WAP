"""
reporting.py
===========

Creates human‑readable scorecards and credential summaries from scores.
This simplified implementation uses rubric thresholds to assign tiers
such as Bronze, Silver, and Gold.  In a production system, the
reporting service would generate formatted documents, embed evidence
pointers, and provide links for employers to verify credentials.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

try:
    from scoring_engine.score_runs import ScoreRun, ResponseSnapshot
except ModuleNotFoundError:
    from ..scoring_engine.score_runs import ScoreRun, ResponseSnapshot

if TYPE_CHECKING:
    from scoring_engine.scoring_service import ScoringService


class ReportingService:
    def __init__(self, rubric: Dict[str, Any]):
        self.rubric = rubric

    def _tier(self, score: float, thresholds: Dict[str, float]) -> str:
        if score >= thresholds.get("gold", float("inf")):
            return "Gold"
        elif score >= thresholds.get("silver", float("inf")):
            return "Silver"
        elif score >= thresholds.get("bronze", float("inf")):
            return "Bronze"
        else:
            return "Insufficient"

    def generate_scorecard(
        self,
        candidate_id: str,
        score_run: ScoreRun,
        response_snapshot: ResponseSnapshot,
    ) -> Dict[str, Any]:
        scores = score_run.score_output
        cps_score = scores.get("CPS", 0)
        asi_score = scores.get("ASI", 0)
        cps_tier = self._tier(cps_score, self.rubric["cps"].get("thresholds", {}))
        asi_tier = self._tier(asi_score, self.rubric["asi"].get("thresholds", {}))
        # Example credential level: apprentice_ready if ASI >= threshold and integrity ok
        apprentice_threshold = (
            self.rubric["asi"].get("thresholds", {}).get("apprentice_ready", 85)
        )
        credential_level = (
            "Apprentice‑Ready" if asi_score >= apprentice_threshold else asi_tier
        )
        evidence = {
            item_id: response_snapshot.responses[item_id]
            for item_id in sorted(response_snapshot.responses.keys())
        }
        return {
            "candidate_id": candidate_id,
            "score_run_id": score_run.score_run_id,
            "response_snapshot_id": response_snapshot.snapshot_id,
            "rubric_version": score_run.rubric_version,
            "feature_version": score_run.feature_version,
            "CPS": cps_score,
            "ASI": asi_score,
            "CPS_tier": cps_tier,
            "ASI_tier": asi_tier,
            "credential_level": credential_level,
            "cps_breakdown": scores.get("cps_breakdown", {}),
            "asi_breakdown": scores.get("asi_breakdown", {}),
            "evidence": evidence,
        }


def generate_scorecard_with_evidence(
    score_run_id: str, scoring_service: Optional["ScoringService"] = None
) -> Dict[str, Any]:
    if scoring_service is None:
        raise ValueError("ScoringService is required to generate evidence scorecards")

    score_run = scoring_service.get_score_run(score_run_id)
    if score_run is None:
        raise ValueError(f"Score run {score_run_id} not found")

    response_snapshot = scoring_service.get_response_snapshot(
        score_run.response_snapshot_id
    )
    if response_snapshot is None:
        raise ValueError("Response snapshot not found for score run")

    rubric = scoring_service.get_rubric()
    reporting_service = ReportingService(rubric)
    return reporting_service.generate_scorecard(
        response_snapshot.candidate_id, score_run, response_snapshot
    )
