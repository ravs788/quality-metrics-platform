"""
Pytest fixtures for testing Quality Metrics Platform.

Provides database setup, test client, and common test data.
"""

import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Ensure repo root is on sys.path for VSCode pytest discovery
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.database import Base, get_db
from src.main import app
from src.models.db_models import Team, Project

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    engine = create_engine(
        TEST_DATABASE_URL,
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
def client(test_db):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_team(test_db):
    """Create a sample team for testing."""
    team = Team(team_name="Test Team", team_lead="Test Lead")
    test_db.add(team)
    test_db.commit()
    test_db.refresh(team)
    return team


@pytest.fixture
def sample_project(test_db, sample_team):
    """Create a sample project for testing."""
    project = Project(
        project_name="Test Project",
        team_id=sample_team.team_id,
        repository_url="https://github.com/test/repo"
    )
    test_db.add(project)
    test_db.commit()
    test_db.refresh(project)
    return project
