"""
irt_analysis.py
===============

Item Response Theory (IRT) based analysis for fairness assessment.

This module provides:
- estimate_ability_3pl: 3-parameter logistic IRT ability estimation
- calculate_item_discrimination: Item discrimination parameters
- calculate_item_difficulty_irt: IRT difficulty parameters
- detect_dfit: Differential Functioning of Items and Tests (DFIT) analysis

Uses numpy for matrix operations and implements a simplified 3PL model.
"""

from typing import Dict, List, Tuple, Union

import numpy as np


def estimate_ability_3pl(
    responses: Union[List[List[int]], np.ndarray],
    a: Union[List[float], np.ndarray, None] = None,
    b: Union[List[float], np.ndarray, None] = None,
    c: Union[List[float], np.ndarray, None] = None,
    max_iterations: int = 50,
    tolerance: float = 1e-4,
) -> np.ndarray:
    """
    Estimate examinee ability using 3-parameter logistic IRT model.

    The 3PL model: P(x=1|theta) = c + (1-c) / (1 + exp(-Da(theta - b)))
    Where:
    - a = discrimination parameter
    - b = difficulty parameter
    - c = guessing parameter

    Args:
        responses: Response matrix (rows=examinees, columns=items)
        a: Item discrimination parameters (if None, estimate from data)
        b: Item difficulty parameters (if None, estimate from data)
        c: Item guessing parameters (default 0.25 for multiple choice)
        max_iterations: Maximum EM iterations
        tolerance: Convergence tolerance

    Returns:
        Array of ability estimates (theta) for each examinee

    Example:
        >>> # 10 examinees, 5 items
        >>> responses = [[1,1,1,0,0], [1,1,0,0,0], [1,0,1,1,0], [0,1,1,1,0]]
        >>> theta = estimate_ability_3pl(responses)
    """
    responses = np.array(responses)
    n_examinees, n_items = responses.shape

    # Set default item parameters if not provided
    if a is None:
        # Initialize discrimination (typically 0.5 to 2.5)
        a = np.random.uniform(0.5, 1.5, n_items)
    else:
        a = np.array(a)

    if b is None:
        # Initialize difficulty (centered at 0)
        b = np.linspace(-1.5, 1.5, n_items)
    else:
        b = np.array(b)

    if c is None:
        # Default guessing parameter for multiple choice
        c = np.full(n_items, 0.25)
    else:
        c = np.array(c)

    # Ensure c is bounded
    c = np.clip(c, 0, 0.5)

    # Initialize theta using total score
    total_scores = np.sum(responses, axis=1)
    theta = (total_scores - n_items / 2) / np.sqrt(n_items / 4)  # Approx z-score

    # Newton-Raphson iteration for ability estimation
    for iteration in range(max_iterations):
        theta_old = theta.copy()

        # Calculate probabilities
        D = 1.7  # Scaling factor
        z = D * a * (theta[:, np.newaxis] - b)
        probs = c + (1 - c) / (1 + np.exp(-z))
        probs = np.clip(probs, 1e-10, 1 - 1e-10)

        # Information matrix and first derivative
        p_c = probs - c[:, np.newaxis].T
        p_c_1 = 1 - probs

        # First derivative of log-likelihood
        residuals = responses - probs
        info = D**2 * np.sum(
            p_c * p_c_1 * a[:, np.newaxis].T ** 2 * (1 - c[:, np.newaxis].T), axis=1
        )
        info = np.maximum(info, 1e-10)  # Avoid division by zero

        score = D * np.sum(p_c * residuals * a[:, np.newaxis].T, axis=1)

        # Update theta
        theta = theta + score / info

        # Check convergence
        if np.max(np.abs(theta - theta_old)) < tolerance:
            break

    return theta


def calculate_item_discrimination(
    responses: Union[List[List[int]], np.ndarray],
) -> np.ndarray:
    """
    Calculate item discrimination parameters using the 2PL model.

    The discrimination parameter (a) indicates how well an item
    distinguishes between high and low ability examinees.

    Args:
        responses: Response matrix (rows=examinees, columns=items)

    Returns:
        Array of discrimination parameters for each item

    Interpretation:
    - a < 0.5: Poor discrimination
    - 0.5 <= a < 1.0: Moderate discrimination
    - 1.0 <= a < 1.5: Good discrimination
    - a >= 1.5: Excellent discrimination
    """
    responses = np.array(responses)
    n_examinees, n_items = responses.shape

    # Get total scores for each examinee
    total_scores = np.sum(responses, axis=1)

    # Calculate point-biserial correlation for each item
    discriminations = np.zeros(n_items)

    for j in range(n_items):
        item_responses = responses[:, j]
        item_std = np.std(item_responses)

        if item_std > 0:
            # Point-biserial correlation
            r = np.corrcoef(item_responses, total_scores)[0, 1]
            # Convert to discrimination parameter (approximation)
            a_j = r * np.sqrt(n_examinees / (1 - r**2 + 1e-10))
            # Bound the discrimination parameter
            discriminations[j] = np.clip(a_j, 0.1, 3.0)
        else:
            discriminations[j] = 0.5  # Default

    return discriminations


def calculate_item_difficulty_irt(
    responses: Union[List[List[int]], np.ndarray],
) -> np.ndarray:
    """
    Calculate item difficulty parameters using IRT.

    The difficulty parameter (b) is the ability level at which
    the probability of a correct response is 0.5 (for 2PL/3PL).

    Args:
        responses: Response matrix (rows=examinees, columns=items)

    Returns:
        Array of difficulty parameters for each item

    Interpretation:
    - b < -1: Very easy item
    - -1 <= b < 0: Easy item
    - 0 <= b < 1: Medium difficulty
    - 1 <= b < 2: Hard item
    - b >= 2: Very hard item
    """
    responses = np.array(responses)
    n_examinees, n_items = responses.shape

    # Calculate proportion correct for each item
    p_values = np.mean(responses, axis=0)

    # Convert p-value to difficulty using inverse logistic
    # b = logit(p) / D, where D = 1.7
    D = 1.7

    # Handle edge cases for p-values
    difficulties = np.zeros(n_items)
    for j, p in enumerate(p_values):
        if p <= 0:
            difficulties[j] = 3.0  # Very hard
        elif p >= 1:
            difficulties[j] = -3.0  # Very easy
        else:
            # Inverse logit: b = log(p/(1-p)) / D
            difficulties[j] = np.log(p / (1 - p)) / D

    return difficulties


def detect_dfit(
    item_responses: Union[List[int], np.ndarray],
    group_membership: Union[List[int], np.ndarray],
    ability: Union[List[float], np.ndarray],
) -> Dict[str, Union[float, str, int, list]]:
    """
    Detect Differential Functioning of Items and Tests (DFIT).

    DFIT is a IRT-based approach that quantifies the difference between
    item characteristic curves (ICCs) for different groups.

    Args:
        item_responses: Binary item responses
        group_membership: Group membership (0=reference, 1=focal)
        ability: Ability estimates for examinees

    Returns:
        Dictionary with:
        - ddf: Differential Distractor Functioning statistic
        - dtf: Differential Test Functioning statistic
        - ddf_pvalue: P-value for DDF
        - dtf_pvalue: P-value for DTF
        - classification: "no_DFIT", "item_DFIT", "test_DFIT"
        - item_impact: List of per-item impact measures

    Example:
        >>> responses = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
        >>> groups = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        >>> ability = [0.5, -0.3, 1.2, 0.8, 0.1, -0.5, 0.2, 0.9, 0.1, 0.6]
        >>> result = detect_dfit(responses, groups, ability)
    """
    from scipy import stats

    # Convert to numpy arrays
    item_responses = np.array(item_responses)
    group_membership = np.array(group_membership)
    ability = np.array(ability)

    # Separate groups
    ref_mask = group_membership == 0
    focal_mask = group_membership == 1

    ref_responses = item_responses[ref_mask]
    focal_responses = item_responses[focal_mask]
    ref_ability = ability[ref_mask]
    focal_ability = ability[focal_mask]

    # Get ability ranges for matching
    ability_range = [
        max(
            ref_ability.min() if len(ref_ability) > 0 else -3,
            focal_ability.min() if len(focal_ability) > 0 else -3,
        ),
        min(
            ref_ability.max() if len(ref_ability) > 0 else 3,
            focal_ability.max() if len(focal_ability) > 0 else 3,
        ),
    ]

    # Create ability bins
    n_bins = 5
    try:
        bin_edges = np.linspace(ability_range[0], ability_range[1], n_bins + 1)
        ref_bins = np.digitize(ref_ability, bin_edges) - 1
        focal_bins = np.digitize(focal_ability, bin_edges) - 1
    except Exception:
        ref_bins = np.zeros(len(ref_ability), dtype=int)
        focal_bins = np.zeros(len(focal_ability), dtype=int)

    # Calculate DDF (Differential Distractor Functioning) for each bin
    ddf_squared_sum = 0.0
    dtf_squared_sum = 0.0
    item_impacts = []
    valid_comparisons = 0

    for i in range(n_bins):
        ref_in_bin = ref_bins == i
        focal_in_bin = focal_bins == i

        n_ref = np.sum(ref_in_bin)
        n_focal = np.sum(focal_in_bin)

        if n_ref < 2 or n_focal < 2:
            continue

        ref_p = np.mean(ref_responses[ref_in_bin])
        focal_p = np.mean(focal_responses[focal_in_bin])

        # DDF: squared difference in proportions weighted by sample
        n_combined = n_ref + n_focal
        ddf_squared_sum += n_combined * (ref_p - focal_p) ** 2
        dtf_squared_sum += n_combined * (ref_p - focal_p) ** 2

        # Item impact for this bin
        item_impacts.append(
            {
                "bin": i,
                "n_reference": int(n_ref),
                "n_focal": int(n_focal),
                "ref_proportion": float(ref_p),
                "focal_proportion": float(focal_p),
                "difference": float(ref_p - focal_p),
            }
        )
        valid_comparisons += 1

    # Calculate statistics
    if valid_comparisons > 0:
        ddf = ddf_squared_sum / valid_comparisons
        dtf = dtf_squared_sum / valid_comparisons
    else:
        ddf = 0.0
        dtf = 0.0

    # P-values (chi-square approximation)
    if ddf > 0:
        ddf_pvalue = 1 - stats.chi2.cdf(ddf, df=1)
    else:
        ddf_pvalue = 1.0

    if dtf > 0:
        dtf_pvalue = 1 - stats.chi2.cdf(dtf, df=1)
    else:
        dtf_pvalue = 1.0

    # Classification
    if ddf_pvalue < 0.05 and dtf_pvalue < 0.05:
        classification = "test_DFIT"
    elif ddf_pvalue < 0.05:
        classification = "item_DFIT"
    else:
        classification = "no_DFIT"

    # Calculate overall impact (standardized)
    # Using effect size (Cohen's h approximation)
    n_total = len(item_responses)
    if n_total > 0:
        ref_mean = np.mean(item_responses[ref_mask])
        focal_mean = np.mean(item_responses[focal_mask])
        impact = abs(ref_mean - focal_mean)
    else:
        impact = 0.0

    return {
        "ddf": float(ddf),
        "dtf": float(dtf),
        "ddf_pvalue": float(ddf_pvalue),
        "dtf_pvalue": float(dtf_pvalue),
        "classification": classification,
        "item_impact": item_impacts,
        "n_reference": int(np.sum(ref_mask)),
        "n_focal": int(np.sum(focal_mask)),
        "overall_impact": float(impact),
    }
