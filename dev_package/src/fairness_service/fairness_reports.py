"""
fairness_reports.py
===================

Comprehensive fairness assessment report generation.

This module provides:
- generate_fairness_report: Runs both chi-square and logistic regression DIF
- get_fairness_impact_score: Calculates overall fairness impact score

Generates reports suitable for compliance documentation.
"""

from typing import Dict, List, Optional, Union

import numpy as np

from dev_package.src.fairness_service.dif_logistic import (
    dif_with_matching,
    logistic_dif_analysis,
)


def generate_fairness_report(
    assessment_id: str,
    group_attribute: str,
    item_responses: Union[List[List[int]], np.ndarray],
    group_membership: Union[List[int], np.ndarray],
    ability_estimates: Union[List[float], np.ndarray],
    item_ids: Optional[Union[List[str], List[int]]] = None,
    reference_group: int = 0,
) -> Dict[str, Union[str, int, float, list, dict]]:
    """
    Generate comprehensive fairness report for an assessment.

    This function runs both chi-square and logistic regression DIF analysis
    and aggregates results into a comprehensive fairness assessment report.

    Args:
        assessment_id: Unique identifier for the assessment
        group_attribute: The demographic attribute being analyzed (e.g., "gender", "ethnicity")
        item_responses: Matrix of item responses (rows=examinees, columns=items)
        group_membership: Group membership for each examinee
        ability_estimates: Ability estimates for each examinee
        item_ids: Optional list of item identifiers
        reference_group: The reference group value (default 0)

    Returns:
        Dictionary containing:
        - assessment_id: The assessment identifier
        - group_attribute: The analyzed demographic attribute
        - total_items: Total number of items analyzed
        - items_with_dif: List of items with DIF detected
        - recommendations: List of recommendations
        - impact_score: Overall fairness impact score (0-100)
        - details: Detailed results for each item
        - summary: Summary statistics

    Example:
        >>> responses = [[1,1,1,0,0], [1,1,0,0,0], [1,0,1,1,0]]
        >>> groups = [0, 0, 1]
        >>> ability = [0.5, -0.3, 1.2]
        >>> report = generate_fairness_report("ASMT001", "gender", responses, groups, ability)
    """
    # Convert to numpy arrays
    item_responses = np.array(item_responses)
    group_membership = np.array(group_membership)
    ability_estimates = np.array(ability_estimates)

    n_examinees, n_items = item_responses.shape

    # Create item IDs if not provided
    if item_ids is None:
        item_ids = [f"item_{i + 1}" for i in range(n_items)]
    else:
        item_ids = list(item_ids)

    # Analyze each item
    item_results = []
    items_with_dif = []
    dif_classifications = {
        "uniform_DIF": 0,
        "nonuniform_DIF": 0,
        "no_DIF": 0,
    }

    for item_idx in range(n_items):
        item_response = item_responses[:, item_idx]
        item_id = item_ids[item_idx]

        # Run logistic regression DIF analysis
        lr_result = logistic_dif_analysis(
            item_response, group_membership, ability_estimates
        )

        # Run matched DIF analysis
        matched_result = dif_with_matching(
            item_response, group_membership, ability_estimates
        )

        # Determine if item has DIF
        has_dif = (
            lr_result["classification"] != "no_DIF"
            or matched_result["classification"] != "no_DIF"
        )

        if has_dif:
            items_with_dif.append(
                {
                    "item_id": item_id,
                    "item_index": item_idx,
                    "logistic_classification": lr_result["classification"],
                    "matched_classification": matched_result["classification"],
                    "odds_ratio": lr_result.get("odds_ratio", 1.0),
                    "p_value": lr_result.get("p_value", 1.0),
                }
            )
            dif_classifications[lr_result["classification"]] = (
                dif_classifications.get(lr_result["classification"], 0) + 1
            )
        else:
            dif_classifications["no_DIF"] += 1

        # Store item result
        item_results.append(
            {
                "item_id": item_id,
                "item_index": item_idx,
                "difficulty": float(np.mean(item_response)),
                "has_dif": has_dif,
                "logistic_dif": lr_result,
                "matched_dif": matched_result,
            }
        )

    # Calculate impact score
    impact_score = get_fairness_impact_score(items_with_dif, n_items)

    # Generate recommendations
    recommendations = _generate_recommendations(
        items_with_dif, dif_classifications, n_items
    )

    # Calculate summary statistics
    reference_n = int(np.sum(group_membership == reference_group))
    focal_n = int(np.sum(group_membership != reference_group))

    summary = {
        "total_examinees": n_examinees,
        "reference_group_size": reference_n,
        "focal_group_size": focal_n,
        "total_items_analyzed": n_items,
        "items_with_dif_count": len(items_with_dif),
        "items_with_dif_percentage": (
            (len(items_with_dif) / n_items * 100) if n_items > 0 else 0
        ),
        "dif_by_type": dif_classifications,
    }

    return {
        "assessment_id": assessment_id,
        "group_attribute": group_attribute,
        "total_items": n_items,
        "items_with_dif": items_with_dif,
        "recommendations": recommendations,
        "impact_score": impact_score,
        "details": item_results,
        "summary": summary,
    }


def get_fairness_impact_score(
    items_with_dif: Union[List[Dict], List],
    total_items: int,
) -> float:
    """
    Calculate overall fairness impact score.

    The impact score ranges from 0 to 100:
    - 0-20: Excellent - minimal DIF, assessment is fair
    - 21-40: Good - minor DIF detected, low impact
    - 41-60: Moderate - moderate DIF, review recommended
    - 61-80: Fair - significant DIF, action recommended
    - 81-100: Poor - severe DIF, immediate action required

    Args:
        items_with_dif: List of items with detected DIF
        total_items: Total number of items in the assessment

    Returns:
        Impact score (0-100)

    Example:
        >>> items = [{"item_id": "item_1", "classification": "uniform_DIF"}]
        >>> score = get_fairness_impact_score(items, 50)
    """
    if total_items == 0:
        return 0.0

    # Calculate proportion of items with DIF
    dif_proportion = len(items_with_dif) / total_items

    # Weight by severity (different classifications have different impacts)
    severity_weights = {
        "uniform_DIF": 1.0,
        "nonuniform_DIF": 1.2,  # Non-uniform is harder to detect and fix
        "severe_DIF": 1.5,
        "moderate_DIF": 1.2,
        "mild_DIF": 0.8,
    }

    weighted_count = 0
    for item in items_with_dif:
        classification = item.get("classification", "uniform_DIF")
        weight = severity_weights.get(classification, 1.0)

        # Also consider effect size (odds ratio)
        odds_ratio = item.get("odds_ratio", 1.0)
        if odds_ratio > 1:
            effect_weight = min(1.5, odds_ratio / 2)
        else:
            effect_weight = min(1.5, 1.0 / odds_ratio)
            effect_weight = max(0.5, effect_weight)

        weighted_count += weight * effect_weight

    # Calculate final score
    base_score = dif_proportion * 100
    weighted_score = (weighted_count / total_items) * 100

    # Combine base and weighted (weighted accounts for severity)
    impact_score = base_score * 0.4 + weighted_score * 0.6

    # Ensure bounds
    return float(min(100.0, max(0.0, impact_score)))


def _generate_recommendations(
    items_with_dif: List[Dict],
    dif_classifications: Dict[str, int],
    total_items: int,
) -> List[Dict[str, str]]:
    """
    Generate recommendations based on DIF analysis results.

    Args:
        items_with_dif: List of items with detected DIF
        dif_classifications: Count of each DIF classification
        total_items: Total number of items

    Returns:
        List of recommendations with priority and description
    """
    recommendations = []

    # Calculate percentage
    dif_percentage = (len(items_with_dif) / total_items * 100) if total_items > 0 else 0

    # Overall assessment
    if dif_percentage < 5:
        recommendations.append(
            {
                "priority": "info",
                "category": "overall",
                "message": "Assessment shows minimal DIF - overall fairness is acceptable",
            }
        )
    elif dif_percentage < 15:
        recommendations.append(
            {
                "priority": "medium",
                "category": "overall",
                "message": f"Moderate DIF detected ({dif_percentage:.1f}% of items) - review recommended",
            }
        )
    else:
        recommendations.append(
            {
                "priority": "high",
                "category": "overall",
                "message": f"High level of DIF ({dif_percentage:.1f}% of items) - immediate review required",
            }
        )

    # Specific issues
    if dif_classifications.get("uniform_DIF", 0) > 0:
        recommendations.append(
            {
                "priority": "medium",
                "category": "uniform_dif",
                "message": f"{dif_classifications['uniform_DIF']} items show uniform DIF - "
                "these items may be easier/harder for one group regardless of ability",
            }
        )

    if dif_classifications.get("nonuniform_DIF", 0) > 0:
        recommendations.append(
            {
                "priority": "high",
                "category": "nonuniform_dif",
                "message": f"{dif_classifications['nonuniform_DIF']} items show nonuniform DIF - "
                "differential item functioning varies by ability level",
            }
        )

    # Specific item recommendations
    if len(items_with_dif) > 0:
        severe_items = [
            item["item_id"]
            for item in items_with_dif
            if item.get("classification", "").lower().find("severe") >= 0
        ]
        if severe_items:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "items",
                    "message": f"Review items: {', '.join(severe_items[:5])} - severe DIF detected",
                }
            )

    # Compliance recommendation
    if dif_percentage > 10:
        recommendations.append(
            {
                "priority": "high",
                "category": "compliance",
                "message": "Assessment may not meet fairness standards - "
                "consider revising items or adjusting scoring",
            }
        )
    else:
        recommendations.append(
            {
                "priority": "info",
                "category": "compliance",
                "message": "Assessment appears to meet standard fairness criteria",
            }
        )

    return recommendations
