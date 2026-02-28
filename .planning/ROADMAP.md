# Roadmap: WAA-ADS Milestone v2.0

**Milestone:** Institutional Production Readiness & Intelligent Growth
**Status:** Planning Complete
**Current Focus:** Phase 06 (Infrastructure)

## Phases

- [ ] **Phase 06: Production Infrastructure & Security** — HA Kubernetes stack, `pgcrypto` PII encryption, sticky sessions.
  **Plans:** 3 plans
  - [ ] 06-01-PLAN.md — Containerization & K8s Foundation
  - [ ] 06-02-PLAN.md — Database Hardening (pgcrypto)
  - [ ] 06-03-PLAN.md — WebSocket Resilience & Verification
- [ ] **Phase 07: Adaptive Engine (CAT)** — Live 3PL IRT logic, MFI selection, EAP estimation engine.
- [ ] **Phase 08: AI Item Generation (AIG)** — LLM pipeline for QTI 3.0, validation service, calibration seeding.
- [ ] **Phase 09: Wizards Apprentice Agent** — Social candidate discovery (HeroHunt), personalized outreach (Instantly).
- [ ] **Phase 10: Institutional Compliance & UI** — WCAG 2.2 audit, Unified Candidate Portal, performance optimization.

---

## Phase Details

### Phase 06: Production Infrastructure & Security
**Goal:** Build the secure, high-availability foundation required for high-stakes institutional deployment.
**Depends on:** Milestone v1.0 complete
**Requirements:** HRDN-01, HRDN-02, HRDN-03
**Success Criteria:**
1. System deployed on K8s with HA Postgres and Redis Sentinel.
2. Candidate PII encrypted at the application layer via `pgcrypto`.
3. WebSocket connections persist across horizontal scaling events.

### Phase 07: Adaptive Engine (CAT)
**Goal:** Implement the live Item Response Theory (IRT) engine for precision assessment.
**Depends on:** Phase 06
**Requirements:** INTL-01, INTL-02
**Success Criteria:**
1. Ability estimate ($\theta$) updates in real-time after each response.
2. Selection algorithm picks items that maximize information for the current $\theta$.

### Phase 08: AI Item Generation (AIG)
**Goal:** Scale the item bank automatically using Large Language Models.
**Depends on:** Phase 07
**Requirements:** INTL-03, INTL-04
**Success Criteria:**
1. Valid QTI 3.0 XML generated from source text prompts.
2. Uncalibrated items seeded into sessions for data collection.

### Phase 09: Wizards Apprentice Agent
**Goal:** Automate candidate acquisition through intelligent social discovery and outreach.
**Depends on:** Phase 06
**Requirements:** GRTH-01, GRTH-02, GRTH-03
**Success Criteria:**
1. Discovered profiles from LinkedIn/GitHub aggregated in WAA-ADS.
2. Personalized outreach emails sent automatically with tracking.

### Phase 10: Institutional Compliance & UI
**Goal:** Final polish for legal accessibility requirements and unified user experience.
**Depends on:** Phase 08, Phase 09
**Requirements:** HRDN-04, ACCS-03, ACCS-04
**Success Criteria:**
1. unified Candidate Portal handles registration, testing, and results.
2. System passes automated and manual WCAG 2.2 audit.

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 06. Infrastructure | 0/3 | In Progress | - |
| 07. Adaptive Engine| 0/? | Planned | - |
| 08. AI Generation | 0/? | Planned | - |
| 09. Growth Agent | 0/? | Planned | - |
| 10. Compliance/UI | 0/? | Planned | - |

---
**Milestone v1.0 History:** [✓ Complete & Archived](.planning/milestones/v1.0-ROADMAP.md)
