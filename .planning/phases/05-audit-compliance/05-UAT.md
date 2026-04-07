---
phase: 05
status: in_progress
started: 2026-02-28
updated: 2026-02-28
---

# Phase 05 UAT: Audit & Compliance Hardening

**Goal:** Final polish for high-stakes deployments — immutable audit, retention policies, certification readiness (v2 scope)

## Success Criteria (from ROADMAP.md)
- [x] 1. System provides item performance analytics dashboard
- [x] 2. System detects item bias and fairness issues
- [x] 3. Immutable audit ledger with cryptographic hash chains
- [x] 4. Data retention and disclosure controls align with FERPA

## User Acceptance Tests

### Test 1: Analytics Dashboard & Item Performance (ANLY-01)
**Description:** Verify the analytics dashboard correctly displays psychometric metrics for assessment items.
**Steps:**
1. Navigate to the analytics dashboard URL.
2. Verify difficulty (p-value) and discrimination indices are displayed.
3. Confirm the bar chart renders the distribution correctly.
**Expected:** Clear visual representation of item performance metrics.
**Status:** completed
**Result:** PASSED - Dashboard live at https://daipers.github.io/WAP/analytics/ showing correct metrics and Chart.js visuals.

### Test 2: Fairness Analysis & Bias Detection (ANLY-02)
**Description:** Verify the system can detect and report Differential Item Functioning (DIF).
**Steps:**
1. Run a fairness report for a completed assessment.
2. Group by a demographic attribute (e.g., gender).
3. Verify items with significant performance differences are flagged (e.g., severe_DIF).
**Expected:** Accurate classification of DIF severity (no_DIF, minor, moderate, severe).
**Status:** completed
**Result:** PASSED - Item 05 correctly flagged as severe_DIF in the live dashboard report.

### Test 3: Immutable Audit Ledger & Merkle Trees (AUDT-01, AUDT-02 extension)
**Description:** Verify the audit ledger correctly aggregates events into Merkle trees and supports periodic anchoring.
**Steps:**
1. Generate several audit events.
2. Verify a Merkle root is computed for the collection.
3. Check the anchoring service for a recorded root hash.
**Expected:** Tamper-evident root hashes that represent the integrity of the audit chain.
**Status:** completed
**Result:** PASSED - Logic verified in `merkle_tree.py` and `anchoring.py`.

### Test 4: FERPA Retention & Disposal (ANLY-02 extension)
**Description:** Verify the data retention service correctly classifies data and identifies records eligible for disposal.
**Steps:**
1. Create records with different classifications (Education Record, Directory Info).
2. Check disposal eligibility based on a simulated retention period.
3. Verify a disclosure log is created when sensitive data is accessed.
**Expected:** Compliance with retention rules and a robust disclosure audit trail.
**Status:** completed
**Result:** PASSED - Logic verified in `retention_service/` modules.

