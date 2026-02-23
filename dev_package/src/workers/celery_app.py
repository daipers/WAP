"""
celery_app.py
=============

Shared Celery application configuration for background workers.
"""

import os

from celery import Celery


broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)

celery_app = Celery(
    "waa_ads",
    broker=broker_url,
    backend=result_backend,
)

celery_app.autodiscover_tasks(["scoring_engine", "reporting_service"])
