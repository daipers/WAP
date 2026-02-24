"""
feature_extractor.py
====================

Deterministic feature extraction helpers used by scoring services.
"""

from __future__ import annotations

from typing import Any, Dict


def _normalized(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return max(0.0, min(1.0, value / max_value))


def _detect_high_risk(responses: Dict[str, Any]) -> bool:
    for response in responses.values():
        if isinstance(response, dict):
            flags = response.get("integrity_flags") or {}
            if isinstance(flags, dict) and flags.get("high_risk"):
                return True
    return False


def extract_features(response_snapshot: Dict[str, Any]) -> Dict[str, Any]:
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
    high_risk = _detect_high_risk(responses)

    values: Dict[str, Any] = {
        "structure.plan_quality": _normalized(item_count, 5),
        "structure.decomposition_depth": _normalized(item_count, 8),
        "structure.logical_consistency": 0.8 if item_count else 0.0,
        "structure.correctness_rate": _normalized(total_length, 800),
        "structure.constraint_compliance": 1.0 if not high_risk else 0.2,
        "tooling_instincts.tool_selection_score": _normalized(avg_length, 400),
        "tooling_instincts.verification_rate": 0.6 if item_count else 0.0,
        "structure.output_clarity": _normalized(avg_length, 300),
        "structure.succinctness": max(0.0, 1.0 - _normalized(avg_length, 600)),
        "evaluation_discipline.self_check_rate": 0.5 if item_count else 0.0,
        "evaluation_discipline.test_count": float(item_count),
        "adaptation.response_latency": _normalized(item_count, 10),
        "adaptation.revision_count": 0.0,
        "failure_recovery.ack_latency": _normalized(item_count, 10),
        "failure_recovery.correction_success": 0.7 if item_count else 0.0,
        "meta_cognition.uncertainty_statements": _normalized(total_length, 1000),
        "meta_cognition.assumption_calls": _normalized(item_count, 6),
        "risk_anticipation.checklist_quality": _normalized(item_count, 6),
        "risk_anticipation.contingency_plans": _normalized(item_count, 6),
        "composure.prioritization_score": 0.8 if item_count else 0.0,
        "improvement_instinct.refinement_cycles": _normalized(item_count, 4),
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
