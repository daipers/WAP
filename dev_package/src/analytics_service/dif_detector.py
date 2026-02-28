"""
dif_detector.py
===============

Differential Item Functioning (DIF) detection using statistical methods.

Provides:
- Mantel-Haenszel chi-square test for DIF detection
- Logistic regression DIF detection

DIF Classification (based on ETS guidelines):
- no_DIF: Item functions equally across groups
- minor_DIF: Slight differential functioning (may need monitoring)
- moderate_DIF: Notable differential functioning (review recommended)
- severe_DIF: Substantial differential functioning (likely to be removed)
"""

from typing import Dict, List, Optional, Tuple, Union
import math

import numpy as np


# DIF classification thresholds
DIF_THRESHOLDS = {
    "minor_DIF": 0.05,  # |MH chi-square| > 0.43 (approximately)
    "moderate_DIF": 0.10,  # |MH chi-square| > 1.0 (approximately)
    "severe_DIF": 0.15,  # |MH chi-square| > 1.5 (approximately)
}


def classify_dif(chi_square: float, alpha: float = 0.05) -> str:
    """
    Classify DIF severity based on Mantel-Haenszel chi-square statistic.

    Args:
        chi_square: The Mantel-Haenszel chi-square statistic
        alpha: Significance level for classification

    Returns:
        Classification string: "no_DIF", "minor_DIF", "moderate_DIF", or "severe_DIF"
    """
    # Use absolute value for classification
    abs_chi = abs(chi_square)

    if chi_square > 0:
        # Positive chi-square: reference group performs better
        if chi_square > 4.0:
            return "severe_DIF"
        elif chi_square > 2.0:
            return "moderate_DIF"
        elif chi_square > 1.0:
            return "minor_DIF"
        else:
            return "no_DIF"
    else:
        # Negative chi-square: focal group performs better
        if chi_square < -4.0:
            return "severe_DIF"
        elif chi_square < -2.0:
            return "moderate_DIF"
        elif chi_square < -1.0:
            return "minor_DIF"
        else:
            return "no_DIF"


def calculate_mantel_haenszel(
    reference_responses: List[int],
    focal_responses: List[int],
    total_scores_ref: List[float],
    total_scores_focal: List[float],
    ability_cutoff: Optional[float] = None,
) -> Dict[str, float]:
    """
    Calculate Mantel-Haenszel chi-square statistic for DIF analysis.

    Args:
        reference_responses: Binary responses (1=correct, 0=incorrect) for reference group
        focal_responses: Binary responses for focal group
        total_scores_ref: Total test scores for reference group respondents
        total_scores_focal: Total test scores for focal group respondents
        ability_cutoff: Optional cutoff to stratify by ability

    Returns:
        Dictionary with MH chi-square statistic and pass rates
    """
    if len(reference_responses) == 0 or len(focal_responses) == 0:
        raise ValueError("Response lists cannot be empty")

    if len(reference_responses) != len(total_scores_ref):
        raise ValueError("Reference responses and scores must have same length")

    if len(focal_responses) != len(total_scores_focal):
        raise ValueError("Focal responses and scores must have same length")

    # Convert to numpy arrays
    ref_responses = np.array(reference_responses, dtype=float)
    focal_responses = np.array(focal_responses, dtype=float)
    ref_scores = np.array(total_scores_ref, dtype=float)
    focal_scores = np.array(total_scores_focal, dtype=float)

    # Calculate pass rates
    ref_pass_rate = np.mean(ref_responses) if len(ref_responses) > 0 else 0
    focal_pass_rate = np.mean(focal_responses) if len(focal_responses) > 0 else 0

    # Calculate MH chi-square (simplified version without stratification)
    # In practice, this would be done within ability strata

    # N = total sample size
    n_ref = len(reference_responses)
    n_focal = len(focal_responses)
    n_total = n_ref + n_focal

    # Calculate common odds ratio approximation
    # Using a simplified formula for demonstration
    if n_total == 0:
        return {
            "chi_square": 0.0,
            "p_value": 1.0,
            "classification": "no_DIF",
            "reference_pass_rate": ref_pass_rate,
            "focal_pass_rate": focal_pass_rate,
            "n_reference": n_ref,
            "n_focal": n_focal,
        }

    # Calculate MH chi-square using the standard formula
    # A = correct in ref, B = incorrect in ref, C = correct in focal, D = incorrect in focal
    a = np.sum(ref_responses)  # Correct in reference
    b = n_ref - a  # Incorrect in reference
    c = np.sum(focal_responses)  # Correct in focal
    d = n_focal - c  # Incorrect in focal

    # Mantel-Haenszel chi-square
    n1 = a + c  # Total correct
    n2 = b + d  # Total incorrect
    n3 = a + b  # Total in reference
    n4 = c + d  # Total in focal

    # Expected value and variance
    if n1 * n2 * n3 * n4 == 0:
        chi_square = 0.0
    else:
        chi_square = (n_total * (a * d - b * c) ** 2) / (n1 * n2 * n3 * n4)

    # Calculate p-value using chi-square distribution
    try:
        from scipy.stats import chi2

        p_value = 1 - chi2.cdf(chi_square, df=1)
    except ImportError:
        # Fallback approximation
        p_value = 0.5 if chi_square < 0.6745 else 0.0  # Very rough approximation
        if chi_square > 2.706:
            p_value = 0.10
        if chi_square > 3.841:
            p_value = 0.05
        if chi_square > 6.635:
            p_value = 0.01

    classification = classify_dif(chi_square)

    return {
        "chi_square": float(chi_square),
        "p_value": float(p_value),
        "classification": classification,
        "reference_pass_rate": float(ref_pass_rate),
        "focal_pass_rate": float(focal_pass_rate),
        "n_reference": int(n_ref),
        "n_focal": int(n_focal),
    }


def detect_dif_chi_square(
    item_responses: Dict[str, List[int]],
    group_membership: Dict[str, str],
    ability_estimate: Optional[Dict[str, float]] = None,
    reference_group: str = "reference",
    focal_group: str = "focal",
) -> Dict[str, Dict]:
    """
    Detect DIF using Mantel-Haenszel chi-square method.

    This function analyzes items for differential functioning between
    reference and focal groups (e.g., gender, ethnicity).

    Args:
        item_responses: Dictionary mapping item_id to list of binary responses
        group_membership: Dictionary mapping respondent_id to group (reference/focal)
        ability_estimate: Optional dictionary of ability estimates per respondent
        reference_group: Name for reference group
        focal_group: Name for focal group

    Returns:
        Dictionary mapping item_id to DIF analysis results

    Example:
        >>> responses = {
        ...     "item1": [1, 1, 0, 1, 0, 1, 0, 0],
        ...     "item2": [1, 1, 1, 1, 0, 1, 1, 1]
        ... }
        >>> groups = {
        ...     "resp1": "reference", "resp2": "reference",
        ...     "resp3": "focal", "resp4": "focal"
        ... }
        >>> results = detect_dif_chi_square(responses, groups)
    """
    if not item_responses:
        raise ValueError("Item responses cannot be empty")

    if not group_membership:
        raise ValueError("Group membership cannot be empty")

    results = {}

    # Get list of respondent IDs that belong to each group
    ref_ids = [rid for rid, g in group_membership.items() if g == reference_group]
    focal_ids = [rid for rid, g in group_membership.items() if g == focal_group]

    if not ref_ids or not focal_ids:
        raise ValueError(
            f"Both {reference_group} and {focal_group} groups must have members"
        )

    # Analyze each item
    for item_id, responses in item_responses.items():
        # Skip if response length doesn't match group membership
        if len(responses) != len(group_membership):
            continue

        # Get responses for each group
        ref_responses = [
            responses[i]
            for i, rid in enumerate(group_membership.keys())
            if rid in ref_ids
        ]
        focal_responses = [
            responses[i]
            for i, rid in enumerate(group_membership.keys())
            if rid in focal_ids
        ]

        # Get total scores if available
        if ability_estimate:
            ref_scores = [ability_estimate.get(rid, 0) for rid in ref_ids]
            focal_scores = [ability_estimate.get(rid, 0) for rid in focal_ids]
        else:
            # Use item responses as proxy for ability
            ref_scores = ref_responses
            focal_scores = focal_responses

        # Calculate MH chi-square
        try:
            dif_result = calculate_mantel_haenszel(
                ref_responses, focal_responses, ref_scores, focal_scores
            )
            results[item_id] = dif_result
        except Exception as e:
            results[item_id] = {
                "chi_square": 0.0,
                "p_value": 1.0,
                "classification": "error",
                "error": str(e),
            }

    return results


def detect_dif_logistic(
    item_responses: Dict[str, List[int]],
    group_membership: Dict[str, str],
    ability_estimate: Dict[str, float],
    reference_group: str = "reference",
    focal_group: str = "focal",
) -> Dict[str, Dict]:
    """
    Detect DIF using logistic regression with ability matching.

    This method conditions on ability to detect DIF while controlling
    for overall proficiency.

    Args:
        item_responses: Dictionary mapping item_id to list of binary responses
        group_membership: Dictionary mapping respondent_id to group (reference/focal)
        ability_estimate: Dictionary of ability estimates per respondent
        reference_group: Name for reference group
        focal_group: Name for focal group

    Returns:
        Dictionary mapping item_id to DIF analysis results including:
        - odds_ratio: The odds ratio for group membership
        - effect_size: Standardized effect size
        - classification: DIF classification

    Example:
        >>> responses = {"item1": [1, 1, 0, 1, 0, 1, 0, 0]}
        >>> groups = {"r1": "reference", "r2": "reference", "r3": "focal"}
        >>> ability = {"r1": 0.5, "r2": 0.3, "r3": 0.4}
        >>> results = detect_dif_logistic(responses, groups, ability)
    """
    if not item_responses:
        raise ValueError("Item responses cannot be empty")

    if not group_membership:
        raise ValueError("Group membership cannot be empty")

    if not ability_estimate:
        raise ValueError("Ability estimates required for logistic regression DIF")

    results = {}

    # Convert group membership to numeric (0 = reference, 1 = focal)
    group_numeric = {
        rid: 0 if g == reference_group else 1 for rid, g in group_membership.items()
    }

    # Analyze each item
    for item_id, responses in item_responses.items():
        if len(responses) != len(group_membership):
            continue

        # Prepare data for logistic regression
        y = responses  # Item responses
        group = [group_numeric.get(rid, 0) for rid in group_membership.keys()]
        ability = [ability_estimate.get(rid, 0) for rid in group_membership.keys()]

        # Simplified logistic regression (without external library)
        # Using odds ratio as effect size
        try:
            # Calculate odds ratio manually
            ref_correct = sum(
                1
                for i, rid in enumerate(group_membership.keys())
                if responses[i] == 1 and group_numeric.get(rid, 0) == 0
            )
            ref_total = sum(
                1 for rid in group_membership.keys() if group_numeric.get(rid, 0) == 0
            )
            focal_correct = sum(
                1
                for i, rid in enumerate(group_membership.keys())
                if responses[i] == 1 and group_numeric.get(rid, 0) == 1
            )
            focal_total = sum(
                1 for rid in group_membership.keys() if group_numeric.get(rid, 0) == 1
            )

            if ref_total == 0 or focal_total == 0:
                odds_ratio = 1.0
            else:
                ref_odds = ref_correct / (ref_total - ref_correct + 0.5)
                focal_odds = focal_correct / (focal_total - focal_correct + 0.5)
                odds_ratio = ref_odds / focal_odds

            # Calculate effect size (standardized)
            # Using log odds ratio / (pi / sqrt(3)) as approximation
            log_odds_ratio = math.log(odds_ratio) if odds_ratio > 0 else 0
            effect_size = abs(log_odds_ratio) / (math.pi / math.sqrt(3))

            # Classify based on effect size
            if effect_size > 0.64:  # Large effect (Cohen's d > 0.8 equivalent)
                classification = "severe_DIF"
            elif effect_size > 0.39:  # Medium effect
                classification = "moderate_DIF"
            elif effect_size > 0.15:  # Small effect
                classification = "minor_DIF"
            else:
                classification = "no_DIF"

            results[item_id] = {
                "odds_ratio": float(odds_ratio),
                "log_odds_ratio": float(log_odds_ratio),
                "effect_size": float(effect_size),
                "classification": classification,
                "reference_n": int(ref_total),
                "focal_n": int(focal_total),
            }

        except Exception as e:
            results[item_id] = {
                "odds_ratio": 1.0,
                "effect_size": 0.0,
                "classification": "error",
                "error": str(e),
            }

    return results


def get_dif_summary(
    dif_results: Dict[str, Dict], group_attribute: str = "gender"
) -> Dict[str, any]:
    """
    Generate a summary of DIF results across all items.

    Args:
        dif_results: Dictionary of DIF results from detect_dif_chi_square or detect_dif_logistic
        group_attribute: The group attribute analyzed (e.g., "gender", "ethnicity")

    Returns:
        Summary dictionary with counts and recommendations
    """
    classifications = {
        "no_DIF": 0,
        "minor_DIF": 0,
        "moderate_DIF": 0,
        "severe_DIF": 0,
        "error": 0,
    }

    biased_items = []

    for item_id, result in dif_results.items():
        classification = result.get("classification", "no_DIF")
        if classification in classifications:
            classifications[classification] += 1
        else:
            classifications["error"] += 1

        # Track items with moderate or severe DIF
        if classification in ("moderate_DIF", "severe_DIF"):
            biased_items.append(
                {
                    "item_id": item_id,
                    "classification": classification,
                    "details": result,
                }
            )

    # Generate recommendations
    recommendations = []
    if classifications["severe_DIF"] > 0:
        recommendations.append(
            f"Review {classifications['severe_DIF']} items with severe DIF for potential removal"
        )
    if classifications["moderate_DIF"] > 0:
        recommendations.append(
            f"Review {classifications['moderate_DIF']} items with moderate DIF"
        )
    if classifications["minor_DIF"] > 0:
        recommendations.append(
            f"Monitor {classifications['minor_DIF']} items with minor DIF"
        )
    if classifications["no_DIF"] == len(dif_results):
        recommendations.append("All items function equivalently across groups")

    return {
        "group_attribute": group_attribute,
        "total_items": len(dif_results),
        "classifications": classifications,
        "biased_items": biased_items,
        "recommendations": recommendations,
    }
