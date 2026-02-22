# State: WAA-ADS

**Project:** WAA-ADS (Automated Assessment Delivery System)
**Core Value:** Deliver a reliable, end-to-end assessment pipeline that produces trustworthy, explainable scorecards.
**Current Focus:** Planning phase 1

---

## Current Position

| Attribute | Value |
|-----------|-------|
| Current Phase | Roadmap (planning) |
| Current Plan | - |
| Status | Not started |
| Progress | 0% |

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Requirements (v1) | 24 |
| Requirements (v2) | 8 |
| Phases | 5 |
| Plans created | 0 |
| Plans completed | 0 |

---

## Accumulated Context

### Key Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| FastAPI + PostgreSQL + Celery | Recommended stack from research — async-first, production-mature | Decided in research |
| QTI 3.0 for content format | Industry standard (1EdTech), ensures portability | Decided in research |
| LTI 1.3 for LMS integration | Fits institutional workflows immediately | Decided in research |
| Python service skeletons | Provided in dev package — extend rather than rewrite | Decided in PROJECT.md |

### Phase Order Rationale

1. **Phase 1 (Content Bank & Identity):** Foundation — nothing works without content and identity
2. **Phase 2 (Delivery Orchestration):** User-facing core — timing, navigation, save/resume
3. **Phase 3 (Scoring & Reporting):** Core value — trustworthy, explainable scorecards
4. **Phase 4 (Integrity & Identity):** Risk-tiered controls — depends on scoring context
5. **Phase 5 (Audit & Compliance):** High-stakes polish — depends on everything

### Research Notes

- Stack: FastAPI 0.115+ / Python 3.11+ / PostgreSQL 16+ / Celery 5.5+
- Architecture: Service-oriented with clear boundaries
- Key pitfalls front-loaded: Item exposure, session resilience, accommodation handling
- Phase 3 (scoring) is the hardest — get pipeline right before adding integrity

### Research Flags

- Phase 1: QTI conformance testing, LTI 1.3 security (nonce, replay protection)
- Phase 3: ML model validation, regrade reproducibility
- Phase 4: Behavioral proctoring ML, NIST identity assurance mapping
- Phase 5: FERPA compliance, WCAG 2.2 testing

---

## Session Continuity

**Last updated:** 2026-02-22

**Next action:** Approve roadmap → `/gsd-plan-phase 1`
