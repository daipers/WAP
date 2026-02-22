# Technology Stack

**Domain:** Automated Assessment Delivery System (WAA-ADS)
**Researched:** February 22, 2026
**Confidence:** HIGH

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | 0.115+ | Web framework | Async-first, native OpenAPI/Swagger, automatic Pydantic validation. Dominates 2025/2026 Python web development for API-heavy workloads. Pairs naturally with async SQLAlchemy. |
| Uvicorn | 0.32+ | ASGI server | Production-ready ASGI server, recommended by FastAPI. Use `uvicorn[standard]` for auto-reload in development. |
| Python | 3.11+ | Runtime | Required for latest FastAPI async features. 3.12 offers ~10-25% performance gains over 3.11. |

**Sources:**
- Context7: FastAPI async best practices verified
- WebSearch: Multiple 2025/2026 comparison articles confirm FastAPI as default choice for async APIs

### Database

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| PostgreSQL | 16+ | Primary database | Standard for relational data. JSON support for flexible content storage. Strong ACID compliance needed for assessment integrity. |
| SQLAlchemy | 2.0+ | ORM | The 2025 standard for Python ORMs. Async support via `sqlalchemy[asyncio]`. Type-safe with `Mapped[]` syntax. |
| asyncpg | 0.30+ | PostgreSQL driver | Fast async driver, ~3x faster than psycopg2 for async workloads. Use `postgresql+asyncpg://` |
| Alembic | 1.14+ | Migrations | Official SQLAlchemy migration tool. Required for production schema evolution. |

**Sources:**
- Context7: SQLAlchemy 2.0 async patterns verified
- WebSearch: PostgreSQL 16 features, asyncpg benchmarks

### Authentication & Sessions

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| python-jose | 3.3+ | JWT handling | Full JWT spec support, RS256/HS256, recommended for FastAPI. Use `python-jose[cryptography]` for full algorithm support. |
| passlib | 1.7+ | Password hashing | Industry standard. Use `passlib[bcrypt]` for bcrypt hashing (NIST recommended). |
| OAuth2PasswordBearer | built-in | Token extraction | FastAPI built-in for Bearer token extraction from Authorization header. |
| Redis | 7.4+ | Session storage | For distributed session state. Use `redis-py` with async support. |

**Sources:**
- IETF draft-sheffer-oauth-rfc8725bis (JWT Best Current Practices)
- WebSearch: JWT implementation patterns for FastAPI 2025

### Task Orchestration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Celery | 5.5+ | Background tasks | De facto standard for Python async tasks. Used by Instagram, Pinterest, GitLab. Redis broker recommended for most workloads. |
| Redis | 7.4+ | Message broker | Faster than RabbitMQ for most use cases. Use as both broker AND result backend initially. |
| celery-redbeat | 2.0+ | Celery Beat scheduler | If you need scheduled tasks (assessment timeouts, cleanup). Better than cron + Celery. |

**Sources:**
- Deepnote: "Celery is on version 5.5.3 (codename Immunity)" - 2025
- WebSearch: Production Celery patterns, Celery + Redis + FastAPI 2025 guides
- Official docs: Celery broker/worker patterns verified

### State Machine (Assessment Workflow)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| python-statemachine | 2.5+ | Workflow state | Pythonic API, async support, Django integration optional. Clean definition of states, events, transitions. Supports diagram generation. |
| Transitions | 0.9+ | Alternative | More flexible, broader Python version support. Good for complex conditional logic. |

**Sources:**
- GitHub: fgmacedo/python-statemachine (1.2k stars, active)
- PyPI: Version 2.5.0 released June 2024

### Content & Media Storage

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| boto3 | 1.35+ | S3 SDK | AWS SDK for Python. Use for content bank storage (questions, media files, submissions). |
| aiobotocore | 2.15+ | Async S3 | If content operations need async. Otherwise sync boto3 in Celery tasks is acceptable. |
| MinIO | latest | Local S3 | For development/testing. S3-compatible, runs locally via Docker. |

**Sources:**
- AWS boto3 documentation (official)
- WebSearch: Python S3 best practices 2025

### Feature Extraction & ML

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| scikit-learn | 1.6+ | ML framework | Standard for tabular feature extraction, scoring models. TF-IDF, text classification, regression. |
| transformers | 4.46+ | NLP models | Hugging Face. For advanced text understanding, semantic similarity, automated scoring. |
| pandas | 2.2+ | Data processing | Data manipulation, feature engineering. |
| numpy | 2.1+ | Numerical ops | Required by scikit-learn, pandas. |

**Sources:**
- Official: scikit-learn.org (feature_extraction module)
- WebSearch: NLP with transformers 2025 patterns

### Scoring Engine

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Custom Python | - | Rubric scoring | Implement rubric-based scoring as domain logic. Celery tasks for async processing. |
| numpy/pandas | - | Statistical scoring | For score normalization, weighted aggregations, statistical analysis. |

### Integrity & Proctoring

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| OpenCV | 4.10+ | Image processing | For video frame analysis, face detection. |
| MediaPipe | latest | Pose/face detection | Google's library. Lightweight, real-time face/pose for proctoring. |
| PyYAML | 6.0+ | Config | For rubric and integrity rule definitions. |

**Sources:**
- GitHub: Multiple proctoring projects (Examify, exam-cheating-detection) use OpenCV + MediaPipe
- WebSearch: Online proctoring AI libraries 2025

### Reporting

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| ReportLab | 4.2+ | PDF generation | Industry standard. Used by banks for automated reports. Full programmatic control over PDF layout. |
| Jinja2 | 3.1+ | Templating | For HTML report templates (can convert to PDF via other tools). |
| matplotlib | 3.9+ | Charts | For scorecard visualizations. |

**Sources:**
- Official: docs.reportlab.com (version 4.2.2)
- WebSearch: ReportLab vs alternatives 2025

### Audit & Logging

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python logging | built-in | Core logging | Standard library. Configure structured JSON logging for audit trails. |
| structlog | 24.4+ | Structured logging | JSON logging, better than plain logging for audit. |
| hashlib | built-in | Cryptographic hashing | For hash chains in audit logs (SHA-256). |
| OpenTelemetry | 1.26+ | Observability | Standard for distributed tracing. Integrates with audit trail. |

**Sources:**
- WebSearch: Immutable audit log patterns 2025
- Official: OpenTelemetry Python SDK

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.10+ | Data validation | Required for FastAPI. Use for request/response schemas. |
| Pydantic Settings | 2.6+ | Configuration | Type-safe settings from env vars. |
| httpx | 0.28+ | HTTP client | Async HTTP client for external API calls. Better than requests for async code. |
| python-multipart | 0.0+ | Form parsing | Required for OAuth2 password flow form handling. |
| pytest | 8.3+ | Testing | Standard Python testing. |
| pytest-asyncio | 0.25+ | Async testing | For testing async FastAPI routes. |
| faker | 33+ | Fake data | For generating test data, demos. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Docker | Containerization | For reproducible dev environments, Celery workers |
| Docker Compose | Local orchestration | Run PostgreSQL, Redis, app together |
| Poetry | Dependency management | Better than pip for lock files, virtual envs |
| black | Code formatting | Python formatter (use `--check` in CI) |
| ruff | Linting | 10-100x faster than flake8 |
| mypy | Type checking | Catch type errors before runtime |

## Installation

```bash
# Core
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic
pip install pydantic pydantic-settings

# Auth
pip install "python-jose[cryptography]" passlib[bcrypt] python-multipart

# Task Queue
pip install celery redis

# State Machine
pip install python-statemachine

# Storage
pip install boto3 aiobotocore

# ML/Feature Extraction
pip install scikit-learn pandas numpy transformers

# Integrity/Proctoring
pip install opencv-python mediapipe pyyaml

# Reporting
pip install reportlab jinja2 matplotlib

# Audit/Logging
pip install structlog opentelemetry-api opentelemetry-sdk

# HTTP/Testing
pip install httpx pytest pytest-asyncio faker

# Dev tools
pip install black ruff mypy docker-compose
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Web Framework | FastAPI | Django | Django is monolithic, slower for async. Use only if you need built-in admin, ORM, auth (but you're building custom auth). |
| Web Framework | FastAPI | Flask | Flask requires more boilerplate for async. No automatic OpenAPI. |
| Database | PostgreSQL | SQLite | SQLite doesn't scale, no proper concurrent writes, unsuitable for production assessments. |
| Database | PostgreSQL | MySQL | PostgreSQL has better JSON support, more mature CTE support, better for complex scoring queries. |
| Task Queue | Celery | Redis Queue (RQ) | RQ simpler but less features. Celery has better monitoring (Flower), retry policies, task routing. |
| Task Queue | Celery | Dramatiq | Newer but smaller ecosystem. Celery has 15+ years of production hardening. |
| ORM | SQLAlchemy 2.0 | Django ORM | Django ORM tied to Django. SQLAlchemy 2.0 is async-native and framework-agnostic. |
| State Machine | python-statemachine | Transitions | python-statemachine has cleaner Pythonic API, but transitions offers more callbacks. Either works. |
| PDF | ReportLab | PDFKit/wkhtmltopdf | wkhtmltopdf requires external binary, harder to containerize. ReportLab is pure Python. |
| ML | scikit-learn | XGBoost | XGBoost is for tabular. scikit-learn has broader feature extraction, text processing. Use together for ensemble scoring. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Flask-SocketIO | Legacy, synchronous design | FastAPI with websockets (native) |
| Django | Monolithic, overkill for API service | FastAPI (or Django only if you need admin) |
| Celery with RabbitMQ (default) | More complex setup, slower than Redis for most cases | Celery with Redis broker |
| psycopg2 (sync) | Blocks event loop | asyncpg (async) |
| pickle serialization (Celery) | Security risk | JSON serialization |
| PyJWT | Less maintained than python-jose | python-jose |
| XML config for rubrics | Hard to version, parse | YAML or JSON |
| Local file storage | Doesn't scale, no audit trail | S3 with versioning |

## Stack Patterns by Variant

**If building primarily REST API with background workers:**
- FastAPI + SQLAlchemy async + Celery + Redis
- Stateless API, workers process scoring/integrity

**If building real-time proctoring:**
- FastAPI + WebSockets + Redis Pub/Sub
- MediaPipe/OpenCV in separate worker processes

**If scoring requires ML models:**
- Celery workers with scikit-learn/transformers
- Model caching in worker memory

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| FastAPI 0.115+ | SQLAlchemy 2.0+, Pydantic 2.5+ | Use async session makers |
| SQLAlchemy 2.0+ | asyncpg 0.30+, psycopg 3.0+ | Use async engines |
| Celery 5.5+ | Redis 7.x, python 3.11+ | Use JSON serializer |
| python-statemachine 2.5+ | Python 3.8+ | Async support in 2.x |
| ReportLab 4.x | Python 3.8+ | Check commercial license for RML |

## Sources

- **Context7:** FastAPI JWT auth patterns, SQLAlchemy 2.0 async sessions
- **Codesearch:** FastAPI + Celery + Redis integration patterns
- **IETF draft-sheffer-oauth-rfc8725bis:** JWT Best Current Practices (January 2026)
- **WebSearch:** Django vs FastAPI vs Flask 2025/2026 comparisons
- **Deepnote:** "Celery is on version 5.5.3 (codename Immunity)" - August 2025
- **GitHub:** fgmacedo/python-statemachine (1.2k stars, active maintenance)
- **docs.reportlab.com:** Version 4.2.2 documentation
- **AWS boto3 docs:** S3 Python SDK documentation

---

*Stack research for: WAA-ADS (Automated Assessment Delivery System)*
*Researched: February 22, 2026*
