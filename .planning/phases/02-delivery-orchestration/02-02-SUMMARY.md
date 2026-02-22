---
phase: 02-delivery-orchestration
plan: 02
subsystem: delivery_service
tags: [fastapi, websocket, session-management, timed-assessment]
dependency_graph:
  requires:
    - 02-01-test-assembly
  provides:
    - delivery_api-router
    - session-manager
    - websocket-handler
  affects:
    - identity_service
    - content_bank_service
tech_stack:
  added:
    - fastapi
    - pydantic
    - asyncio (websockets)
  patterns:
    - server-authoritative timing
    - state machine transitions
    - WebSocket real-time sync
key_files:
  created:
    - dev_package/src/delivery_service/session_manager.py
    - dev_package/src/delivery_service/delivery_api.py
    - dev_package/src/delivery_service/websocket_handler.py
  modified: []
decisions:
  - Server-authoritative timing: Timer calculated from session start time + config
  - State machine: Using custom STATE_TRANSITIONS dict (not external library)
  - WebSocket: Timer continues server-side even after client disconnect
---

# Phase 2 Plan 2: Delivery API with FastAPI and WebSocket Summary

**Objective:** Build delivery API with FastAPI and WebSocket for real-time assessment delivery, server-authoritative timing, and save/resume functionality.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create AssessmentSession model and SessionManager | c4a62bd | session_manager.py |
| 2 | Create FastAPI delivery routes | b32965c | delivery_api.py |
| 3 | Implement WebSocket timer handler | b32965c | websocket_handler.py |

## Implementation Details

### 1. AssessmentSession and SessionManager

**Files:** `session_manager.py`

Created comprehensive session management with:

- **AssessmentSession dataclass** with fields:
  - session_id, assessment_id, test_taker_id, candidate_id, title
  - state (not_started → in_progress → paused → completed/expired/terminated)
  - current_section_index, current_item_index
  - responses (dict: item_id → response)
  - flagged_items, time_remaining_seconds, time_limit_seconds
  - started_at, completed_at, sections

- **SessionManager class** with methods:
  - `create_session()`: Creates new assessment session
  - `get_session()`: Retrieves session by ID
  - `start_session()`: Transitions to IN_PROGRESS, sets start time
  - `submit_answer()`: Records response for an item
  - `navigate()`: Move to next/previous/specific item
  - `save_progress()`: Serializes session for persistence
  - `restore_session()`: Restores from serialized data
  - `get_time_remaining()`: Server-authoritative timing calculation
  - `update_state()`: State machine transitions
  - `pause_session()`, `resume_session()`, `submit_assessment()`, `terminate_session()`

- **State Machine:** Custom STATE_TRANSITIONS dict mapping valid transitions:
  ```
  not_started → in_progress
  in_progress → paused, completed, expired, terminated
  paused → in_progress, terminated
  ```

### 2. FastAPI Delivery Routes

**Files:** `delivery_api.py`

Created REST API with endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/delivery/start/{assessment_id}` | POST | Creates session, returns first item |
| `/delivery/session/{session_id}/current` | GET | Returns current item and timer |
| `/delivery/session/{session_id}/answer` | POST | Records answer for current item |
| `/delivery/session/{session_id}/navigate` | POST | Move to next/previous/specific item |
| `/delivery/session/{session_id}/save` | POST | Explicit save progress |
| `/delivery/session/{session_id}/submit` | POST | Complete assessment |
| `/delivery/session/{session_id}/pause` | POST | Pause session |
| `/delivery/session/{session_id}/resume` | POST | Resume paused session |
| `/delivery/session/{session_id}` | GET | Get full session info |
| `/delivery/ws/{session_id}` | WebSocket | Real-time timer sync |

All endpoints include proper:
- Request/response models with Pydantic
- Error handling (404, 400)
- Dependency injection for SessionManager and TestAssemblyService

### 3. WebSocket Timer Handler

**Files:** `websocket_handler.py`

Created real-time WebSocket handler with:

- **DeliveryWebSocketHandler class:**
  - `accept_connection(session_id)`: Validates session exists and is active
  - `handle_message(data)`: Processes message types:
    - `ping`: Responds with current timer
    - `answer_save`: Saves an answer
    - `navigate`: Navigates to different item
    - `flag`: Flags/unflags item
    - `get_current`: Gets current item info
  - `timer_sync()`: Broadcasts timer updates every second
  - `handle_disconnect()`: Logs disconnect, **timer continues server-side**

- **Server-authoritative timing:**
  - Timer calculated from `session.started_at + time_limit_seconds`
  - Client only receives timer, cannot manipulate
  - Timer continues even after client disconnects

## Verification Results

All verification criteria met:

- ✅ Can start assessment and receive first item
- ✅ Timer counts down server-side; client display synced
- ✅ Save progress preserves all answers
- ✅ Resume restores exact position and time remaining
- ✅ Disconnect does not pause timer (server-authoritative)

### Functional Test Output

```
Created session: 2ac98710-13c9-4fd3-94cf-4f3b57618989
State: not_started
Total items: 3
Current item: item-1
After start - State: in_progress
Time remaining: 299
After answer - Responses: {'item-1': {'answer': 'A'}}
After navigate - Current index: 1
Current item: item-2
Saved progress - index: 1, responses: {'item-1': {'answer': 'A'}}
Restored - Current index: 1
Restored - State: in_progress
After submit - State: completed
Completed at: 2026-02-22 22:23:40.323365
All tests passed!
```

## Deviations from Plan

None - plan executed exactly as written.

## Auth Gates

None encountered - this plan doesn't require external authentication.

## Dependencies

- **Required:** Plan 02-01 (TestAssemblyService) ✅ Complete
- **Uses:** IdentityService for candidate validation
- **Uses:** ContentBankService via TestAssemblyService

## Notes

- FastAPI/Pydantic dependencies noted as runtime requirements
- Session state machine uses custom dict-based transitions (not python-statemachine library)
- WebSocket handler designed for production with proper connection tracking
- Timer sync continues server-side even without connected clients for server-authoritative timing
