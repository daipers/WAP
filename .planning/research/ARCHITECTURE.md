# Architecture Research

**Domain:** Automated assessment delivery systems (WAA-ADS)
**Researched:** 2026-02-22
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│ External Platforms & Data Feeds                                      │
│  LTI (launch/grade passback)  OneRoster (roster)  Proctoring  Caliper │
└───────────────┬─────────────────────────┬─────────────────────────────┘
                │                         │
┌───────────────┴─────────────────────────┴─────────────────────────────┐
│ Identity & Session Layer                                              │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────────┐   │
│  │ Identity Svc │  │ Session Manager │  │ Policy/Access Control    │   │
│  └──────┬───────┘  └───────┬────────┘  └──────────┬───────────────┘   │
└─────────┴──────────────────┴─────────────────────┴───────────────────┘
          │
┌─────────┴─────────────────────────────────────────────────────────────┐
│ Orchestration & Delivery Layer                                        │
│  ┌───────────────┐  ┌─────────────────┐  ┌─────────────────────────┐ │
│  │ Orchestrator  │  │ Delivery/Agent  │  │ Content Bank/Assembler  │ │
│  └──────┬────────┘  └──────┬──────────┘  └──────────┬──────────────┘ │
└─────────┴──────────────────┴────────────────────────┴────────────────┘
          │                              │
┌─────────┴──────────────────────────────┴──────────────────────────────┐
│ Scoring, Integrity, Reporting                                         │
│  ┌─────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │
│  │ Feature Extract │  │ Scoring Engine │  │ Reporting/Scorecards    │ │
│  └────────┬────────┘  └────────┬───────┘  └─────────┬──────────────┘ │
│           │                   │                    │                 │
│  ┌────────▼────────┐   ┌───────▼────────┐   ┌───────▼──────────────┐  │
│  │ Integrity Check │   │ Explanation    │   │ Audit Ledger         │  │
│  └─────────────────┘   └────────────────┘   └──────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
                │
┌───────────────┴───────────────────────────────────────────────────────┐
│ Data Stores                                                            │
│  Item/Content Store  Session/Attempt Store  Response Store  Audit Log  │
│  Feature Store        Score Store           Report Store               │
└───────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Identity/Access | AuthN/AuthZ, roles, policy enforcement | OAuth/OIDC gateway, policy engine, user/role DB |
| Session Manager | Create/track attempts, timing, state transitions | Stateful service + session DB + cache |
| Orchestrator | Sequence steps, enforce workflow, retries | Workflow engine/state machine + queue |
| Content Bank/Assembler | Store items/tests, assemble forms/adaptive pools | QTI-aligned item store + test assembly service |
| Delivery/Interview Agent | Render items, capture responses, client events | Web app + API service + streaming events |
| Feature Extractor | Normalize/derive scoring features | Batch/stream processors, feature store |
| Scoring Engine | Apply scoring logic, compute scores/partials | Rule engine + ML inference service |
| Integrity Checker | Detect anomalies, proctoring signals, audit flags | Event correlation service + rules |
| Reporting/Scorecards | Generate explainable outputs | Report generator + templating |
| Audit Ledger | Immutable attempt + scoring trail | Append-only log + hash chain |

## Recommended Project Structure

```
src/
├── services/                 # Deployment units
│   ├── identity/             # AuthN/AuthZ, policy checks
│   ├── session/              # Attempt lifecycle, timing, locks
│   ├── orchestrator/         # Workflow state machine, retries
│   ├── content_bank/         # Item storage, assembly, QTI I/O
│   ├── delivery_agent/       # Item delivery, response capture
│   ├── feature_extractor/    # Feature normalization and derivation
│   ├── scoring_engine/       # Scoring rules/ML and explainers
│   ├── integrity_checker/    # Proctoring/anomaly detection
│   ├── reporting/            # Scorecards, exports, API
│   └── audit_ledger/          # Immutable attempt/scoring log
├── common/                   # Shared schemas, events, auth, errors
├── storage/                  # DB adapters, object storage, ledger
├── integrations/             # LTI, OneRoster, Caliper adapters
└── contracts/                # API specs, event schemas, data models
```

### Structure Rationale

- **services/** isolates domain boundaries so delivery and scoring can scale independently.
- **integrations/** keeps external standards (LTI, OneRoster, Caliper) decoupled from core logic.

## Architectural Patterns

### Pattern 1: Assessment Attempt as State Machine

**What:** Model an attempt as explicit states (created → launched → in-progress → submitted → scored → reported).
**When to use:** Any timed/secure assessment or multi-step scoring pipeline.
**Trade-offs:** More modeling overhead, but removes ambiguity and eases auditing.

**Example:**
```python
class AttemptState(Enum):
    CREATED = "created"
    LAUNCHED = "launched"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    SCORED = "scored"
    REPORTED = "reported"

def transition(attempt, next_state):
    assert (attempt.state, next_state) in ALLOWED_TRANSITIONS
    attempt.state = next_state
    audit_log.append({"attempt_id": attempt.id, "state": next_state})
```

### Pattern 2: Immutable Response + Derived Features

**What:** Store raw responses immutably, compute features and scores as derived data.
**When to use:** Any system requiring traceability and re-scoring.
**Trade-offs:** Extra storage and reprocessing cost, but supports explainability and audits.

**Example:**
```python
raw_response_id = response_store.write(raw_payload)
features = feature_extractor.compute(raw_response_id)
score = scoring_engine.score(features)
```

### Pattern 3: Orchestrated Scoring Pipeline

**What:** Orchestrator sequences feature extraction → scoring → reporting with retries and idempotency.
**When to use:** Multi-step scoring or mixed auto/manual scoring.
**Trade-offs:** Adds coordination complexity, but makes the pipeline observable and restartable.

## Data Flow

### Request Flow

```
LMS/LTI Launch
    ↓
Identity + Session → Orchestrator → Delivery/Agent → Response Store
    ↓                      ↓              ↓
Integrity Signals     Content Bank     Event Stream
    ↓                      ↓
Feature Extractor → Scoring Engine → Reporting → Grade Passback (LTI/OneRoster)
    ↓                                         ↓
Audit Ledger ←──────────── All steps and artifacts ────────────────→ Analytics (Caliper)
```

### Session State Management

```
Attempt Store
    ↓ (state transitions)
Session Manager ↔ Orchestrator ↔ Delivery Agent
    ↓
Audit Ledger (immutable transition log)
```

### Key Data Flows

1. **Content lifecycle:** Author/import items → content bank → assembly rules → delivery runtime.
2. **Assessment runtime:** Launch → session creation → item delivery → response capture → submission.
3. **Scoring pipeline:** Raw responses → feature extraction → scoring → explanation → scorecards.
4. **Trust and integrity:** Client telemetry + proctoring signals → integrity checker → flags → report.
5. **Reporting and exchange:** Scorecards → LMS grade passback (LTI/OneRoster) → analytics (Caliper).

### Build Order Implications

1. **Identity/Session + Audit Ledger:** Required before trustworthy data flows exist.
2. **Content Bank + Delivery Agent:** Enables end-to-end attempt capture.
3. **Feature Extractor + Scoring Engine:** Requires response capture and stable schemas.
4. **Reporting + Integrations:** Depends on scoring outputs and identity mapping.
5. **Integrity Checker:** Best added after event capture is stable.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k users | Single orchestrator + DB; prioritize traceability over throughput. |
| 1k-100k users | Queue-based scoring, cache session state, split delivery from scoring. |
| 100k+ users | Shard attempts by tenant/test, async reporting, dedicated audit ledger. |

### Scaling Priorities

1. **First bottleneck:** Delivery concurrency and session state writes; fix via cache + async event ingest.
2. **Second bottleneck:** Scoring throughput; fix via queue workers and idempotent scoring tasks.

## Anti-Patterns

### Anti-Pattern 1: Mutable Responses

**What people do:** Overwrite response records during scoring fixes.
**Why it's wrong:** Breaks auditability and explainability.
**Do this instead:** Store raw responses immutably and version derived scores.

### Anti-Pattern 2: Scoring Logic Inside Delivery

**What people do:** Compute scores in the delivery UI or session service.
**Why it's wrong:** Ties scoring to runtime UX, blocks re-scoring and batch processing.
**Do this instead:** Keep scoring in a separate pipeline with explicit contracts.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| LTI (1.3 + Advantage) | OIDC launch + grade passback | Standard LMS launch + grade return. |
| OneRoster | REST/CSV data exchange | Roster and gradebook exchange. |
| Caliper | Event stream | Analytics events for assessment activity. |
| LTI Proctoring | Optional LTI service | Proctoring signals for integrity checks. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Orchestrator ↔ Delivery | API + events | Delivery is stateless; state in session service. |
| Delivery ↔ Feature Extractor | Event stream | Features derived from immutable responses. |
| Scoring ↔ Reporting | API | Report generation is idempotent by score version. |
| All services ↔ Audit Ledger | Append-only API | Every transition logged. |

## Sources

- https://www.1edtech.org/standards/qti
- https://www.1edtech.org/standards/lti
- https://www.1edtech.org/standards/oneroster
- https://www.1edtech.org/standards/caliper

---
*Architecture research for: automated assessment delivery systems*
*Researched: 2026-02-22*
