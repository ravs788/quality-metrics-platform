"""
End-to-End (E2E) test fixtures.

Provides full stack setup for E2E tests.
E2E tests simulate real user scenarios with complete system integration.
"""

import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database import Base, get_db
from src.main import app


# Use PostgreSQL for E2E tests (requires Docker container running)
E2E_DATABASE_URL = os.getenv(
    "E2E_DATABASE_URL",
    "postgresql://postgres:mysecretpassword@localhost:5432/quality_metrics_e2e_test"
)


@pytest.fixture(scope="module")
def e2e_db_engine():
    """Create database engine for E2E tests (module scope)."""
    engine = create_engine(E2E_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup after all E2E tests in module.
    # Views in schema.sql depend on tables, so drop schema objects with CASCADE.
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


@pytest.fixture(scope="function")
def e2e_db(e2e_db_engine):
    """
    Create a database session for E2E tests.
    Truncates tables before each test for clean state.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=e2e_db_engine)
    db = TestingSessionLocal()
    
    # Clean all tables before test
    tables = ["coverage_metrics", "defect_metrics", "deployment_metrics", "projects", "teams"]
    for table in tables:
        db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    db.commit()
    
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def e2e_client(e2e_db):
    """Create a test client for E2E tests with real PostgreSQL database."""
    def override_get_db():
        try:
            yield e2e_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def e2e_test_data(e2e_db):
    """
    Seed realistic test data for E2E scenarios.
    Returns dict with created entities for use in tests.
    """
    from src.models.db_models import Team, Project
    from datetime import date, timedelta
    
    # Create teams
    teams = [
        Team(team_name="Platform Engineering", team_lead="Alice Johnson"),
        Team(team_name="Backend Services", team_lead="Bob Smith"),
        Team(team_name="Frontend Experience", team_lead="Carol White")
    ]
    for team in teams:
        e2e_db.add(team)
    e2e_db.commit()
    
    # Create projects
    projects = [
        Project(project_name="API Gateway", team_id=teams[0].team_id, repository_url="https://github.com/test/api-gateway"),
        Project(project_name="User Service", team_id=teams[1].team_id, repository_url="https://github.com/test/user-service"),
        Project(project_name="Web Dashboard", team_id=teams[2].team_id, repository_url="https://github.com/test/web-dashboard"),
    ]
    for project in projects:
        e2e_db.add(project)
    e2e_db.commit()
    
    return {
        "teams": teams,
        "projects": projects
    }