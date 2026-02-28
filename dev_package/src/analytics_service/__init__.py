"""
analytics_service
==================

Analytics service for psychometric analysis and DIF detection.

Modules:
- metrics: Psychometric calculations (difficulty, discrimination, Cronbach's alpha)
- dif_detector: DIF detection using Mantel-Haenszel chi-square and logistic regression
- dashboard: Analytics dashboard API endpoints
"""

from .metrics import (
    calculate_item_difficulty,
    calculate_discrimination_index,
    calculate_cronbach_alpha,
    calculate_confidence_interval,
    calculate_item_stats,
)


def get_dif_detector():
    """Lazy import for DIF detector module."""
    from .dif_detector import detect_dif_chi_square, detect_dif_logistic

    return detect_dif_chi_square, detect_dif_logistic


def get_dashboard():
    """Lazy import for dashboard module."""
    from .dashboard import router

    return router


__all__ = [
    # Metrics
    "calculate_item_difficulty",
    "calculate_discrimination_index",
    "calculate_cronbach_alpha",
    "calculate_confidence_interval",
    "calculate_item_stats",
    # Lazy imports
    "get_dif_detector",
    "get_dashboard",
]
