"""
csv_export.py
=============

Utilities for exporting scorecards and evidence to CSV.
"""

from typing import Dict, Any
import csv
import json


def _stringify_response(response: Any) -> str:
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    return json.dumps(response, sort_keys=True)


def export_scorecard_to_csv(scorecard: Dict[str, Any], file_path: str) -> str:
    columns = [
        "candidate_id",
        "score_run_id",
        "rubric_version",
        "feature_version",
        "CPS",
        "ASI",
        "CPS_tier",
        "ASI_tier",
        "credential_level",
        "item_id",
        "response",
    ]
    evidence = scorecard.get("evidence") or {}

    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for item_id in sorted(evidence.keys()):
            response = evidence.get(item_id)
            writer.writerow(
                {
                    "candidate_id": scorecard.get("candidate_id"),
                    "score_run_id": scorecard.get("score_run_id"),
                    "rubric_version": scorecard.get("rubric_version"),
                    "feature_version": scorecard.get("feature_version"),
                    "CPS": scorecard.get("CPS"),
                    "ASI": scorecard.get("ASI"),
                    "CPS_tier": scorecard.get("CPS_tier"),
                    "ASI_tier": scorecard.get("ASI_tier"),
                    "credential_level": scorecard.get("credential_level"),
                    "item_id": item_id,
                    "response": _stringify_response(response),
                }
            )

    return file_path


def export_scorecard_csv(scorecard: Dict[str, Any], output_path: str) -> str:
    return export_scorecard_to_csv(scorecard, output_path)
