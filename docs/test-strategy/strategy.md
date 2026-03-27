# Quality Metrics Platform - Test Strategy

**Version:** 1.1  
**Last Updated:** March 27, 2026  
**Status:** Active

---

## Table of Contents

1. [Overview](#overview)
2. [Testing Pyramid](#testing-pyramid)
3. [Test Levels](#test-levels)
4. [Test Organization](#test-organization)
5. [API Testing Strategy](#api-testing-strategy)
6. [Test Data Management](#test-data-management)
7. [Testing Standards](#testing-standards)
8. [Tools & Frameworks](#tools--frameworks)
9. [CI/CD Integration](#cicd-integration)
10. [Coverage & Quality Metrics](#coverage--quality-metrics)

---

## Overview

### Current Execution Snapshot (March 27, 2026)
- Total tests: **106**
- Unit: **36**
- Component: **40**
- Integration (API + code): **17 + 11**
- E2E: **2**
- Coverage (`src/`): **100%** (563 statements, 0 missed)

### Purpose
This document defines the comprehensive testing strategy for the Quality Metrics Platform, an API-driven system for tracking DORA metrics, defect trends, and test coverage across engineering teams.

### Testing Goals
- **Reliability:** Ensure 99.9% uptime through comprehensive test coverage
- **Performance:** Validate API response times < 200ms (p95)
- **Correctness:** Verify metric calculations and aggregations are accurate
- **Maintainability:** Create tests that are easy to understand and maintain
- **Confidence:** Enable safe refactoring and feature development

### Scope
- FastAPI REST endpoints
- Database operations and aggregations
- Business logic in CRUD layer
- Data validation and schema enforcement
- API workflows and chained operations
- Performance characteristics

---

## Testing Pyramid

```
                    ┌─────────────┐
                    │     E2E     │  <- ~2%
                    │  (2 tests)  │
                    └─────────────┘
               ┌───────────────────────┐
               │    Integration        │  <- ~26%
               │  (28 tests)           │
               │ • API Flows           │
               │ • Code Integration    │
               └───────────────────────┘
          ┌─────────────────────────────────┐
          │        Component                │  <- ~40%
          │     (40 tests)                  │
          │  • Endpoint Tests               │
          │  • Router Logic                 │
          └─────────────────────────────────┘
     ┌──────────────────────────────────────────┐
     │            Unit                          │  <- ~34%
     │       (36 tests)                         │
     │  • Services/Dependencies/Main branches   │
     │  • Validators                            │
     │  • Utilities                             │
     └──────────────────────────────────────────┘
```

### Distribution Rationale
- **Unit (~34%):** Expanded to cover service/dependency/main control-flow branches for faster feedback.
- **Component (~40%):** Primary API endpoint confidence layer.
- **Integration (~26%):** Strong API-flow and DB integration safety net.
- **E2E (~2%):** Minimal but focused on critical full-system scenarios.

---

## Test Levels

### 1. Unit Tests

**Definition:** Test individual functions/methods in isolation with mocked dependencies.

**Characteristics:**
- Fast execution (< 1ms per test)
- No external dependencies (database, network, filesystem)
- Focused on single responsibility
- Use mocks/stubs for dependencies

**Examples:**
```python
# test_crud_unit.py
def test_calculate_change_failure_rate():
    """Unit test for failure rate calculation."""
    result = calculate_failure_rate(
        successful=85,
        failed=15
    )
    assert result == 15.0  # 15% failure rate

def test_validate_metric_date_format():
    """Unit test for date validation."""
    assert is_valid_date("2026-03-25") is True
    assert is_valid_date("25-03-2026") is False
```

**Coverage Target:** 95%+ for pure business logic

---

### 2. Component Tests

**Definition:** Test API endpoints with test doubles (in-memory database, mocked external services).

**Characteristics:**
- Test single API endpoint behavior
- Use FastAPI TestClient
- SQLite in-memory database
- No external service calls
- Fast execution (< 100ms per test)

**Examples:**
```python
# test_deployment_endpoint.py
def test_create_deployment_success(client: TestClient):
    """Component test for deployment creation."""
    payload = {
        "project_name": "API Gateway",
        "successful": True,
        "lead_time_hours": 2.5
    }
    
    response = client.post("/api/v1/deployments", json=payload)
    
    assert response.status_code == 201
    assert response.json()["project_name"] == "API Gateway"
    assert "id" in response.json()

def test_deployment_validation_error(client: TestClient):
    """Test validation error handling."""
    response = client.post("/api/v1/deployments", json={})
    assert response.status_code == 422
```

**Coverage Target:** 100% of endpoints, all happy paths + validation errors

---

### 3. Integration Tests

#### 3a. Code-Level Integration

**Definition:** Test multiple modules working together with real dependencies.

**Characteristics:**
- Test interactions between layers (API → CRUD → Database)
- Use real PostgreSQL database (via Docker)
- Test database views and aggregations
- Slower execution (< 1s per test)

**Examples:**
```python
# test_crud_db_integration.py
def test_team_project_creation_workflow(postgres_db: Session):
    """Integration test for team → project creation."""
    # Create team
    team = get_or_create_team(postgres_db, "Platform Team")
    
    # Create project under team
    project = get_or_create_project(
        postgres_db,
        "API Gateway",
        team
    )
    
    # Verify foreign key relationship
    assert project.team_id == team.team_id
    assert project.team.team_name == "Platform Team"

# test_view_aggregation.py
def test_dora_metrics_view_calculation(postgres_db: Session):
    """Integration test for DORA metrics aggregation view."""
    # Create test data
    create_deployments(postgres_db, project_id=1, count=10)
    
    # Query aggregated view
    result = postgres_db.execute(
        "SELECT * FROM dora_metrics_summary WHERE project_id = 1"
    ).fetchone()
    
    assert result.successful_deployments == 8
    assert result.change_failure_rate_percent == 20.0
```

**Coverage Target:** All critical database operations, view calculations

#### 3b. API Integration (Flow Testing)

**Definition:** Test chained API calls simulating real workflows.

**Characteristics:**
- Multiple API calls in sequence
- Validate data propagation across endpoints
- Test state management
- Use real or test database

**Examples:**
```python
# test_deployment_flow.py
def test_deployment_to_dora_metrics_flow(client: TestClient):
    """
    API Flow: POST deployments → GET DORA metrics
    Validates end-to-end deployment tracking workflow.
    """
    project = "API Gateway"
    
    # Step 1: Create successful deployment
    client.post("/api/v1/deployments", json={
        "project_name": project,
        "successful": True,
        "lead_time_hours": 2.0
    })
    
    # Step 2: Create failed deployment
    client.post("/api/v1/deployments", json={
        "project_name": project,
        "successful": False,
        "lead_time_hours": 1.5
    })
    
    # Step 3: Retrieve DORA metrics
    response = client.get(f"/api/v1/dora-metrics?project_name={project}")
    
    # Step 4: Validate aggregation
    data = response.json()[0]
    assert data["successful_deployments"] == 1
    assert data["change_failure_rate_percent"] == 50.0
    assert data["avg_lead_time_hours"] == 1.75

# test_defect_lifecycle.py
def test_defect_creation_to_trends_flow(client: TestClient):
    """
    API Flow: POST defects → GET defect trends
    Validates defect tracking and trend calculation.
    """
    # Step 1: Create high-priority defect
    client.post("/api/v1/defects", json={
        "project_name": "User Service",
        "defect_id": "BUG-123",
        "priority": "high",
        "status": "open"
    })
    
    # Step 2: Create and resolve medium-priority defect
    client.post("/api/v1/defects", json={
        "project_name": "User Service",
        "defect_id": "BUG-124",
        "priority": "medium",
        "status": "resolved",
        "resolution_time_hours": 48.0
    })
    
    # Step 3: Get defect trends
    response = client.get("/api/v1/defect-trends?project_name=User Service")
    
    # Step 4: Validate calculations
    trends = response.json()[0]
    assert trends["defects_created"] == 2
    assert trends["high_priority_defects"] == 1
    assert trends["avg_resolution_time_hours"] == 48.0
```

**Coverage Target:** All critical user workflows, 80%+ of API combinations

---

### 4. End-to-End (E2E) Tests

**Definition:** Test complete business scenarios from end-user perspective.

**Characteristics:**
- Full system integration
- Real database, real services
- Simulate production scenarios
- Performance validation
- Slowest execution (1-10s per test)

**Examples:**
```python
# test_cicd_pipeline_simulation.py
def test_complete_cicd_tracking_workflow():
    """
    E2E: Simulate a complete CI/CD pipeline tracking scenario.
    
    Workflow:
    1. Team deploys to production (3 successful, 1 failed)
    2. QA reports defects found in production
    3. Coverage metrics are updated
    4. Dashboard queries all metrics
    """
    project = "Payment Service"
    team = "Backend Team"
    
    # Simulate 1 week of deployments
    for day in range(7):
        for deployment in range(3):
            client.post("/api/v1/deployments", json={
                "project_name": project,
                "team_name": team,
                "successful": deployment < 2,  # 2 success, 1 fail per day
                "lead_time_hours": random.uniform(1.0, 4.0)
            })
    
    # Simulate defects from production issues
    for defect_num in range(5):
        client.post("/api/v1/defects", json={
            "project_name": project,
            "defect_id": f"PROD-{defect_num}",
            "priority": "high" if defect_num < 2 else "medium",
            "status": "open"
        })
    
    # Simulate weekly coverage report
    client.post("/api/v1/coverage", json={
        "project_name": project,
        "line_coverage": 85.5,
        "branch_coverage": 78.0
    })
    
    # Validate complete dashboard query
    dora = client.get(f"/api/v1/dora-metrics?project_name={project}")
    defects = client.get(f"/api/v1/defect-trends?project_name={project}")
    coverage = client.get(f"/api/v1/coverage-trends?project_name={project}")
    
    # Assertions for complete workflow
    assert dora.status_code == 200
    assert len(dora.json()) > 0
    assert defects.json()[0]["defects_created"] == 5
    assert coverage.json()[0]["avg_line_coverage"] == 85.5

# test_multi_team_scenario.py
def test_multi_team_multi_project_scenario():
    """E2E: Validate platform handles multiple teams and projects."""
    teams = ["Platform", "Backend", "Frontend"]
    projects = {
        "Platform": ["API Gateway", "Auth Service"],
        "Backend": ["User Service", "Payment Service"],
        "Frontend": ["Web Dashboard", "Mobile App"]
    }
    
    # Each team creates projects and metrics
    for team, team_projects in projects.items():
        for project in team_projects:
            # Ingest various metrics
            client.post("/api/v1/deployments", json={
                "project_name": project,
                "team_name": team,
                "successful": True
            })
    
    # Validate cross-team aggregations work
    all_dora = client.get("/api/v1/dora-metrics")
    assert len(all_dora.json()) == 6  # 6 projects total
```

**Coverage Target:** 5-10 critical business scenarios

---

## Test Organization

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures (SQLite, PostgreSQL, TestClient)
│
├── unit/                          # Unit tests (20%)
│   ├── __init__.py
│   ├── conftest.py               # Unit-specific fixtures
│   ├── test_crud_unit.py         # CRUD logic without DB
│   ├── test_validators.py        # Validation functions
│   └── test_calculations.py      # Business logic calculations
│
├── component/                     # Component tests (40%)
│   ├── __init__.py
│   ├── conftest.py               # Component fixtures (TestClient + SQLite)
│   ├── test_health_endpoint.py
│   ├── test_deployment_endpoint.py
│   ├── test_defect_endpoint.py
│   ├── test_coverage_endpoint.py
│   ├── test_dora_metrics_endpoint.py
│   ├── test_defect_trends_endpoint.py
│   └── test_coverage_trends_endpoint.py
│
├── integration/
│   ├── __init__.py
│   ├── conftest.py               # Integration fixtures (PostgreSQL)
│   │
│   ├── code/                     # Code-level integration (15%)
│   │   ├── __init__.py
│   │   ├── test_crud_db_integration.py
│   │   ├── test_view_aggregation.py
│   │   └── test_team_project_workflow.py
│   │
│   └── api/                      # API flow integration (15%)
│       ├── __init__.py
│       ├── test_deployment_flow.py
│       ├── test_defect_lifecycle.py
│       ├── test_coverage_workflow.py
│       └── test_cross_metric_consistency.py
│
└── e2e/                          # End-to-end tests (10%)
    ├── __init__.py
    ├── conftest.py               # E2E fixtures (full stack)
    ├── test_cicd_pipeline_simulation.py
    ├── test_multi_team_scenario.py
    ├── test_performance.py
    └── test_api_contracts.py
```

### Migration Path

**Current State:** Tests are in flat `tests/` directory, mostly component-level.

**Migration Steps:**
1. Create new directory structure
2. Move existing tests to appropriate layers:
   - `test_health.py` → `component/test_health_endpoint.py`
   - `test_deployments.py` → `component/test_deployment_endpoint.py`
   - `test_crud.py` → `unit/test_crud_unit.py` + `integration/code/test_crud_db_integration.py`
3. Update imports and fixture references
4. Add new integration and E2E tests
5. Update CI/CD pipeline configuration

---

## API Testing Strategy

### API Flow Testing Principles

Since the Quality Metrics Platform is API-driven, testing API workflows and chaining is critical.

#### 1. **Identify Critical Flows**

**Flow 1: Deployment Tracking**
```
POST /deployments → POST /deployments → GET /dora-metrics
```

**Flow 2: Defect Lifecycle**
```
POST /defects (open) → POST /defects (resolved) → GET /defect-trends
```

**Flow 3: Coverage Evolution**
```
POST /coverage (week1) → POST /coverage (week2) → GET /coverage-trends
```

**Flow 4: Cross-Metric Dashboard**
```
POST /deployments + POST /defects + POST /coverage → 
GET /dora-metrics + GET /defect-trends + GET /coverage-trends
```

#### 2. **State Management**

- **Stateless Tests:** Each test creates its own data, cleans up after
- **Shared State:** Use fixtures for common setup, but reset between tests
- **Database Isolation:** Use transactions or separate test databases

#### 3. **Validation Points**

For each flow, validate:
1. **HTTP Status Codes:** 200, 201, 400, 404, 422, 500
2. **Response Schemas:** Pydantic validation
3. **Data Consistency:** Data persists correctly across calls
4. **Aggregations:** Calculated metrics are accurate
5. **Error Handling:** Invalid data, missing resources

#### 4. **API Chaining Patterns**

**Pattern 1: Create → Retrieve**
```python
def test_create_then_retrieve():
    # Create resource
    create_resp = client.post("/api/v1/deployments", json=payload)
    deployment_id = create_resp.json()["id"]
    
    # Retrieve and validate
    get_resp = client.get(f"/api/v1/deployments/{deployment_id}")
    assert get_resp.json() == create_resp.json()
```

**Pattern 2: Multiple Creates → Aggregate Query**
```python
def test_multiple_creates_aggregate():
    # Create multiple resources
    for i in range(10):
        client.post("/api/v1/deployments", json=deployment_payload(i))
    
    # Query aggregated data
    aggregate = client.get("/api/v1/dora-metrics")
    assert len(aggregate.json()) == 10
```

**Pattern 3: Update → Verify State Change**
```python
def test_state_transition():
    # Create open defect
    create_resp = client.post("/api/v1/defects", json={
        "defect_id": "BUG-1",
        "status": "open"
    })
    
    # Resolve defect
    update_resp = client.put(f"/api/v1/defects/BUG-1", json={
        "status": "resolved"
    })
    
    # Verify trends reflect resolution
    trends = client.get("/api/v1/defect-trends")
    assert trends.json()[0]["resolved_defects"] == 1
```

---

## Test Data Management

### 1. **Fixture Strategy**

**Shared Fixtures (conftest.py):**
```python
@pytest.fixture(scope="function")
def test_db():
    """SQLite in-memory DB for component tests."""
    # Create fresh DB per test
    
@pytest.fixture(scope="function")
def postgres_db():
    """PostgreSQL DB for integration tests."""
    # Use Docker PostgreSQL, transaction rollback per test

@pytest.fixture
def client(test_db):
    """FastAPI TestClient with SQLite."""
    
@pytest.fixture
def postgres_client(postgres_db):
    """FastAPI TestClient with PostgreSQL."""
```

**Test-Specific Fixtures:**
```python
@pytest.fixture
def sample_team(test_db):
    """Pre-created team for tests."""
    
@pytest.fixture
def sample_project(test_db, sample_team):
    """Pre-created project for tests."""
    
@pytest.fixture
def deployment_batch(test_db, sample_project):
    """Batch of deployment records for aggregation tests."""
```

### 2. **Data Builders**

Use builder pattern for complex test data:

```python
# test_builders.py
class DeploymentBuilder:
    def __init__(self):
        self.data = {
            "project_name": "Test Project",
            "successful": True,
            "lead_time_hours": 2.0
        }
    
    def with_project(self, name):
        self.data["project_name"] = name
        return self
    
    def failed(self):
        self.data["successful"] = False
        return self
    
    def with_lead_time(self, hours):
        self.data["lead_time_hours"] = hours
        return self
    
    def build(self):
        return self.data

# Usage in tests
def test_failed_deployment():
    payload = (DeploymentBuilder()
        .with_project("API Gateway")
        .failed()
        .with_lead_time(5.0)
        .build())
    
    response = client.post("/api/v1/deployments", json=payload)
    assert response.json()["successful"] is False
```

### 3. **Database Seeding**

For integration/E2E tests, use seed data:

```python
# tests/integration/conftest.py
@pytest.fixture(scope="module")
def seeded_db():
    """PostgreSQL with realistic seed data."""
    db = create_postgres_db()
    seed_teams(db, count=3)
    seed_projects(db, count=10)
    seed_metrics(db, days=30)
    return db
```

### 4. **Cleanup Strategy**

- **Unit/Component:** Automatic cleanup via SQLite in-memory (destroyed after test)
- **Integration:** Use database transactions, rollback after test
- **E2E:** Use separate test database, truncate tables after suite

---

## Testing Standards

### 1. **Naming Conventions**

**Test Files:**
- `test_<module>_unit.py` - Unit tests
- `test_<feature>_endpoint.py` - Component tests
- `test_<feature>_integration.py` - Integration tests
- `test_<scenario>_e2e.py` - E2E tests

**Test Functions:**
```python
# Good
def test_create_deployment_success()
def test_create_deployment_missing_project_name()
def test_dora_metrics_calculation_with_failures()

# Bad
def test_deployment()
def test_1()
def testDeployment()
```

**Pattern:** `test_<what>_<condition>_<expected>`

### 2. **Test Structure (AAA Pattern)**

```python
def test_deployment_flow():
    # ARRANGE - Set up test data
    project = "API Gateway"
    payload = {"project_name": project, "successful": True}
    
    # ACT - Execute the operation
    response = client.post("/api/v1/deployments", json=payload)
    
    # ASSERT - Verify the outcome
    assert response.status_code == 201
    assert response.json()["project_name"] == project
```

### 3. **Assertion Guidelines**

- **Specific:** Assert exact values, not just truthiness
- **Multiple:** Break complex assertions into multiple checks
- **Meaningful:** Use descriptive failure messages

```python
# Good
assert response.status_code == 201, "Deployment creation should return 201"
assert "id" in data, "Response should include deployment ID"
assert data["successful"] is True, "Deployment should be marked successful"

# Bad
assert response.ok
assert data
```

### 4. **Documentation Standards**

```python
def test_deployment_to_dora_flow():
    """
    Test API flow: deployment ingestion to DORA metrics retrieval.
    
    Workflow:
    1. Create 2 successful deployments
    2. Create 1 failed deployment
    3. Query DORA metrics
    4. Validate failure rate = 33.33%
    
    Validates:
    - Data propagation from ingestion to aggregation
    - Change failure rate calculation
    - Date-based filtering
    """
```

---

## Tools & Frameworks

### Primary Stack

| Purpose | Tool | Version | Usage |
|---------|------|---------|-------|
| Test Runner | pytest | 7.4+ | All test levels |
| API Testing | FastAPI TestClient | 0.104+ | Component, Integration |
| HTTP Client | requests | 2.31+ | E2E tests |
| Database | SQLite (test), PostgreSQL (integration) | - | Test isolation |
| Fixtures | pytest fixtures | - | Test data setup |
| Coverage | pytest-cov | 4.1+ | Code coverage |
| Mutation | Cosmic Ray | 8.3+ | Test quality |

### Additional Tools

| Purpose | Tool | When to Use |
|---------|------|-------------|
| API Contract Testing | Schemathesis | Validate OpenAPI compliance |
| Performance Testing | pytest-benchmark | Response time validation |
| Load Testing | Locust | Concurrent user simulation |
| Test Data | Faker | Generate realistic test data |
| Mocking | pytest-mock | Mock external dependencies |
| Parameterization | pytest.mark.parametrize | Test multiple inputs |

### Tool Selection Criteria

- **pytest:** Industry standard, excellent fixture system, extensive plugin ecosystem
- **TestClient:** Built into FastAPI, perfect for component tests, no network overhead
- **requests:** Real HTTP calls for E2E, validates full stack
- **SQLite:** Fast in-memory DB for isolated component tests
- **PostgreSQL:** Real DB for integration tests, validates production behavior

---

## CI/CD Integration

### Test Execution Strategy

#### Local Development
```bash
# Run all tests
pytest

# Run specific level
pytest tests/unit/
pytest tests/component/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run fast tests only (unit + component)
pytest -m "not slow"

# Run integration tests with PostgreSQL
docker-compose up -d
pytest tests/integration/
```

#### CI Pipeline (GitHub Actions Example)

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-component:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit + component tests
        run: pytest tests/unit/ tests/component/ --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
      - name: Run integration tests
        run: pytest tests/integration/
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Run E2E tests
        run: pytest tests/e2e/ --maxfail=1
      - name: Cleanup
        run: docker-compose down
```

#### Test Execution Time Budget

| Level | Time Budget | Frequency |
|-------|-------------|-----------|
| Unit | < 5 seconds | Every commit |
| Component | < 30 seconds | Every commit |
| Integration (code) | < 2 minutes | Every commit |
| Integration (API) | < 3 minutes | Every PR |
| E2E | < 5 minutes | Pre-merge |
| Full Suite | < 10 minutes | Post-merge |

### Failure Handling

- **Unit/Component Failure:** Block PR merge
- **Integration Failure:** Block PR merge, investigate immediately
- **E2E Failure:** Review before merge, may proceed if non-critical
- **Performance Regression:** Warning, investigate before next release

---

## Coverage & Quality Metrics

### Coverage Targets

| Level | Line Coverage | Branch Coverage | Mutation Score |
|-------|---------------|-----------------|----------------|
| Unit | 95%+ | 90%+ | 80%+ |
| Component | 100% (endpoints) | 95%+ | 75%+ |
| Integration | 90%+ | 85%+ | - |
| Overall | 95%+ | 100% |

### Coverage Reports

```bash
# Generate all coverage formats
pytest --cov=src \
  --cov-report=term-missing \
  --cov-report=html:coverage_html \
  --cov-report=xml:coverage.xml \
  --cov-report=json:coverage.json

# View HTML report
open coverage_html/index.html
```

### Quality Gates

**Pre-Commit:**
- All unit + component tests pass
- No linter errors

**Pre-Push:**
- All tests pass (unit + component + integration)
- Coverage > 95%

**Pre-Merge:**
- All tests pass (including E2E)
- Coverage > 95%
- Mutation score > 75%
- No critical security vulnerabilities

**Release:**
- All quality gates passed
- Performance benchmarks met
- API contract tests passed

### Mutation Testing

```bash
# Initialize mutation testing
cosmic-ray init cosmic-ray.toml mutation-tests/session.sqlite

# Execute mutations
cosmic-ray exec cosmic-ray.toml mutation-tests/session.sqlite

# Generate report
cr-report mutation-tests/session.sqlite > mutation-tests/report.json

# Summarize survivors
python tools/cosmic_ray_summarize.py mutation-tests/report.json
```

**Mutation Score Target:** 75%+ (indicates test quality, not just coverage)

---

## Appendix

### A. Test Examples by Type

See `/tests/` directory for complete implementations.

### B. Troubleshooting

**Issue:** Tests fail locally but pass in CI
- **Solution:** Check environment variables, database state, timezone differences

**Issue:** Slow test execution
- **Solution:** Profile tests with `pytest --durations=10`, parallelize with `pytest-xdist`

**Issue:** Flaky tests
- **Solution:** Identify non-deterministic behavior (random data, timing), fix or mark as `@pytest.mark.flaky`

### C. References

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://testingpython.com/)
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)

---

**Document Owners:** QE Architecture Team  
**Review Cycle:** Quarterly  
**Next Review:** June 2026