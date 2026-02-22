# Pitfalls Research

**Domain:** Automated assessment delivery systems (WAA-ADS)
**Researched:** 2026-02-22
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Item Exposure and Content Bank Drift

**What goes wrong:**
Items leak or are reused too frequently, form equivalence breaks, and score validity degrades because content versions are not controlled or exposure is not monitored.

**Why it happens:**
Teams treat item content as static assets and skip lifecycle controls, exposure metrics, and form assembly rules.

**How to avoid:**
Implement item lifecycle states, versioning, and exposure caps; enforce QTI import validation; add form assembly constraints and item usage analytics with automatic retirement.

**Warning signs:**
Repeated item IDs across administrations, sudden score inflation on specific items, or manual hotfixes to remove leaked items.

**Phase to address:**
Phase 1 (Content Bank Foundations) and Phase 2 (Delivery Orchestration).

---

### Pitfall 2: Non-Deterministic Scoring and Missing Auditability

**What goes wrong:**
Scores change after reprocessing, explanations do not match evidence, and audit trails are incomplete for disputes.

**Why it happens:**
Scoring depends on mutable feature extraction, model drift, or external services without versioning and immutable inputs.

**How to avoid:**
Version scoring rules/models, snapshot all inputs, make scoring deterministic, and write immutable audit ledger entries with input hashes and scoring artifacts.

**Warning signs:**
Regrades produce different outcomes with same responses, or score explanations cannot be reconstructed from stored data.

**Phase to address:**
Phase 3 (Scoring and Reporting) and Phase 5 (Audit and Compliance Hardening).

---

### Pitfall 3: Session Resiliency Gaps (Save/Resume/Timeout)

**What goes wrong:**
Test sessions are lost on network drops, device restarts, or browser crashes; timing is inconsistent across clients.

**Why it happens:**
Session state is kept only in-memory or client-side; server time is not authoritative; retry logic is missing.

**How to avoid:**
Event-source session state, persist response checkpoints, make server time authoritative, and provide explicit resume tokens with idempotent submission endpoints.

**Warning signs:**
Support tickets about lost work, inconsistent timers between proctor and student, or duplicate submissions.

**Phase to address:**
Phase 2 (Delivery Orchestration).

---

### Pitfall 4: Accommodation and Accessibility Mismatch

**What goes wrong:**
Students with accommodations receive inconsistent timing, read-aloud, or display options; accessibility regressions invalidate administrations.

**Why it happens:**
Accommodations are applied ad hoc per UI or per item type, and accessibility requirements are treated as QA-only concerns.

**How to avoid:**
Centralize accommodation policies (timing, presentation, input), map to QTI/AfA where applicable, and align UI behavior with WCAG 2.2; enforce automated accessibility checks and manual audits.

**Warning signs:**
Manual overrides for accommodations, inconsistent timing multipliers, or accessibility bugs discovered late in pilot.

**Phase to address:**
Phase 1 (Content Bank Foundations) and Phase 2 (Delivery Orchestration).

---

### Pitfall 5: Weak Identity Assurance and Proctoring Overreach

**What goes wrong:**
Identity verification is too weak for high-stakes tests or too intrusive, producing false flags and legal risk.

**Why it happens:**
Identity proofing and monitoring requirements are not tied to risk tier; the system lacks policy-driven verification levels.

**How to avoid:**
Adopt risk-tiered identity assurance aligned to NIST Digital Identity Guidelines; implement configurable verification and monitoring policies with evidence capture and human review.

**Warning signs:**
High rate of integrity flags with no actionable evidence, or auditors rejecting identity verification methods.

**Phase to address:**
Phase 4 (Integrity and Identity Controls).

---

### Pitfall 6: QTI/LTI Interop Drift

**What goes wrong:**
Imported items render incorrectly, scoring keys mismatch, or LTI launches fail due to partial spec implementation.

**Why it happens:**
Teams implement a subset of QTI/LTI features without conformance testing or validation tooling.

**How to avoid:**
Validate QTI packages against schemas, adopt conformance tests, and build strict LTI 1.3 launch validation; maintain a compatibility matrix for supported item types and LTI services.

**Warning signs:**
Item rendering discrepancies between authoring and delivery, or frequent support escalations for LTI launch failures.

**Phase to address:**
Phase 1 (Content Bank Foundations) and Phase 2 (Delivery Orchestration).

---

### Pitfall 7: Integrity Signals Without Explainable Evidence

**What goes wrong:**
Integrity checker outputs unreviewable flags, leading to mistrust, disputes, and unusable reporting.

**Why it happens:**
Signals are aggregated into a single score without preserving raw evidence or rationale.

**How to avoid:**
Store raw evidence, timestamped events, and reasoning; expose clear criteria for each flag and provide an appeal workflow.

**Warning signs:**
Stakeholders cannot justify decisions, or appeals cannot be resolved due to missing evidence.

**Phase to address:**
Phase 4 (Integrity and Identity Controls) and Phase 5 (Audit and Compliance Hardening).

---

### Pitfall 8: Privacy and Data Retention Violations

**What goes wrong:**
PII is logged or shared beyond allowed scope, retention exceeds policy, or data access is overly broad.

**Why it happens:**
Teams treat telemetry and audit data as exempt from privacy rules and lack data classification and retention policy enforcement.

**How to avoid:**
Classify data (PII, assessment content, integrity evidence), enforce least-privilege access, and implement retention and disclosure controls aligned with FERPA and applicable regulations.

**Warning signs:**
PII appears in logs, access controls are role-ambiguous, or retention defaults are “keep forever.”

**Phase to address:**
Phase 3 (Scoring and Reporting) and Phase 5 (Audit and Compliance Hardening).

---

### Pitfall 9: Cut Score and Scale Instability

**What goes wrong:**
Scores are not comparable across forms or time; scorecards appear inconsistent and undermine trust.

**Why it happens:**
Cut scores and scale transformations are applied without psychometric validation or item calibration.

**How to avoid:**
Define scale design early, plan calibration studies, and keep scoring rules and scale transforms versioned and testable; include regrade protocols.

**Warning signs:**
Large score swings between administrations with similar cohorts or inability to explain scale changes.

**Phase to address:**
Phase 3 (Scoring and Reporting) with validation checkpoints in Phase 5 (Audit and Compliance Hardening).

---

### Pitfall 10: Reporting Without Evidence Links

**What goes wrong:**
Scorecards summarize results but cannot trace back to item-level evidence or scoring logic.

**Why it happens:**
Reporting is built as a separate layer without direct links to response data and scoring artifacts.

**How to avoid:**
Link score reports to item-level evidence, scoring rules, and integrity flags; provide explainability artifacts in the reporting service.

**Warning signs:**
Users request “why” and the system only offers summary stats; audit requests require manual data pulls.

**Phase to address:**
Phase 3 (Scoring and Reporting).

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store responses without item version IDs | Faster ingestion | Impossible regrade and audit trails | Never |
| Hardcode accommodations in UI only | Quick MVP delivery | Compliance failures and inconsistent timing | Never |
| Use ad hoc scoring scripts | Rapid iteration | Non-repeatable scoring and audit failures | Only in prototype with explicit “non-production” flag |
| Skip item exposure metrics | Less analytics work | Item leakage and invalid score trends | Never |
| Reuse session tokens across devices | Simplifies support | Integrity and security risks | Never |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| QTI import/export | Partial schema support without validation | Validate packages against QTI schemas and document supported item types |
| LTI 1.3 launch | Ignoring deployment_id and claim validation | Enforce LTI 1.3 claim validation and deployment_id scoping |
| SSO/IdP | Over-trusting upstream identity without assurance level | Map IdP assurance to test risk tier and require step-up auth |
| Proctoring vendors | Accepting black-box flags | Require evidence payloads and appeal workflows |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous scoring on submit | Slow submits, timeouts | Queue scoring jobs and return receipt | 1k+ concurrent submissions |
| Large media items without CDN | Slow load, timeouts | Use CDN and prefetch policies | 100+ concurrent test takers |
| Monolithic session store | Lock contention, lost saves | Partition session storage and use append-only events | Multi-region or peak loads |
| On-demand report generation | Reports time out | Precompute aggregates and cache | Large cohorts or district rollups |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Exposing answer keys in client payloads | Cheating, item leakage | Keep keys server-side and use signed response templates |
| Weak token scoping for sessions | Session hijack | Scope tokens to device, time, and assessment ID |
| Storing integrity evidence unencrypted | Legal exposure | Encrypt at rest and restrict access with audited roles |
| Replaying launch payloads | Unauthorized access | Enforce nonce and replay protection for LTI/OIDC |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No clear save/resume status | Anxiety, lost work | Show real-time save state and last sync time |
| Timer not aligned with accommodations | Unfair timing | Display adjusted timer and rationale per accommodation |
| Unclear integrity rules | Distrust | Explain monitoring rules and provide consent notices |
| Ambiguous submission confirmation | Accidental incomplete submissions | Provide explicit confirmation and receipt ID |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Assessment delivery:** Missing resume tokens and checkpoint persistence — verify recovery from network drop.
- [ ] **Scoring engine:** Missing deterministic replay with versioned rules — verify regrade reproducibility.
- [ ] **Integrity checker:** Missing evidence links — verify audit trails per flag.
- [ ] **Content bank:** Missing item version and exposure metadata — verify item lifecycle controls.
- [ ] **Reporting:** Missing item-level traceability — verify “why” for any score.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Item exposure/leak | HIGH | Retire items, rebuild forms, re-norm or regrade, notify stakeholders |
| Non-deterministic scoring | HIGH | Freeze scoring version, reprocess with locked inputs, issue corrected reports |
| Session data loss | MEDIUM | Restore from server checkpoints, allow retake with audit note |
| Accommodation mismatch | MEDIUM | Pause affected administrations, correct policy engine, re-offer with accommodations |
| Integrity false positives | MEDIUM | Conduct human review, adjust thresholds, issue appeals process |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Item exposure and content drift | Phase 1 | Item version + exposure reports show retirement rules applied |
| Non-deterministic scoring | Phase 3 | Regrade produces identical results from same inputs |
| Session resiliency gaps | Phase 2 | Simulated drop/resume preserves state and time accurately |
| Accommodation mismatch | Phase 2 | Accommodation policy tests cover timing/read-aloud/display |
| Weak identity assurance | Phase 4 | Identity proofing aligned to risk tier with audit logs |
| QTI/LTI interop drift | Phase 1-2 | Conformance tests pass for supported item/launch types |
| Integrity without evidence | Phase 4 | Each flag links to evidence timeline and rationale |
| Privacy and retention violations | Phase 5 | Data inventory and retention policy enforced in storage |
| Cut score and scale instability | Phase 3 | Scale versioning and calibration documented |
| Reporting without evidence | Phase 3 | Reports include drill-down to item evidence |

## Sources

- https://www.imsglobal.org/standards/qti (QTI overview and specs)
- https://www.imsglobal.org/spec/lti/v1p3/ (LTI 1.3 core specification)
- https://www.w3.org/TR/WCAG22/ (WCAG 2.2 accessibility requirements)
- https://studentprivacy.ed.gov/ferpa (FERPA regulations and guidance)
- https://pages.nist.gov/800-63-3/ (Digital Identity Guidelines; superseded by 800-63-4)
- Operational experience and industry practice (LOW confidence)

---
*Pitfalls research for: automated assessment delivery systems*
*Researched: 2026-02-22*
