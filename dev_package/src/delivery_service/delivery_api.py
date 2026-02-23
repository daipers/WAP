"""
delivery_api.py
===============

FastAPI routes for assessment delivery.
Provides endpoints for starting, navigating, answering, saving, and submitting assessments.

Endpoints:
- POST /delivery/start/{assessment_id} - Creates session, returns first item
- GET /delivery/session/{session_id}/current - Returns current item and timer
- POST /delivery/session/{session_id}/answer - Records answer for current item
- POST /delivery/session/{session_id}/navigate - Move to next/previous/specific item
- POST /delivery/session/{session_id}/save - Explicit save progress
- POST /delivery/session/{session_id}/submit - Complete assessment
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .models import AssessmentDefinition
from .session_manager import (
    AssessmentSession,
    SessionManager,
    SessionState,
    InvalidStateTransitionError,
)
from .test_assembly import TestAssemblyService
from content_bank_service.content_bank import ContentBankService


# ============================================================================
# Request/Response Models
# ============================================================================


class StartAssessmentRequest(BaseModel):
    """Request to start an assessment."""

    candidate_id: str
    test_taker_id: str


class AnswerSubmission(BaseModel):
    """Submission of an answer for an item."""

    item_id: str
    response: Dict[str, Any]
    is_flagged: bool = False


class NavigationRequest(BaseModel):
    """Request to navigate to a different item."""

    direction: str = Field(..., description="next, previous, or specific")
    target_index: Optional[int] = Field(
        None, description="Required if direction is specific"
    )


class SaveProgressResponse(BaseModel):
    """Response after saving progress."""

    session_id: str
    saved_at: datetime
    current_item_index: int
    time_remaining_seconds: Optional[int]
    responses_count: int


class CurrentItemResponse(BaseModel):
    """Response containing current item and session state."""

    session_id: str
    current_item_index: int
    total_items: int
    item: Optional[Dict[str, Any]]
    time_remaining_seconds: Optional[int]
    is_flagged: bool
    state: str
    navigation_mode: str
    can_go_previous: bool
    can_go_next: bool


class StartAssessmentResponse(BaseModel):
    """Response after starting an assessment."""

    session_id: str
    assessment_id: str
    title: str
    current_item_index: int
    total_items: int
    item: Optional[Dict[str, Any]]
    time_limit_seconds: Optional[int]
    time_remaining_seconds: Optional[int]
    state: str
    navigation_mode: str


class AnswerResponse(BaseModel):
    """Response after submitting an answer."""

    session_id: str
    item_id: str
    saved: bool
    current_item_index: int


class NavigateResponse(BaseModel):
    """Response after navigating."""

    session_id: str
    current_item_index: int
    total_items: int
    item: Optional[Dict[str, Any]]
    state: str
    can_go_previous: bool
    can_go_next: bool


class SubmitResponse(BaseModel):
    """Response after submitting assessment."""

    session_id: str
    state: str
    completed_at: datetime
    total_items: int
    responses_count: int


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str


# ============================================================================
# Dependencies
# ============================================================================


# Global instances (would be injected via dependency injection in production)
_session_manager: Optional[SessionManager] = None
_test_assembly_service: Optional[TestAssemblyService] = None
_content_bank: Optional[ContentBankService] = None
_assessment_definitions: Dict[str, AssessmentDefinition] = {}

# Default paths for development
DEFAULT_BANK_PATH = "dev_package/data/item_bank.json"
DEFAULT_INJECTIONS_PATH = "dev_package/data/injections.json"


def get_session_manager() -> SessionManager:
    """Get the session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def get_test_assembly_service() -> TestAssemblyService:
    """Get the test assembly service instance."""
    global _test_assembly_service, _content_bank
    if _test_assembly_service is None:
        if _content_bank is None:
            # Try to load with default paths, fail gracefully if not found
            try:
                _content_bank = ContentBankService(
                    DEFAULT_BANK_PATH, DEFAULT_INJECTIONS_PATH
                )
            except FileNotFoundError:
                # Create empty content bank for testing
                _content_bank = ContentBankService.__new__(ContentBankService)
                _content_bank.items = {}
                _content_bank._challenges = []
                _content_bank._injections = {}
        _test_assembly_service = TestAssemblyService(_content_bank)
    return _test_assembly_service


def get_assessment_definition(assessment_id: str) -> AssessmentDefinition:
    """Get an assessment definition by ID."""
    global _assessment_definitions
    if assessment_id not in _assessment_definitions:
        raise HTTPException(
            status_code=404, detail=f"Assessment {assessment_id} not found"
        )
    return _assessment_definitions[assessment_id]


def register_assessment_definition(definition: AssessmentDefinition) -> None:
    """Register an assessment definition for delivery."""
    global _assessment_definitions
    _assessment_definitions[definition.assessment_id] = definition


def set_session_manager(manager: SessionManager) -> None:
    """Set the session manager (for testing/initialization)."""
    global _session_manager
    _session_manager = manager


def set_test_assembly_service(service: TestAssemblyService) -> None:
    """Set the test assembly service (for testing/initialization)."""
    global _test_assembly_service
    _test_assembly_service = service


def set_content_bank(bank: ContentBankService) -> None:
    """Set the content bank (for testing/initialization)."""
    global _content_bank
    _content_bank = bank


# ============================================================================
# API Router
# ============================================================================


router = APIRouter(prefix="/delivery", tags=["delivery"])


# ============================================================================
# Routes
# ============================================================================


@router.post(
    "/start/{assessment_id}",
    response_model=StartAssessmentResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def start_assessment(
    assessment_id: str,
    request: StartAssessmentRequest,
    session_manager: SessionManager = Depends(get_session_manager),
    test_assembly: TestAssemblyService = Depends(get_test_assembly_service),
) -> StartAssessmentResponse:
    """
    Start an assessment session.

    Creates a new session, assembles the test, and returns the first item.
    """
    # Get assessment definition
    try:
        definition = get_assessment_definition(assessment_id)
    except HTTPException:
        raise HTTPException(
            status_code=404, detail=f"Assessment {assessment_id} not found"
        )

    # Assemble the test
    try:
        assembled_test = test_assembly.build_test(definition)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to assemble test: {str(e)}"
        )

    # Create session
    try:
        session = session_manager.create_session(
            assessment_definition=definition,
            candidate_id=request.candidate_id,
            test_taker_id=request.test_taker_id,
            assembled_test=assembled_test,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Start the session
    session = session_manager.start_session(session.session_id)

    # Get first item
    current_item = session.current_item
    item_dict = None
    if current_item:
        item_dict = {
            "item_id": current_item.item_id,
            "content": current_item.content,
            "metadata": current_item.metadata,
        }

    return StartAssessmentResponse(
        session_id=session.session_id,
        assessment_id=session.assessment_id,
        title=session.title,
        current_item_index=session.current_item_index,
        total_items=session.total_items,
        item=item_dict,
        time_limit_seconds=session.time_limit_seconds,
        time_remaining_seconds=session.calculate_time_remaining(),
        state=session.state.value,
        navigation_mode=session.navigation_mode,
    )


@router.get(
    "/session/{session_id}/current",
    response_model=CurrentItemResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_current_item(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> CurrentItemResponse:
    """
    Get the current item and session state.

    Returns the current item, timer, and navigation capabilities.
    """
    # Get session
    try:
        session = session_manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Check for time expiry
    if session.is_time_expired():
        session_manager.update_state(session_id, SessionState.EXPIRED)
        session = session_manager.get_session(session_id)

    # Get current item
    current_item = session.current_item
    item_dict = None
    if current_item:
        item_dict = {
            "item_id": current_item.item_id,
            "content": current_item.content,
            "metadata": current_item.metadata,
        }

    # Check navigation
    total_items = session.total_items
    can_go_previous = session.current_item_index > 0
    can_go_next = session.current_item_index < total_items - 1

    # For LINEAR mode, can only go forward
    if session.navigation_mode == "LINEAR":
        can_go_previous = False

    return CurrentItemResponse(
        session_id=session.session_id,
        current_item_index=session.current_item_index,
        total_items=total_items,
        item=item_dict,
        time_remaining_seconds=session.calculate_time_remaining(),
        is_flagged=current_item.item_id in session.flagged_items
        if current_item
        else False,
        state=session.state.value,
        navigation_mode=session.navigation_mode,
        can_go_previous=can_go_previous,
        can_go_next=can_go_next,
    )


@router.post(
    "/session/{session_id}/answer",
    response_model=AnswerResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def submit_answer(
    session_id: str,
    answer: AnswerSubmission,
    session_manager: SessionManager = Depends(get_session_manager),
) -> AnswerResponse:
    """
    Record an answer for the current item.

    The item_id should match the current item, but we accept any item_id
    for flexibility in non-linear navigation.
    """
    # Get session
    try:
        session = session_manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Check session state
    if session.state not in (SessionState.IN_PROGRESS, SessionState.PAUSED):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit answer in state: {session.state.value}",
        )

    # Check for time expiry
    if session.is_time_expired():
        session_manager.update_state(session_id, SessionState.EXPIRED)
        raise HTTPException(status_code=400, detail="Time expired")

    # Submit the answer
    session_manager.submit_answer(session_id, answer.item_id, answer.response)

    # Handle flagging
    if answer.is_flagged:
        session.flag_item(answer.item_id)
    else:
        session.unflag_item(answer.item_id)

    return AnswerResponse(
        session_id=session_id,
        item_id=answer.item_id,
        saved=True,
        current_item_index=session.current_item_index,
    )


@router.post(
    "/session/{session_id}/navigate",
    response_model=NavigateResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def navigate(
    session_id: str,
    navigation: NavigationRequest,
    session_manager: SessionManager = Depends(get_session_manager),
) -> NavigateResponse:
    """
    Navigate to a different item.

    Direction can be:
    - "next": Move to the next item
    - "previous": Move to the previous item
    - "specific": Move to a specific index (requires target_index)
    """
    # Get session
    try:
        session = session_manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Check session state
    if session.state != SessionState.IN_PROGRESS:
        raise HTTPException(
            status_code=400, detail=f"Cannot navigate in state: {session.state.value}"
        )

    # Check for time expiry
    if session.is_time_expired():
        session_manager.update_state(session_id, SessionState.EXPIRED)
        raise HTTPException(status_code=400, detail="Time expired")

    # Navigate
    try:
        session = session_manager.navigate(
            session_id,
            direction=navigation.direction,
            target_index=navigation.target_index,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get current item
    current_item = session.current_item
    item_dict = None
    if current_item:
        item_dict = {
            "item_id": current_item.item_id,
            "content": current_item.content,
            "metadata": current_item.metadata,
        }

    # Check navigation
    total_items = session.total_items
    can_go_previous = session.current_item_index > 0
    can_go_next = session.current_item_index < total_items - 1

    if session.navigation_mode == "LINEAR":
        can_go_previous = False

    return NavigateResponse(
        session_id=session_id,
        current_item_index=session.current_item_index,
        total_items=total_items,
        item=item_dict,
        state=session.state.value,
        can_go_previous=can_go_previous,
        can_go_next=can_go_next,
    )


@router.post(
    "/session/{session_id}/save",
    response_model=SaveProgressResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def save_progress(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> SaveProgressResponse:
    """
    Explicitly save session progress.

    Returns the saved state including current position and time remaining.
    """
    # Get session
    try:
        session = session_manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Save progress
    saved_data = session_manager.save_progress(session_id)

    return SaveProgressResponse(
        session_id=session_id,
        saved_at=datetime.utcnow(),
        current_item_index=saved_data["current_item_index"],
        time_remaining_seconds=saved_data["time_remaining_seconds"],
        responses_count=len(saved_data["responses"]),
    )


@router.post(
    "/session/{session_id}/submit",
    response_model=SubmitResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def submit_assessment(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> SubmitResponse:
    """
    Submit/complete the assessment.

    Transitions the session to COMPLETED state and returns final stats.
    """
    # Get session
    try:
        session = session_manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    # Check session state
    if session.state not in (SessionState.IN_PROGRESS, SessionState.PAUSED):
        raise HTTPException(
            status_code=400, detail=f"Cannot submit in state: {session.state.value}"
        )

    # Submit
    try:
        session = session_manager.submit_assessment(session_id)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return SubmitResponse(
        session_id=session_id,
        state=session.state.value,
        completed_at=session.completed_at or datetime.utcnow(),
        total_items=session.total_items,
        responses_count=len(session.responses),
    )


@router.post(
    "/session/{session_id}/pause",
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def pause_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> Dict[str, Any]:
    """Pause an assessment session."""
    try:
        session = session_manager.pause_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "session_id": session_id,
        "state": session.state.value,
        "paused_at": datetime.utcnow().isoformat(),
    }


@router.post(
    "/session/{session_id}/resume",
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def resume_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> Dict[str, Any]:
    """Resume a paused assessment session."""
    try:
        session = session_manager.resume_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "session_id": session_id,
        "state": session.state.value,
        "time_remaining_seconds": session.calculate_time_remaining(),
    }


@router.get(
    "/session/{session_id}",
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_session_info(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager),
) -> Dict[str, Any]:
    """Get full session information."""
    try:
        session = session_manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    return session.to_dict()


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@router.websocket("/ws/{session_id}")
async def delivery_websocket(
    websocket: WebSocket,
    session_id: str,
    session_manager: SessionManager = Depends(lambda: get_session_manager()),
):
    """
    WebSocket endpoint for real-time timer sync and session events.

    Client connections receive timer updates every second.
    """
    from .websocket_handler import DeliveryWebSocketHandler

    handler = DeliveryWebSocketHandler(session_manager)
    await handler.handle_connection(websocket, session_id)
