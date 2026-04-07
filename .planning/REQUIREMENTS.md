# Requirements: WAA-ADS Milestone v2.0

**Milestone:** Institutional Production Readiness & Intelligent Growth
**Defined:** 2026-02-27
**Core Value:** Transform WAA-ADS into a secure, scalable, and self-growing assessment platform.

## v2 Requirements

### Production Hardening (HRDN)
- **HRDN-01**: Implement application-layer PII encryption using `pgcrypto` for sensitive candidate data.
- **HRDN-02**: Establish highly available (HA) infrastructure using Kubernetes with Redis Sentinel and Postgres StatefulSets.
- **HRDN-03**: Implement WebSocket sticky sessions in Ingress to ensure stateful delivery stability.
- **HRDN-04**: Enable `pgAudit` for legally defensible compliance tracking of all data modifications.

### Intelligent Assessment (INTL)
- **INTL-01**: Implement a live 3PL IRT engine for real-time ability estimation (EAP method).
- **INTL-02**: Develop a next-item selection algorithm based on Maximum Fisher Information (MFI).
- **INTL-03**: Build an LLM-powered AIG pipeline that generates valid QTI 3.0 items from source text.
- **INTL-04**: Implement experimental seeding logic to collect calibration data for AI-generated items.

### Growth & Acquisition (GRTH)
- **GRTH-01**: Build the Wizards Apprentice Agent to discover candidates via HeroHunt.ai API across LinkedIn and GitHub.
- **GRTH-02**: Implement AI-driven personalized outreach sequences via Instantly.ai integration.
- **GRTH-03**: Create automated assessment funnel that links discovered profiles to active WAA-ADS sessions.

### Accessibility & UI (ACCS)
- **ACCS-03**: Achieve WCAG 2.2 Level AA compliance for the unified Candidate Portal.
- **ACCS-04**: Implement keyboard-navigable "Grab-and-Place" patterns for complex QTI interaction types.

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| HRDN-01, 02, 03 | Phase 06 | Pending |
| INTL-01, 02 | Phase 07 | Pending |
| INTL-03, 04 | Phase 08 | Pending |
| GRTH-01, 02, 03 | Phase 09 | Pending |
| HRDN-04, ACCS-03, 04 | Phase 10 | Pending |

## Success Criteria (Operational Readiness)
1. **Security**: Audit confirms all PII is encrypted at rest and in transit with comprehensive access logs.
2. **Precision**: Adaptive engine converges on ability estimates with SE < 0.3 within 20 items.
3. **Growth**: Wizards Agent successfully converts 5% of discovered profiles to assessment starts.
4. **Compliance**: Lighthouse Accessibility score > 95 and passing manual WCAG 2.2 audit.
