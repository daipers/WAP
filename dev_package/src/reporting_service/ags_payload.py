"""
ags_payload.py
==============

Helpers to build LTI AGS score payloads from scorecards.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_ags_payload(scorecard: Dict[str, Any]) -> Dict[str, Any]:
    cps = _to_float(scorecard.get("CPS"))
    asi = _to_float(scorecard.get("ASI"))
    total_score = _to_float(scorecard.get("total_score"), cps + asi)
    max_score = _to_float(
        scorecard.get("max_score"),
        _to_float(scorecard.get("CPS_max"), 100.0)
        + _to_float(scorecard.get("ASI_max"), 100.0),
    )

    comment = scorecard.get("summary") or f"CPS {cps:.2f}, ASI {asi:.2f}"
    timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "scoreGiven": total_score,
        "scoreMaximum": max_score,
        "comment": comment,
        "timestamp": timestamp,
        "activityProgress": "Completed",
        "gradingProgress": "FullyGraded",
        "CPS": cps,
        "ASI": asi,
    }
