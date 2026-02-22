# Feature Research

**Domain:** Automated assessment delivery systems (WAA-ADS)
**Researched:** 2026-02-22
**Confidence:** MEDIUM

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Item bank with metadata | Reuse, search, and assemble exams efficiently | MEDIUM | Align items to standards; support tags, difficulty, time, and versioning (QTI metadata model). |
| Standards-based item import/export (QTI) | Content portability across tools | MEDIUM | Use QTI packages to exchange items/tests and metadata. |
| Core item types (choice, text, upload, media) | Baseline question formats across systems | MEDIUM | QTI defines interaction types including choice, text entry, upload, media. |
| Test assembly (sections, item selection, ordering) | Build exams at scale with consistent structure | MEDIUM | QTI supports sections, selection, ordering, and branch rules. |
| Timing, navigation, attempts, save/resume | Basic exam control and student expectations | MEDIUM | QTI test structures include time limits, session control, and review options. |
| Scoring and outcomes processing | Immediate results for auto-gradable items | HIGH | QTI response processing supports partial scoring and external scoring. |
| Accessibility and accommodations | Legal and usability requirements | HIGH | QTI 3 includes accessibility, PNP, and accommodations guidance. |
| Integrity baseline (secure browser / lockdown option) | High-stakes users expect deterrents | MEDIUM | Integrate a lockdown mode or third-party tool (e.g., Respondus LockDown Browser). |
| Reporting and exports (scorecards, CSV) | Stakeholders need results and auditability | MEDIUM | Produce candidate-level score reports and exports for downstream systems. |
| LMS integration (LTI launch and grade passback) | Institutions need seamless workflows | MEDIUM | LTI 1.3 is the standard for launching tools from LMS platforms. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Adaptive testing (branching / IRT) | Shorter tests with higher precision | HIGH | QTI 3 includes adaptive testing structures; requires calibrated item statistics. |
| Explainable scorecards | Trustworthy, defensible outcomes | HIGH | Link scores to evidence, rubric criteria, and feature extraction. |
| Integrity analytics (behavioral + device signals) | Stronger fraud detection without full proctoring | HIGH | Correlate session telemetry with suspicious patterns. |
| Multi-modal assessment pipeline | Covers interviews, coding, and simulations | HIGH | Integrate video, coding sandboxes, and artifact upload. |
| Offline/low-bandwidth delivery | Expands access in constrained environments | HIGH | Requires secure local caching, sync, and conflict resolution. |
| Item analytics and bias/fairness checks | Better validity and compliance | HIGH | Track item performance, drift, and DIF-like signals. |
| Custom interactions (PCI) | Enables domain-specific tasks | MEDIUM | QTI Portable Custom Interactions allow bespoke widgets. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Proprietary-only item format | “Simplify authoring” | Creates vendor lock-in and blocks interoperability | Use QTI import/export as the canonical exchange format. |
| Always-on webcam proctoring for all exams | “Stop all cheating” | Privacy, accessibility, and false-positive risks | Risk-based proctoring with human review. |
| Maximal lockdown that blocks assistive tech | “Harden security” | Breaks accessibility accommodations and legal compliance | Configurable restrictions + accommodation exemptions. |
| Fully automated pass/fail for high-stakes | “Faster decisions” | Due-process and appeal risks | Human-in-the-loop review for borderline cases. |

## Feature Dependencies

```
Item bank + metadata
    └──requires──> Standards-based import/export (QTI)
                         └──requires──> Content packaging + identifiers

Test assembly
    └──requires──> Item bank + core item types

Scoring and outcomes processing
    └──requires──> Response capture during delivery

Reporting and scorecards
    └──requires──> Scoring and outcomes processing
                         └──requires──> Audit/event logging

LTI integration
    └──requires──> Identity + session management

Integrity analytics
    └──requires──> Telemetry/event logging during delivery

Adaptive testing
    └──requires──> Calibrated item metadata + scoring reliability
```

### Dependency Notes

- **Item bank requires standards-based import/export:** interoperability keeps content portable and lowers vendor switching costs.
- **Reporting requires scoring and audit logging:** explainable scorecards depend on scored outcomes and traceable events.
- **LTI integration requires identity/session management:** LTI launch relies on stable user and context identity.
- **Integrity analytics requires telemetry logging:** behavioral signals only exist if delivery events are captured.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Item bank + QTI import/export — ensures content portability and reuse.
- [ ] Test assembly + delivery controls — enables real assessments with timing and navigation.
- [ ] Scoring + reporting (scorecards) — delivers the core value of trustworthy results.
- [ ] Basic integrity controls + audit log — minimum defensibility for outcomes.
- [ ] LTI launch integration — fits institutional workflows quickly.

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Accommodations + accessibility enhancements — expand to broader audiences and compliance.
- [ ] Proctoring integrations (lockdown/monitoring) — add for higher-stakes customers.
- [ ] Item analytics dashboard — improve content quality and performance.

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Adaptive testing — high complexity and requires calibration data.
- [ ] Offline/low-bandwidth delivery — significant platform and security investment.
- [ ] AI integrity analytics at scale — requires large behavioral baselines.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Item bank + QTI import/export | HIGH | MEDIUM | P1 |
| Test assembly + delivery controls | HIGH | MEDIUM | P1 |
| Scoring + reporting | HIGH | HIGH | P1 |
| LTI integration | MEDIUM | MEDIUM | P2 |
| Proctoring/lockdown integration | MEDIUM | MEDIUM | P2 |
| Adaptive testing | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A (Respondus LockDown Browser) | Competitor B (QTI-compliant platforms) | Our Approach |
|---------|-------------------------------------------|----------------------------------------|--------------|
| Secure browser lockdown | Full-screen lockdown, blocks apps and copy/paste | Varies by platform | Provide lockdown integration option; keep accessibility exceptions. |
| Standards-based content (QTI) | Not core focus | Core capability | Make QTI import/export first-class. |
| LMS integration | Often via LMS plugins | Common via LTI | Implement LTI 1.3 launch and outcomes. |

## Sources

- https://www.imsglobal.org/spec/qti/v3p0/impl (QTI 3.0: item types, test structure, outcomes, accessibility)
- https://www.imsglobal.org/spec/lti/v1p3/ (LTI 1.3: LMS integration standard)
- https://web.respondus.com/he/lockdownbrowser/ (LockDown Browser: secure delivery features)

---
*Feature research for: automated assessment delivery systems*
*Researched: 2026-02-22*
