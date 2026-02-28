"""
metrics.py
==========

Psychometric analysis functions for item performance metrics.

Provides:
- Item difficulty (p-value)
- Discrimination index (point-biserial correlation)
- Cronbach's alpha (internal consistency)
- Confidence intervals (Wilson score)

Uses pandas for data manipulation and scipy.stats for calculations.
"""

from typing import Dict, List, Optional, Tuple, Union
import math

import numpy as np


def calculate_item_difficulty(
    responses: Union[List[int], List[bool], np.ndarray],
) -> float:
    """
    Calculate item difficulty as the proportion of correct responses (p-value).

    The p-value ranges from 0 to 1, where:
    - Higher values indicate easier items (more correct responses)
    - Lower values indicate harder items (fewer correct responses)

    Args:
        responses: List of binary responses (1=correct, 0=incorrect) or
                  boolean (True=correct, False=incorrect)

    Returns:
        float: The p-value (proportion of correct responses)

    Raises:
        ValueError: If responses list is empty

    Example:
        >>> calculate_item_difficulty([1, 1, 0, 1, 0, 1, 1, 0])
        0.625
    """
    if len(responses) == 0:
        raise ValueError("Response list cannot be empty")

    # Convert boolean to int if needed
    if responses and isinstance(responses[0], bool):
        responses = [int(r) for r in responses]

    responses = np.array(responses)
    return float(np.mean(responses))


def calculate_discrimination_index(
    item_responses: Union[List[int], np.ndarray],
    total_scores: Union[List[float], np.ndarray],
) -> float:
    """
    Calculate discrimination index using point-biserial correlation.

    The discrimination index ranges from -1 to 1:
    - Positive values indicate the item discriminates well (high scorers get it right)
    - Negative values indicate the item is negatively discriminating
    - Values near 0 indicate poor discrimination

    Args:
        item_responses: Binary item responses (1=correct, 0=incorrect)
        total_scores: Total test scores for each respondent

    Returns:
        float: Point-biserial correlation coefficient

    Raises:
        ValueError: If input lists are empty or have different lengths
    """
    if len(item_responses) == 0 or len(total_scores) == 0:
        raise ValueError("Input lists cannot be empty")

    if len(item_responses) != len(total_scores):
        raise ValueError("Item responses and total scores must have same length")

    item_responses = np.array(item_responses, dtype=float)
    total_scores = np.array(total_scores, dtype=float)

    # Handle edge case: all responses are the same
    if np.std(item_responses) == 0 or np.std(total_scores) == 0:
        return 0.0

    # Calculate point-biserial correlation
    correlation = np.corrcoef(item_responses, total_scores)[0, 1]

    return float(correlation)


def calculate_cronbach_alpha(item_matrix: Union[List[List[int]], np.ndarray]) -> float:
    """
    Calculate Cronbach's alpha for internal consistency reliability.

    Cronbach's alpha ranges from 0 to 1:
    - >= 0.9: Excellent reliability
    - >= 0.8: Good reliability
    - >= 0.7: Acceptable reliability
    - >= 0.6: Questionable reliability
    - >= 0.5: Poor reliability
    - < 0.5: Unacceptable reliability

    Args:
        item_matrix: Matrix of item responses (rows=respondents, columns=items)
                    Each cell should be 0 or 1

    Returns:
        float: Cronbach's alpha coefficient

    Raises:
        ValueError: If item matrix is empty or has insufficient items

    Example:
        >>> # 5 respondents, 4 items
        >>> matrix = [
        ...     [1, 1, 1, 0],
        ...     [1, 1, 0, 0],
        ...     [0, 0, 1, 1],
        ...     [1, 0, 0, 0],
        ...     [0, 1, 1, 1]
        ... ]
        >>> calculate_cronbach_alpha(matrix)
        0.55...
    """
    item_matrix = np.array(item_matrix)

    if item_matrix.size == 0:
        raise ValueError("Item matrix cannot be empty")

    n_items = item_matrix.shape[1]
    if n_items < 2:
        raise ValueError("Need at least 2 items to calculate Cronbach's alpha")

    n_respondents = item_matrix.shape[0]

    # Calculate variance for each item
    item_variances = np.var(item_matrix, axis=0, ddof=1)

    # Calculate variance of total scores
    total_scores = np.sum(item_matrix, axis=1)
    total_variance = np.var(total_scores, ddof=1)

    # Calculate Cronbach's alpha
    sum_item_variances = np.sum(item_variances)

    if total_variance == 0:
        return 0.0

    alpha = (n_items / (n_items - 1)) * (1 - (sum_item_variances / total_variance))

    return float(alpha)


def calculate_confidence_interval(
    responses: Union[List[int], List[bool], np.ndarray], confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for item difficulty.

    The Wilson score interval is more accurate than the normal approximation
    especially for proportions near 0 or 1.

    Args:
        responses: List of binary responses (1=correct, 0=incorrect)
        confidence: Confidence level (default 0.95 for 95% CI)

    Returns:
        Tuple of (lower_bound, upper_bound)

    Raises:
        ValueError: If responses list is empty or confidence is invalid

    Example:
        >>> calculate_confidence_interval([1, 1, 0, 1, 0, 1, 1, 0], 0.95)
        (0.307..., 0.843...)
    """
    if len(responses) == 0:
        raise ValueError("Response list cannot be empty")

    if not (0 < confidence < 1):
        raise ValueError("Confidence must be between 0 and 1")

    # Convert boolean to int if needed
    if responses and isinstance(responses[0], bool):
        responses = [int(r) for r in responses]

    responses = np.array(responses)
    n = len(responses)
    p = np.mean(responses)

    # Wilson score formula
    z = (
        1.96 if confidence == 0.95 else 1.645
    )  # Approximate z for common confidence levels
    if confidence != 0.95:
        # Calculate z for arbitrary confidence level
        from scipy import stats

        z = stats.norm.ppf(1 - (1 - confidence) / 2)

    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator

    lower = max(0, center - margin)
    upper = min(1, center + margin)

    return (float(lower), float(upper))


def calculate_item_stats(
    item_responses: Union[List[int], np.ndarray],
    total_scores: Union[List[float], np.ndarray],
) -> Dict[str, float]:
    """
    Calculate comprehensive statistics for a single item.

    Args:
        item_responses: Binary item responses
        total_scores: Total test scores for each respondent

    Returns:
        Dictionary with difficulty, discrimination, and response count
    """
    difficulty = calculate_item_difficulty(item_responses)
    discrimination = calculate_discrimination_index(item_responses, total_scores)
    response_count = len(item_responses)

    return {
        "difficulty": difficulty,
        "discrimination": discrimination,
        "response_count": response_count,
    }
