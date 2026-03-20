"""
Unit tests for coverage trends summary endpoint.
"""

from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.crud import create_coverage_metric


class TestCoverageTrendsEndpoint:
    """Test GET /api/v1/coverage-trends endpoint."""
    
    def test_get_coverage_trends_empty(self, client: TestClient):
        """Test retrieving coverage trends when no data exists."""
        response = client.get("/api/v1/coverage-trends")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_coverage_trends_with_data(self, client: TestClient, test_db: Session):
        """Test retrieving coverage trends with data."""
        # Create some coverage metrics
        create_coverage_metric(
            db=test_db,
            project_name="Web Dashboard",
            team_name="Frontend Team",
            week_start=date(2026, 3, 17),
            line_coverage_percent=85.5,
            branch_coverage_percent=78.3,
        )
        
        create_coverage_metric(
            db=test_db,
            project_name="Web Dashboard",
            team_name="Frontend Team",
            week_start=date(2026, 3, 17),
            line_coverage_percent=87.0,
            branch_coverage_percent=80.0,
        )
        
        response = client.get("/api/v1/coverage-trends")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify structure
        first_item = data[0]
        assert "project_id" in first_item
        assert "project_name" in first_item
        assert "week_start" in first_item
        assert "avg_line_coverage" in first_item
        assert "avg_branch_coverage" in first_item
        assert "max_line_coverage" in first_item
        assert "min_line_coverage" in first_item
