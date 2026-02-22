# Project Research Summary

**Project:** WAA-ADS (Automated Assessment Delivery System)
**Domain:** Automated assessment delivery (ed-tech assessment platform)
**Researched:** February 22, 2026
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project builds an automated assessment delivery system — a platform for creating, assembling, delivering, and scoring educational assessments. Based on research into QTI standards (the industry content format), LTI integration (the LMS interop standard), and production assessment platforms, the recommended approach centers on **FastAPI + PostgreSQL + Celery** with a service-oriented architecture that separates content delivery from scoring pipelines.

The core insight is that assessment systems are fundamentally state machines with strict audit requirements. Every attempt must be traceable from launch through scoring to reporting. The architecture must enforce immutable responses and deterministic scoring from day one — retrofitting auditability later is extremely costly. The recommended MVP prioritizes QTI-compliant content import/export, test assembly, core delivery controls, and LTI integration to fit into institutional workflows immediately.

Key risks include item exposure management (leaked content invalidates administrations), non-deterministic scoring (breaks auditability and re-grading), and session resiliency (lost work destroys trust). These should be addressed in early phases, not deferred.

## Key Findings

### Recommended Stack

**Core framework:** FastAPI 0.115+ with Python 3.11+ — async-first, native OpenAPI, Pydantic validation. This is the 2025/2026 default for Python API workloads. Use Uvicorn 0.32+ as the ASGI server.

**Database:** PostgreSQL 16+ with SQLAlchemy 2.0+ (async via `sqlalchemy[asyncio]`) and asyncpg driver. PostgreSQL provides the ACID compliance and JSON support needed for assessment integrity. SQLAlchemy 2.0's async support is production-mature.

**Task queue:** Celery 5.5+ with Redis broker — the de facto standard for Python background tasks. Use JSON serialization (not pickle) for security.

**State machine:** python-statemachine 2.5+ — Pythonic API for modeling assessment attempt lifecycles (created → launched → in-progress → submitted → scored → reported).

**ML/Scoring:** scikit-learn 1.6+ for feature extraction, transformers 4.46+ for NLP scoring, ReportLab 4.2+ for PDF scorecards.

**Proctoring (optional):** OpenCV 4.10+ and MediaPipe for behavioral signals — but this is Phase 4+ only.

Full installation and version matrix in `.planning/research/STACK.md`.

### Expected Features

**Must have (table stakes):**
- Item bank with metadata + QTI import/export — ensures content portability and reuse
- Test assembly + delivery controls (timing, navigation, attempts) — enables real assessments
- Scoring + reporting (scorecards) — delivers core value of trustworthy results
- Basic integrity controls + audit log — minimum defensibility for outcomes
- LTI 1.3 launch integration — fits institutional workflows immediately

**Should have (competitive):**
- Explainable scorecards — link scores to evidence, rubric criteria
- Integrity analytics (behavioral + device signals) — fraud detection without full proctoring
- Accommodations + accessibility (timing, presentation) — legal and usability requirements
- Item analytics dashboard — improve content quality

**Defer (v2+):**
- Adaptive testing (IRT-based) — requires calibrated item statistics
- Offline/low-bandwidth delivery — significant platform investment
- AI integrity at scale — requires large behavioral baselines

Full feature landscape in `.planning/research/FEATURES.md`.

### Architecture Approach

The system follows a layered architecture with clear boundaries:

1. **Identity & Session Layer** — AuthN/AuthZ, session management, attempt lifecycle
2. **Orchestration & Delivery Layer** — Workflow state machine, content assembly, item delivery
3. **Scoring, Integrity, Reporting** — Feature extraction, scoring engine, explainability, audit ledger
4. **Data Stores** — Item bank, response store, audit log (append-only)

**Critical patterns:**
- Assessment attempt as explicit state machine — enables auditability and retry logic
- Immutable raw responses + derived features — supports re-scoring and explanation
- Orchestrated scoring pipeline — separates scoring from delivery for restartability

Project structure organizes by service domain: `identity/`, `session/`, `orchestrator/`, `content_bank/`, `delivery_agent/`, `feature_extractor/`, `scoring_engine/`, `integrity_checker/`, `reporting/`, `audit_ledger/`.

Full architecture in `.planning/research/ARCHITECTURE.md`.

### Critical Pitfalls

1. **Item exposure and content drift** — Items leak or are reused too frequently, breaking form equivalence. Must implement item lifecycle states, versioning, exposure caps from Phase 1.

2. **Non-deterministic scoring** — Scores change on regrade, breaking auditability. Must version scoring rules/models, snapshot inputs, and write immutable audit entries from Phase 3.

3. **Session resiliency gaps** — Lost sessions on network drops, browser crashes. Must event-source session state, persist checkpoints, make server time authoritative from Phase 2.

4. **Accommodation mismatch** — Inconsistent timing/display for students with accommodations. Must centralize accommodation policies and align with QTI/AfA from Phase 1-2.

5. **QTI/LTI interop drift** — Imported items render incorrectly or launches fail. Must validate QTI packages against schemas and enforce LTI 1.3 conformance from Phase 1-2.

6. **Privacy and data retention** — PII in logs, retention exceeds policy. Must classify data, enforce least-privilege, align with FERPA from Phase 3-5.

Full pitfalls analysis with recovery strategies in `.planning/research/PITFALLS.md`.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Content Bank & Identity Foundations
**Rationale:** Nothing else works without content and identity. QTI import/export is the foundation for content portability; identity/session is required before any attempt can be trusted.

**Delivers:**
- Item bank with metadata (versioning, exposure tracking)
- QTI 3.0 import/export with schema validation
- Identity service with OAuth/OIDC
- Session manager with attempt lifecycle
- Audit ledger (foundations)

**Implements from FEATURES.md:** Item bank + QTI import/export (P1), LTI launch requirements
**Avoids from PITFALLS.md:** Item exposure, accommodation mismatch, QTI interop drift, privacy violations

**Research flags:** QTI conformance testing — validate against IMS Global test suite. LTI 1.3 launch validation — verify deployment_id scoping.

---

### Phase 2: Delivery Orchestration
**Rationale:** With identity and content in place, delivery can be built. This is the user-facing core — must handle timing, navigation, save/resume, and checkpoint persistence.

**Delivers:**
- Content assembler (test forms, selection rules)
- Delivery agent (item rendering, response capture)
- Session state with server-authoritative timing
- Save/resume with idempotent endpoints
- Event stream for client telemetry

**Implements from FEATURES.md:** Test assembly + delivery controls (P1)
**Uses from STACK.md:** FastAPI + WebSockets for real-time delivery, python-statemachine for attempt workflow
**Avoids from PITFALLS.md:** Session resiliency gaps, accommodation mismatch

**Research flags:** Real-time delivery patterns — may need WebSocket research for high-concurrency sessions. QTI test rendering — verify all supported item types.

---

### Phase 3: Scoring & Reporting Engine
**Rationale:** Scoring is the hardest part and must be correct from day one. Scoring determines outcomes — get the pipeline right before adding integrity controls.

**Delivers:**
- Feature extraction pipeline (normalize responses → derive features)
- Scoring engine with versioned rules
- Rubric-based and ML-assisted scoring
- Explainable scorecards with evidence links
- Grade passback (LTI Outcomes)
- PDF report generation

**Implements from FEATURES.md:** Scoring + reporting (P1)
**Uses from STACK.md:** Celery + Redis for async scoring, scikit-learn/transformers for ML scoring, ReportLab for PDFs
**Avoids from PITFALLS.md:** Non-deterministic scoring, reporting without evidence, cut score instability, privacy violations

**Research flags:** ML scoring model validation — needs calibration and bias testing. Regrade reproducibility — verify deterministic replay.

---

### Phase 4: Integrity & Identity Controls
**Rationale:** With scoring working, add integrity verification. This is where proctoring signals and identity assurance come in — risk-tiered, not blanket.

**Delivers:**
- Integrity checker with behavioral signals
- Configurable identity assurance (risk-tiered)
- Evidence preservation for flags
- Human review workflow for appeals
- Lockdown browser integration option

**Implements from FEATURES.md:** Integrity analytics (P2), proctoring integration
**Avoids from PITFALLS.md:** Weak identity assurance, integrity signals without evidence, false positives

**Research flags:** Behavioral proctoring ML models — complex, may need dedicated research phase. NIST 800-63-4 identity assurance levels — verify compliance mapping.

---

### Phase 5: Audit & Compliance Hardening
**Rationale:** Final polish for high-stakes deployments. Scale the audit ledger, add retention policies, and prepare for certification.

**Delivers:**
- Immutable audit ledger with hash chains
- Data retention and disclosure controls
- Compliance reporting (FERPA, accessibility)
- Scale optimizations (session sharding, precomputed reports)
- Calibration tracking for psychometric validity

**Avoids from PITFALLS.md:** Privacy violations, cut score instability, audit gaps

**Research flags:** FERPA compliance verification — may need legal review. Accessibility audit — WCAG 2.2 conformance testing.

---

### Phase Ordering Rationale

- **1→2→3 is linear dependency:** Identity → Content → Delivery → Scoring. Each layer depends on the previous.
- **4 (Integrity) depends on 3 (Scoring):** Integrity flags need scoring context and evidence links.
- **5 (Compliance) depends on all:** Audit and compliance only make sense once everything else works.
- **Pitfall prevention is front-loaded:** Item exposure, session resilience, and accommodation handling are in early phases — retrofitting these is extremely costly.
- **Scoring (Phase 3) is the hardest:** Get the pipeline correct before adding integrity controls on top.

---

### Research Flags

Phases needing deeper research during planning:
- **Phase 1:** QTI conformance testing methodology, LTI 1.3 security (nonce, replay protection)
- **Phase 3:** ML model validation and bias detection, regrade reproducibility patterns
- **Phase 4:** Behavioral proctoring ML model selection, NIST identity assurance mapping
- **Phase 5:** FERPA compliance details, WCAG 2.2 testing automation

Phases with standard patterns (skip research-phase):
- **Phase 2:** FastAPI + WebSocket delivery is well-documented
- **Phase 3:** Celery + Redis task patterns are mature

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified with Context7, web searches, official docs. FastAPI + SQLAlchemy async + Celery is the 2025/2026 standard. |
| Features | MEDIUM | QTI/LTI specs are authoritative; competitive analysis is based on public documentation. Some differentiation features need validation. |
| Architecture | MEDIUM | Based on industry patterns and 1EdTech standards. State machine + immutable responses pattern is well-established. |
| Pitfalls | MEDIUM | Derived from operational experience and standards documentation. Some patterns (item exposure, session loss) are well-known; others need implementation verification. |

**Overall confidence:** MEDIUM-HIGH

The stack recommendation is highly confident — these are proven technologies. The architecture and features are confident based on QTI/LTI standards. The pitfalls are based on operational experience but some (especially ML scoring and proctoring) need implementation validation.

### Gaps to Address

- **ML scoring validation:** How to calibrate and validate ML-assisted scoring for high-stakes assessments — needs psychometric expertise or partnership.
- **Proctoring model training:** Behavioral proctoring requires training data; may need synthetic data or third-party models initially.
- **Psychometric calibration:** Cut scores and scale stability require statistical expertise — may need external consultant or built-in tooling.
- **Accessibility testing automation:** QTI/AfA accommodation mapping needs manual verification against WCAG 2.2.

## Sources

### Primary (HIGH confidence)
- Context7 — FastAPI async patterns, SQLAlchemy 2.0 sessions
- IETF draft-sheffer-oauth-rfc8725bis — JWT Best Current Practices
- 1EdTech QTI 3.0 specification — item types, test structure, outcomes
- 1EdTech LTI 1.3 specification — launch, grade passback
- Official FastAPI, SQLAlchemy, Celery documentation

### Secondary (MEDIUM confidence)
- WebSearch: Django vs FastAPI 2025/2026 comparisons
- GitHub: python-statemachine (1.2k stars), proctoring projects
- Respondus LockDown Browser documentation
- NIST 800-63-4 Digital Identity Guidelines

### Tertiary (LOW confidence)
- Operational experience patterns in pitfalls — needs validation during implementation
- Competitor feature analysis — based on public documentation only

---

*Research completed: February 22, 2026*
*Ready for roadmap: yes*
