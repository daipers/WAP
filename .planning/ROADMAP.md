# Roadmap: WAA-ADS

**Created:** 2026-02-22
**Depth:** Quick (3-5 phases)
**Core Value:** Deliver a reliable, end-to-end assessment pipeline that produces trustworthy, explainable scorecards.

## Phases

- [ ] **Phase 1: Content Bank & Identity Foundations** — Item bank, QTI import/export, identity, session management, audit foundations
- [ ] **Phase 2: Delivery Orchestration** — Test assembly, content delivery, timing, navigation, save/resume
- [ ] **Phase 3: Scoring & Reporting Engine** — Feature extraction, scoring engine, scorecards, LTI grade passback
- [ ] **Phase 4: Integrity & Identity Controls** — Behavioral signals, risk-tiered identity assurance, lockdown controls (v2)
- [ ] **Phase 5: Audit & Compliance Hardening** — Immutable audit ledger, data retention, compliance reporting (v2)

---

## Phase Details

### Phase 1: Content Bank & Identity Foundations

**Goal:** Build the foundation — content storage with QTI import/export, identity/auth, session management, and audit logging foundations

**Depends on:** Nothing (first phase)

**Requirements:** IDEN-01, IDEN-02, IDEN-03, CONT-01, CONT-02, CONT-03, CONT-04, AUDT-01, AUDT-02

**Success Criteria** (what must be TRUE):
1. User can create, view, update, and delete identity records for assessment candidates
2. User can authenticate and authorize access to assessment sessions with proper credentials
3. Session persists across browser refresh and maintains attempt state
4. User can import assessment items from QTI packages into the system
5. User can export items to QTI format for portability and reuse
6. User can store items with metadata including tags, difficulty ratings, and time limits
7. User can version items and track changes over time
8. System records immutable audit log entries for each assessment attempt
9. System captures delivery events including start, answer, submit, and terminate actions

**Plans:** 3 plans

- [ ] 01-identity-session-PLAN.md — Identity & Session Service (IDEN-01, IDEN-02, IDEN-03)
- [ ] 02-content-bank-PLAN.md — Content Bank with QTI Import/Export (CONT-01, CONT-02, CONT-03, CONT-04)
- [ ] 03-audit-ledger-PLAN.md — Audit Ledger Foundations (AUDT-01, AUDT-02)

---

### Phase 2: Delivery Orchestration

**Goal:** Enable test assembly and delivery — the user-facing core that handles timing, navigation, and session resilience

**Depends on:** Phase 1

**Requirements:** TEST-01, TEST-02, TEST-03, DELV-01, DELV-02, DELV-03, INTG-01, INTG-02

**Success Criteria** (what must be TRUE):
1. User can assemble tests from the item bank with defined sections
2. User can define item selection rules and specify ordering logic
3. User can configure timing constraints, navigation behavior, and attempt limits
4. Candidate can take assessment with a timed, navigable interface
5. Candidate can save progress and resume within an active session
6. Server maintains authoritative timing even on client disconnect
7. System supports configurable lockdown and integrity controls
8. Integrity events are logged with precise timestamps

**Plans:** TBD

---

### Phase 3: Scoring & Reporting Engine

**Goal:** Produce trustworthy scorecards — the core value delivery with explainable, reproducible results

**Depends on:** Phase 2

**Requirements:** SCR-01, SCR-02, SCR-03, REPT-01, REPT-02, REPT-03, INTG-03, INTG-04

**Success Criteria** (what must be TRUE):
1. System automatically scores response-based items using configured rules
2. System supports custom scoring rules defined per item or per test
3. Scores are versioned and reproducible — re-scoring produces identical results
4. System generates candidate scorecard with detailed performance breakdown
5. System exports results to CSV format for external analysis
6. Scorecards link scores to evidence showing item responses
7. System supports LTI 1.3 launch from LMS for seamless integration
8. System sends grade passback via LTI Outcomes to update LMS grades

**Plans:** TBD

---

### Phase 4: Integrity & Identity Controls

**Goal:** Add risk-tiered integrity verification and identity assurance (v2 scope)

**Depends on:** Phase 3

**Requirements:** (v2 requirements - ACCS-01, ACCS-02, ADPT-01, ADPT-02)

**Success Criteria** (what must be TRUE):
1. System captures behavioral signals during assessment for integrity analysis
2. System provides risk scoring for manual integrity review
3. System supports accessibility accommodations including extra time and alternative formats
4. System respects PNP (personal needs and preferences) from LTI launch

**Plans:** TBD

---

### Phase 5: Audit & Compliance Hardening

**Goal:** Final polish for high-stakes deployments — immutable audit, retention policies, certification readiness (v2 scope)

**Depends on:** Phase 4

**Requirements:** (v2 requirements - ANLY-01, ANLY-02)

**Success Criteria** (what must be TRUE):
1. System provides item performance analytics dashboard
2. System detects item bias and fairness issues
3. Immutable audit ledger with cryptographic hash chains
4. Data retention and disclosure controls align with FERPA

**Plans:** TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Content Bank & Identity | 0/3 | Not started | - |
| 2. Delivery Orchestration | 0/1 | Not started | - |
| 3. Scoring & Reporting | 0/1 | Not started | - |
| 4. Integrity & Identity | 0/1 | Not started | - |
| 5. Audit & Compliance | 0/1 | Not started | - |

---

## Coverage

| Phase | Requirements |
|-------|--------------|
| 1 | IDEN-01, IDEN-02, IDEN-03, CONT-01, CONT-02, CONT-03, CONT-04, AUDT-01, AUDT-02 |
| 2 | TEST-01, TEST-02, TEST-03, DELV-01, DELV-02, DELV-03, INTG-01, INTG-02 |
| 3 | SCR-01, SCR-02, SCR-03, REPT-01, REPT-02, REPT-03, INTG-03, INTG-04 |
| 4 | ACCS-01, ACCS-02, ADPT-01, ADPT-02 (v2) |
| 5 | ANLY-01, ANLY-02 (v2) |

**Total:** 24/24 v1 requirements mapped ✓
