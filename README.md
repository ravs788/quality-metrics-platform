# Quality Metrics Platform

A comprehensive engineering metrics and quality intelligence system designed to provide visibility into CICD pipelines, defect trends, test coverage, and overall engineering productivity.

## Overview

The Quality Metrics Platform is a production-ready system for tracking DORA metrics, defect patterns, and test coverage trends across engineering teams. Built with Python, FastAPI, PostgreSQL, and designed for Grafana dashboards.

**Key Features:**
- CICD pipeline metrics tracking (DORA metrics)
- Defect trend analysis and visualization
- Test coverage monitoring over time
- Engineering productivity dashboards
- RESTful API for data ingestion
- Pre-aggregated views for fast dashboards

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                  QUALITY METRICS PLATFORM                  │
└────────────────────────────────────────────────────────────┘

    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
    │   Grafana    │         │   FastAPI    │         │  PostgreSQL  │
    │  Dashboards  │ ◄─────► │     API      │ ◄─────► │   Database   │
    └──────────────┘         └──────────────┘         └──────────────┘
           │                        │                        │
           │                        │                        │
    ┌──────▼────────┐        ┌─────▼────────┐        ┌─────▼─────────┐
    │ DORA Metrics  │        │   Ingestion  │        │ 5 Tables      │
    │ Defect Trends │        │   Endpoints  │        │ 3 Views       │
    │ Coverage      │        │   Auth       │        │ 1M+ records   │
    └───────────────┘        └──────────────┘        └───────────────┘
```

## Project Structure

```
quality-metrics-platform/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── docker-compose.yml                 # Docker services configuration
├── .gitignore                        # Git ignore rules
│
├── src/                              # Application source code
│   ├── __init__.py
│   ├── main.py                       # FastAPI application entry point
│   ├── database.py                   # DB session/engine (lazy init via env)
│   ├── crud.py                       # Persistence + summary aggregation helpers
│   ├── models/
│   │   ├── schemas.py                # Pydantic request/response models
│   │   └── db_models.py              # SQLAlchemy ORM models
│   └── routers/
│       └── metrics.py                # API endpoints
│
├── database/                         # Database setup and seed data
│   ├── README.md                     # Database setup guide
│   ├── schema.sql                    # PostgreSQL schema (tables, views, indexes)
│   └── seed_data.py                  # Dummy data generator script
│
└── docs/                             # Documentation
    ├── architecture.md               # Repo architecture + implementation status
    └── quality-metrics-platform-architecture.md  # Platform architecture details
```

## Technology Stack

- **Backend:** Python 3.9+, FastAPI
- **Database:** PostgreSQL 14+
- **Visualization:** Grafana (planned)
- **Containerization:** Docker, Docker Compose
- **ORM:** SQLAlchemy
- **Data Generation:** Faker (for development/testing)

## Database Schema

### Tables

1. **teams** - Engineering teams using the platform
2. **projects** - Projects tracked in the metrics platform
3. **deployment_metrics** - CICD deployment metrics for DORA tracking
4. **defect_metrics** - Bug/defect tracking metrics
5. **coverage_metrics** - Test coverage metrics over time

### Views (Pre-aggregated for Performance)

1. **dora_metrics_summary** - Daily DORA metrics by project
2. **defect_trends_summary** - Weekly defect trends
3. **coverage_trends_summary** - Weekly test coverage trends

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.9+ (for local development)
- PostgreSQL client tools (optional, for direct DB access)

### 1. Start PostgreSQL

```bash
# Start PostgreSQL via Docker Compose
docker-compose up -d

# Verify PostgreSQL is running
docker ps | grep postgres-local
```

### 2. Set Up Database

```bash
# Create database
docker exec -it postgres-local psql -U postgres -c "CREATE DATABASE quality_metrics;"

# Create schema (tables, views, indexes)
docker exec -i postgres-local psql -U postgres -d quality_metrics < database/schema.sql
```

### 3. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Generate Dummy Data

```bash
# Populate database with realistic dummy data
python database/seed_data.py
```

Expected output:
```
Quality Metrics Platform - Dummy Data Generator
============================================================
✓ Connected to database
✓ Inserted 3 teams
✓ Inserted 6 projects
✓ Inserted 1529 deployment records
✓ Inserted 600 defect records
✓ Inserted 132 coverage records

============================================================
DATA SUMMARY
============================================================
Teams: 3
Projects: 6
Deployment records: 1529
Defect records: 600
Coverage records: 132
```

### 5. Configure Environment
Create a `.env` (not committed) based on `.env.example`:

```bash
cp .env.example .env
# edit DATABASE_URL as needed
```

### 6. Run FastAPI Application

```bash
# Start FastAPI development server
uvicorn src.main:app --reload

# API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Database Connection Details

- **Host:** localhost
- **Port:** 5432
- **Database:** quality_metrics
- **User:** postgres
- **Password:** mysecretpassword

## Dummy Data Overview

The seed data script (`database/seed_data.py`) generates:

- **3 teams:** Platform Engineering, Backend Services, Frontend Experience
- **6 projects:** API Gateway, User Service, Payment Service, Web Dashboard, Mobile App, Analytics Engine
- **1,529 deployment records:** 5 months of CICD data (85% success rate)
- **600 defect records:** Realistic priority distribution (70% resolved)
- **132 coverage records:** Weekly snapshots showing gradual improvement

## Sample Queries

### DORA Metrics (Last 30 Days)

```sql
SELECT 
    project_name,
    metric_date,
    successful_deployments,
    avg_lead_time_hours,
    change_failure_rate_percent
FROM dora_metrics_summary
WHERE metric_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY metric_date DESC, project_name;
```

### Defect Trends (Last 8 Weeks)

```sql
SELECT 
    week_start,
    SUM(defects_created) as total_created,
    SUM(high_priority_defects) as high_priority,
    AVG(avg_resolution_time_hours) as avg_resolution_hours
FROM defect_trends_summary
WHERE week_start >= CURRENT_DATE - INTERVAL '8 weeks'
GROUP BY week_start
ORDER BY week_start DESC;
```

### Coverage Trends

```sql
SELECT 
    project_name,
    week_start,
    avg_line_coverage,
    avg_branch_coverage
FROM coverage_trends_summary
WHERE week_start >= CURRENT_DATE - INTERVAL '12 weeks'
ORDER BY week_start DESC, project_name;
```

## Development Workflow

### Connect to Database

```bash
# Using Docker exec
docker exec -it postgres-local psql -U postgres -d quality_metrics

# Using psql directly
psql -h localhost -U postgres -d quality_metrics
```

### Useful psql Commands

```sql
\dt              -- List all tables
\dv              -- List all views
\d table_name    -- Describe table structure
\q               -- Exit psql
```

### Reset Database

```bash
# Drop and recreate database
docker exec -it postgres-local psql -U postgres -c "DROP DATABASE IF EXISTS quality_metrics;"
docker exec -it postgres-local psql -U postgres -c "CREATE DATABASE quality_metrics;"

# Recreate schema and data
docker exec -i postgres-local psql -U postgres -d quality_metrics < database/schema.sql
python database/seed_data.py
```

## Testing and Coverage

### Run Unit Tests
```bash
pytest
```

### Run with Coverage (writes files)
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html:coverage_html --cov-report=xml:coverage.xml --cov-report=json:coverage.json
```

Coverage outputs:
- `coverage_html/` (HTML)
- `coverage.xml`
- `coverage.json`

### Current Coverage (latest local run)
From `pytest --cov=src`:

| Module | Coverage | Notes |
|---|---:|---|
| **TOTAL** | **99%** | Overall |
| `src/crud.py` | 99% | 1 line missed |
| `src/database.py` | 100% | Fully covered (lazy engine/session init + error paths tested) |
| `src/main.py` | 82% | Misses `if __name__ == "__main__"` block |
| `src/models/db_models.py` | 100% | ORM models covered via CRUD/API tests |
| `src/models/schemas.py` | 100% | Schemas covered via API payload validation |
| `src/routers/metrics.py` | 100% | All endpoints covered |

Note: coverage numbers can vary slightly depending on how tests are executed and which modules are imported during collection.

### VSCode Testing Tab (Pytest Discovery)
If discovery fails:
1. Command Palette → **Python: Select Interpreter** → choose the project virtualenv.
2. Command Palette → **Python: Configure Tests** → pytest → `tests`
3. Testing tab → Refresh

## API Endpoints

### Health Check
- `GET /health` - API health status

### Metrics Ingestion
- `POST /api/v1/deployments` - Ingest deployment metrics
- `POST /api/v1/defects` - Ingest defect data
- `POST /api/v1/coverage` - Ingest coverage metrics

### Metrics Retrieval
- `GET /api/v1/dora-metrics` - Get DORA metrics summary
- `GET /api/v1/defect-trends` - Get defect trend analysis
- `GET /api/v1/coverage-trends` - Get coverage trends

## Roadmap

### Phase 1: Foundation (Current - March 2026)
- [x] Database schema design
- [x] Seed data generation
- [x] Docker Compose setup
- [x] FastAPI application skeleton
- [x] Basic API endpoints
- [x] Unit tests + coverage reporting

### Phase 2: Data Ingestion (April-May 2026)
- [ ] CICD integration (Jenkins/GitHub Actions)
- [ ] Defect tracking integration (Jira/GitHub Issues)
- [ ] Coverage integration (SonarQube/Codecov)
- [ ] Background job processing

### Phase 3: Visualization (May-June 2026)
- [ ] Grafana setup
- [ ] DORA metrics dashboard
- [ ] Defect trends dashboard
- [ ] Coverage dashboard
- [ ] Alerting configuration

### Phase 4: Production (June 2026)
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Production deployment
- [ ] Team onboarding (3+ teams)

## Success Criteria

### Technical
- ✓ Handles 1M+ data points
- ✓ API response time < 200ms (p95)
- ✓ 99.9% uptime
- ✓ Test coverage > 80%

### Business
- ✓ 3+ internal teams using
- ✓ Daily active users > 20
- ✓ All DORA metrics tracked
- ✓ 20% reduction in metrics reporting time

## Documentation

- [Repository Architecture](docs/architecture.md) - Repo architecture + current implementation status
- [Platform Architecture](docs/quality-metrics-platform-architecture.md) - Detailed platform design, features, and milestones
- [Database Setup](database/README.md) - Complete database setup guide
- [Activity Log](activity-log.md) - High-level milestone log

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is part of a learning initiative for Principal Engineer track development.

## Contact

For questions or feedback, please refer to the project documentation or open an issue.

---

**Last Updated:** March 17, 2026  
**Status:** Phase 1 - Foundation (In Progress)  
**Version:** 0.1.0
