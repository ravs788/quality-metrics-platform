"""
Integration test fixtures.

Provides PostgreSQL database connections for integration tests.
Integration tests validate interactions between multiple modules and real database operations.
"""

import pytest
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database import Base, get_db
from src.main import app
from src.models.db_models import Team, Project


# Use PostgreSQL for integration tests (requires Docker container running)
INTEGRATION_DATABASE_URL = os.getenv(
    "INTEGRATION_DATABASE_URL",
    "postgresql://postgres:mysecretpassword@localhost:5432/quality_metrics_integration_test"
)


@pytest.fixture(scope="function")
def postgres_db():
    """
    Create a PostgreSQL database session for integration tests.
    Uses transaction rollback for test isolation.
    """
    engine = create_engine(INTEGRATION_DATABASE_URL)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Ensure clean state before each test
    tables = ["coverage_metrics", "defect_metrics", "deployment_metrics", "projects", "teams"]
    for table in tables:
        db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    db.commit()
    
    try:
        yield db
    finally:
        # Cleanup after each test (tests may call commit)
        for table in tables:
            db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        db.commit()
        db.close()


@pytest.fixture(scope="function")
def postgres_client(postgres_db):
    """Create a test client with PostgreSQL database for integration tests."""
    def override_get_db():
        try:
            yield postgres_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def integration_team(postgres_db):
    """Create a sample team for integration tests."""
    team = Team(team_name="Integration Test Team", team_lead="Integration Lead")
    postgres_db.add(team)
    postgres_db.commit()
    postgres_db.refresh(team)
    return team


@pytest.fixture
def integration_project(postgres_db, integration_team):
    """Create a sample project for integration tests."""
    project = Project(
        project_name="Integration Test Project",
        team_id=integration_team.team_id,
        repository_url="https://github.com/test/integration-repo"
    )
    postgres_db.add(project)
    postgres_db.commit()
    postgres_db.refresh(project)
    return project


@pytest.fixture(scope="function")
def clean_postgres_db(postgres_db):
    """
    Provides a clean PostgreSQL database by truncating all tables.
    Use for tests that need a completely clean state.
    """
    # Truncate all tables
    tables = ["coverage_metrics", "defect_metrics", "deployment_metrics", "projects", "teams"]
    for table in tables:
        postgres_db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    postgres_db.commit()
    
    yield postgres_db