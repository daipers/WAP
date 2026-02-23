"""
app.py
======

FastAPI application entrypoint for WAA-ADS services.
"""

from fastapi import FastAPI

from delivery_service.delivery_api import router as delivery_router
from lti_service.lti_api import router as lti_router


app = FastAPI(title="WAA-ADS API")

app.include_router(delivery_router)
app.include_router(lti_router)
