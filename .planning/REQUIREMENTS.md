# Requirements: WAA-ADS

**Defined:** 2026-02-22
**Core Value:** Deliver a reliable, end-to-end assessment pipeline that produces trustworthy, explainable scorecards.

## v1 Requirements

### Identity & Session

- [ ] **IDEN-01**: User can create and manage identity records for assessment candidates
- [ ] **IDEN-02**: User can authenticate and authorize access to assessment sessions
- [ ] **IDEN-03**: Session persists across browser refresh and maintains attempt state

### Content Bank

- [ ] **CONT-01**: User can import items from QTI packages
- [ ] **CONT-02**: User can export items to QTI format for portability
- [ ] **CONT-03**: User can store items with metadata (tags, difficulty, time limits)
- [ ] **CONT-04**: User can version items and track changes

### Test Assembly

- [ ] **TEST-01**: User can assemble tests from item bank with sections
- [ ] **TEST-02**: User can define item selection rules and ordering
- [ ] **TEST-03**: User can set timing, navigation, and attempt limits

### Delivery

- [ ] **DELV-01**: Candidate can take assessment with timed, navigable interface
- [ ] **DELV-02**: Candidate can save progress and resume within session
- [ ] **DELV-03**: Server maintains authoritative timing even on client disconnect

### Scoring

- [ ] **SCR-01**: System scores response-based items automatically
- [ ] **SCR-02**: System supports custom scoring rules per item/test
- [ ] **SCR-03**: Scores are versioned and reproducible

### Reporting

- [ ] **REPT-01**: System generates candidate scorecard with breakdown
- [ ] **REPT-02**: System exports results to CSV format
- [ ] **REPT-03**: Scorecards link scores to evidence (item responses)

### Audit & Integrity

- [ ] **AUDT-01**: System records immutable audit log for each assessment attempt
- [ ] **AUDT-02**: System captures delivery events (start, answer, submit, terminate)
- [ ] **INTG-01**: System supports configurable lockdown/integrity controls
- [ ] **INTG-02**: Integrity events are logged with timestamps

### Integration

- [ ] **INTG-03**: System supports LTI 1.3 launch from LMS
- [ ] **INTG-04**: System sends grade passback via LTI Outcomes

## v2 Requirements

### Accessibility

- **ACCS-01**: System supports accessibility accommodations (extra time, alternative formats)
- **ACCS-02**: System respects PNP (personal needs and preferences) from LTI

### Adaptive Testing

- **ADPT-01**: System supports branching/adaptive item selection
- **ADPT-02**: System tracks item statistics for IRT calibration

### Advanced Integrity

- **INTG-05**: System captures behavioral signals during assessment
- **INTG-06**: System provides risk scoring for integrity review

### Analytics

- **ANLY-01**: System provides item performance analytics dashboard
- **ANLY-02**: System detects item bias/fairness issues

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time video proctoring | High privacy/cost concerns, defer to v2 with risk-based approach |
| Offline/low-bandwidth delivery | Significant platform investment, not core to v1 |
| Proprietary item format | QTI is the standard, avoid vendor lock-in |
| Fully automated pass/fail for high-stakes | Due-process risks, require human review for edge cases |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| IDEN-01 | Phase 1 | Pending |
| IDEN-02 | Phase 1 | Pending |
| IDEN-03 | Phase 1 | Pending |
| CONT-01 | Phase 1 | Pending |
| CONT-02 | Phase 1 | Pending |
| CONT-03 | Phase 1 | Pending |
| CONT-04 | Phase 1 | Pending |
| TEST-01 | Phase 2 | Pending |
| TEST-02 | Phase 2 | Pending |
| TEST-03 | Phase 2 | Pending |
| DELV-01 | Phase 2 | Pending |
| DELV-02 | Phase 2 | Pending |
| DELV-03 | Phase 2 | Pending |
| SCR-01 | Phase 3 | Pending |
| SCR-02 | Phase 3 | Pending |
| SCR-03 | Phase 3 | Pending |
| REPT-01 | Phase 3 | Pending |
| REPT-02 | Phase 3 | Pending |
| REPT-03 | Phase 3 | Pending |
| AUDT-01 | Phase 1 | Pending |
| AUDT-02 | Phase 1 | Pending |
| INTG-01 | Phase 2 | Pending |
| INTG-02 | Phase 2 | Pending |
| INTG-03 | Phase 3 | Pending |
| INTG-04 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-22*
*Last updated: 2026-02-22 after initial definition*
