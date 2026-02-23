"""
scoring.py
==========

This module implements a simple deterministic scoring engine based on the
rubric.  It reads the rubric YAML and computes scores by multiplying
feature values by dimension weights and summing them.  Disqualifiers
can zero out scores.  The output includes a breakdown by dimension
and signal as well as total CPS and ASI.
"""

from typing import Dict, Any
import yaml


class ScoringEngine:
    def __init__(self, rubric_path: str):
        with open(rubric_path, "r", encoding="utf-8") as f:
            self.rubric = yaml.safe_load(f)

    def score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        values = features.get("values", {})
        cps_total = 0.0
        cps_breakdown: Dict[str, float] = {}
        asi_total = 0.0
        asi_breakdown: Dict[str, float] = {}
        cps_config = self.rubric.get("cps", {})
        asi_config = self.rubric.get("asi", {})
        cps_max_points = cps_config.get("total_points", 100)
        asi_max_points = asi_config.get("total_points", 100)

        # Check for disqualifiers
        for dq in self.rubric.get("disqualifiers", []):
            condition = dq.get("condition")
            # Very simple interpreter: we only handle integrity_flags.high_risk
            if condition == "integrity_flags.high_risk == true":
                if values.get("integrity_flags.high_risk", False):
                    return {
                        "CPS": 0,
                        "ASI": 0,
                        "cps_total": 0,
                        "asi_total": 0,
                        "total_score": 0,
                        "max_score": round(cps_max_points + asi_max_points, 2),
                        "cps_breakdown": {},
                        "asi_breakdown": {},
                        "disqualified": dq["name"],
                    }

        # CPS scoring
        total_points = cps_max_points
        for dim_name, dim_info in cps_config.get("dimensions", {}).items():
            weight = dim_info.get("weight", 0)
            feature_keys = dim_info.get("features", [])
            # Average of features
            if feature_keys:
                avg = sum(values.get(k, 0) for k in feature_keys) / len(feature_keys)
            else:
                avg = 0
            points = avg * weight * total_points
            cps_breakdown[dim_name] = round(points, 4)
            cps_total += points

        # ASI scoring
        total_points_asi = asi_max_points
        for sig_name, sig_info in asi_config.get("signals", {}).items():
            weight = sig_info.get("weight", 0)
            feature_keys = sig_info.get("features", [])
            if feature_keys:
                avg = sum(values.get(k, 0) for k in feature_keys) / len(feature_keys)
            else:
                avg = 0
            points = avg * weight * total_points_asi
            asi_breakdown[sig_name] = round(points, 4)
            asi_total += points

        cps_total_rounded = round(cps_total, 2)
        asi_total_rounded = round(asi_total, 2)
        total_score = round(cps_total_rounded + asi_total_rounded, 2)
        max_score = round(cps_max_points + asi_max_points, 2)

        return {
            "CPS": cps_total_rounded,
            "ASI": asi_total_rounded,
            "cps_total": cps_total_rounded,
            "asi_total": asi_total_rounded,
            "total_score": total_score,
            "max_score": max_score,
            "cps_breakdown": cps_breakdown,
            "asi_breakdown": asi_breakdown,
            "disqualified": None,
        }
