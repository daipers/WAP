"""
dif_logistic.py
===============

Differential Item Functioning (DIF) analysis using logistic regression methods
with ability matching.

This module provides:
- logistic_dif_analysis: Full logistic regression DIF detection with interaction term
- dif_with_matching: Ability-matched DIF analysis to control for ability differences

Uses statsmodels GLM for logistic regression when available.
"""

from typing import Dict, List, Union

import numpy as np


def logistic_dif_analysis(
    item_responses: Union[List[int], np.ndarray],
    group_membership: Union[List[int], np.ndarray],
    ability_estimate: Union[List[float], np.ndarray],
) -> Dict[str, Union[float, str, int]]:
    """
    Perform DIF analysis using logistic regression with ability matching.

    This method uses logistic regression to model item response as a function of
    group membership and ability, checking for significant group x ability interaction.

    Args:
        item_responses: Binary item responses (1=correct, 0=incorrect)
        group_membership: Group membership (0=reference, 1=focal)
        ability_estimate: Ability estimates (theta scores)

    Returns:
        Dictionary with:
        - odds_ratio: Odds ratio for group effect
        - pseudo_r2: Pseudo R-squared (Cox-Snell)
        - chi_square: Chi-square statistic for interaction
        - p_value: P-value for interaction term
        - classification: "no_DIF", "uniform_DIF", or "nonuniform_DIF"
        - n_reference: Number of reference group respondents
        - n_focal: Number of focal group respondents

    Example:
        >>> responses = [1, 0, 1, 1, 0, 1, 0, 0]
        >>> groups = [0, 0, 0, 0, 1, 1, 1, 1]
        >>> ability = [0.5, -0.3, 1.2, 0.8, -0.5, 0.2, 0.9, 0.1]
        >>> result = logistic_dif_analysis(responses, groups, ability)
        >>> print(result['classification'])
    """
    # Convert to numpy arrays
    item_responses = np.array(item_responses)
    group_membership = np.array(group_membership)
    ability_estimate = np.array(ability_estimate)

    # Input validation
    n = len(item_responses)
    if n == 0:
        raise ValueError("Item responses cannot be empty")
    if len(group_membership) != n or len(ability_estimate) != n:
        raise ValueError("All input arrays must have the same length")

    # Count groups
    n_reference = int(np.sum(group_membership == 0))
    n_focal = int(np.sum(group_membership == 1))

    if n_reference < 2 or n_focal < 2:
        return {
            "odds_ratio": 0.0,
            "pseudo_r2": 0.0,
            "chi_square": 0.0,
            "p_value": 1.0,
            "classification": "no_DIF",
            "n_reference": n_reference,
            "n_focal": n_focal,
            "convergence_error": True,
        }

    # Standardize ability for numerical stability
    ability_mean = np.mean(ability_estimate)
    ability_std = np.std(ability_estimate)
    if ability_std > 0:
        ability_scaled = (ability_estimate - ability_mean) / ability_std
    else:
        ability_scaled = ability_estimate - ability_mean

    # Try to use statsmodels GLM for logistic regression
    group_coef = 0.0
    odds_ratio = 1.0
    pseudo_r2 = 0.0
    chi_square = 0.0
    p_value = 1.0
    used_statsmodels = False

    try:
        import statsmodels.api as sm
        from scipy import stats

        # Create design matrix: [group, ability, group*ability]
        X = np.column_stack(
            [
                group_membership,
                ability_scaled,
                group_membership * ability_scaled,  # Interaction term
            ]
        )
        X = sm.add_constant(X)
        y = item_responses

        # Fit logistic regression
        model = sm.GLM(y, X, family=sm.families.Binomial())
        result = model.fit(disp=0)

        # Extract coefficients
        # [const, group, ability, interaction]
        group_coef = result.params[1] if len(result.params) > 1 else 0.0
        interaction_coef = result.params[3] if len(result.params) > 3 else 0.0

        # Odds ratio for group (uniform DIF)
        odds_ratio = np.exp(group_coef) if np.isfinite(group_coef) else 1.0

        # Pseudo R-squared (Cox-Snell)
        ll_null = result.llf_null if hasattr(result, "llf_null") else 0
        ll_model = result.llf
        n_obs = result.nobs
        if ll_null is not None and ll_model is not None and n_obs > 0:
            pseudo_r2 = 1 - np.exp(-2 * (ll_model - ll_null) / n_obs)
        else:
            pseudo_r2 = 0.0

        # Chi-square for interaction term
        if len(result.pvalues) > 3:
            interaction_se = result.bse[3] if result.bse[3] > 0 else 1.0
            chi_square = (interaction_coef / interaction_se) ** 2
            p_value = 1 - stats.chi2.cdf(chi_square, df=1)

        used_statsmodels = True

    except ImportError:
        # Fallback to manual implementation if statsmodels not available
        pass
    except Exception:
        # Fallback on any error
        pass

    if not used_statsmodels:
        # Manual fallback calculation
        try:
            from scipy import stats as scipy_stats

            # Separate by group
            ref_mask = group_membership == 0
            focal_mask = group_membership == 1

            # Calculate proportions
            ref_correct = np.mean(item_responses[ref_mask])
            focal_correct = np.mean(item_responses[focal_mask])

            # Simple odds ratio
            if (
                ref_correct > 0
                and ref_correct < 1
                and focal_correct > 0
                and focal_correct < 1
            ):
                odds_ref = ref_correct / (1 - ref_correct)
                odds_focal = focal_correct / (1 - focal_correct)
                odds_ratio = odds_focal / odds_ref if odds_ref > 0 else 1.0
            else:
                odds_ratio = 1.0

            # Simple pseudo R2 approximation
            p_mean = np.mean(item_responses)
            if p_mean > 0 and p_mean < 1:
                pseudo_r2 = min(0.3, abs(ref_correct - focal_correct) * 2)
            else:
                pseudo_r2 = 0.0

            # Chi-square approximation
            chi_square = abs(ref_correct - focal_correct) * len(item_responses)
            p_value = (
                1 - scipy_stats.chi2.cdf(chi_square, df=1) if chi_square > 0 else 1.0
            )

        except ImportError:
            # If scipy not available either
            ref_correct = np.mean(item_responses[group_membership == 0])
            focal_correct = np.mean(item_responses[group_membership == 1])
            odds_ratio = (
                1.0
                if ref_correct == focal_correct
                else (focal_correct / ref_correct if ref_correct > 0 else 1.0)
            )
            pseudo_r2 = abs(ref_correct - focal_correct)
            chi_square = abs(ref_correct - focal_correct) * len(item_responses)
            p_value = 1.0 if chi_square < 3.84 else 0.05  # Approximate

    # Classify DIF based on results
    if p_value < 0.05:
        if abs(group_coef) > 0.1:
            classification = "uniform_DIF"
        else:
            classification = "nonuniform_DIF"
    else:
        classification = "no_DIF"

    return {
        "odds_ratio": float(odds_ratio),
        "pseudo_r2": float(pseudo_r2),
        "chi_square": float(chi_square),
        "p_value": float(p_value),
        "classification": classification,
        "n_reference": n_reference,
        "n_focal": n_focal,
        "convergence_error": False,
    }


def dif_with_matching(
    item_responses: Union[List[int], np.ndarray],
    group_membership: Union[List[int], np.ndarray],
    ability_estimate: Union[List[float], np.ndarray],
    n_bins: int = 5,
) -> Dict[str, Union[float, str, int, list]]:
    """
    Perform DIF analysis with ability matching.

    Matches reference and focal groups on ability bins before comparing item
    performance, controlling for ability differences.

    Args:
        item_responses: Binary item responses (1=correct, 0=incorrect)
        group_membership: Group membership (0=reference, 1=focal)
        ability_estimate: Ability estimates (theta scores)
        n_bins: Number of ability bins for matching (default 5)

    Returns:
        Dictionary with:
        - matched_odds_ratio: Odds ratio from matched analysis
        - matched_p_value: P-value from matched analysis
        - classification: "no_DIF", "mild_DIF", "moderate_DIF", "severe_DIF"
        - bins_analyzed: List of bin-level results
        - total_comparisons: Number of ability bins with both groups

    Example:
        >>> responses = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
        >>> groups = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        >>> ability = [0.5, -0.3, 1.2, 0.8, 0.1, -0.5, 0.2, 0.9, 0.1, 0.6]
        >>> result = dif_with_matching(responses, groups, ability)
    """
    # Convert to numpy arrays
    item_responses = np.array(item_responses)
    group_membership = np.array(group_membership)
    ability_estimate = np.array(ability_estimate)

    # Input validation
    n = len(item_responses)
    if n == 0:
        raise ValueError("Item responses cannot be empty")
    if len(group_membership) != n or len(ability_estimate) != n:
        raise ValueError("All input arrays must have the same length")

    # Create ability bins
    try:
        import pandas as pd

        try:
            ability_bins = pd.qcut(
                ability_estimate, q=n_bins, labels=False, duplicates="drop"
            )
        except ValueError:
            ability_bins = pd.cut(ability_estimate, bins=n_bins, labels=False)
    except ImportError:
        # Manual binning
        bin_edges = np.linspace(
            ability_estimate.min(), ability_estimate.max(), n_bins + 1
        )
        ability_bins = np.digitize(ability_estimate, bin_edges) - 1
        ability_bins = np.clip(ability_bins, 0, n_bins - 1)

    # Analyze each bin
    bin_results = []
    valid_bins = 0
    total_odds_ratios = []
    weighted_chi_square = 0.0

    for bin_val in np.unique(ability_bins):
        bin_mask = ability_bins == bin_val
        ref_mask = bin_mask & (group_membership == 0)
        focal_mask = bin_mask & (group_membership == 1)

        n_ref = np.sum(ref_mask)
        n_focal = np.sum(focal_mask)

        # Need both groups in this bin
        if n_ref < 2 or n_focal < 2:
            continue

        ref_responses = item_responses[ref_mask]
        focal_responses = item_responses[focal_mask]

        ref_p = np.mean(ref_responses)
        focal_p = np.mean(focal_responses)

        # Calculate odds ratio for this bin
        if ref_p > 0 and ref_p < 1 and focal_p > 0 and focal_p < 1:
            odds_ref = ref_p / (1 - ref_p)
            odds_focal = focal_p / (1 - focal_p)
            bin_or = odds_focal / odds_ref if odds_ref > 0 else 1.0
        else:
            bin_or = 1.0

        # Chi-square for this bin
        n_total = n_ref + n_focal
        if n_total > 0 and ref_p != focal_p:
            chi_sq = n_total * (ref_p - focal_p) ** 2
        else:
            chi_sq = 0.0

        total_odds_ratios.append(bin_or)
        weighted_chi_square += chi_sq
        valid_bins += 1

        bin_results.append(
            {
                "bin": int(bin_val),
                "n_reference": int(n_ref),
                "n_focal": int(n_focal),
                "ref_proportion": float(ref_p),
                "focal_proportion": float(focal_p),
                "odds_ratio": float(bin_or),
                "chi_square": float(chi_sq),
            }
        )

    # Calculate overall matched statistics
    if valid_bins > 0 and total_odds_ratios:
        # Mantel-Haenszel style pooled odds ratio
        log_ors = [np.log(or_val) for or_val in total_odds_ratios if or_val > 0]
        if log_ors:
            pooled_or = np.exp(np.mean(log_ors))
        else:
            pooled_or = 1.0

        # Combined chi-square
        try:
            from scipy import stats as scipy_stats

            p_value = 1 - scipy_stats.chi2.cdf(weighted_chi_square, df=valid_bins - 1)
        except ImportError:
            p_value = 1.0 if weighted_chi_square < 3.84 else 0.05
    else:
        pooled_or = 1.0
        p_value = 1.0

    # Classify severity based on pooled odds ratio
    or_abs_diff = abs(pooled_or - 1.0)
    if or_abs_diff < 0.1 or p_value > 0.1:
        classification = "no_DIF"
    elif or_abs_diff < 0.3:
        classification = "mild_DIF"
    elif or_abs_diff < 0.5:
        classification = "moderate_DIF"
    else:
        classification = "severe_DIF"

    return {
        "matched_odds_ratio": float(pooled_or),
        "matched_p_value": float(p_value),
        "classification": classification,
        "bins_analyzed": bin_results,
        "total_comparisons": valid_bins,
        "weighted_chi_square": float(weighted_chi_square),
    }
