# Phase 2: Delivery Orchestration - Research

**Researched:** February 22, 2026
**Domain:** Assessment Delivery, Test Assembly, Session Management
**Confidence:** HIGH

## Summary

Phase 2 delivers the user-facing assessment delivery system that orchestrates test assembly, timed delivery, navigation, and session resilience. Building on Phase 1's content bank and identity services, this phase implements the core exam experience with server-authoritative timing, save/resume capability, and configurable lockdown controls.

**Primary recommendation:** Use FastAPI with WebSockets for real-time timer sync, SQLAlchemy for session persistence, python-statemachine for delivery workflow, and QTI 3.0 assessment structure for test definitions. Leverage existing audit ledger from Phase 1 for integrity event logging.

## User Constraints (from CONTEXT.md)

> No CONTEXT.md exists for this phase - all decisions are open.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | Web framework | Required by project stack |
| SQLAlchemy | 2.0+ | ORM | Required by project stack |
| python-statemachine | 2.5+ | Delivery workflow | Clean state transitions for assessment flow |
| python-jose | 3.3+ | JWT handling | Required by project stack |

### Phase-Specific
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI WebSockets | built-in | Real-time timer sync | For server-authoritative timing updates |
| redis-py | 5.0+ | Session cache | For fast session state lookups, pub/sub |
| sqlalchemy-fsm | 2.0+ | DB state transitions | For persisting delivery state to PostgreSQL |
| httpx | 0.28+ | Async HTTP | For client-side item fetching |

### Frontend (for Delivery UI)
| Library | Purpose | When to Use |
|---------|---------|-------------|
| React/Vue | SPA framework | For responsive assessment interface |
| js-cookie | Cookie handling | For session token management |
| Native Web APIs | Browser lockdown | Fullscreen API, visibilitychange |

**Installation:**
```bash
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg
pip install python-statemachine sqlalchemy-fsm redis
pip install httpx pytest pytest-asyncio
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── delivery_service/           # Core delivery orchestration
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy models for tests/sessions
│   ├── service.py              # Delivery business logic
│   ├── router.py               # FastAPI routes
│   ├── websocket.py            # Real-time timer/push
│   └── state_machine.py        # Delivery workflow states
├── test_assembly/              # Test construction from item bank
│   ├── __init__.py
│   ├── selector.py             # Item selection algorithms
│   ├── builder.py             # Test assembly from sections
│   └── schemas.py             # Pydantic models
├── delivery_ui/                # Candidate-facing interface
│   ├── components/             # React/Vue components
│   ├── hooks/                  # Timer sync, save/resume
│   └── pages/                  # Assessment pages
└── integrity/                  # Lockdown controls
    ├── __init__.py
    ├── events.py               # Integrity event logging
    └── config.py               # Lockdown configuration
```

### Pattern 1: Server-Authoritative Timing

**What:** Server maintains exact time remaining; client displays synced time. Client cannot manipulate timer.

**When to use:** All timed assessments where time limits are strict.

**Implementation:**
```python
# Source: FastAPI WebSocket docs + assessment system patterns
from fastapi import WebSocket
from datetime import datetime, timedelta

class TimerManager:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def start_timer(self, session_id: str, duration_seconds: int):
        end_time = datetime.utcnow() + timedelta(seconds=duration_seconds)
        await self.redis.setex(
            f"timer:{session_id}",
            duration_seconds,
            end_time.isoformat()
        )
    
    async def get_remaining(self, session_id: str) -> int:
        ttl = await self.redis.ttl(f"timer:{session_id}")
        return max(0, ttl)
    
    async def sync_timer(self, websocket: WebSocket, session_id: str):
        while True:
            remaining = await self.get_remaining(session_id)
            await websocket.send_json({
                "type": "timer_sync",
                "remaining_seconds": remaining,
                "server_time": datetime.utcnow().isoformat()
            })
            await asyncio.sleep(1)  # Sync every second
```

### Pattern 2: Test Assembly with Item Selection

**What:** Build assessments dynamically from item bank using configurable selection rules.

**When to use:** When you need randomized tests, adaptive testing, or configurable test forms.

**Implementation:**
```python
# Source: QTI 3.0 assessment model + item bank patterns
from dataclasses import dataclass
from enum import Enum
import random

class SelectionMode(Enum):
    RANDOM = "random"
    FIXED = "fixed"
    ADAPTIVE = "adaptive"

class OrderMode(Enum):
    SEQUENTIAL = "sequential"
    RANDOM = "random"
    SHUFFLE_SECTIONS = "shuffle_sections"

@dataclass
class SectionConfig:
    section_id: str
    item_pool_ids: list[str]
    selection_mode: SelectionMode
    items_to_select: int
    order_mode: OrderMode
    time_limit: int | None = None  # seconds

class ItemSelector:
    def select_items(self, config: SectionConfig, available_items: list) -> list:
        if config.selection_mode == SelectionMode.RANDOM:
            return random.sample(
                available_items,
                min(config.items_to_select, len(available_items))
            )
        elif config.selection_mode == SelectionMode.FIXED:
            return available_items[:config.items_to_select]
        raise ValueError(f"Unknown selection mode: {config.selection_mode}")
    
    def order_items(self, items: list, mode: OrderMode) -> list:
        if mode == OrderMode.SEQUENTIAL:
            return items
        elif mode == OrderMode.RANDOM:
            return random.sample(items, len(items))
        raise ValueError(f"Unknown order mode: {mode}")
```

### Pattern 3: Assessment Session State Machine

**What:** Define clear states and transitions for delivery workflow.

**When to use:** Required for requirements DELV-01, DELV-02, DELV-03.

**Implementation:**
```python
# Source: python-statemachine documentation
from python_statemachine import StateMachine, State, Event

class AssessmentDeliveryMachine(StateMachine):
    initial = State(initial=True)
    
    not_started = initial
    in_progress = State()
    paused = State()  # For save/resume
    completed = State()
    expired = State()
    terminated = State()
    
    start = Event(from_=not_started, to=in_progress)
    pause = Event(from_=in_progress, to=paused)
    resume = Event(from_=paused, to=in_progress)
    complete = Event(from_=in_progress, to=completed)
    expire = Event(from_=in_progress, to=expired)
    terminate = Event(from_=["in_progress", "paused"], to=terminated)
```

### Pattern 4: Save/Resume with Progress Persistence

**What:** Persist candidate answers and position to database; restore on resume.

**When to use:** Required for DELV-02 (candidate can save progress and resume).

**Implementation:**
```python
@dataclass
class AssessmentSession:
    session_id: str
    assessment_id: str
    candidate_id: str
    state: str
    started_at: datetime | None
    completed_at: datetime | None
    current_item_index: int
    responses: dict  # item_id -> response
    time_remaining: int  # seconds
    
    async def save_progress(self, db_session):
        await db_session.execute(
            update(AssessmentSession)
            .where(AssessmentSession.session_id == self.session_id)
            .values(
                current_item_index=self.current_item_index,
                responses=self.responses,
                time_remaining=self.time_remaining,
                state="paused"
            )
        )
    
    async def restore(self, session_id: str, db_session) -> "AssessmentSession":
        result = await db_session.execute(
            select(AssessmentSession)
            .where(AssessmentSession.session_id == session_id)
        )
        return result.scalar_one()
```

### Pattern 5: Integrity Event Logging

**What:** Log security-relevant events with precise timestamps to audit ledger.

**When to use:** Required for INTG-01, INTG-02.

**Implementation:**
```python
# Leverage existing audit ledger from Phase 1
from audit_ledger_service.ledger import AuditLedger
from datetime import datetime

class IntegrityEventTypes:
    FULLSCREEN_ENTER = "fullscreen_enter"
    FULLSCREEN_EXIT = "fullscreen_exit"
    TAB_VISIBLE = "tab_visible"
    TAB_HIDDEN = "tab_hidden"
    COPY_ATTEMPT = "copy_attempt"
    KEYBOARD_SHORTCUT = "keyboard_shortcut"
    NETWORK_DISCONNECT = "network_disconnect"
    NETWORK_RECONNECT = "network_reconnect"

async def log_integrity_event(
    ledger: AuditLedger,
    session_id: str,
    event_type: str,
    metadata: dict | None = None
):
    await ledger.record_event(
        session_id=session_id,
        actor="client",
        action=event_type,
        payload={
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
    )
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Session state management | Custom in-memory state | SQLAlchemy + Redis | Complex to handle concurrency, expiration, distributed systems |
| Timer synchronization | Client-side only | Server-authoritative with WebSocket sync | Client can manipulate time; server must be source of truth |
| State transitions | Raw if/else logic | python-statemachine | Hard to maintain, easy to have invalid states |
| Item randomization | Python random module | Cryptographically secure random for exams | Candidates may predict "random" sequences |
| Test definition format | Custom JSON | QTI 3.0 | Industry standard, import/export from LMS |

**Key insight:** Assessment delivery has strict integrity requirements. Server-authoritative timing and immutable audit logging are non-negotiable for high-stakes assessments.

## Common Pitfalls

### Pitfall 1: Client-Side Timer Manipulation
**What goes wrong:** Client can alter JavaScript timer, gaining extra time.
**Why it happens:** Trusting client-reported time.
**How to avoid:** Server maintains authoritative end_time; client only displays. Validate on submission.
**Warning signs:** Candidates consistently submitting after visible timer expires.

### Pitfall 2: Race Conditions in Save/Resume
**What goes wrong:** Multiple save requests cause lost responses.
**Why it happens:** Concurrent updates without proper locking.
**How to avoid:** Use database transactions with SELECT FOR UPDATE or optimistic locking.
**Warning signs:** Candidates reporting lost answers after save.

### Pitfall 3: Incomplete Session Recovery
**What goes wrong:** Disconnected candidate cannot resume; session appears stuck.
**Why it happens:** Not persisting intermediate state or not handling WebSocket disconnect.
**How to avoid:** Persist on every answer submission, not just explicit save. Implement heartbeat/ping-pong.
**Warning signs:** Multiple "session lost" support tickets.

### Pitfall 4: Time Drift in Long Assessments
**What goes wrong:** Over time, client/server clocks drift, causing confusion.
**Why it happens:** Not periodically re-syncing time.
**How to avoid:** Re-sync timer every 30 seconds via WebSocket; calculate remaining from server.
**Warning signs:** Discrepancies between client and server time near end of exam.

### Pitfall 5: Browser Fullscreen API Limitations
**What goes wrong:** User can exit fullscreen easily; lockdown is weak.
**Why it happens:** Browsers require user gesture to enter fullscreen; exiting is always allowed.
**How to monitor:** Log fullscreen exit events, trigger warnings. Use third-party lockdown browser for stronger controls.
**Warning signs:** High rate of fullscreen_exit events in audit log.

## Code Examples

### WebSocket Endpoint for Assessment Delivery
```python
# Source: FastAPI WebSocket documentation
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

manager = ConnectionManager()

@app.websocket("/ws/delivery/{session_id}")
async def delivery_websocket(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Handle: {"type": "answer", "item_id": "...", "response": "..."}
            # Handle: {"type": "save_progress"}
            # Handle: {"type": "ping"}
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        # Log disconnect for integrity
```

### Database Schema for Assessment Session
```python
# Source: SQLAlchemy 2.0 patterns
from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class AssessmentDefinition(Base):
    __tablename__ = "assessment_definitions"
    
    id = Column(Integer, primary_key=True)
    assessment_id = Column(String, unique=True, index=True)
    title = Column(String)
    sections = Column(JSON)  # Section configs as JSON
    time_limit = Column(Integer)  # Total seconds
    attempt_limit = Column(Integer, default=1)
    navigation_mode = Column(String)  # linear, non-linear, hybrid

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True)
    assessment_id = Column(String, ForeignKey("assessment_definitions.assessment_id"))
    candidate_id = Column(String, index=True)
    state = Column(String, default="not_started")
    current_item_index = Column(Integer, default=0)
    responses = Column(JSON, default=dict)
    time_remaining = Column(Integer)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Server-generated HTML | SPA with API | 2015+ | Better UX, real-time updates |
| Client-side timer | Server-authoritative + WebSocket sync | 2020+ | Prevents time manipulation |
| Linear navigation only | Configurable navigation modes | QTI 3.0 | Supports varied assessment styles |
| Single attempt only | Configurable attempt limits | Modern systems | Supports practice tests, retries |
| Static test forms | Dynamic assembly from item bank | 2010+ | Randomized tests, item banking |

**Deprecated/outdated:**
- **iframe item delivery:** Security concerns, replaced by API-based delivery
- **Long polling for timer:** WebSocket is superior for real-time sync
- **Cookie-only sessions:** JWT tokens with Redis for scalability

## Open Questions

1. **Offline/Resume Support**
   - What we know: Browser Page Visibility API can detect tab switching
   - What's unclear: Whether to support true offline (local storage + sync) in v1
   - Recommendation: Start with online-only; add offline in v2 if needed

2. **Browser Lockdown Strength**
   - What we know: Fullscreen API + visibilitychange can detect most violations
   - What's unclear: Whether to integrate Safe Exam Browser (SEB) or build custom
   - Recommendation: Implement JavaScript controls; offer SEB integration as option

3. **Real-Time Collaboration**
   - What we know: Not required for single-candidate assessments
   - What's unclear: Future need for proctored shared sessions
   - Recommendation: Design WebSocket architecture to support later; don't over-engineer now

## Sources

### Primary (HIGH confidence)
- **Context7:** FastAPI WebSocket patterns, SQLAlchemy 2.0 async sessions
- **QTI 3.0 Spec:** IMS Global - Assessment, Section and Item Information Model v3.0
- **python-statemachine:** Official documentation - transitions and events

### Secondary (MEDIUM confidence)
- **WebSearch:** Assessment delivery system architecture patterns 2025
- **WebSearch:** FastAPI WebSocket real-time timer sync patterns
- **Safe Exam Browser:** seb Höldrich - JavaScript API for lockdown

### Tertiary (LOW confidence)
- **WebSearch:** Item selection algorithms - marked for validation with domain experts

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses project-mandated FastAPI, SQLAlchemy, verified libraries
- Architecture: HIGH - Patterns from production assessment systems
- Pitfalls: MEDIUM - Based on common issues; may need project-specific validation

**Research date:** February 22, 2026
**Valid until:** March 22, 2026 (30 days - stable domain)
