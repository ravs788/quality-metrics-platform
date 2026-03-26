"""
Component test fixtures.

Provides FastAPI TestClient with SQLite in-memory database for component tests.
Component tests validate individual API endpoints in isolation.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.database import Base, get_db
from src.main import app
from src.models.db_models import Team, Project


# Use in-memory SQLite for component tests
COMPONENT_TEST_DATABASE_URL = "sqlite:///./component_test.db"


@pytest.fixture(scope="function")
def component_db():
    """Create a fresh SQLite database for each component test."""
    engine = create_engine(
        COMPONENT_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def component_client(component_db):
    """Create a test client with SQLite database for component tests."""
    def override_get_db():
        try:
            yield component_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_team(component_db):
    """Create a sample team for component tests."""
    team = Team(team_name="Component Test Team", team_lead="Test Lead")
    component_db.add(team)
    component_db.commit()
    component_db.refresh(team)
    return team


@pytest.fixture
def sample_project(component_db, sample_team):
    """Create a sample project for component tests."""
    project = Project(
        project_name="Component Test Project",
        team_id=sample_team.team_id,
        repository_url="https://github.com/test/component-repo"
    )
    component_db.add(project)
    component_db.commit()
    component_db.refresh(project)
    return project