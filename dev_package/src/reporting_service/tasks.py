"""
tasks.py
========

Celery task definitions for reporting workflows.
"""

from typing import Any, Dict

from workers.celery_app import celery_app
from reporting_service.reporting import ReportingService
from reporting_service.csv_export import export_scorecard_csv
from scoring_engine.score_runs import ScoreRun, ResponseSnapshot


@celery_app.task
def generate_scorecard_task(
    candidate_id: str,
    score_run_payload: Dict[str, Any],
    response_snapshot_payload: Dict[str, Any],
    rubric: Dict[str, Any],
) -> Dict[str, Any]:
    score_run = ScoreRun(**score_run_payload)
    response_snapshot = ResponseSnapshot(**response_snapshot_payload)
    reporting_service = ReportingService(rubric)
    return reporting_service.generate_scorecard(
        candidate_id, score_run, response_snapshot
    )


@celery_app.task
def export_scorecard_csv_task(scorecard: Dict[str, Any], output_path: str) -> str:
    return export_scorecard_csv(scorecard, output_path)
