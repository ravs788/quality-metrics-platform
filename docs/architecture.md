# Quality Metrics Platform Architecture
## Scope
This document describes only the architecture of the `quality-metrics-platform` repository.

## Component Overview
- **API Layer**: FastAPI application (`src/main.py`) exposing health check and metric routers.
- **Routers**: Metric ingestion and retrieval endpoints (`src/routers/metrics.py`).
- **Models**: 
  - Pydantic schemas for request/response validation (`src/models/schemas.py`)
  - SQLAlchemy ORM models for database mapping (`src/models/db_models.py`)
- **Database Layer**: 
  - Connection management and session factory (`src/database.py`)
  - Repository layer for teams, projects, and metric persistence (`src/repositories/`)
  - Service layer for business/aggregation logic (`src/services/`)
  - PostgreSQL (via `docker-compose.yml`) with schema in `database/schema.sql` and seed scripts in `database/seed_data.py`
- **Configuration**: Environment-based configuration via `.env` file (template in `.env.example`)
- **Docs**: Additional architecture notes in `docs/quality-metrics-platform-architecture.md`.

## High-level Architecture
```
┌─────────────────────┐
│   Clients / CI      │
└─────────▲───────────┘
          │  HTTP (JSON)
┌─────────▼───────────┐
│   FastAPI Service   │
│   (src/main.py)     │
└─────────▲───────────┘
          │  SQL
┌─────────▼───────────┐
│   PostgreSQL DB     │
│ (docker-compose)    │
└─────────────────────┘
```

## Request Flow
1. Clients POST metric data to the API endpoints (see `src/routers/metrics.py`).
2. FastAPI validates payloads via Pydantic models (`src/models/schemas.py`).
3. Router handlers inject database sessions via dependency injection (`get_db`).
4. Repository/service flow handles:
   - Auto-creation of teams and projects if they don't exist
   - Insertion of metrics into respective tables
   - Querying of aggregated views for analytics
5. The service persists and queries data in PostgreSQL using SQLAlchemy ORM.
6. Aggregated metrics are retrieved from database views (DORA metrics, defect trends, coverage trends).

## Implementation Status
### Completed (Phase 1)
- ✓ Database schema with tables and views
- ✓ Database connection and session management
  - Lazy `DATABASE_URL` validation (prevents tool/test discovery crashes when env is unset)
- ✓ SQLAlchemy ORM models
- ✓ Pydantic request/response schemas
- ✓ Repository + service operations for all metric types
- ✓ API endpoints:
  - POST `/api/v1/deployments` - Ingest deployment metrics
  - POST `/api/v1/defects` - Ingest defect metrics
  - POST `/api/v1/coverage` - Ingest coverage metrics
  - GET `/api/v1/dora-metrics` - Retrieve DORA metrics summary
  - GET `/api/v1/defect-trends` - Retrieve defect trends
  - GET `/api/v1/coverage-trends` - Retrieve coverage trends
  - GET `/health` - Health check endpoint
- ✓ Auto-creation of teams and projects on metric ingestion
- ✓ Environment-based configuration
- ✓ Automated tests and coverage reporting
  - Endpoint tests per route + database module tests
  - Coverage reports written to `coverage_html/`, `coverage.xml`, `coverage.json`
- ✓ Cross-database aggregation for summary endpoints (SQLite tests + PostgreSQL runtime)
  - DORA metrics aggregated via ORM
  - Defect/Coverage trends aggregated in Python (week buckets)
- ✓ Layered test architecture implemented
  - `tests/unit`, `tests/component`, `tests/integration`, `tests/e2e`
- ✓ CRUD module retired (`src/crud.py` removed)
- ✓ VSCode pytest discovery compatibility
  - `tests/conftest.py` ensures repo root is on `sys.path`

### Pending (Future Phases)
- Authentication and authorization
- API versioning and deprecation strategy
- Rate limiting and quotas
- Batch ingestion endpoints
- Data validation rules and constraints
- Visualization dashboard
- Export functionality
- Monitoring and alerting

## Out of Scope
- Personal career plans, learning roadmaps, and non-repository project portfolios.
- Architectures for unrelated projects.

## Change Log
| Date | Version | Changes |
|------|---------|------------|
| 2026-03-26 | 3.2 | Updated docs for service/repository architecture and layered test suite; removed `src/crud.py` references. |
| 2026-03-20 | 3.1 | Added comprehensive test suite + coverage reporting; improved cross-DB behavior for summary endpoints; fixed VSCode pytest discovery. |
| 2026-03-18 | 3.0 | Implemented basic API endpoints with database integration. Added CRUD layer, ORM models, and all core endpoints. |
| 2026-03-17 | 2.1 | Removed remaining non-project sections; document now covers only this repository. |
