# Research Summary: WAA-ADS Milestone v2.0

**Domain:** Institutional Production Readiness & Intelligent Growth
**Researched:** February 27, 2026
**Overall confidence:** HIGH

## Executive Summary

Milestone v2.0 transforms WAA-ADS from a functional demo into a production-hardened assessment platform capable of institutional deployment and automated growth. The research covers three critical pillars: **Production Hardening** (Security/Scaling), **Intelligent Assessment** (AIG/CAT), and **Candidate Acquisition** (Wizards Apprentice Agent).

For production, we move to a highly available FastAPI stack on Kubernetes, securing student PII with application-layer encryption (pgcrypto) and comprehensive auditing (pgAudit) to meet FERPA/GDPR standards. Accessibility is elevated to WCAG 2.2 through advanced ARIA patterns for complex QTI 3.0 interactions.

The intelligence layer introduces **Computer Adaptive Testing (CAT)** using the 3-Parameter Logistic (3PL) IRT model for precise ability estimation, alongside **Automated Item Generation (AIG)** powered by Claude 3.5. This allows for dynamic, overexposure-resistant item banks that scale with candidate volume.

Finally, the **Wizards Apprentice Agent** provides an automated growth loop, discovering potential candidates on platforms like LinkedIn and GitHub via HeroHunt.ai/Firecrawl and initiating personalized outreach that feeds directly into the WAA-ADS assessment pipeline.

## Key Findings

- **Discovery Engine**: **HeroHunt.ai** is the superior discovery hub for 2026, aggregating LinkedIn/GitHub/StackOverflow via a stable API.
- **Adaptive Engine**: **3PL IRT** with **Maximum Fisher Information (MFI)** selection and **Expected A Posteriori (EAP)** estimation is the gold standard for live adaptive testing.
- **Security**: Application-layer encryption (pgcrypto) is required to supplement disk encryption for true multi-tenant PII security in high-stakes environments.
- **Accessibility**: WCAG 2.2 compliance for QTI 3.0 requires "Grab-and-Place" keyboard patterns and 24px minimum touch targets.

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Phase 06: Production Infrastructure & Security** - Establishing the HA K8s stack and PII security protocols.
2. **Phase 07: Adaptive Engine (CAT)** - Implementing the 3PL IRT logic and live adaptive delivery.
3. **Phase 08: AI Item Generation (AIG)** - Deploying the LLM-based generation and calibration seeding pipeline.
4. **Phase 09: Wizards Apprentice Agent** - Building the social discovery and outreach automation engine.
5. **Phase 10: Institutional Hardening (WCAG 2.2)** - Final accessibility audit and performance optimization for scale.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Market-leading tools (HeroHunt, FastAPI, 3PL IRT) are well-validated. |
| Features | HIGH | AIG/CAT and AI-SDR patterns are production-ready in 2026. |
| Architecture | HIGH | Standard decoupled service patterns fit the existing WAA-ADS structure. |
| Pitfalls | HIGH | Risks (GDPR, LinkedIn bans, LLM difficulty bias) are well-documented. |

## Gaps to Address

- **Bias Detection**: Need specialized LLM prompts for S&B review of generated content.
- **Offline Resilience**: Service Worker strategies for mid-exam disconnects in high-stakes environments.
- **Identity Collision**: Logic for merging social identities with official assessment records.
