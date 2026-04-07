# Technology Stack: WAA-ADS Milestone v2.0

**Project:** WAA-ADS
**Researched:** February 27, 2026

## Recommended Stack

### Core Infrastructure (Hardening)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI | 0.115+ | API Framework | High performance, async, production-mature. |
| PostgreSQL | 16.x | Main Database | Relational integrity, JSONB support for QTI. |
| pgcrypto | Extension | PII Encryption | Application-layer encryption for FERPA/GDPR. |
| pgAudit | Extension | Compliance Logging | Legally defensible audit trail of data access. |
| Redis | 7.x | Task Broker / State | High-speed brokering for Celery and WebSocket state. |
| Kubernetes | 1.30+ | Orchestration | Scalable deployment with sticky sessions for WebSockets. |

### Intelligence Layer (AIG/CAT)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Claude 3.5 Sonnet | Latest | AIG Engine | Superior structured output (XML/JSON) and reasoning. |
| IRT-3PL | Algorithm | Adaptive Logic | Standard for ability estimation and item selection. |
| MFI / EAP | Methodology | Next-Item / Ability | Optimal balance of precision and stability. |

### Sourcing Agent (Wizards Apprentice)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| HeroHunt.ai | API | Discovery | Aggregates 1B+ profiles across LinkedIn/GitHub/StackOverflow. |
| Firecrawl | Latest | Web Scraping | High-performance scraping for profile enrichment. |
| Instantly.ai | API | Outreach | Sophisticated cold email rotation and warm-up. |

## Installation (Additions)

```bash
# Production dependencies
pip install sqlalchemy[postgresql] cryptography redis celery

# AI & Data dependencies
pip install anthropic pandas numpy scipy statsmodels

# Discovery dependencies
# (Custom SDKs for HeroHunt/Instantly as needed)
```
