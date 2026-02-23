"""
lti_api.py
==========

FastAPI routes for LTI 1.3 login and launch.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from audit_ledger_service.ledger import AuditLedger
from lti_service.lti_service import LTIService
from lti_service.models import load_lti_config


class LaunchResponse(BaseModel):
    launch_id: str
    user_id: str
    line_item_url: str


class LoginResponse(BaseModel):
    redirect_url: str


class ErrorResponse(BaseModel):
    detail: str


_lti_service: Optional[LTIService] = None


def get_lti_service() -> LTIService:
    global _lti_service
    if _lti_service is None:
        platform_config, tool_config = load_lti_config()
        audit_ledger = AuditLedger()
        _lti_service = LTIService(platform_config, tool_config, audit_ledger)
    return _lti_service


def set_lti_service(service: LTIService) -> None:
    global _lti_service
    _lti_service = service


router = APIRouter(prefix="/lti", tags=["lti"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={400: {"model": ErrorResponse}},
)
async def lti_login(request: Request) -> LoginResponse:
    """Start LTI OIDC login flow."""
    params = await _extract_form_params(request)
    try:
        redirect_url = get_lti_service().start_login(params)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return LoginResponse(redirect_url=redirect_url)


@router.post(
    "/launch",
    response_model=LaunchResponse,
    responses={400: {"model": ErrorResponse}},
)
async def lti_launch(request: Request) -> LaunchResponse:
    """Validate LTI launch and return launch context info."""
    params = await _extract_form_params(request)
    try:
        context = get_lti_service().validate_launch(params)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return LaunchResponse(
        launch_id=context.launch_id,
        user_id=context.user_id,
        line_item_url=context.line_item_url,
    )


async def _extract_form_params(request: Request) -> Dict[str, Any]:
    form = await request.form()
    return {key: value for key, value in form.items()}
