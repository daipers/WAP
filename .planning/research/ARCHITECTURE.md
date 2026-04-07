# Architecture Patterns: WAA-ADS Milestone v2.0

**Domain:** Institutional Production Readiness & Intelligent Growth
**Researched:** February 27, 2026

## Recommended Architecture

A multi-service architecture that extends the v1.0 foundations with specialized intelligence and growth components.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **Wizards Agent** | Sourcing candidates from social media/web. | Identity Service, HeroHunt API, Instantly API |
| **AIG Service** | Orchestrating LLM-based item generation. | Item Bank, Claude 3.5 API |
| **CAT Engine** | Live psychometric next-item selection. | Delivery Engine, Redis (state) |
| **Production Infra** | Load balanced API, secure DB, task queue. | All Services, K8s Ingress |

### Data Flow (Intelligent Growth Loop)

1. **Growth**: Wizards Agent discovers candidate -> Outreach sent -> Candidate clicks link -> Account auto-created in Identity Service.
2. **Adaptive Prep**: Candidate starts Assessment -> Orchestrator initializes CAT Engine (Theta=0).
3. **Adaptive Loop**: CAT Engine selects optimal item -> Delivery Engine renders (WCAG 2.2) -> Candidate responds -> CAT Engine updates Theta via EAP.
4. **Closing the Loop**: Responses stored in Audit Ledger -> Periodic IRT calibration updates Item Bank parameters.

## Patterns to Follow

### Pattern 1: Multi-Layered PII Security
Combine disk-level encryption with application-level column encryption (`pgcrypto`) for sensitive fields (email, names, score details).

### Pattern 2: Bayesian EAP Estimation
Use quadrature-based EAP for ability estimation to ensure stability during the first 10 items of an adaptive test.

### Pattern 3: API-Buffered Sourcing
Use aggregator APIs (HeroHunt) instead of direct social media scraping to prevent platform bans and ensure GDPR-compliant data handling.

## Anti-Patterns to Avoid

### Anti-Pattern: Client-Side Scoring/Selection
Never expose the adaptive selection logic or item IRT parameters to the browser. All selection must be server-authoritative.

### Anti-Pattern: Raw XML Generation
LLMs should generate JSON structures, which are then converted to QTI 3.0 XML via a strict validation schema.

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| **DB Performance**| Standard RDS | Read Replicas; pgcrypto indexing | Sharded clusters; pre-aggregated metrics |
| **CAT Latency** | Direct Math | Cached IRF curves in Redis | Specialized C++ estimation service |
| **Agent Outreach**| Manual trigger | Automated sequences (Instantly) | Multi-domain rotation; AI triage |
