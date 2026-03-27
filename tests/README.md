# Quality Metrics Platform - Test Suite

Comprehensive test suite following the test pyramid strategy.

## Current Snapshot (March 27, 2026)

- **Total tests:** 106
- **Overall coverage (`src/`):** 100% (563 statements, 0 missed)
- **Layer distribution:**
  - Unit: 36 tests
  - Component: 40 tests
  - Integration: 17 API + 11 code
  - E2E: 2 tests

## Test Structure

```
tests/
├── unit/                  # Unit tests (isolated, mocked dependencies)
├── component/             # Component tests (API endpoints with test doubles)
├── integration/
│   ├── code/             # Code-level integration (CRUD + DB)
│   └── api/              # API integration (chained workflows)
└── e2e/                  # End-to-end tests (complete scenarios)
```

## Quick Start

### Run All Tests
```bash
pytest
```

### Run by Test Level

```bash
# Unit tests only (fast)
pytest tests/unit/

# Component tests (API endpoints)
pytest tests/component/

# Integration tests (requires PostgreSQL)
pytest tests/integration/

# E2E tests (full system)
pytest tests/e2e/
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=term-missing --cov-report=html:coverage_html

# View HTML report
open coverage_html/index.html
```

## Prerequisites

### Unit & Component Tests
- Python 3.9+
- Dependencies from `requirements.txt`
- No external services required (uses SQLite in-memory)

### Integration & E2E Tests
- PostgreSQL running (via Docker Compose)
- Test databases created

#### Start PostgreSQL
```bash
# Start PostgreSQL
docker-compose up -d

# Create integration test database
docker exec -it postgres-local psql -U postgres -c "CREATE DATABASE quality_metrics_integration_test;"

# Create E2E test database
docker exec -it postgres-local psql -U postgres -c "CREATE DATABASE quality_metrics_e2e_test;"

# Apply schema to test databases
docker exec -i postgres-local psql -U postgres -d quality_metrics_integration_test < database/schema.sql
docker exec -i postgres-local psql -U postgres -d quality_metrics_e2e_test < database/schema.sql
```

## Test Levels Explained

### Unit Tests (`tests/unit/`)
**Purpose:** Test individual functions/methods in isolation

**Characteristics:**
- Use mocked dependencies
- Very fast (< 1ms per test)
- No database or external services

**Example:**
```python
def test_calculate_change_failure_rate(mock_db_session):
    result = calculate_failure_rate(successful=85, failed=15)
    assert result == 15.0
```

### Component Tests (`tests/component/`)
**Purpose:** Test API endpoints with test doubles

**Characteristics:**
- Use FastAPI TestClient
- SQLite in-memory database
- Test single endpoint behavior
- Fast (< 100ms per test)

**Example:**
```python
def test_create_deployment_success(component_client):
    response = component_client.post("/api/v1/deployments", json={
        "project_name": "API Gateway",
        "successful": True
    })
    assert response.status_code == 201
```

### Integration Tests

#### Code-Level Integration (`tests/integration/code/`)
**Purpose:** Test module interactions with real database

**Characteristics:**
- Real PostgreSQL database
- Test CRUD + Database + Models together
- Transaction rollback for cleanup
- Moderate speed (< 1s per test)

**Example:**
```python
def test_team_project_workflow(postgres_db):
    team = get_or_create_team(postgres_db, "Platform Team")
    project = get_or_create_project(postgres_db, "API Gateway", team)
    assert project.team_id == team.team_id
```

#### API Integration (`tests/integration/api/`)
**Purpose:** Test API chaining and workflows

**Characteristics:**
- Multiple API calls in sequence
- Real or test database
- Validate data propagation
- Test API flows

**Example:**
```python
def test_deployment_to_dora_flow(postgres_client):
    # POST deployments
    postgres_client.post("/api/v1/deployments", json={...})
    
    # GET DORA metrics
    response = postgres_client.get("/api/v1/dora-metrics")
    
    # Validate aggregation
    assert response.json()[0]["successful_deployments"] == 1
```

### E2E Tests (`tests/e2e/`)
**Purpose:** Test complete business scenarios

**Characteristics:**
- Full system integration
- Real PostgreSQL database
- Simulate production workflows
- Slowest (1-10s per test)

**Example:**
```python
def test_cicd_pipeline_simulation(e2e_client):
    # Simulate 1 week of deployments
    # Create defects
    # Update coverage
    # Query all metrics
    # Validate complete workflow
```

## Running Specific Test Categories

### Fast Tests Only (Unit + Component)
```bash
pytest tests/unit/ tests/component/ -v
```

### Integration Tests Only
```bash
# Requires PostgreSQL running
pytest tests/integration/ -v
```

### API Flow Tests
```bash
pytest tests/integration/api/ -v
```

### Smoke Test (Critical Flows)
```bash
pytest -m "smoke" -v
```

## Test Markers

Mark tests with pytest markers for selective execution:

```python
@pytest.mark.smoke
def test_critical_workflow():
    # Critical test that should always pass
    pass

@pytest.mark.slow
def test_performance_benchmark():
    # Slow test, skip in fast runs
    pass
```

Run marked tests:
```bash
pytest -m "smoke"          # Run only smoke tests
pytest -m "not slow"       # Skip slow tests
```

## Debugging Tests

### Run Single Test
```bash
pytest tests/integration/api/test_deployment_flow.py::TestDeploymentToDoraMetricsFlow::test_single_deployment_to_dora_metrics -v
```

### Show Print Statements
```bash
pytest -s tests/unit/
```

### Drop into Debugger on Failure
```bash
pytest --pdb tests/integration/
```

### Show Test Durations
```bash
pytest --durations=10
```

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- Every push to main
- Every pull request
- Pre-merge validation

Test stages:
1. **Unit + Component** (< 30s)
2. **Integration** (< 5 min)
3. **E2E** (< 5 min)

See `.github/workflows/test.yml` for configuration.

## Troubleshooting

### Issue: Integration tests fail with connection error
**Solution:** Ensure PostgreSQL is running and test databases exist
```bash
docker-compose up -d
docker exec -it postgres-local psql -U postgres -l  # List databases
```

### Issue: Tests fail with "Database already exists"
**Solution:** The test databases should already exist. If you need to recreate:
```bash
docker exec -it postgres-local psql -U postgres -c "DROP DATABASE IF EXISTS quality_metrics_integration_test;"
docker exec -it postgres-local psql -U postgres -c "CREATE DATABASE quality_metrics_integration_test;"
```

### Issue: Tests are slow
**Solution:** 
- Run only unit/component tests: `pytest tests/unit/ tests/component/`
- Use pytest-xdist for parallel execution: `pytest -n auto`

### Issue: Flaky test failures
**Solution:**
- Check for timing issues (add explicit waits)
- Check for test data conflicts (ensure proper isolation)
- Use `pytest --lf` to rerun only failed tests

## Coverage Targets

| Level | Target | Current |
|-------|--------|---------|
| Unit | 95%+ | 100% (covered modules) |
| Component | 100% (endpoints) | Met |
| Integration | 90%+ | Met |
| Overall | 95%+ | 100% |

## Best Practices

1. **Test Independence:** Each test should be runnable in isolation
2. **Clean State:** Tests should not depend on each other
3. **Clear Names:** Test names should describe what they test
4. **AAA Pattern:** Arrange, Act, Assert
5. **One Assertion Focus:** Test one thing at a time
6. **Fast Feedback:** Keep unit/component tests fast

## Additional Resources

- [Test Strategy Document](../docs/test-strategy/strategy.md)
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Maintained by:** QE Architecture Team  
**Last Updated:** March 27, 2026