"""
fairness_service
================

Advanced fairness analysis services for DIF detection using logistic regression
and IRT-based methods.

Modules:
- dif_logistic: Logistic regression DIF analysis with ability matching
- irt_analysis: IRT-based analysis and ability estimation
- fairness_reports: Fairness assessment report generation

This service provides advanced fairness analysis beyond basic chi-square methods.
"""

from dev_package.src.fairness_service.dif_logistic import (
    dif_with_matching,
    logistic_dif_analysis,
)
from dev_package.src.fairness_service.irt_analysis import (
    detect_dfit,
    estimate_ability_3pl,
)
from dev_package.src.fairness_service.fairness_reports import (
    generate_fairness_report,
    get_fairness_impact_score,
)

__all__ = [
    # DIF Logistic
    "logistic_dif_analysis",
    "dif_with_matching",
    # IRT Analysis
    "estimate_ability_3pl",
    "detect_dfit",
    # Fairness Reports
    "generate_fairness_report",
    "get_fairness_impact_score",
]
