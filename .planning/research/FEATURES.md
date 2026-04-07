# Feature Landscape: WAA-ADS Milestone v2.0

**Domain:** Institutional Production Readiness & Intelligent Growth
**Researched:** February 27, 2026

## Table Stakes (Institutional Readiness)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Unified Candidate Portal** | Professional interface for test-takers. | Medium | Consolidates identity, delivery, and score results. |
| **FERPA/GDPR PII Encryption** | Legal requirement for educational records. | Medium | Use `pgcrypto` for sensitive identifiers. |
| **High Availability (HA) K8s** | System reliability during high-stakes exams. | High | Redis Sentinel, StatefulSets for Postgres. |
| **WCAG 2.2 Navigation** | Legal accessibility compliance. | Medium | Focus on keyboard-only patterns for QTI items. |

## Intelligence Layer (AIG/CAT)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **3PL Next-Item Selection** | Precise targeting of student ability. | Medium | Maximum Fisher Information (MFI) algorithm. |
| **EAP Ability Estimation** | Stable psychometric scoring. | Medium | Bayesian approach handling extreme cases. |
| **LLM-Based AIG** | Infinite, dynamic item pools. | High | QTI 3.0 generation via Claude 3.5. |
| **Calibration Seeding** | Live data-driven IRT updates. | High | Injecting uncalibrated items into live tests. |

## Growth Agent (Wizards Apprentice)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Cross-Platform Discovery** | Automated candidate sourcing. | Medium | HeroHunt API for LinkedIn/GitHub/StackOverflow. |
| **3-Layer Personalization** | High outreach response rates. | Medium | Context + Job Match + Task Specificity (Claude). |
| **Automated Assessment Trigger**| Instant funnel conversion. | Low | Discover -> Outreach -> Assessment Link. |

## MVP Recommendation

1. **Phase 06: Hardening**: Secure DB, HA Infrastructure, and PII Encryption.
2. **Phase 07: Adaptive**: 3PL CAT Engine with MFI/EAP.
3. **Phase 08: Generation**: AIG Pipeline with XSD and S&B validation.
4. **Phase 09: Growth**: Wizards Apprentice discovery and outreach agent.
5. **Phase 10: Compliance**: WCAG 2.2 Audit and final performance tuning.
