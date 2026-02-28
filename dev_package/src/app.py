"""
app.py
======

FastAPI application entrypoint for WAA-ADS services.
"""

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from delivery_service.delivery_api import router as delivery_router
from lti_service.lti_api import router as lti_router
from analytics_service.dashboard import router as analytics_router


app = FastAPI(title="WAA-ADS API")

# Include routers
app.include_router(delivery_router)
app.include_router(lti_router)
app.include_router(analytics_router)

# Setup templates
templates = Jinja2Templates(directory="dev_package/templates")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to analytics dashboard."""
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WAA-ADS</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                ul { list-style-type: none; padding: 0; }
                li { margin: 10px 0; }
                a { color: #667eea; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>WAA-ADS API</h1>
            <p>Welcome to the WAA-ADS (Web Assessment Delivery System) API.</p>
            <h2>Available Services:</h2>
            <ul>
                <li><a href="/analytics">Analytics Dashboard</a> - Item performance and fairness analysis</li>
                <li>/delivery/* - Assessment delivery endpoints</li>
                <li>/lti/* - LTI 1.3 integration</li>
                <li>/api/analytics/* - Analytics API endpoints</li>
            </ul>
        </body>
        </html>
        """
    )


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_dashboard():
    """Serve the analytics dashboard HTML."""
    dashboard_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "templates", "analytics_dashboard.html"
    )

    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)
