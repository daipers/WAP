"""
dashboard.py
============

Analytics dashboard API endpoints for item performance and fairness reports.

Provides endpoints:
- GET /api/analytics/item-performance?assessment_id=xxx
- GET /api/analytics/fairness-report?assessment_id=xxx&group_attribute=gender
- GET /api/analytics/export?assessment_id=xxx&format=csv

Uses existing database patterns from Phase 1-3.
"""

import csv
import io
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .metrics import (
    calculate_item_difficulty,
    calculate_discrimination_index,
    calculate_cronbach_alpha,
    calculate_item_stats,
)
from .dif_detector import (
    detect_dif_chi_square,
    detect_dif_logistic,
    get_dif_summary,
)


# ============================================================================
# Request/Response Models
# ============================================================================


class ItemPerformanceResponse(BaseModel):
    """Response model for item performance data."""

    assessment_id: str
    items: List[Dict[str, Any]]
    summary: Dict[str, float]


class FairnessReportResponse(BaseModel):
    """Response model for fairness/DIF report."""

    assessment_id: str
    group_attribute: str
    dif_results: Dict[str, Any]
    summary: Dict[str, Any]


class ExportResponse(BaseModel):
    """Response for data export."""

    assessment_id: str
    format: str
    data: str  # Base64 encoded or CSV string


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str


# ============================================================================
# Mock Data Store (would be replaced with database in production)
# ============================================================================

# In-memory storage for demo purposes
# In production, this would query the actual database
_mock_item_responses: Dict[str, Dict[str, List[int]]] = {}
_mock_group_membership: Dict[str, Dict[str, str]] = {}
_mock_total_scores: Dict[str, Dict[str, float]] = {}


def _initialize_mock_data(assessment_id: str) -> None:
    """Initialize mock data for demo purposes."""
    if assessment_id in _mock_item_responses:
        return  # Already initialized

    # Create mock data for demonstration
    import random

    random.seed(42)

    n_respondents = 100
    n_items = 20

    # Generate group membership (gender: M/F)
    groups = {}
    for i in range(n_respondents):
        respondent_id = f"resp_{i}"
        groups[respondent_id] = "M" if i < 50 else "F"

    _mock_group_membership[assessment_id] = groups

    # Generate item responses
    items = {}
    total_scores = {}

    for i in range(n_respondents):
        respondent_id = f"resp_{i}"

        # Base ability (slightly different by group for demonstration)
        base_ability = random.gauss(0.5, 0.2)
        group = groups[respondent_id]
        if group == "F":
            base_ability += 0.05  # Slight advantage for demo

        total_score = 0

        for j in range(n_items):
            item_id = f"item_{j}"

            # Item difficulty varies
            item_difficulty = 0.3 + (j / n_items) * 0.5  # 0.3 to 0.8

            # Probability of correct response
            prob = min(1.0, max(0.0, base_ability - item_difficulty + 0.5))

            # Add slight DIF for some items
            if j == 3 and group == "F":  # Item 3 has slight DIF
                prob = min(1.0, prob + 0.15)

            response = 1 if random.random() < prob else 0
            total_score += response

            if item_id not in items:
                items[item_id] = []
            items[item_id].append(response)

        total_scores[respondent_id] = total_score

    _mock_item_responses[assessment_id] = items
    _mock_total_scores[assessment_id] = total_scores


# ============================================================================
# Dependencies
# ============================================================================


def get_assessment_data(assessment_id: str) -> Dict[str, Any]:
    """
    Get assessment data from storage.

    In production, this would query the database.
    """
    _initialize_mock_data(assessment_id)

    return {
        "item_responses": _mock_item_responses.get(assessment_id, {}),
        "group_membership": _mock_group_membership.get(assessment_id, {}),
        "total_scores": _mock_total_scores.get(assessment_id, {}),
    }


# ============================================================================
# API Router
# ============================================================================

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ============================================================================
# Routes
# ============================================================================


@router.get(
    "/item-performance",
    response_model=ItemPerformanceResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_item_performance(
    assessment_id: str = Query(..., description="Assessment identifier"),
) -> ItemPerformanceResponse:
    """
    Get item performance metrics for an assessment.

    Returns difficulty, discrimination index, and response counts
    for each item in the assessment.
    """
    # Get assessment data
    data = get_assessment_data(assessment_id)
    item_responses = data["item_responses"]
    total_scores = data["total_scores"]

    if not item_responses:
        raise HTTPException(
            status_code=404, detail=f"Assessment {assessment_id} not found"
        )

    # Calculate metrics for each item
    items_data = []
    difficulties = []
    discriminations = []

    # Convert total_scores to list in same order as item_responses
    respondent_ids = list(total_scores.keys())
    scores_list = [total_scores[rid] for rid in respondent_ids]

    for item_id, responses in item_responses.items():
        # Calculate difficulty
        difficulty = calculate_item_difficulty(responses)

        # Calculate discrimination
        discrimination = calculate_discrimination_index(responses, scores_list)

        items_data.append(
            {
                "item_id": item_id,
                "difficulty": round(difficulty, 4),
                "discrimination": round(discrimination, 4),
                "response_count": len(responses),
            }
        )

        difficulties.append(difficulty)
        discriminations.append(discrimination)

    # Sort by item_id
    items_data.sort(key=lambda x: x["item_id"])

    # Calculate summary statistics
    avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 0
    avg_discrimination = (
        sum(discriminations) / len(discriminations) if discriminations else 0
    )

    # Calculate Cronbach's alpha if we have enough items
    alpha = 0.0
    if len(item_responses) >= 2:
        # Build item matrix (respondents x items)
        item_matrix = []
        for rid in respondent_ids:
            row = [
                item_responses[item_id][i]
                for i, item_id in enumerate(item_responses.keys())
            ]
            item_matrix.append(row)
        alpha = calculate_cronbach_alpha(item_matrix)

    summary = {
        "average_difficulty": round(avg_difficulty, 4),
        "average_discrimination": round(avg_discrimination, 4),
        "cronbach_alpha": round(alpha, 4),
        "total_items": len(item_responses),
        "total_respondents": len(total_scores),
    }

    return ItemPerformanceResponse(
        assessment_id=assessment_id, items=items_data, summary=summary
    )


@router.get(
    "/fairness-report",
    response_model=FairnessReportResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_fairness_report(
    assessment_id: str = Query(..., description="Assessment identifier"),
    group_attribute: str = Query(
        "gender",
        description="Group attribute to analyze (gender, ethnicity, disability_status)",
    ),
    method: str = Query(
        "chi_square", description="DIF detection method: chi_square or logistic"
    ),
) -> FairnessReportResponse:
    """
    Get fairness report with DIF analysis for an assessment.

    Analyzes items for differential functioning between groups
    (e.g., gender, ethnicity, disability status).
    """
    # Get assessment data
    data = get_assessment_data(assessment_id)
    item_responses = data["item_responses"]
    group_membership = data["group_membership"]
    total_scores = data["total_scores"]

    if not item_responses:
        raise HTTPException(
            status_code=404, detail=f"Assessment {assessment_id} not found"
        )

    # Convert group membership to reference/focal format
    # For gender: M = reference, F = focal
    # For other attributes, use first unique value as reference
    unique_groups = set(group_membership.values())
    if len(unique_groups) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Group attribute {group_attribute} has only one value",
        )

    unique_groups_list = list(unique_groups)
    reference_group = unique_groups_list[0]
    focal_group = unique_groups_list[1]

    # Convert to reference/focal format
    group_membership_rf = {
        rid: ("reference" if g == reference_group else "focal")
        for rid, g in group_membership.items()
    }

    # Run DIF detection
    if method == "logistic":
        dif_results = detect_dif_logistic(
            item_responses=item_responses,
            group_membership=group_membership_rf,
            ability_estimate=total_scores,
            reference_group="reference",
            focal_group="focal",
        )
    else:
        dif_results = detect_dif_chi_square(
            item_responses=item_responses,
            group_membership=group_membership_rf,
            ability_estimate=total_scores,
            reference_group="reference",
            focal_group="focal",
        )

    # Generate summary
    summary = get_dif_summary(dif_results, group_attribute)

    return FairnessReportResponse(
        assessment_id=assessment_id,
        group_attribute=group_attribute,
        dif_results=dif_results,
        summary=summary,
    )


@router.get(
    "/export",
    responses={
        200: {"content": {"text/csv": {}}},
        404: {"model": ErrorResponse},
    },
)
async def export_analytics(
    assessment_id: str = Query(..., description="Assessment identifier"),
    format: str = Query("csv", description="Export format: csv"),
) -> Dict[str, Any]:
    """
    Export item performance data.

    Exports psychometric metrics and DIF results to CSV format.
    """
    # Get item performance data
    perf_response = await get_item_performance(assessment_id)

    if format.lower() == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["item_id", "difficulty", "discrimination", "response_count"])

        # Data rows
        for item in perf_response.items:
            writer.writerow(
                [
                    item["item_id"],
                    item["difficulty"],
                    item["discrimination"],
                    item["response_count"],
                ]
            )

        csv_data = output.getvalue()

        return {
            "assessment_id": assessment_id,
            "format": "csv",
            "data": csv_data,
            "summary": perf_response.summary,
        }
    else:
        raise HTTPException(
            status_code=400, detail=f"Format {format} not supported. Use 'csv'."
        )


@router.get("/health")
async def analytics_health() -> Dict[str, str]:
    """Health check endpoint for analytics service."""
    return {"status": "healthy", "service": "analytics"}
