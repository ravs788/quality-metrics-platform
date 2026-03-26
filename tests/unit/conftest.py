"""
Unit test fixtures.

Provides mocked dependencies and test data for unit tests.
Unit tests should not depend on database or external services.
"""

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests."""
    mock_session = MagicMock()
    return mock_session


@pytest.fixture
def sample_team_data():
    """Sample team data for unit tests."""
    return {
        "team_id": 1,
        "team_name": "Test Team",
        "team_lead": "Test Lead"
    }


@pytest.fixture
def sample_project_data():
    """Sample project data for unit tests."""
    return {
        "project_id": 1,
        "project_name": "Test Project",
        "team_id": 1,
        "repository_url": "https://github.com/test/repo"
    }


@pytest.fixture
def sample_deployment_data():
    """Sample deployment data for unit tests."""
    return {
        "project_name": "API Gateway",
        "team_name": "Platform Team",
        "successful": True,
        "lead_time_hours": 2.5,
        "metric_date": "2026-03-25"
    }