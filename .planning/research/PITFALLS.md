# Domain Pitfalls: WAA-ADS Milestone v2.0

**Domain:** Assessment Operations
**Researched:** February 27, 2026

## Critical Pitfalls

### Pitfall 1: Calibration Cold-Start (AIG)
**What goes wrong:** AI-generated items lack psychometric parameters ($a, b, c$). Using them in an adaptive engine without calibration leads to invalid ability scores.
**Prevention:** Implement "Experimental Seeding". Mix uncalibrated items into live tests without scoring them. Use LLM "Proxy Calibration" for initial values, but weight them low.

### Pitfall 2: PII Leakage in Logs
**What goes wrong:** Fast-moving dev teams often log request/response bodies that contain student emails or scores.
**Prevention:** Mandatory PII masking in logging middleware. Use `pgAudit` to track who accessed sensitive rows rather than what the data was.

### Pitfall 3: Platform Bans (Sourcing Agent)
**What goes wrong:** Automated social media outreach (LinkedIn/X) triggers anti-spam mechanisms, resulting in permanent account bans.
**Prevention:** **Do not scrape.** Use HeroHunt.ai or similar API-first profile providers. Use "warm-up" services for email domains before starting large outreach campaigns.

## Moderate Pitfalls

### Pitfall 1: QTI Schema Drift
**What goes wrong:** LLMs mix QTI 2.1 and 3.0 tags, causing rendering failures in the delivery engine.
**Prevention:** Mandatory XSD validation in the AIG service pipeline. Reject non-compliant XML immediately.

### Pitfall 2: WebSocket State Fragmentation
**What goes wrong:** In a load-balanced K8s environment, a client's WebSocket may reconnect to a different pod that doesn't have their session state.
**Prevention:** Use **Sticky Sessions** (Session Affinity) in the Ingress controller and Redis for shared session state.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| **Hardening** | Migration Downtime | Blue/Green deployment for DB schema changes. |
| **Adaptive** | Infinite Testing | Add "Max Items" and "Max Time" hard stops to CAT sessions. |
| **AIG** | Semantic Redundancy | Use vector similarity checks to ensure generated items are unique. |
| **Growth** | GDPR Fines | Include mandatory "Right to be forgotten" links in every outreach email. |
